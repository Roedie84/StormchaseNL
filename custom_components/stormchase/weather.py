"""Weerentiteit voor Stormchase.

Toont het weer op de locatie die de integratie gebruikt. Reist die mee met een
device_tracker, dan doet het weerbericht dat ook.
"""

from __future__ import annotations

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, WMO_CONDITIES
from .coordinator import MeteoCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Zet de weerentiteit op."""
    meteo: MeteoCoordinator = hass.data[DOMAIN][entry.entry_id]["meteo"]
    async_add_entities([StormchaseWeather(meteo, entry)])


def _conditie(code: int | None, is_dag: bool = True) -> str | None:
    """Vertaal een WMO-weercode naar een Home Assistant conditie."""
    if code is None:
        return None
    conditie = WMO_CONDITIES.get(int(code))
    # Een heldere nacht is geen zon.
    if conditie == "sunny" and not is_dag:
        return "clear-night"
    return conditie


class StormchaseWeather(CoordinatorEntity[MeteoCoordinator], WeatherEntity):
    """Het weer op de actieve locatie."""

    _attr_has_entity_name = True
    _attr_name = None  # neemt de apparaatnaam over
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(self, coordinator: MeteoCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de entiteit."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_weather"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Stormchase",
            manufacturer="Stormchase",
            model="Onweersmonitor",
        )

    @property
    def _nu(self) -> dict:
        """De huidige waarden."""
        return (self.coordinator.data or {}).get("current") or {}

    @property
    def condition(self) -> str | None:
        """Huidige weersgesteldheid."""
        return _conditie(self._nu.get("weather_code"), bool(self._nu.get("is_day", 1)))

    @property
    def native_temperature(self) -> float | None:
        """Temperatuur."""
        return self._nu.get("temperature_2m")

    @property
    def native_apparent_temperature(self) -> float | None:
        """Gevoelstemperatuur."""
        return self._nu.get("apparent_temperature")

    @property
    def humidity(self) -> float | None:
        """Luchtvochtigheid."""
        return self._nu.get("relative_humidity_2m")

    @property
    def native_pressure(self) -> float | None:
        """Luchtdruk."""
        return self._nu.get("pressure_msl")

    @property
    def native_wind_speed(self) -> float | None:
        """Windsnelheid."""
        return self._nu.get("wind_speed_10m")

    @property
    def wind_bearing(self) -> float | None:
        """Windrichting."""
        return self._nu.get("wind_direction_10m")

    @property
    def native_wind_gust_speed(self) -> float | None:
        """Windstoten."""
        return self._nu.get("wind_gusts_10m")

    @property
    def cloud_coverage(self) -> float | None:
        """Bewolking."""
        return self._nu.get("cloud_cover")

    @property
    def attribution(self) -> str:
        """Bronvermelding."""
        return "Weergegevens van Open-Meteo"

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Verwachting per uur, vanaf nu."""
        data = self.coordinator.data or {}
        uurlijks = data.get("hourly") or {}
        start = data.get("hourly_index") or 0
        tijden = uurlijks.get("time") or []

        def reeks(sleutel: str) -> list:
            return uurlijks.get(sleutel) or []

        verwachting: list[Forecast] = []
        for i in range(start, min(start + 48, len(tijden))):
            moment = dt_util.parse_datetime(tijden[i])
            if moment is None:
                continue
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=dt_util.now().tzinfo)

            def op(sleutel: str, index: int = i):
                waarden = reeks(sleutel)
                return waarden[index] if index < len(waarden) else None

            verwachting.append(
                Forecast(
                    datetime=moment.isoformat(),
                    condition=_conditie(op("weather_code")),
                    native_temperature=op("temperature_2m"),
                    native_apparent_temperature=op("apparent_temperature"),
                    native_precipitation=op("precipitation"),
                    precipitation_probability=op("precipitation_probability"),
                    humidity=op("relative_humidity_2m"),
                    native_pressure=op("pressure_msl"),
                    native_wind_speed=op("wind_speed_10m"),
                    wind_bearing=op("wind_direction_10m"),
                    native_wind_gust_speed=op("wind_gusts_10m"),
                )
            )

        return verwachting or None

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Verwachting per dag."""
        dagelijks = (self.coordinator.data or {}).get("daily") or {}
        tijden = dagelijks.get("time") or []

        verwachting: list[Forecast] = []
        for i, stempel in enumerate(tijden):
            moment = dt_util.parse_datetime(f"{stempel}T12:00:00")
            if moment is None:
                continue
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=dt_util.now().tzinfo)

            def op(sleutel: str, index: int = i):
                waarden = dagelijks.get(sleutel) or []
                return waarden[index] if index < len(waarden) else None

            verwachting.append(
                Forecast(
                    datetime=moment.isoformat(),
                    condition=_conditie(op("weather_code")),
                    native_temperature=op("temperature_2m_max"),
                    native_templow=op("temperature_2m_min"),
                    native_precipitation=op("precipitation_sum"),
                    precipitation_probability=op("precipitation_probability_max"),
                    native_wind_speed=op("wind_speed_10m_max"),
                    wind_bearing=op("wind_direction_10m_dominant"),
                )
            )

        return verwachting or None
