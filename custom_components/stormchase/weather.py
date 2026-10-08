"""Weerentiteit voor Stormchase.

Toont het weer op de locatie die de integratie gebruikt. Reist die mee met een
device_tracker, dan doet het weerbericht dat ook.

0.49.0: in Nederland komen de huidige conditie, temperatuur, wind en de uur-
en dagverwachting van het KNMI (de API achter de KNMI-app). Luchtvochtigheid,
luchtdruk en bewolking blijven van Open-Meteo, net als alles buiten
Nederland. Regent het volgens de radar, dan wint de radar (0.48.0).
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

from .conditie import huidige_conditie, radar_intensiteit, wmo_conditie
from .const import DOMAIN, WMO_CONDITIES
from .coordinator import MeteoCoordinator, StormCoordinator
from .rain import RainCoordinator

# Een KNMI-verwachting ouder dan dit (storing) maakt plaats voor Open-Meteo
KNMI_MAX_VEROUDERD_MIN = 60


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Zet de weerentiteit op."""
    gegevens = hass.data[DOMAIN][entry.entry_id]
    meteo: MeteoCoordinator = gegevens["meteo"]
    async_add_entities(
        [
            StormchaseWeather(
                meteo,
                entry,
                gegevens.get("rain"),
                gegevens.get("storm"),
                gegevens.get("alerts"),
            )
        ]
    )


def _conditie(code: int | None, is_dag: bool = True) -> str | None:
    """Vertaal een WMO-weercode naar een Home Assistant conditie."""
    return wmo_conditie(code, WMO_CONDITIES, is_dag)


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

    def __init__(
        self,
        coordinator: MeteoCoordinator,
        entry: ConfigEntry,
        regen: RainCoordinator | None = None,
        storm: StormCoordinator | None = None,
        waarschuwingen=None,
    ) -> None:
        """Initialiseer de entiteit."""
        super().__init__(coordinator)
        # 0.48.0: de radar stuurt de huidige conditie bij als het nu regent.
        self._regen = regen
        self._storm = storm
        # 0.49.0: de KNMI-verwachting komt mee met de waarschuwingen
        self._waarschuwingen = waarschuwingen
        self._attr_unique_id = f"{entry.entry_id}_weather"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Stormchase",
            manufacturer="Stormchase",
            model="Onweersmonitor",
        )

    async def async_added_to_hass(self) -> None:
        """Ook bijwerken als de regen- of onweersgegevens veranderen."""
        await super().async_added_to_hass()
        for bron in (self._regen, self._storm, self._waarschuwingen):
            if bron is not None:
                self.async_on_remove(
                    bron.async_add_listener(self._handle_coordinator_update)
                )

    def _radar_mm(self) -> float | None:
        """Radarintensiteit van nu (mm/u), None als die ontbreekt of oud is."""
        regen = self._regen
        if regen is None:
            return None
        gelukt = getattr(regen, "_laatst_gelukt", None)
        leeftijd = (
            (dt_util.utcnow() - gelukt).total_seconds() if gelukt is not None else None
        )
        return radar_intensiteit(regen.data, leeftijd)

    def _onweer_dichtbij(self) -> bool:
        """Zelfde regel als binary_sensor 'onweer dichtbij'."""
        storm = self._storm
        data = getattr(storm, "data", None) if storm is not None else None
        afstand = getattr(data, "distance", None)
        if afstand is None:
            return False
        try:
            return afstand < storm.warn_distance
        except (TypeError, ValueError):
            return False

    @property
    def _nu(self) -> dict:
        """De huidige waarden."""
        return (self.coordinator.data or {}).get("current") or {}

    @property
    def _knmi(self) -> dict | None:
        """De KNMI-verwachting, alleen als die actueel is (in Nederland)."""
        bron = self._waarschuwingen
        data = getattr(bron, "data", None) if bron is not None else None
        if not isinstance(data, dict) or data.get("bron") != "knmi":
            return None
        if (data.get("verouderd_minuten") or 0) > KNMI_MAX_VEROUDERD_MIN:
            return None
        weer = data.get("knmi_weer") or {}
        return weer if weer.get("uren") else None

    def _knmi_uren(self) -> list[dict]:
        """De KNMI-uren vanaf het lopende uur (opgehaald kan tot een kwartier oud zijn)."""
        weer = self._knmi
        if not weer:
            return []
        begin = dt_util.utcnow().replace(minute=0, second=0, microsecond=0)
        uit = []
        for uur in weer.get("uren") or []:
            moment = dt_util.parse_datetime(str(uur.get("datetime")))
            if moment is not None and moment >= begin:
                uit.append(uur)
        return uit

    @property
    def _knmi_uur(self) -> dict:
        """Het lopende uur uit de KNMI-verwachting, of leeg."""
        uren = self._knmi_uren()
        return uren[0] if uren else {}

    def _knmi_of(self, sleutel: str, terugval):
        waarde = self._knmi_uur.get(sleutel)
        return waarde if waarde is not None else terugval

    @property
    def condition(self) -> str | None:
        """Huidige weersgesteldheid: KNMI of Open-Meteo, maar regen op de radar wint."""
        model = self._knmi_uur.get("condition") or _conditie(
            self._nu.get("weather_code"), bool(self._nu.get("is_day", 1))
        )
        mm = self._radar_mm()
        if mm is None:
            return model
        return huidige_conditie(model, mm, self._onweer_dichtbij())

    @property
    def native_temperature(self) -> float | None:
        """Temperatuur."""
        return self._knmi_of("native_temperature", self._nu.get("temperature_2m"))

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
        return self._knmi_of("native_wind_speed", self._nu.get("wind_speed_10m"))

    @property
    def wind_bearing(self) -> float | None:
        """Windrichting."""
        return self._knmi_of("wind_bearing", self._nu.get("wind_direction_10m"))

    @property
    def native_wind_gust_speed(self) -> float | None:
        """Windstoten."""
        return self._knmi_of("native_wind_gust_speed", self._nu.get("wind_gusts_10m"))

    @property
    def cloud_coverage(self) -> float | None:
        """Bewolking."""
        return self._nu.get("cloud_cover")

    @property
    def attribution(self) -> str:
        """Bronvermelding."""
        if self._knmi is not None:
            return "Weergegevens van het KNMI (CC BY 4.0) en Open-Meteo"
        return "Weergegevens van Open-Meteo"

    @property
    def extra_state_attributes(self) -> dict:
        """Waar de verwachting vandaan komt."""
        return {"verwachting_bron": "knmi" if self._knmi is not None else "open-meteo"}

    @staticmethod
    def _als_forecast(items: list[dict]) -> list[Forecast] | None:
        """KNMI-items naar Forecast, zonder de eigen hulpvelden."""
        uit = [
            Forecast(**{k: v for k, v in item.items() if k != "weercode"})
            for item in items
        ]
        return uit or None

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Verwachting per uur, vanaf nu."""
        if self._knmi is not None:
            return self._als_forecast(self._knmi_uren())
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
        knmi = self._knmi
        if knmi is not None and knmi.get("dagen"):
            dagen = []
            for dag in knmi["dagen"]:
                # Zelfde vorm als bij Open-Meteo: de dag om 12:00 lokale tijd
                moment = dt_util.parse_datetime(f"{dag.get('datetime')}T12:00:00")
                if moment is None:
                    continue
                if moment.tzinfo is None:
                    moment = moment.replace(tzinfo=dt_util.now().tzinfo)
                dagen.append({**dag, "datetime": moment.isoformat()})
            return self._als_forecast(dagen)
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
