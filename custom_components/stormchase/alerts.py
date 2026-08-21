"""Officiele weerwaarschuwingen via MeteoAlarm.

MeteoAlarm is de Europese koepel waar nationale weerdiensten hun
waarschuwingen aan leveren, waaronder het KNMI. Dat maakt het bruikbaar in
heel Europa, in plaats van alleen in Nederland.
"""

from __future__ import annotations

import logging
from datetime import datetime

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    ALERT_INTERVAL,
    MODE_HOME,
    MODE_TRACKER,
    MODE_ZONE,
    GEOCODE_URL,
    LANDCODES,
    ALERT_LEVEL_CHOICES,
    ALERT_LEVELS,
    CONF_ALERT_COUNTRY,
    CONF_ALERT_MIN_LEVEL,
    CONF_ALERT_REGION,
    DEFAULT_ALERT_COUNTRY,
    DEFAULT_ALERT_MIN_LEVEL,
    EVENT_ALERT,
    METEOALARM_URL,
)
from .coordinator import LocationMixin

_LOGGER = logging.getLogger(__name__)

# CAP-velden zitten in een eigen namespace; de feed gebruikt Atom eromheen.
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "cap": "urn:oasis:names:tc:emergency:cap:1.2",
}


def _parse_xml(tekst: str):
    """Parseer XML, bij voorkeur met defusedxml."""
    try:
        from defusedxml import ElementTree as veilig_et

        return veilig_et.fromstring(tekst)
    except ImportError:  # pragma: no cover - defusedxml zit in Home Assistant
        from xml.etree import ElementTree as et

        return et.fromstring(tekst)


def _tekst(element, pad: str) -> str | None:
    """Haal de tekst van een subelement op, of None."""
    gevonden = element.find(pad, NS)
    if gevonden is None or gevonden.text is None:
        return None
    return gevonden.text.strip()


def _tijd(waarde: str | None) -> datetime | None:
    """Zet een CAP-tijdstempel om naar een datetime."""
    if not waarde:
        return None
    return dt_util.parse_datetime(waarde)


class AlertCoordinator(LocationMixin, DataUpdateCoordinator[dict]):
    """Haalt de actieve waarschuwingen op voor het ingestelde land."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiseer de coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.title} waarschuwingen",
            update_interval=ALERT_INTERVAL,
        )
        self.entry = entry
        self._session = async_get_clientsession(hass)
        self._gemeld: set[str] = set()
        # Onthoud waar we het land voor hebben opgezocht, zodat we niet bij
        # elke ronde opnieuw hoeven te geocoderen.
        self._land_voor: tuple[float, float] | None = None
        self._gevonden_land: str | None = None
        # Namen van de gebieden waar je nu bent: stad, streek, provincie.
        # Daarmee filteren we de landelijke feed terug naar jouw omgeving.
        self._gebiedsnamen: list[str] = []

    @property
    def instelling(self) -> str:
        """Wat de gebruiker heeft gekozen."""
        return self._opt(CONF_ALERT_COUNTRY, DEFAULT_ALERT_COUNTRY)

    async def _bepaal_land(
        self, latitude: float, longitude: float, onthouden: bool = True
    ) -> str | None:
        """Zoek het land op bij de huidige coordinaten.

        Alleen de landcode is nodig, geen adres. Het resultaat wordt bewaard
        tot je meer dan een halve graad verplaatst, ongeveer vijftig
        kilometer, want landsgrenzen verschuiven niet.
        """
        if self._land_voor is not None:
            verschil = max(
                abs(self._land_voor[0] - latitude),
                abs(self._land_voor[1] - longitude),
            )
            if verschil < 0.5:
                return self._gevonden_land

        params = {
            "latitude": round(latitude, 3),
            "longitude": round(longitude, 3),
            "localityLanguage": "en",
        }

        try:
            async with async_timeout.timeout(15):
                response = await self._session.get(GEOCODE_URL, params=params)
                response.raise_for_status()
                payload = await response.json()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Land niet te bepalen: %s", err)
            if self.stats is not None:
                self.stats.bronnen["geocodering"].fout(err)
            return self._gevonden_land

        if self.stats is not None:
            self.stats.bronnen["geocodering"].succes()

        code = (payload.get("countryCode") or "").upper()
        land = LANDCODES.get(code)

        # Verzamel de bestuurlijke namen rond deze coordinaten. MeteoAlarm
        # beschrijft gebieden met namen als "Kreis und Stadt Augsburg", dus
        # een naam die daarin voorkomt is een bruikbaar filter.
        namen: list[str] = []
        for sleutel in ("locality", "city", "principalSubdivision"):
            waarde = payload.get(sleutel)
            if waarde:
                namen.append(str(waarde))

        info = payload.get("localityInfo") or {}
        for niveau in info.get("administrative") or []:
            naam = niveau.get("name")
            if naam:
                namen.append(str(naam))

        # Korte namen leveren toevalstreffers op, dus die laten we vallen.
        self._gebiedsnamen = sorted(
            {n.lower() for n in namen if len(n) >= 4}, key=len, reverse=True
        )
        _LOGGER.debug("Gebiedsnamen voor filtering: %s", self._gebiedsnamen)

        if land is None:
            _LOGGER.debug("Geen MeteoAlarm-feed voor landcode %s", code or "onbekend")

        if onthouden:
            self._land_voor = (latitude, longitude)
            self._gevonden_land = land
        return land

    @property
    def regio(self) -> str:
        """Optioneel filter op regionaam."""
        return (self._opt(CONF_ALERT_REGION) or "").strip().lower()

    @property
    def drempel(self) -> int:
        """Minimaal niveau waarop we melden."""
        keuze = self._opt(CONF_ALERT_MIN_LEVEL, DEFAULT_ALERT_MIN_LEVEL)
        try:
            return ALERT_LEVEL_CHOICES.index(keuze) + 1
        except ValueError:
            return 1

    def _relevant(self, waarschuwing: dict) -> bool:
        """Valt deze waarschuwing in jouw omgeving?

        Een handmatig ingevuld filter gaat voor. Staat dat leeg, dan gebruiken
        we de gebiedsnamen die bij de landbepaling zijn opgehaald. Zonder een
        van beide zou je alle waarschuwingen van een heel land krijgen, en dat
        zegt niets over waar jij bent.
        """
        gebied = (waarschuwing.get("gebied") or "").lower()

        if self.regio:
            return self.regio in gebied

        if not self._gebiedsnamen:
            return True

        return any(naam in gebied for naam in self._gebiedsnamen)

    async def _async_update_data(self) -> dict:
        """Haal de feed op en filter de actieve waarschuwingen."""
        if self.instelling == "uit":
            return {"actief": [], "aantal": 0, "niveau": None, "rang": 0, "land": "uit"}

        if self.instelling == "auto":
            latitude, longitude, bron = self.resolve_location()

            # Bij het opstarten is een device_tracker soms nog niet geladen en
            # valt resolve_location terug op de thuislocatie. Dat resultaat
            # mogen we niet onthouden, anders blijf je waarschuwingen van je
            # thuisland krijgen terwijl je ergens anders bent.
            modus = self._opt("location_mode", MODE_HOME)
            nog_niet_klaar = modus in (MODE_TRACKER, MODE_ZONE) and bron == "thuis"

            land = await self._bepaal_land(
                latitude, longitude, onthouden=not nog_niet_klaar
            )
            if land is None:
                return {
                    "actief": [], "aantal": 0, "niveau": None, "rang": 0,
                    "land": "onbekend",
                }
        else:
            land = self.instelling

        url = f"{METEOALARM_URL}{land}"

        try:
            async with async_timeout.timeout(20):
                response = await self._session.get(url)
                response.raise_for_status()
                tekst = await response.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            if self.stats is not None:
                self.stats.bronnen["meteoalarm"].fout(err)
            raise UpdateFailed(f"MeteoAlarm niet bereikbaar: {err}") from err

        try:
            wortel = _parse_xml(tekst)
        except Exception as err:  # noqa: BLE001 - feed kan van vorm wisselen
            if self.stats is not None:
                self.stats.bronnen["meteoalarm"].fout(err)
            raise UpdateFailed(f"MeteoAlarm gaf onleesbare data: {err}") from err

        nu = dt_util.utcnow()
        actief: list[dict] = []
        alles: list[dict] = []

        for entry in wortel.findall("atom:entry", NS):
            ernst = _tekst(entry, "cap:severity")
            kleur, rang = ALERT_LEVELS.get(ernst or "", (None, 0))
            if kleur is None:
                continue

            verloopt = _tijd(_tekst(entry, "cap:expires"))
            if verloopt is not None and verloopt < nu:
                continue

            waarschuwing = {
                "titel": _tekst(entry, "atom:title"),
                "soort": _tekst(entry, "cap:event"),
                "niveau": kleur,
                "rang": rang,
                "gebied": _tekst(entry, "cap:areaDesc"),
                "vanaf": _tekst(entry, "cap:effective") or _tekst(entry, "cap:onset"),
                "tot": _tekst(entry, "cap:expires"),
                "zekerheid": _tekst(entry, "cap:certainty"),
                "urgentie": _tekst(entry, "cap:urgency"),
                "id": _tekst(entry, "atom:id"),
            }

            alles.append(waarschuwing)
            if self._relevant(waarschuwing):
                actief.append(waarschuwing)

        totaal = len(alles)
        actief.sort(key=lambda w: w["rang"], reverse=True)

        if self.stats is not None:
            self.stats.bronnen["meteoalarm"].succes()
            self.stats.alert_laatste_in_land = totaal
            self.stats.alert_laatste_na_filter = len(actief)
            self.stats.alert_filternamen = (
                [self.regio] if self.regio else list(self._gebiedsnamen)
            )
        zwaarste = actief[0] if actief else None

        data = {
            "actief": actief,
            "aantal": len(actief),
            "niveau": zwaarste["niveau"] if zwaarste else None,
            "rang": zwaarste["rang"] if zwaarste else 0,
            "soort": zwaarste["soort"] if zwaarste else None,
            "gebied": zwaarste["gebied"] if zwaarste else None,
            "land": land,
            "gefilterd_op": self.regio or (
                ", ".join(self._gebiedsnamen[:3]) if self._gebiedsnamen else None
            ),
            "aantal_in_land": totaal,
        }

        self._vuur_events(actief)
        return data

    def _vuur_events(self, actief: list[dict]) -> None:
        """Meld nieuwe waarschuwingen, elk hoogstens een keer."""
        huidige_ids = set()

        for waarschuwing in actief:
            sleutel = waarschuwing.get("id") or (
                f"{waarschuwing.get('soort')}|{waarschuwing.get('gebied')}|"
                f"{waarschuwing.get('tot')}"
            )
            huidige_ids.add(sleutel)

            if sleutel in self._gemeld:
                continue
            if waarschuwing["rang"] < self.drempel:
                continue

            self._gemeld.add(sleutel)
            if self.stats is not None:
                self.stats.noteer_event("alert")
            self.hass.bus.async_fire(EVENT_ALERT, waarschuwing)

        # Verlopen waarschuwingen vergeten, zodat een herhaling later opnieuw
        # gemeld mag worden.
        self._gemeld &= huidige_ids
