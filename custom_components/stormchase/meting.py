"""Metingen van het dichtstbijzijnde weerstation.

Alles wat de integratie verder toont is voorspeld: CAPE, schering, wind,
temperatuur. Deze bron levert wat er daadwerkelijk gemeten is, door de
Duitse weerdienst, op het dichtstbijzijnde station. Dat maakt zichtbaar of
het model er die dag naast zit.

Gratis en zonder sleutel. Dekt Duitsland en de directe omgeving; daarbuiten
komt er niets terug en blijft de sensor leeg.

0.49.0: in Nederland, met een EDR-sleutel van het KNMI Data Platform, komen
de metingen van de automatische KNMI-stations (elke tien minuten), per
grootheid van het dichtstbijzijnde station dat hem meet. Daarbij windstoten
in Beaufort, de weercode (onweer en hagel bij het station) en het
luchtdrukverloop over een en drie uur. Zonder sleutel, buiten Nederland of
bij een storing: Bright Sky zoals altijd.
"""

from __future__ import annotations

import logging
from datetime import datetime

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import BRIGHTSKY_URL, METING_INTERVAL, METING_INTERVAL_KNMI
from .coordinator import LocationMixin
from .herpoging import HerpogingMixin
from .knmi_api import OngeldigVerzoek, poging
from .knmi_verwerk import (
    EDR_EXTRA,
    EDR_PARAMETERS,
    Drukhistorie,
    beaufort,
    metingen,
    tendens,
)
from .verouderd import VerouderdMixin

_LOGGER = logging.getLogger(__name__)

# Stationsnamen een dag bewaren; ze veranderen zelden
STATIONSNAMEN_GELDIG_S = 24 * 3600


def _stempel(waarde) -> float | None:
    """ISO-tijd naar epoch-seconden, of None."""
    if isinstance(waarde, datetime):
        return waarde.timestamp()
    if not isinstance(waarde, str):
        return None
    moment = dt_util.parse_datetime(waarde)
    return moment.timestamp() if moment is not None else None


class MetingCoordinator(HerpogingMixin, VerouderdMixin, LocationMixin, DataUpdateCoordinator[dict]):
    """Haalt de meting van het dichtstbijzijnde station op."""

    # Bronnen die na een storing een herkansing krijgen (0.43.0)
    _herpoging_bronnen = ("meting",)

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiseer de coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.title} meting",
            update_interval=METING_INTERVAL,
        )
        self.entry = entry
        self._session = async_get_clientsession(hass)
        self.stats = None
        self.knmi = None  # KnmiBronnen, wordt na het aanmaken gezet
        self.bewaarplan = None  # voor de drukhistorie (0.49.0)
        self.druk = Drukhistorie()
        self._stationsnamen: dict[str, str] = {}
        self._namen_op = 0.0
        self._zonder_extra = False

    def zet_knmi(self, knmi) -> None:
        """Koppel de KNMI-bronnen; met EDR elke tien minuten in plaats van 15."""
        self.knmi = knmi
        if knmi is not None and knmi.edr is not None:
            self.update_interval = METING_INTERVAL_KNMI

    # ---- 0.49.0: drukhistorie over een herstart ----

    def druk_naar_opslag(self) -> list:
        return self.druk.naar_opslag()

    def herstel_druk(self, bewaard) -> None:
        self.druk.herstel(bewaard, dt_util.utcnow().timestamp())

    def _drukverloop(self, data: dict, station: str | None) -> dict:
        """Noteer de druk en voeg de verandering over 1 en 3 uur toe."""
        if self.druk.bij(
            _stempel(data.get("waargenomen_op")), data.get("luchtdruk"), station
        ) and self.bewaarplan is not None:
            self.bewaarplan.plan()
        een = self.druk.verandering(60, 10)
        drie = self.druk.verandering(180, 15)
        return {
            **data,
            "druk_verandering_1u": een,
            "druk_verandering_3u": drie,
            "druk_tendens_1u": tendens(een),
            "druk_tendens_3u": tendens(drie),
        }

    # ---- KNMI EDR ----

    async def _knmi(self, latitude: float, longitude: float) -> dict | None:
        """Metingen van de KNMI-stations, of None (terugval Bright Sky)."""
        knmi = self.knmi
        if knmi is None or knmi.edr is None:
            return None
        if not knmi.land.in_nederland(latitude, longitude):
            return None

        async def ophalen():
            nu = dt_util.utcnow()
            if nu.timestamp() - self._namen_op > STATIONSNAMEN_GELDIG_S:
                try:
                    self._stationsnamen = await knmi.edr.stations(nu)
                    self._namen_op = nu.timestamp()
                except OngeldigVerzoek:
                    self._namen_op = nu.timestamp()
            parameters = EDR_PARAMETERS + (() if self._zonder_extra else EDR_EXTRA)
            try:
                coverages = await knmi.edr.kubus(nu, parameters)
            except OngeldigVerzoek:
                if self._zonder_extra:
                    raise
                # Een parameter die de bron niet kent: zonder de extra's
                self._zonder_extra = True
                coverages = await knmi.edr.kubus(nu, EDR_PARAMETERS)
            return metingen(coverages, latitude, longitude, self._stationsnamen)

        stats = self.stats
        data, _ = await poging(
            knmi.afremming["edr"],
            stats.bronnen["knmi_edr"] if stats is not None else None,
            "waarnemingen",
            ophalen,
        )
        if data is None:
            return None
        return self._drukverloop(data, data.get("luchtdruk_station_id"))

    async def _haal_op(self) -> dict:
        """Vraag de laatste waarneming op."""
        latitude, longitude, _ = self.resolve_location()

        knmi = await self._knmi(latitude, longitude)
        if knmi is not None:
            # Gemeten bij het KNMI: Bright Sky is niet nodig
            self._normaal_interval = METING_INTERVAL_KNMI
            return self.onthoud(knmi)
        self._normaal_interval = METING_INTERVAL

        try:
            async with async_timeout.timeout(20):
                antwoord = await self._session.get(
                    BRIGHTSKY_URL,
                    params={"lat": round(latitude, 4), "lon": round(longitude, 4)},
                )
                antwoord.raise_for_status()
                payload = await antwoord.json()
            if self.stats is not None:
                self.stats.bronnen["meting"].succes()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Geen meting beschikbaar: %s", err)
            if self.stats is not None:
                self.stats.bronnen["meting"].fout(err)
            return self.val_terug(err)

        weer = payload.get("weather") or {}
        bronnen = payload.get("sources") or []
        station = bronnen[0] if bronnen else {}
        stoten = weer.get("wind_gust_speed_10")

        data = {
            "temperatuur": weer.get("temperature"),
            "wind": weer.get("wind_speed_10"),
            "windstoten": stoten,
            "neerslag": weer.get("precipitation_10"),
            "luchtdruk": weer.get("pressure_msl"),
            "luchtvochtigheid": weer.get("relative_humidity"),
            "zicht": weer.get("visibility"),
            "bewolking": weer.get("cloud_cover"),
            "waargenomen_op": weer.get("timestamp"),
            "station": station.get("station_name"),
            "station_afstand_km": (
                round(station["distance"] / 1000, 1)
                if station.get("distance") is not None
                else None
            ),
            # 0.49.0: dezelfde extra velden als bij het KNMI, voor zover
            # Bright Sky ze levert
            "windstoten_ms": round(stoten / 3.6, 1) if stoten is not None else None,
            "windstoten_bft": beaufort(stoten / 3.6) if stoten is not None else None,
            "windstoten_station": station.get("station_name"),
            "luchtdruk_station": station.get("station_name"),
            "bron": "brightsky",
        }
        return self.onthoud(
            self._drukverloop(data, station.get("dwd_station_id") or station.get("station_name"))
        )
