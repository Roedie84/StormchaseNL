"""Neerslagverwachting voor Stormchase.

Gebruikt bij voorkeur de neerslagtekst van Buienradar: die geeft per vijf
minuten een verwachting voor de komende twee uur, op exacte coordinaten.
Dat is nauwkeurig genoeg voor een melding als "over tien minuten regen".

Buiten het radarbereik van Buienradar valt hij terug op de kwartierwaarden
van Open-Meteo. Grover, maar wereldwijd beschikbaar.

0.49.0: in Nederland eerst de neerslagverwachting van het KNMI zelf (de API
achter de KNMI-app, per radarcel van een vierkante kilometer, met exacte
UTC-tijdstempels). Buienradar is dan de terugval, Open-Meteo de laatste.
De reeks heeft dezelfde vorm, dus buienreeks, conditie en weerentiteit
werken ongewijzigd.
"""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    BUIENRADAR_URL,
    CONF_RAIN_LEAD,
    CONF_RAIN_THRESHOLD,
    DEFAULT_RAIN_LEAD,
    DEFAULT_RAIN_THRESHOLD,
    EVENT_RAIN_INCOMING,
    METEO_URL,
    RAIN_INTERVAL,
)
from .buienreeks import lees_reeks
from .knmi_api import NietGevonden, poging, vijf_minuten_slot
from .knmi_grid import radarcel
from .knmi_verwerk import nowcast_reeks
from .coordinator import LocationMixin
from .herpoging import HerpogingMixin
from .verouderd import VerouderdMixin

_LOGGER = logging.getLogger(__name__)


def _naar_mmu(waarde: int) -> float:
    """Zet een Buienradar-waarde om naar millimeter per uur.

    De schaal is logaritmisch; dit is de omrekening die Buienradar zelf
    documenteert. Waarde 0 betekent droog.
    """
    if waarde <= 0:
        return 0.0
    return round(10 ** ((waarde - 109) / 32), 2)


class RainCoordinator(HerpogingMixin, VerouderdMixin, LocationMixin, DataUpdateCoordinator[dict]):
    """Haalt de neerslagverwachting op en bepaalt wanneer het gaat regenen."""

    # Bronnen die na een storing een herkansing krijgen (0.43.0)
    _herpoging_bronnen = ("buienradar",)

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiseer de coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.title} regen",
            update_interval=RAIN_INTERVAL,
        )
        self.entry = entry
        self._session = async_get_clientsession(hass)
        self._was_verwacht: bool | None = None
        self.validatie = None  # wordt na het aanmaken gezet
        self.knmi = None  # KnmiBronnen, wordt na het aanmaken gezet

    @property
    def drempel(self) -> float:
        """Onder deze intensiteit noemen we het droog."""
        return float(self._opt(CONF_RAIN_THRESHOLD, DEFAULT_RAIN_THRESHOLD))

    @property
    def vooruit(self) -> int:
        """Hoeveel minuten vooruit we willen worden gewaarschuwd."""
        return int(self._opt(CONF_RAIN_LEAD, DEFAULT_RAIN_LEAD))

    async def _buienradar(self, latitude: float, longitude: float) -> list[tuple[int, float]]:
        """Haal de neerslagtekst op en zet hem om naar (minuten, mm/u).

        Het formaat is een regel per vijf minuten: 'waarde|HH:MM'.
        """
        url = f"{BUIENRADAR_URL}?lat={latitude:.2f}&lon={longitude:.2f}"

        async with async_timeout.timeout(15):
            response = await self._session.get(url)
            response.raise_for_status()
            tekst = await response.text()

        nu = dt_util.now()
        reeks: list[tuple[int, float]] = []

        for regel in tekst.strip().splitlines():
            regel = regel.strip()
            if "|" not in regel:
                continue

            ruw, _, stempel = regel.partition("|")
            try:
                uur, minuut = (int(x) for x in stempel.split(":"))
                waarde = int(ruw)
            except (ValueError, TypeError):
                continue

            moment = nu.replace(hour=uur, minute=minuut, second=0, microsecond=0)
            # De reeks loopt over middernacht heen; een tijdstip dat ruim
            # achter ons ligt hoort bij morgen.
            if (moment - nu) < timedelta(minutes=-30):
                moment += timedelta(days=1)

            minuten = int((moment - nu).total_seconds() // 60)
            reeks.append((minuten, _naar_mmu(waarde)))

        if not reeks:
            raise ValueError("lege of onleesbare neerslagtekst")

        return sorted(reeks)

    async def _open_meteo(self, latitude: float, longitude: float) -> list[tuple[int, float]]:
        """Terugval: kwartierwaarden van Open-Meteo."""
        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "minutely_15": "precipitation",
            "forecast_days": 1,
            "timezone": str(self.hass.config.time_zone),
        }

        async with async_timeout.timeout(20):
            response = await self._session.get(METEO_URL, params=params)
            response.raise_for_status()
            payload = await response.json()

        blok = payload.get("minutely_15") or {}
        tijden = blok.get("time") or []
        waarden = blok.get("precipitation") or []

        nu = dt_util.now()
        reeks: list[tuple[int, float]] = []

        for stempel, waarde in zip(tijden, waarden):
            if waarde is None:
                continue
            moment = dt_util.parse_datetime(stempel)
            if moment is None:
                continue
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=nu.tzinfo)

            minuten = int((moment - nu).total_seconds() // 60)
            if -15 <= minuten <= 120:
                # Open-Meteo geeft mm per kwartier; omrekenen naar mm/uur.
                reeks.append((max(minuten, 0), round(float(waarde) * 4, 2)))

        if not reeks:
            raise ValueError("geen kwartierdata beschikbaar")

        return sorted(reeks)

    async def _knmi_nowcast(self, latitude: float, longitude: float):
        """KNMI-neerslagverwachting, of None buiten Nederland of bij een fout."""
        knmi = self.knmi
        if knmi is None or not knmi.land.in_nederland(latitude, longitude):
            return None
        cel = radarcel(latitude, longitude)
        if cel is None:
            return None

        async def ophalen():
            slot = vijf_minuten_slot(dt_util.utcnow())
            try:
                grafiek = await knmi.app.neerslaggrafiek(cel, slot)
            except NietGevonden:
                # Het nieuwste vak staat er nog niet: het vorige dan
                grafiek = await knmi.app.neerslaggrafiek(
                    cel, slot - timedelta(minutes=5)
                )
            return nowcast_reeks(grafiek, dt_util.utcnow())

        stats = getattr(self, "stats", None)
        reeks, _ = await poging(
            knmi.afremming["nowcast"],
            stats.bronnen["knmi_nowcast"] if stats is not None else None,
            "neerslagverwachting",
            ophalen,
        )
        return reeks

    async def _haal_op(self) -> dict:
        """Bepaal of en wanneer het gaat regenen."""
        latitude, longitude, _ = self.resolve_location()

        stats = getattr(self, "stats", None)

        reeks = await self._knmi_nowcast(latitude, longitude)
        if reeks is not None:
            bron = "knmi"
            if stats is not None:
                stats.regen_via_knmi += 1
        else:
            reeks, bron = await self._buienradar_of_open_meteo(
                latitude, longitude, stats
            )

        return self._verwerk(reeks, bron)

    async def _buienradar_of_open_meteo(self, latitude, longitude, stats):
        """De bestaande route: Buienradar, en anders Open-Meteo."""
        bron = "buienradar"
        try:
            reeks = await self._buienradar(latitude, longitude)
            if stats is not None:
                stats.bronnen["buienradar"].succes()
                stats.regen_via_buienradar += 1
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Buienradar niet bruikbaar (%s), terugval Open-Meteo", err)
            if stats is not None:
                stats.bronnen["buienradar"].fout(err)
            bron = "open-meteo"
            try:
                reeks = await self._open_meteo(latitude, longitude)
                if stats is not None:
                    stats.regen_via_open_meteo += 1
            except (aiohttp.ClientError, TimeoutError, ValueError) as err2:
                return self.val_terug(err2), None
        return reeks, bron

    def _verwerk(self, reeks, bron) -> dict:
        """Lees de reeks en stel de gegevens samen."""
        if bron is None:
            # Alle bronnen faalden: val_terug gaf de vorige gegevens al terug
            return reeks

        drempel = self.drempel

        gelezen = lees_reeks(reeks, drempel)
        nu_intensiteit = gelezen["intensiteit"]
        regent = gelezen["regent"]
        begint_over = gelezen["begint_over"]
        stopt_over = gelezen["stopt_over"]

        toekomst = [mm for minuten, mm in reeks if 0 <= minuten <= 120]
        piek = max(toekomst) if toekomst else 0.0
        totaal = round(sum(toekomst) / 12, 2)  # mm/u per 5 min -> mm totaal

        data = {
            "bron": bron,
            "intensiteit": nu_intensiteit,
            "regent": regent,
            "begint_over": begint_over,
            "stopt_over": stopt_over,
            "volgende_bui_over": gelezen["volgende_bui_over"],
            "piek": piek,
            "totaal": totaal,
            "verwachting": [
                {"minuten": minuten, "mm_per_uur": mm} for minuten, mm in reeks
            ],
        }

        self.onthoud(data)
        self._vuur_event(data)

        # Voorspelling vastleggen en nakijken: begon het regenen wanneer we
        # dachten?
        if self.validatie is not None:
            nu = dt_util.utcnow().timestamp()
            self.validatie.verlopen(nu)

            if regent:
                self.validatie.uitgekomen(
                    "regen", nu, {"intensiteit": nu_intensiteit}
                )
            elif begint_over is not None and begint_over <= 60:
                self.validatie.voorspel(
                    "regen", nu, begint_over, {"verwachte_piek": piek, "bron": bron}
                )

        return data

    def _vuur_event(self, data: dict) -> None:
        """Meld het als er binnen de ingestelde tijd regen aankomt.

        Alleen bij de overgang van droog naar 'komt eraan', zodat je niet elke
        vijf minuten opnieuw een bericht krijgt.
        """
        begint = data["begint_over"]
        verwacht = begint is not None and begint <= self.vooruit

        if verwacht and self._was_verwacht is False:
            stats = getattr(self, "stats", None)
            if stats is not None:
                stats.noteer_event("rain_incoming")
            self.hass.bus.async_fire(
                EVENT_RAIN_INCOMING,
                {
                    "over_minuten": begint,
                    "intensiteit": data["piek"],
                    "totaal_mm": data["totaal"],
                    "bron": data["bron"],
                },
            )

        # Na een herstart eerst een ronde meekijken, zodat een lopende bui
        # niet meteen een melding oplevert.
        self._was_verwacht = verwacht
