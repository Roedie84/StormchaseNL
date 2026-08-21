"""Coordinators voor de Stormchase integratie."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.util.location import distance as location_distance

from .indices import (
    duiding_cape,
    duiding_schering,
    duiding_stabiliteit,
    duiding_vriesniveau,
    hagelkans,
    onweersverwachting,
    peiling,
    rotatiekans,
    total_totals,
    windschering,
)

from .const import (
    CLEARED_FACTOR,
    CONF_ADDRESS_SENSOR,
    CONF_AZIMUTH_SENSOR,
    CONF_COUNTER_SENSOR,
    CONF_DISTANCE_SENSOR,
    CONF_GEO_PATTERN,
    CONF_LOCATION_MODE,
    CONF_MANUAL_LOCATION,
    CONF_RING_FAR,
    CONF_RING_MID,
    CONF_RING_NEAR,
    CONF_TRACKER_ENTITY,
    CONF_UPDATE_INTERVAL,
    CONF_RING_WINDOW,
    CONF_STATIONARY_MINUTES,
    CONF_WARN_DISTANCE,
    CONF_ZONE_ENTITY,
    DEFAULT_GEO_PATTERN,
    DEFAULT_RING_WINDOW,
    CONF_MOVING_SPEED,
    DEFAULT_MOVING_SPEED,
    DEFAULT_STATIONARY_MINUTES,
    DEFAULT_UPDATE_INTERVAL,
    MAX_SNELHEID,
    SNELHEID_VENSTER,
    MAX_INSLAGEN,
    LOCATIE_GESCHIEDENIS,
    DEFAULT_RING_FAR,
    DEFAULT_RING_MID,
    DEFAULT_RING_NEAR,
    DEFAULT_WARN_DISTANCE,
    EVENT_APPROACHING,
    EVENT_CLEARED,
    CODES_IJZEL,
    CODES_MIST,
    CODES_SNEEUW,
    CONF_FROST_THRESHOLD,
    CONF_HEAT_THRESHOLD,
    CONF_WEATHER_TYPES,
    CONF_WIND_THRESHOLD,
    DEFAULT_FROST_THRESHOLD,
    DEFAULT_HEAT_THRESHOLD,
    DEFAULT_WEATHER_TYPES,
    DEFAULT_WIND_THRESHOLD,
    EVENT_NEARBY,
    CONF_OUTLOOK_LEVEL,
    DEFAULT_OUTLOOK_LEVEL,
    EVENT_OUTLOOK,
    EVENT_WEATHER,
    OUTLOOK_RANGEN,
    EVENT_WIND,
    METEO_HOURLY,
    METEO_INTERVAL,
    METEO_URL,
    MIN_SAMPLES,
    MODE_HOME,
    MODE_MANUAL,
    MODE_TRACKER,
    MODE_ZONE,
    MOVE_THRESHOLD_KM,
    SPEED_DEADZONE,
    TREND_APPROACH,
    TREND_FAST_APPROACH,
    TREND_FAST_RECEDE,
    TREND_RECEDE,
    TREND_STABLE,
    TREND_UNKNOWN,
    TREND_WINDOW,
)

_LOGGER = logging.getLogger(__name__)


class LocationMixin:
    """Bepaalt welke coordinaten de integratie moet gebruiken.

    Standaard de thuislocatie uit Home Assistant, maar je kunt ook een zone
    kiezen, een device_tracker volgen (handig op vakantie) of coordinaten
    handmatig prikken.
    """

    hass: HomeAssistant
    entry: ConfigEntry
    stats = None  # wordt na het aanmaken gezet

    def _opt(self, key: str, default=None):
        """Haal een optie op, met de config-entry data als fallback."""
        return self.entry.options.get(key, self.entry.data.get(key, default))

    def resolve_location(self) -> tuple[float, float, str]:
        """Geef breedte, lengte en een leesbare bron terug.

        Valt altijd terug op de thuislocatie: liever weerdata van thuis dan
        helemaal geen weerdata.
        """
        mode = self._opt(CONF_LOCATION_MODE, MODE_HOME)
        home = (self.hass.config.latitude, self.hass.config.longitude)

        if mode == MODE_ZONE:
            entity_id = self._opt(CONF_ZONE_ENTITY)
            state = self.hass.states.get(entity_id) if entity_id else None
            if state and ATTR_LATITUDE in state.attributes:
                name = state.attributes.get("friendly_name", entity_id)
                return (
                    float(state.attributes[ATTR_LATITUDE]),
                    float(state.attributes[ATTR_LONGITUDE]),
                    f"zone: {name}",
                )
            _LOGGER.debug("Zone %s zonder coordinaten, terug naar thuis", entity_id)

        elif mode == MODE_TRACKER:
            entity_id = self._opt(CONF_TRACKER_ENTITY)
            state = self.hass.states.get(entity_id) if entity_id else None
            if state and ATTR_LATITUDE in state.attributes:
                name = state.attributes.get("friendly_name", entity_id)
                return (
                    float(state.attributes[ATTR_LATITUDE]),
                    float(state.attributes[ATTR_LONGITUDE]),
                    f"tracker: {name}",
                )
            # Een tracker zonder GPS staat vaak op 'home' of 'not_home'
            _LOGGER.debug("Tracker %s zonder coordinaten, terug naar thuis", entity_id)

        elif mode == MODE_MANUAL:
            manual = self._opt(CONF_MANUAL_LOCATION) or {}
            if manual.get("latitude") is not None:
                return (
                    float(manual["latitude"]),
                    float(manual["longitude"]),
                    "handmatig",
                )

        return (home[0], home[1], "thuis")


def blitzortung_locatie(hass: HomeAssistant) -> dict | None:
    """Zoek op vanaf welk punt de Blitzortung-integratie meet.

    Die integratie heeft zelf geen entiteit die haar positie toont, maar de
    instellingen zijn wel uitleesbaar. Zo kun je nagaan of beide integraties
    vanaf hetzelfde punt werken; wijken ze af, dan horen de afstanden tot de
    inslagen niet bij het weer dat je ziet.
    """
    for entry in hass.config_entries.async_entries():
        if "blitzortung" not in entry.domain.lower():
            continue

        gegevens = {**entry.data, **entry.options}

        # Volgt de integratie een tracker of zone, pak dan de positie daarvan
        for sleutel in ("tracker", "tracker_entity", "device_tracker", "zone"):
            entity_id = gegevens.get(sleutel)
            if entity_id:
                state = hass.states.get(entity_id)
                if state and ATTR_LATITUDE in state.attributes:
                    return {
                        "naam": entry.title,
                        "bron": entity_id,
                        "latitude": float(state.attributes[ATTR_LATITUDE]),
                        "longitude": float(state.attributes[ATTR_LONGITUDE]),
                    }

        breedte = gegevens.get("latitude")
        lengte = gegevens.get("longitude")
        if breedte is not None and lengte is not None:
            return {
                "naam": entry.title,
                "bron": "vaste coordinaten",
                "latitude": float(breedte),
                "longitude": float(lengte),
            }

        # Geen positie in de instellingen: dan gebruikt hij de thuislocatie
        return {
            "naam": entry.title,
            "bron": "thuislocatie",
            "latitude": hass.config.latitude,
            "longitude": hass.config.longitude,
        }

    return None


@dataclass
class StormData:
    """Afgeleide gegevens over de actuele onweerssituatie."""

    distance: float | None = None
    azimuth: float | None = None
    counter: int | None = None
    speed: float | None = None  # km/u, POSITIEF = komt dichterbij
    eta: float | None = None  # minuten
    trend: str = TREND_UNKNOWN
    markers: int = 0
    rings: dict[int, int] = field(default_factory=dict)
    ring_bron: str = "geen"
    afstand_bron: str = "sensor"
    last_strike: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_source: str = "thuis"
    adres: str | None = None
    onderweg: bool | None = None
    stil_sinds: int | None = None  # minuten onder de snelheidsdrempel
    reissnelheid: float | None = None  # km/u
    blitzortung: dict | None = None
    afwijking_km: float | None = None


class StormCoordinator(LocationMixin, DataUpdateCoordinator[StormData]):
    """Leest de Blitzortung-sensoren en berekent de afgeleide waarden.

    Bewust geen eigen verbinding met blitzortung.org: de bestaande
    Blitzortung-integratie doet dat al via MQTT. Een tweede verbinding
    zou alleen extra onderhoud opleveren.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiseer de coordinator."""
        # Het interval komt uit de instellingen. De ronde leest alleen lokale
        # toestanden en rekent wat door, dus tien seconden kost weinig.
        seconden = entry.options.get(
            CONF_UPDATE_INTERVAL,
            entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.title} storm",
            update_interval=timedelta(seconds=int(seconden)),
        )
        self.entry = entry
        self.meteo: MeteoCoordinator | None = None
        self.alerts = None  # AlertCoordinator, wordt na het aanmaken gezet
        self._history: deque[tuple[float, float]] = deque(maxlen=240)
        self._was_nearby: bool | None = None
        self._was_approaching: bool | None = None
        # Locatiepunten om te bepalen of je onderweg bent of ergens staat
        self._locaties: deque[tuple[float, float, float]] = deque(
            maxlen=LOCATIE_GESCHIEDENIS
        )
        # Zelf bijgehouden inslagen, voor het geval de Blitzortung-integratie
        # geen geo_location entiteiten aanmaakt. Elke keer dat de
        # afstandssensor verspringt is dat een nieuwe inslag.
        self._inslagen: deque[tuple[float, float]] = deque(maxlen=MAX_INSLAGEN)
        self._vorige_inslag: datetime | None = None
        self._laatste_beweging: float | None = None
        self._vorige_bron: str | None = None

    @property
    def ring_bounds(self) -> list[int]:
        """De drie afstandsringen in km."""
        return [
            int(self._opt(CONF_RING_NEAR, DEFAULT_RING_NEAR)),
            int(self._opt(CONF_RING_MID, DEFAULT_RING_MID)),
            int(self._opt(CONF_RING_FAR, DEFAULT_RING_FAR)),
        ]

    @property
    def warn_distance(self) -> float:
        """Afstand waarbinnen we van een waarschuwing spreken."""
        return float(self._opt(CONF_WARN_DISTANCE, DEFAULT_WARN_DISTANCE))

    @callback
    def _noteer_inslag(self, event) -> None:
        """Leg elke verandering van de afstandssensor vast.

        Via een luisteraar en niet via de dertig-secondenronde, anders mis je
        inslagen die daartussen vallen. Bij een actieve onweersbui komen er
        meerdere per minuut binnen.
        """
        nieuw = event.data.get("new_state")
        if nieuw is None or nieuw.state in ("unknown", "unavailable", ""):
            return
        try:
            afstand = float(nieuw.state)
        except (TypeError, ValueError):
            return

        self._inslagen.append((dt_util.utcnow().timestamp(), afstand))

    def volg_bronsensor(self):
        """Begin met luisteren naar de afstandssensor."""
        entity_id = self._opt(CONF_DISTANCE_SENSOR)
        if not entity_id:
            return None
        return async_track_state_change_event(
            self.hass, [entity_id], self._noteer_inslag
        )

    def _lees_adres(self) -> str | None:
        """Lees de adressensor uit, als er een is ingesteld.

        De companion-app levert een geocoded_location sensor met het adres
        waar je bent. Coordinaten zeggen weinig; een plaatsnaam maakt in een
        oogopslag duidelijk waar de integratie naar kijkt.
        """
        entity_id = self._opt(CONF_ADDRESS_SENSOR)
        if not entity_id:
            return None

        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable", ""):
            return None

        return state.state

    def _read_float(self, entity_id: str | None) -> float | None:
        """Lees een sensorwaarde als float, of None als dat niet lukt."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable", ""):
            return None
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return None

    def _uit_geo_location(
        self, pattern: str, latitude: float, longitude: float
    ) -> tuple[list[tuple[float, float]], datetime | None]:
        """Bereken afstand en richting van elke inslag vanaf onze positie.

        De state van een geo_location entiteit is de afstand zoals de bron
        die berekent, vanaf het punt dat daar is ingesteld. Staat dat punt
        ergens anders dan waar jij bent, dan klopt die afstand niet voor jou.
        De coordinaten in de attributen zijn wel absoluut, dus daaruit valt
        de juiste afstand af te leiden.
        """
        punten: list[tuple[float, float]] = []
        laatste: datetime | None = None

        for state in self.hass.states.async_all("geo_location"):
            if pattern not in state.entity_id:
                continue

            breedte = state.attributes.get(ATTR_LATITUDE)
            lengte = state.attributes.get(ATTR_LONGITUDE)
            if breedte is None or lengte is None:
                continue

            meters = location_distance(latitude, longitude, breedte, lengte)
            if meters is None:
                continue

            punten.append(
                (
                    round(meters / 1000, 1),
                    peiling(latitude, longitude, float(breedte), float(lengte)),
                )
            )

            if laatste is None or state.last_changed > laatste:
                laatste = state.last_changed

        return punten, laatste

    def _count_rings(self, pattern: str) -> tuple[int, dict[int, int], str]:
        """Tel de inslagen per afstandsring.

        Bij voorkeur uit de geo_location entiteiten van de
        Blitzortung-integratie, want die kent alle inslagen. Maakt die ze
        niet aan, dan vallen we terug op de inslagen die we zelf uit de
        afstandssensor hebben opgevangen. Dat is minder volledig, want de
        sensor toont alleen de laatste inslag, maar het geeft wel een
        bruikbaar beeld van de activiteit.
        """
        afstanden: list[float] = []
        for state in self.hass.states.async_all("geo_location"):
            if pattern not in state.entity_id:
                continue
            try:
                afstanden.append(float(state.state))
            except (TypeError, ValueError):
                continue

        if afstanden:
            rings = {
                grens: sum(1 for d in afstanden if d < grens)
                for grens in self.ring_bounds
            }
            return len(afstanden), rings, "geo_location"

        # Terugval: onze eigen reeks, binnen het ingestelde tijdvenster
        venster = int(self._opt(CONF_RING_WINDOW, DEFAULT_RING_WINDOW)) * 60
        grens_tijd = dt_util.utcnow().timestamp() - venster
        recent = [d for t, d in self._inslagen if t >= grens_tijd]

        if not recent:
            return 0, {grens: 0 for grens in self.ring_bounds}, "geen"

        rings = {
            grens: sum(1 for d in recent if d < grens) for grens in self.ring_bounds
        }
        return len(recent), rings, "afstandssensor"

    def _speed_from_history(self) -> float | None:
        """Bereken de naderingssnelheid via lineaire regressie.

        Positief betekent dat de afstand afneemt, dus dat het onweer
        dichterbij komt. Regressie in plaats van eerste-tegen-laatste,
        omdat losse inslagen flink kunnen springen.
        """
        now = dt_util.utcnow().timestamp()
        cutoff = now - TREND_WINDOW.total_seconds()
        samples = [(t, d) for t, d in self._history if t >= cutoff]

        if len(samples) < MIN_SAMPLES:
            return None

        n = len(samples)
        mean_t = sum(t for t, _ in samples) / n
        mean_d = sum(d for _, d in samples) / n

        numerator = sum((t - mean_t) * (d - mean_d) for t, d in samples)
        denominator = sum((t - mean_t) ** 2 for t, _ in samples)

        if denominator == 0:
            return None

        # slope in km per seconde -> km per uur, omgedraaid van teken
        slope = numerator / denominator
        # Plus nul, anders levert een vlakke reeks -0.0 op en staat er
        # "-0,0 km/u" op het dashboard.
        return round(-slope * 3600, 1) + 0.0

    def _beweging(
        self, latitude: float, longitude: float, bron: str
    ) -> tuple[bool | None, int | None, float | None]:
        """Bepaal of je onderweg bent, op basis van snelheid.

        Snelheid en niet afstand: iemand die stilstaat in de file blijft
        binnen een straal maar is wel degelijk onderweg, en een wandelaar die
        een blokje om gaat is dat niet. Boven de drempel ben je onderweg;
        eronder tel je pas weer als ter plaatse zodra je die drempel een tijd
        lang niet meer gehaald hebt.

        Levert de tracker zelf een snelheid, dan heeft die de voorkeur: die
        komt uit de GPS en is nauwkeuriger dan wat wij uit twee punten
        afleiden.
        """
        nu = dt_util.utcnow().timestamp()

        # Wisselt de locatiebron, bijvoorbeeld omdat de tracker na het
        # opstarten alsnog geladen is, dan springt de positie zonder dat je
        # bewogen hebt. De oude punten zijn dan onbruikbaar.
        if bron != self._vorige_bron:
            if self._vorige_bron is not None:
                _LOGGER.debug(
                    "Locatiebron gewijzigd van %s naar %s, reeks gewist",
                    self._vorige_bron,
                    bron,
                )
            self._locaties.clear()
            self._laatste_beweging = None
            self._vorige_bron = bron

        self._locaties.append((nu, latitude, longitude))

        drempel = float(self._opt(CONF_MOVING_SPEED, DEFAULT_MOVING_SPEED))
        venster = int(self._opt(CONF_STATIONARY_MINUTES, DEFAULT_STATIONARY_MINUTES))

        snelheid = self._snelheid_van_tracker()
        if snelheid is None:
            snelheid = self._snelheid_uit_punten(nu, latitude, longitude)

        if snelheid is None:
            return None, None, None

        # Een sprong die geen mens of auto kan maken komt van een verspringende
        # positie, niet van beweging. Reeks wissen en opnieuw beginnen.
        if snelheid > MAX_SNELHEID:
            _LOGGER.debug("Onwaarschijnlijke snelheid %.0f km/u genegeerd", snelheid)
            self._locaties.clear()
            self._locaties.append((nu, latitude, longitude))
            return None, None, None

        if snelheid > drempel:
            self._laatste_beweging = nu

        if self._laatste_beweging is None:
            # Sinds het opstarten nooit boven de drempel geweest: dan sta je
            # gewoon stil, en geldt de nalooptijd niet. Die is er alleen om
            # het stoplicht af te vangen na echt rijden.
            stil = int((nu - self._locaties[0][0]) / 60)
            return snelheid > drempel, stil, round(snelheid, 1)

        stil = int((nu - self._laatste_beweging) / 60)
        onderweg = snelheid > drempel or stil < venster
        return onderweg, stil, round(snelheid, 1)

    def _snelheid_van_tracker(self) -> float | None:
        """Lees de snelheid uit de gevolgde tracker, als die hem meegeeft."""
        if self._opt(CONF_LOCATION_MODE, MODE_HOME) != MODE_TRACKER:
            return None

        entity_id = self._opt(CONF_TRACKER_ENTITY)
        if not entity_id:
            return None

        state = self.hass.states.get(entity_id)
        if state is None:
            return None

        rauw = state.attributes.get("speed")
        if rauw is None:
            return None

        try:
            snelheid = float(rauw)
        except (TypeError, ValueError):
            return None

        # De companion-app geeft meters per seconde; negatief betekent
        # onbekend.
        if snelheid < 0:
            return None
        return snelheid * 3.6

    def _snelheid_uit_punten(
        self, nu: float, latitude: float, longitude: float
    ) -> float | None:
        """Leid de snelheid af uit de bewaarde locatiepunten."""
        oudste = None
        for stempel, lat, lon in self._locaties:
            if nu - stempel <= SNELHEID_VENSTER:
                oudste = (stempel, lat, lon)
                break

        if oudste is None:
            return None

        verstreken = nu - oudste[0]
        if verstreken < 30:
            # Te kort om er iets zinnigs uit te halen
            return None

        meters = location_distance(latitude, longitude, oudste[1], oudste[2])
        if meters is None:
            return None

        return meters / verstreken * 3.6

    @staticmethod
    def _trend_from_speed(speed: float | None) -> str:
        """Vertaal een snelheid naar een leesbare trend."""
        if speed is None:
            return TREND_UNKNOWN
        if speed > 3:
            return TREND_FAST_APPROACH
        if speed > SPEED_DEADZONE:
            return TREND_APPROACH
        if speed < -3:
            return TREND_FAST_RECEDE
        if speed < -SPEED_DEADZONE:
            return TREND_RECEDE
        return TREND_STABLE

    def _fire_events(self, data: StormData) -> None:
        """Vuur events af bij overgangen, niet bij elke update.

        Zo kunnen automatiseringen op één moment reageren zonder zelf te
        moeten bijhouden of de situatie al bekend was.
        """
        payload = {
            "afstand": data.distance,
            "azimut": data.azimuth,
            "snelheid": data.speed,
            "aankomst_minuten": data.eta,
            "trend": data.trend,
            "inslagen": data.rings,
            "locatie_bron": data.location_source,
        }

        if data.distance is not None:
            nearby = data.distance < self.warn_distance
            if nearby and self._was_nearby is False:
                self.hass.bus.async_fire(EVENT_NEARBY, payload)
                if self.stats is not None:
                    self.stats.noteer_event("nearby")
            elif (
                not nearby
                and self._was_nearby
                and data.distance > self.warn_distance * CLEARED_FACTOR
            ):
                self.hass.bus.async_fire(EVENT_CLEARED, payload)
                if self.stats is not None:
                    self.stats.noteer_event("cleared")
                self._was_nearby = False
            if nearby:
                self._was_nearby = True
            elif self._was_nearby is None:
                self._was_nearby = False

        if data.speed is not None:
            approaching = data.speed > SPEED_DEADZONE
            if approaching and self._was_approaching is False:
                self.hass.bus.async_fire(EVENT_APPROACHING, payload)
                if self.stats is not None:
                    self.stats.noteer_event("approaching")
            self._was_approaching = approaching

    async def _async_update_data(self) -> StormData:
        """Werk de afgeleide gegevens bij."""
        distance = self._read_float(self._opt(CONF_DISTANCE_SENSOR))
        azimuth = self._read_float(self._opt(CONF_AZIMUTH_SENSOR))
        counter = self._read_float(self._opt(CONF_COUNTER_SENSOR))
        pattern = self._opt(CONF_GEO_PATTERN, DEFAULT_GEO_PATTERN)

        latitude, longitude, source_name = self.resolve_location()
        onderweg, stil_sinds, eigen_snelheid = self._beweging(
            latitude, longitude, source_name
        )

        # Kunnen we de inslagen zelf doorrekenen vanaf waar we nu zijn? Dan
        # heeft dat de voorkeur boven de waarden van de bron, want die rekent
        # mogelijk vanaf een heel ander punt. Dit moet gebeuren voordat de
        # snelheid wordt bepaald, anders rekent de trend met de oude maatstaf.
        punten, gewijzigd = self._uit_geo_location(pattern, latitude, longitude)
        afstand_bron = "sensor"
        last_strike = None

        if punten:
            punten.sort()
            distance, azimuth = punten[0]
            afstand_bron = "herberekend"
            last_strike = gewijzigd

            markers = len(punten)
            rings = {
                grens: sum(1 for d, _ in punten if d < grens)
                for grens in self.ring_bounds
            }
            ring_bron = "geo_location (herberekend)"
        else:
            markers, rings, ring_bron = self._count_rings(pattern)
            bron_state = self.hass.states.get(self._opt(CONF_DISTANCE_SENSOR, ""))
            if bron_state is not None and distance is not None:
                last_strike = bron_state.last_changed

        # Pas nu de reeks bijwerken, met de afstand die we uiteindelijk
        # gebruiken. Anders lopen twee maatstaven door elkaar en springt de
        # berekende snelheid bij het omschakelen.
        if distance is not None:
            self._history.append((dt_util.utcnow().timestamp(), distance))

        speed = self._speed_from_history()
        trend = self._trend_from_speed(speed)

        eta = None
        if speed is not None and speed > SPEED_DEADZONE and distance:
            eta = int(round(distance / speed * 60))

        # Meet Blitzortung vanaf hetzelfde punt als wij?
        bz = blitzortung_locatie(self.hass)
        afwijking = None
        if bz is not None:
            meters = location_distance(
                latitude, longitude, bz["latitude"], bz["longitude"]
            )
            if meters is not None:
                afwijking = round(meters / 1000, 1)

        # Ben je verplaatst, haal de weerparameters dan meteen opnieuw op
        # in plaats van tot het volgende half uur te wachten.
        if self.meteo is not None:
            self.meteo.note_location(latitude, longitude)
        if self.alerts is not None:
            self.alerts.note_location(latitude, longitude)

        data = StormData(
            distance=distance,
            azimuth=azimuth,
            counter=int(counter) if counter is not None else None,
            speed=speed,
            eta=eta,
            trend=trend,
            markers=markers,
            rings=rings,
            ring_bron=ring_bron,
            afstand_bron=afstand_bron,
            last_strike=last_strike,
            latitude=latitude,
            longitude=longitude,
            location_source=source_name,
            adres=self._lees_adres(),
            onderweg=onderweg,
            stil_sinds=stil_sinds,
            reissnelheid=eigen_snelheid,
            blitzortung=bz,
            afwijking_km=afwijking,
        )

        if self.stats is not None:
            self.stats.noteer_meting(distance, speed)

        self._fire_events(data)
        return data


class MeteoCoordinator(LocationMixin, DataUpdateCoordinator[dict]):
    """Haalt onweersparameters op bij Open-Meteo.

    De coordinaten komen uit de locatie-instelling van de integratie, dus
    op vakantie krijg je de parameters van waar je dan bent.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiseer de coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.title} meteo",
            update_interval=METEO_INTERVAL,
        )
        self.entry = entry
        self._session = async_get_clientsession(hass)
        self._fetched_at: tuple[float, float] | None = None
        self._was_winderig: bool | None = None
        self._vorige_condities: set[str] | None = None
        self._vorige_rang: int | None = None

    def _controleer_wind(self, windstoten: float | None) -> None:
        """Meld het als de wind boven de drempel uitkomt.

        Alleen bij de overgang, zodat je niet elk half uur opnieuw bericht
        krijgt zolang het hard waait.
        """
        if windstoten is None:
            return

        drempel = float(self._opt(CONF_WIND_THRESHOLD, DEFAULT_WIND_THRESHOLD))
        winderig = windstoten >= drempel

        if winderig and self._was_winderig is False:
            if self.stats is not None:
                self.stats.noteer_event("wind")
            self.hass.bus.async_fire(
                CONF_OUTLOOK_LEVEL,
    DEFAULT_OUTLOOK_LEVEL,
    EVENT_OUTLOOK,
    EVENT_WEATHER,
    OUTLOOK_RANGEN,
    EVENT_WIND, {"windstoten": windstoten, "drempel": drempel}
            )

        self._was_winderig = winderig

    def _controleer_vooruitzicht(
        self, oordeel: str, toelichting: str, rang: int
    ) -> None:
        """Meld het wanneer het vooruitzicht opschaalt.

        Alleen omhoog en alleen over de drempel heen: van kans op onweer naar
        kans op zwaar onweer is nieuws, andersom niet. Zakt het weer, dan kan
        een volgende opschaling opnieuw gemeld worden.
        """
        drempel = OUTLOOK_RANGEN.get(
            self._opt(CONF_OUTLOOK_LEVEL, DEFAULT_OUTLOOK_LEVEL), 3
        )

        if self._vorige_rang is None:
            self._vorige_rang = rang
            return

        if rang >= drempel and rang > self._vorige_rang:
            if self.stats is not None:
                self.stats.noteer_event("outlook")
            self.hass.bus.async_fire(
                EVENT_OUTLOOK,
                {"oordeel": oordeel, "toelichting": toelichting, "rang": rang},
            )

        self._vorige_rang = rang

    def _controleer_weer(self, huidig: dict) -> None:
        """Meld bijzondere weersituaties zodra ze intreden.

        Alleen bij het intreden, niet zolang ze duren: bij vorst zou je
        anders elk half uur opnieuw bericht krijgen tot de dooi invalt.
        """
        code = huidig.get("weather_code")
        temperatuur = huidig.get("temperature_2m")

        gekozen = set(self._opt(CONF_WEATHER_TYPES, DEFAULT_WEATHER_TYPES) or [])
        actief: set[str] = set()

        if code is not None:
            code = int(code)
            if code in CODES_SNEEUW:
                actief.add("sneeuw")
            if code in CODES_IJZEL:
                actief.add("ijzel")
            if code in CODES_MIST:
                actief.add("mist")

        if temperatuur is not None:
            hitte = float(self._opt(CONF_HEAT_THRESHOLD, DEFAULT_HEAT_THRESHOLD))
            vorst = float(self._opt(CONF_FROST_THRESHOLD, DEFAULT_FROST_THRESHOLD))
            if temperatuur >= hitte:
                actief.add("hitte")
            if temperatuur <= vorst:
                actief.add("vorst")

        # Eerste ronde na het opstarten alleen vastleggen, anders krijg je bij
        # elke herstart opnieuw bericht over een situatie die al liep.
        if self._vorige_condities is None:
            self._vorige_condities = actief
            return

        for soort in actief - self._vorige_condities:
            if soort not in gekozen:
                continue
            if self.stats is not None:
                self.stats.noteer_event("weather")
            self.hass.bus.async_fire(
                CONF_OUTLOOK_LEVEL,
    DEFAULT_OUTLOOK_LEVEL,
    EVENT_OUTLOOK,
    EVENT_WEATHER,
    OUTLOOK_RANGEN,
                {
                    "soort": soort,
                    "temperatuur": temperatuur,
                    "gevoelstemperatuur": huidig.get("apparent_temperature"),
                    "weercode": code,
                    "sneeuwval": huidig.get("snowfall"),
                    "neerslag": huidig.get("precipitation"),
                    "windstoten": huidig.get("wind_gusts_10m"),
                    "luchtvochtigheid": huidig.get("relative_humidity_2m"),
                },
            )

        self._vorige_condities = actief

    def note_location(self, latitude: float, longitude: float) -> None:
        """Forceer een verversing als de locatie flink verschoven is."""
        if self._fetched_at is None:
            return
        moved = location_distance(
            self._fetched_at[0], self._fetched_at[1], latitude, longitude
        )
        if moved is not None and moved / 1000 > MOVE_THRESHOLD_KM:
            _LOGGER.debug("Locatie %.0f km verschoven, weerdata verversen", moved / 1000)
            self._fetched_at = None
            self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self) -> dict:
        """Haal de laatste modelwaarden op."""
        latitude, longitude, source_name = self.resolve_location()

        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "hourly": (
                f"{METEO_HOURLY},temperature_2m,apparent_temperature,"
                "precipitation,precipitation_probability,weather_code,"
                "wind_speed_10m,wind_direction_10m,wind_gusts_10m,"
                "relative_humidity_2m,pressure_msl,freezing_level_height,"
                # Winden op hoogte, nodig voor de windschering
                "wind_speed_850hPa,wind_direction_850hPa,"
                "wind_speed_500hPa,wind_direction_500hPa,"
                # Temperaturen op hoogte, nodig voor Total Totals
                "temperature_850hPa,dew_point_850hPa,temperature_500hPa"
            ),
            "current": (
                "temperature_2m,apparent_temperature,relative_humidity_2m,"
                "is_day,precipitation,rain,showers,snowfall,weather_code,"
                "cloud_cover,pressure_msl,"
                "wind_speed_10m,wind_direction_10m,wind_gusts_10m"
            ),
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_sum,precipitation_probability_max,"
                "wind_speed_10m_max,wind_direction_10m_dominant"
            ),
            "forecast_days": 7,
            "timezone": str(self.hass.config.time_zone),
        }

        try:
            async with async_timeout.timeout(20):
                response = await self._session.get(METEO_URL, params=params)
                response.raise_for_status()
                payload = await response.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            if self.stats is not None:
                self.stats.bronnen["open_meteo"].fout(err)
            raise UpdateFailed(f"Open-Meteo niet bereikbaar: {err}") from err

        hourly = payload.get("hourly") or {}
        times: list[str] = hourly.get("time") or []
        if not times:
            raise UpdateFailed("Open-Meteo gaf geen uurdata terug")

        # Zoek het huidige uur op; valt dat buiten de reeks, pak dan het
        # eerste uur dat nog komt in plaats van te falen.
        stamp = dt_util.now().strftime("%Y-%m-%dT%H:00")
        if stamp in times:
            index = times.index(stamp)
        else:
            index = next((i for i, t in enumerate(times) if t >= stamp), 0)

        def at_index(key: str):
            values = hourly.get(key) or []
            if index < len(values):
                return values[index]
            return None

        cape_window = [
            v for v in (hourly.get("cape") or [])[index : index + 12] if v is not None
        ]

        self._fetched_at = (latitude, longitude)
        if self.stats is not None:
            self.stats.bronnen["open_meteo"].succes()

        huidig = payload.get("current") or {}
        self._controleer_wind(huidig.get("wind_gusts_10m"))
        self._controleer_weer(huidig)

        # Windschering en de afgeleide kansen op rotatie en hagel. Dit zijn
        # omgevingsinschattingen; zie indices.py voor wat ze wel en niet
        # zeggen.
        schering_6km = windschering(
            at_index("wind_speed_10m"),
            at_index("wind_direction_10m"),
            at_index("wind_speed_500hPa"),
            at_index("wind_direction_500hPa"),
        )
        schering_1km = windschering(
            at_index("wind_speed_10m"),
            at_index("wind_direction_10m"),
            at_index("wind_speed_850hPa"),
            at_index("wind_direction_850hPa"),
        )
        vriesniveau = at_index("freezing_level_height")
        cape_nu = at_index("cape")

        tt = total_totals(
            at_index("temperature_850hPa"),
            at_index("dew_point_850hPa"),
            at_index("temperature_500hPa"),
        )
        li = at_index("lifted_index")

        rotatie, rotatie_detail = rotatiekans(cape_nu, schering_6km)
        hagel, hagel_detail = hagelkans(
            cape_nu, schering_6km, vriesniveau, at_index("weather_code")
        )

        cape_piek = max(cape_window) if cape_window else None
        oordeel, toelichting, rang = onweersverwachting(
            cape_piek, li, tt, schering_6km, rotatie, hagel
        )
        self._controleer_vooruitzicht(oordeel, toelichting, rang)

        return {
            "cape": at_index("cape"),
            "verwachting": oordeel,
            "verwachting_rang": rang,
            "verwachting_toelichting": toelichting,
            "duiding_cape": duiding_cape(cape_piek),
            "duiding_stabiliteit": duiding_stabiliteit(li, tt),
            "duiding_schering": duiding_schering(schering_6km),
            "duiding_vriesniveau": duiding_vriesniveau(vriesniveau),
            "schering_6km": schering_6km,
            "schering_1km": schering_1km,
            "vriesniveau": vriesniveau,
            "total_totals": tt,
            "rotatiekans": rotatie,
            "rotatie_detail": rotatie_detail,
            "hagelkans": hagel,
            "hagel_detail": hagel_detail,
            "cape_peak": cape_piek,
            "lifted_index": at_index("lifted_index"),
            "cin": at_index("convective_inhibition"),
            "latitude": latitude,
            "longitude": longitude,
            "location_source": source_name,
            "windstoten": (payload.get("current") or {}).get("wind_gusts_10m"),
            "current": payload.get("current") or {},
            "hourly": hourly,
            "hourly_index": index,
            "daily": payload.get("daily") or {},
        }
