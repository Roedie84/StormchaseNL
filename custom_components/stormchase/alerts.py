"""Officiele weerwaarschuwingen via MeteoAlarm, in Nederland via het KNMI.

MeteoAlarm is de Europese koepel waar nationale weerdiensten hun
waarschuwingen aan leveren, waaronder het KNMI. Dat maakt het bruikbaar in
heel Europa, in plaats van alleen in Nederland.

0.49.0: in Nederland komen de waarschuwingen eerst rechtstreeks van het KNMI
(de API achter de KNMI-app, geen sleutel nodig): per waarschuwingsregio, met
het niveau per uur vooruit. Hetzelfde antwoord levert de weersverwachting
voor de weerentiteit. Lukt dat niet, of ben je buiten Nederland, dan gewoon
MeteoAlarm zoals altijd.
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
from .herpoging import HerpogingMixin
from .verouderd import VerouderdMixin
from .taal import vertaal_soort
from .herstart import gemeld_naar_opslag, gemeld_uit_opslag
from .knmi_api import poging
from .knmi_grid import KNMI_REGIOS, in_nederland_grof, regio_uit_geocode, verwachtingscel
from .knmi_verwerk import verwachting as knmi_verwachting
from .knmi_verwerk import waarschuwingen as knmi_waarschuwingen
from .const import KNMI_DETAIL_INTERVAL

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


class AlertCoordinator(HerpogingMixin, VerouderdMixin, LocationMixin, DataUpdateCoordinator[dict]):
    """Haalt de actieve waarschuwingen op voor het ingestelde land."""

    # Bronnen die na een storing een herkansing krijgen (0.43.0)
    _herpoging_bronnen = ("meteoalarm", "geocodering")

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
        # 0.47.0: sleutel -> {"tot", "gemeld_op"} (epoch-seconden), bewaard
        # over een herstart zodat een lopende waarschuwing niet opnieuw wordt
        # gemeld. Wordt voor de eerste ophaalronde uit de opslag gevuld.
        self._gemeld: dict[str, dict] = {}
        self.bewaarplan = None  # wordt na het aanmaken gezet
        # Onthoud waar we het land voor hebben opgezocht, zodat we niet bij
        # elke ronde opnieuw hoeven te geocoderen.
        self._land_voor: tuple[float, float] | None = None
        self._gevonden_land: str | None = None
        # Namen van de gebieden waar je nu bent: stad, streek, provincie.
        # Daarmee filteren we de landelijke feed terug naar jouw omgeving.
        self._gebiedsnamen: list[str] = []
        self._wacht_op_land = False
        # 0.49.0: KNMI-bronnen (wordt na het aanmaken gezet) en het laatste
        # geocodeerantwoord, voor de waarschuwingsregio
        self.knmi = None
        self._geocode: dict | None = None
        self._details: dict[str, dict] = {}
        self._details_voor: tuple[str, int] | None = None
        self._details_op = None

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
            if verschil < self._geocodeer_drempel(latitude, longitude):
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
        # 0.49.0: provincie en gemeente voor de KNMI-regio, en het land voor
        # de andere KNMI-bronnen
        self._geocode = payload
        if self.knmi is not None:
            self.knmi.land.noteer(latitude, longitude, code)

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

    def _geocodeer_drempel(self, latitude: float, longitude: float) -> float:
        """Hoe ver je mag verschuiven voor een nieuwe geocodering (graden).

        Een land verandert niet om de paar kilometer, een KNMI-regio wel:
        Eibergen ligt in Gelderland, tien kilometer verderop is het
        Overijssel. In en rond Nederland daarom een fijnere stap.
        """
        if self.knmi is not None and (
            self._gevonden_land == "netherlands"
            or in_nederland_grof(latitude, longitude)
        ):
            return 0.1
        return 0.5

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

    def note_location(self, latitude: float, longitude: float) -> None:
        """Ververs meteen zodra de locatie bruikbaar wordt of flink wijzigt.

        Bij het opstarten is een tracker soms nog niet geladen en valt de
        landbepaling terug op de thuislocatie. Wachten tot het volgende
        kwartier zou betekenen dat je al die tijd waarschuwingen van het
        verkeerde land ziet.
        """
        if self.instelling != "auto":
            return

        if self._gevonden_land is None:
            # Alleen als er niet al een poging loopt, anders vraagt elke
            # ronde van dertig seconden een nieuwe verversing aan.
            if not self._wacht_op_land:
                self._wacht_op_land = True
                self.hass.async_create_task(self._opnieuw())
            return

        if self._land_voor is None:
            return

        verschil = max(
            abs(self._land_voor[0] - latitude),
            abs(self._land_voor[1] - longitude),
        )
        if verschil >= self._geocodeer_drempel(latitude, longitude):
            _LOGGER.debug("Locatie flink verschoven, land opnieuw bepalen")
            self.hass.async_create_task(self.async_request_refresh())

    async def _opnieuw(self) -> None:
        """Probeer het land opnieuw te bepalen."""
        try:
            await self.async_request_refresh()
        finally:
            self._wacht_op_land = False

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

    async def _haal_op(self) -> dict:
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
            latitude, longitude, _ = self.resolve_location()

        # 0.49.0: in Nederland eerst het KNMI zelf; MeteoAlarm is de terugval
        if land == "netherlands" and self.knmi is not None:
            if self.instelling != "auto":
                # Alleen voor de regio; het land staat vast
                await self._bepaal_land(latitude, longitude)
            knmi = await self._knmi(latitude, longitude)
            if knmi is not None:
                self.onthoud(knmi)
                self._vuur_events(knmi["actief"])
                return knmi

        url = f"{METEOALARM_URL}{land}"

        try:
            async with async_timeout.timeout(20):
                response = await self._session.get(url)
                response.raise_for_status()
                tekst = await response.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            if self.stats is not None:
                self.stats.bronnen["meteoalarm"].fout(err)
            return self.val_terug(err)

        try:
            wortel = _parse_xml(tekst)
        except Exception as err:  # noqa: BLE001 - feed kan van vorm wisselen
            if self.stats is not None:
                self.stats.bronnen["meteoalarm"].fout(err)
            return self.val_terug(err)

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

            oorspronkelijk = _tekst(entry, "cap:event")

            waarschuwing = {
                "titel": _tekst(entry, "atom:title"),
                # Vertaald bij de bron, zodat alles wat er verder mee doet
                # Nederlands is. De oorspronkelijke term blijft bewaard om op
                # te kunnen filteren of terug te zoeken.
                "soort": vertaal_soort(oorspronkelijk),
                "soort_origineel": oorspronkelijk,
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
            # Een steekproef van de gebieden zoals de feed ze noemt. Zonder
            # dit valt niet na te gaan of het filter niets vindt omdat er
            # niets is, of omdat de namen niet op elkaar aansluiten.
            "gebieden_in_land": sorted(
                {w.get("gebied") for w in alles if w.get("gebied")}
            )[:25],
            "bron": "meteoalarm",
            "regio": None,
            "niveau_per_uur": None,
        }

        self.onthoud(data)
        self._vuur_events(actief)
        return data

    def _knmi_regio(self, latitude: float, longitude: float) -> tuple[int, str]:
        """De KNMI-waarschuwingsregio voor deze positie.

        Een handmatig regiofilter dat een KNMI-regio noemt, gaat voor.
        Anders uit de geocodering (provincie, Waddeneiland, water), en als
        laatste de regio met het dichtstbijzijnde middelpunt.
        """
        if self.regio:
            for nummer, naam in KNMI_REGIOS.items():
                if naam.lower() == self.regio or self.regio in naam.lower():
                    return nummer, "instelling"
        return regio_uit_geocode(self._geocode, latitude, longitude)

    async def _knmi(self, latitude: float, longitude: float) -> dict | None:
        """Waarschuwingen en verwachting van het KNMI, of None (terugval)."""
        cel = verwachtingscel(latitude, longitude)
        if cel is None:
            return None
        regio, via = self._knmi_regio(latitude, longitude)
        stats = self.stats

        async def ophalen():
            payload = await self.knmi.app.weer(cel, regio)
            if not isinstance(payload, dict) or (
                "alerts" not in payload and "hourly" not in payload
            ):
                raise ValueError("onverwacht antwoord van de KNMI-app")
            return payload

        payload, _ = await poging(
            self.knmi.afremming["waarschuwingen"],
            stats.bronnen["knmi_waarschuwingen"] if stats is not None else None,
            "waarschuwingen",
            ophalen,
        )
        if payload is None:
            return None

        nu = dt_util.utcnow()
        data = knmi_waarschuwingen(payload, regio, KNMI_REGIOS[regio], nu)
        data["regio_bepaald_via"] = via
        data["knmi_cel"] = cel
        data["knmi_weer"] = knmi_verwachting(
            payload, await self._knmi_details(cel, regio, payload), nu
        )
        if stats is not None:
            stats.alert_laatste_in_land = None
            stats.alert_laatste_na_filter = data["aantal"]
            stats.alert_filternamen = [KNMI_REGIOS[regio]]
        return data

    async def _knmi_details(self, cel: str, regio: int, payload: dict) -> dict:
        """Dagdetails (neerslagkans, wind), hooguit elk uur opnieuw."""
        nu = dt_util.utcnow()
        if (
            self._details_voor == (cel, regio)
            and self._details_op is not None
            and nu - self._details_op < KNMI_DETAIL_INTERVAL
        ):
            return self._details

        data = [
            dag.get("date")
            for dag in ((payload.get("daily") or {}).get("forecast") or [])
            if isinstance(dag, dict) and dag.get("date")
        ]

        async def ophalen():
            details = {}
            for datum in data:
                details[datum] = await self.knmi.app.weer_detail(cel, regio, datum)
            return details

        stats = self.stats
        details, _ = await poging(
            self.knmi.afremming["verwachting"],
            stats.bronnen["knmi_verwachting"] if stats is not None else None,
            "verwachting",
            ophalen,
        )
        if details is not None:
            self._details = details
            self._details_voor = (cel, regio)
            self._details_op = nu
        return self._details if self._details_voor == (cel, regio) else {}

    def herstel_gemeld(self, bewaard) -> None:
        """Al gemelde waarschuwingen terugzetten; verlopen vallen weg."""
        self._gemeld = gemeld_uit_opslag(bewaard, dt_util.utcnow().timestamp())

    def gemeld_naar_opslag(self) -> dict:
        """De al gemelde waarschuwingen, voor de Store."""
        return gemeld_naar_opslag(self._gemeld)

    def _vuur_events(self, actief: list[dict]) -> None:
        """Meld nieuwe waarschuwingen, elk hoogstens een keer."""
        huidige_ids = set()
        voor = set(self._gemeld)

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

            tot = _tijd(waarschuwing.get("tot"))
            self._gemeld[sleutel] = {
                "tot": tot.timestamp() if tot is not None else None,
                "gemeld_op": dt_util.utcnow().timestamp(),
            }
            if self.stats is not None:
                self.stats.noteer_event("alert")
            self.hass.bus.async_fire(EVENT_ALERT, waarschuwing)

        # Verlopen waarschuwingen vergeten, zodat een herhaling later opnieuw
        # gemeld mag worden.
        self._gemeld = {
            k: v for k, v in self._gemeld.items() if k in huidige_ids
        }
        if set(self._gemeld) != voor and self.bewaarplan is not None:
            self.bewaarplan.plan()
