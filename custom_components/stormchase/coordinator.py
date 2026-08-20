"""Coordinators voor de Stormchase integratie."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.util.location import distance as location_distance

from .const import (
    CLEARED_FACTOR,
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
    CONF_WARN_DISTANCE,
    CONF_ZONE_ENTITY,
    DEFAULT_GEO_PATTERN,
    DEFAULT_RING_FAR,
    DEFAULT_RING_MID,
    DEFAULT_RING_NEAR,
    DEFAULT_WARN_DISTANCE,
    EVENT_APPROACHING,
    EVENT_CLEARED,
    EVENT_NEARBY,
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
    STORM_INTERVAL,
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
    last_strike: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_source: str = "thuis"


class StormCoordinator(LocationMixin, DataUpdateCoordinator[StormData]):
    """Leest de Blitzortung-sensoren en berekent de afgeleide waarden.

    Bewust geen eigen verbinding met blitzortung.org: de bestaande
    Blitzortung-integratie doet dat al via MQTT. Een tweede verbinding
    zou alleen extra onderhoud opleveren.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiseer de coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.title} storm",
            update_interval=STORM_INTERVAL,
        )
        self.entry = entry
        self.meteo: MeteoCoordinator | None = None
        self._history: deque[tuple[float, float]] = deque(maxlen=240)
        self._was_nearby: bool | None = None
        self._was_approaching: bool | None = None

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

    def _count_rings(self, pattern: str) -> tuple[int, dict[int, int]]:
        """Tel de geo_location markers per afstandsring."""
        distances: list[float] = []
        for state in self.hass.states.async_all("geo_location"):
            if pattern not in state.entity_id:
                continue
            try:
                distances.append(float(state.state))
            except (TypeError, ValueError):
                continue

        rings = {bound: sum(1 for d in distances if d < bound) for bound in self.ring_bounds}
        return len(distances), rings

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
        return round(-slope * 3600, 1)

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
            elif (
                not nearby
                and self._was_nearby
                and data.distance > self.warn_distance * CLEARED_FACTOR
            ):
                self.hass.bus.async_fire(EVENT_CLEARED, payload)
                self._was_nearby = False
            if nearby:
                self._was_nearby = True
            elif self._was_nearby is None:
                self._was_nearby = False

        if data.speed is not None:
            approaching = data.speed > SPEED_DEADZONE
            if approaching and self._was_approaching is False:
                self.hass.bus.async_fire(EVENT_APPROACHING, payload)
            self._was_approaching = approaching

    async def _async_update_data(self) -> StormData:
        """Werk de afgeleide gegevens bij."""
        distance = self._read_float(self._opt(CONF_DISTANCE_SENSOR))
        azimuth = self._read_float(self._opt(CONF_AZIMUTH_SENSOR))
        counter = self._read_float(self._opt(CONF_COUNTER_SENSOR))
        pattern = self._opt(CONF_GEO_PATTERN, DEFAULT_GEO_PATTERN)

        last_strike = None
        if distance is not None:
            self._history.append((dt_util.utcnow().timestamp(), distance))
            source = self.hass.states.get(self._opt(CONF_DISTANCE_SENSOR, ""))
            if source is not None:
                last_strike = source.last_changed

        speed = self._speed_from_history()
        trend = self._trend_from_speed(speed)

        eta = None
        if speed is not None and speed > SPEED_DEADZONE and distance:
            eta = round(distance / speed * 60, 0)

        markers, rings = self._count_rings(pattern)
        latitude, longitude, source_name = self.resolve_location()

        # Ben je verplaatst, haal de weerparameters dan meteen opnieuw op
        # in plaats van tot het volgende half uur te wachten.
        if self.meteo is not None:
            self.meteo.note_location(latitude, longitude)

        data = StormData(
            distance=distance,
            azimuth=azimuth,
            counter=int(counter) if counter is not None else None,
            speed=speed,
            eta=eta,
            trend=trend,
            markers=markers,
            rings=rings,
            last_strike=last_strike,
            latitude=latitude,
            longitude=longitude,
            location_source=source_name,
        )

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
            "hourly": METEO_HOURLY,
            "forecast_days": 2,
            "timezone": str(self.hass.config.time_zone),
        }

        try:
            async with async_timeout.timeout(20):
                response = await self._session.get(METEO_URL, params=params)
                response.raise_for_status()
                payload = await response.json()
        except (aiohttp.ClientError, TimeoutError) as err:
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

        return {
            "cape": at_index("cape"),
            "cape_peak": max(cape_window) if cape_window else None,
            "lifted_index": at_index("lifted_index"),
            "cin": at_index("convective_inhibition"),
            "latitude": latitude,
            "longitude": longitude,
            "location_source": source_name,
        }
