"""Sensoren voor Stormchase."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MeteoCoordinator, StormCoordinator, StormData
from .alerts import AlertCoordinator
from .rain import RainCoordinator


@dataclass(frozen=True, kw_only=True)
class StormSensorDescription(SensorEntityDescription):
    """Beschrijving van een sensor die op de stormcoordinator draait."""

    value: Callable[[StormData], float | str | None]


@dataclass(frozen=True, kw_only=True)
class MeteoSensorDescription(SensorEntityDescription):
    """Beschrijving van een sensor die op de meteocoordinator draait."""

    value: Callable[[dict], float | None]


STORM_SENSORS: tuple[StormSensorDescription, ...] = (
    StormSensorDescription(
        key="distance",
        translation_key="distance",
        native_unit_of_measurement="km",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value=lambda data: data.distance,
    ),
    StormSensorDescription(
        key="azimuth",
        translation_key="azimuth",
        native_unit_of_measurement="\u00b0",
        suggested_display_precision=0,
        value=lambda data: data.azimuth,
    ),
    StormSensorDescription(
        key="approach_speed",
        translation_key="approach_speed",
        native_unit_of_measurement="km/h",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value=lambda data: data.speed,
    ),
    StormSensorDescription(
        key="eta",
        translation_key="eta",
        native_unit_of_measurement="min",
        suggested_display_precision=0,
        value=lambda data: data.eta,
    ),
    StormSensorDescription(
        key="trend",
        translation_key="trend",
        value=lambda data: data.trend,
    ),
    StormSensorDescription(
        key="markers",
        translation_key="markers",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda data: data.markers,
    ),
)

METEO_SENSORS: tuple[MeteoSensorDescription, ...] = (
    MeteoSensorDescription(
        key="cape",
        translation_key="cape",
        native_unit_of_measurement="J/kg",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value=lambda data: data.get("cape"),
    ),
    MeteoSensorDescription(
        key="cape_peak",
        translation_key="cape_peak",
        native_unit_of_measurement="J/kg",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value=lambda data: data.get("cape_peak"),
    ),
    MeteoSensorDescription(
        key="lifted_index",
        translation_key="lifted_index",
        native_unit_of_measurement="K",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value=lambda data: data.get("lifted_index"),
    ),
    MeteoSensorDescription(
        key="wind_gusts",
        translation_key="wind_gusts",
        native_unit_of_measurement="km/h",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value=lambda data: data.get("windstoten"),
    ),
    MeteoSensorDescription(
        key="wind_shear_6km",
        translation_key="wind_shear_6km",
        native_unit_of_measurement="km/h",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value=lambda data: data.get("schering_6km"),
    ),
    MeteoSensorDescription(
        key="wind_shear_1km",
        translation_key="wind_shear_1km",
        native_unit_of_measurement="km/h",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value=lambda data: data.get("schering_1km"),
    ),
    MeteoSensorDescription(
        key="freezing_level",
        translation_key="freezing_level",
        native_unit_of_measurement="m",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value=lambda data: data.get("vriesniveau"),
    ),
    MeteoSensorDescription(
        key="total_totals",
        translation_key="total_totals",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value=lambda data: data.get("total_totals"),
    ),
    MeteoSensorDescription(
        key="cin",
        translation_key="cin",
        native_unit_of_measurement="J/kg",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value=lambda data: data.get("cin"),
    ),
)


RAIN_SENSORS: tuple[MeteoSensorDescription, ...] = (
    MeteoSensorDescription(
        key="rain_starts",
        translation_key="rain_starts",
        native_unit_of_measurement="min",
        suggested_display_precision=0,
        value=lambda data: data.get("begint_over"),
    ),
    MeteoSensorDescription(
        key="rain_intensity",
        translation_key="rain_intensity",
        native_unit_of_measurement="mm/h",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value=lambda data: data.get("intensiteit"),
    ),
    MeteoSensorDescription(
        key="rain_peak",
        translation_key="rain_peak",
        native_unit_of_measurement="mm/h",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value=lambda data: data.get("piek"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Zet de sensoren op."""
    data = hass.data[DOMAIN][entry.entry_id]
    storm: StormCoordinator = data["storm"]
    meteo: MeteoCoordinator = data["meteo"]

    entities: list[SensorEntity] = [
        StormSensor(storm, entry, description) for description in STORM_SENSORS
    ]
    entities += [
        MeteoSensor(meteo, entry, description) for description in METEO_SENSORS
    ]
    entities += [
        RingSensor(storm, entry, bound, position)
        for position, bound in enumerate(storm.ring_bounds)
    ]
    entities.append(ChasePotentialSensor(meteo, storm, entry))

    waarschuwingen: AlertCoordinator = data["alerts"]
    entities.append(AlertSensor(waarschuwingen, entry))

    regen: RainCoordinator = data["rain"]
    entities += [RainSensor(regen, entry, beschrijving) for beschrijving in RAIN_SENSORS]
    entities.append(LocationSensor(storm, entry))
    entities += [
        SevereSensor(meteo, entry, "rotation", "rotatiekans", "rotatie_detail"),
        SevereSensor(meteo, entry, "hail", "hagelkans", "hagel_detail"),
    ]

    async_add_entities(entities)


def _device(entry: ConfigEntry) -> DeviceInfo:
    """Eén apparaat waar alle entiteiten onder hangen."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Stormchase",
        manufacturer="Stormchase",
        model="Onweersmonitor",
        entry_type=None,
    )


class StormSensor(CoordinatorEntity[StormCoordinator], SensorEntity):
    """Sensor op basis van de afgeleide stormgegevens."""

    _attr_has_entity_name = True
    entity_description: StormSensorDescription

    def __init__(
        self,
        coordinator: StormCoordinator,
        entry: ConfigEntry,
        description: StormSensorDescription,
    ) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = _device(entry)

    @property
    def native_value(self):
        """Huidige waarde."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict:
        """Context bij de waarde."""
        data = self.coordinator.data
        if not data:
            return {}

        if self.entity_description.key == "approach_speed":
            return {
                "afstand": data.distance,
                "azimut": data.azimuth,
                "trend": data.trend,
            }

        if self.entity_description.key == "distance":
            # herberekend = vanaf jouw positie, sensor = zoals de bron hem
            # aanlevert, mogelijk vanaf een heel ander punt
            return {"gemeten_via": data.afstand_bron, "inslagen": data.markers}

        return {}


class RingSensor(CoordinatorEntity[StormCoordinator], SensorEntity):
    """Aantal inslagen binnen een afstandsring."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:target"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: StormCoordinator,
        entry: ConfigEntry,
        bound: int,
        position: int,
    ) -> None:
        """Initialiseer de ringsensor."""
        super().__init__(coordinator)
        self._position = position
        self._attr_unique_id = f"{entry.entry_id}_ring_{position}"
        self._attr_name = f"Inslagen binnen {bound} km"
        self._attr_device_info = _device(entry)

    @property
    def _bound(self) -> int:
        """De actuele grens; volgt wijzigingen in de opties."""
        return self.coordinator.ring_bounds[self._position]

    @property
    def name(self) -> str:
        """Naam met de actuele grens erin."""
        return f"Inslagen binnen {self._bound} km"

    @property
    def native_value(self) -> int | None:
        """Aantal inslagen binnen deze ring."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.rings.get(self._bound)

    @property
    def extra_state_attributes(self) -> dict:
        """Waar de telling vandaan komt.

        geo_location is het meest volledig. Staat hier afstandssensor, dan
        maakt je Blitzortung-integratie geen geo_location entiteiten aan en
        tellen we de sprongen van de afstandssensor zelf.
        """
        if self.coordinator.data is None:
            return {}
        return {"telling_via": self.coordinator.data.ring_bron}


class MeteoSensor(CoordinatorEntity[MeteoCoordinator], SensorEntity):
    """Sensor op basis van de Open-Meteo modelwaarden."""

    _attr_has_entity_name = True
    entity_description: MeteoSensorDescription

    def __init__(
        self,
        coordinator: MeteoCoordinator,
        entry: ConfigEntry,
        description: MeteoSensorDescription,
    ) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = _device(entry)

    @property
    def native_value(self):
        """Huidige waarde."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value(self.coordinator.data)


class ChasePotentialSensor(CoordinatorEntity[MeteoCoordinator], SensorEntity):
    """Samengestelde score 0-100 voor de kans op iets interessants.

    Bewust simpel gehouden en volledig navolgbaar via de attributen:
    CAPE en Lifted Index bepalen het grootste deel, actieve inslagen in de
    buurt geven een opslag. Dit is een hulpmiddel, geen verwachting.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "chase_potential"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        meteo: MeteoCoordinator,
        storm: StormCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialiseer de sensor."""
        super().__init__(meteo)
        self._storm = storm
        self._attr_unique_id = f"{entry.entry_id}_chase_potential"
        self._attr_device_info = _device(entry)

    async def async_added_to_hass(self) -> None:
        """Luister ook naar de stormcoordinator."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._storm.async_add_listener(self.async_write_ha_state)
        )

    def _scores(self) -> tuple[float, float, float]:
        """Bereken de drie deelscores."""
        data = self.coordinator.data or {}

        cape = data.get("cape_peak") or 0
        cape_score = min(cape / 2500 * 50, 50)

        li = data.get("lifted_index")
        li_score = 0.0
        if li is not None and li < 0:
            li_score = min(abs(li) / 8 * 30, 30)

        strike_score = 0.0
        if self._storm.data and self._storm.data.rings:
            far = max(self._storm.ring_bounds)
            nearby = self._storm.data.rings.get(far, 0)
            strike_score = min(nearby / 50 * 20, 20)

        return cape_score, li_score, strike_score

    @property
    def native_value(self) -> int | None:
        """De totaalscore."""
        if self.coordinator.data is None:
            return None
        return round(sum(self._scores()))

    @property
    def extra_state_attributes(self) -> dict:
        """Laat zien hoe de score is opgebouwd."""
        cape_score, li_score, strike_score = self._scores()
        return {
            "cape_bijdrage": round(cape_score),
            "lifted_index_bijdrage": round(li_score),
            "inslagen_bijdrage": round(strike_score),
            "toelichting": (
                "CAPE-piek max 50, Lifted Index max 30, inslagen in de "
                "buitenste ring max 20"
            ),
        }


class LocationSensor(CoordinatorEntity[StormCoordinator], SensorEntity):
    """Laat zien welke locatie de integratie op dit moment gebruikt.

    Handig als je de zone of een device_tracker volgt: dan zie je in één
    oogopslag of de weerparameters bij je vakantieadres horen of nog bij
    thuis.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "location"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: StormCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_location"
        self._attr_device_info = _device(entry)

    @property
    def native_value(self) -> str | None:
        """De bron van de coordinaten."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.location_source

    @property
    def extra_state_attributes(self) -> dict:
        """De coordinaten, plus of Blitzortung vanaf hetzelfde punt meet.

        Die integratie heeft geen eigen locatie-entiteit, dus zonder deze
        vergelijking valt niet te controleren of de afstanden tot de inslagen
        bij het getoonde weer horen.
        """
        data = self.coordinator.data
        if not data:
            return {}

        uit = {
            "latitude": data.latitude,
            "longitude": data.longitude,
        }

        if data.adres:
            uit["adres"] = data.adres

        uit["afstand_via"] = data.afstand_bron

        if data.blitzortung:
            uit["blitzortung_meet_vanaf"] = data.blitzortung.get("bron")
            uit["blitzortung_integratie"] = data.blitzortung.get("naam")
            uit["afwijking_km"] = data.afwijking_km

            # Alleen waarschuwen als we het niet zelf kunnen rechttrekken
            if (
                data.afwijking_km is not None
                and data.afwijking_km > 5
                and data.afstand_bron != "herberekend"
            ):
                uit["let_op"] = (
                    f"Blitzortung meet {data.afwijking_km} km verderop. "
                    "Kies daar dezelfde locatiebron, anders horen de "
                    "bliksemafstanden niet bij dit weerbeeld."
                )
        else:
            uit["blitzortung_meet_vanaf"] = "niet gevonden"

        return uit


class RainSensor(CoordinatorEntity[RainCoordinator], SensorEntity):
    """Sensor op basis van de neerslagverwachting."""

    _attr_has_entity_name = True
    entity_description: MeteoSensorDescription

    def __init__(
        self,
        coordinator: RainCoordinator,
        entry: ConfigEntry,
        description: MeteoSensorDescription,
    ) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = _device(entry)

    @property
    def native_value(self):
        """Huidige waarde."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict:
        """De volledige verwachting hangt aan de starttijd-sensor.

        Zo kun je er zelf een grafiek of automatisering op bouwen zonder dat
        elke sensor dezelfde lijst meedraagt.
        """
        data = self.coordinator.data
        if not data or self.entity_description.key != "rain_starts":
            return {}
        return {
            "regent": data.get("regent"),
            "stopt_over": data.get("stopt_over"),
            "totaal_mm_2u": data.get("totaal"),
            "bron": data.get("bron"),
            "verwachting": data.get("verwachting"),
        }


class AlertSensor(CoordinatorEntity[AlertCoordinator], SensorEntity):
    """Het zwaarste actieve waarschuwingsniveau."""

    _attr_has_entity_name = True
    _attr_translation_key = "alert_level"

    def __init__(self, coordinator: AlertCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_alert_level"
        self._attr_device_info = _device(entry)

    @property
    def native_value(self) -> str | None:
        """Groen als er niets speelt, anders de kleur van de waarschuwing."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("niveau") or "groen"

    @property
    def extra_state_attributes(self) -> dict:
        """Alle actieve waarschuwingen, zwaarste eerst."""
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "aantal": data.get("aantal"),
            "soort": data.get("soort"),
            "gebied": data.get("gebied"),
            "land": data.get("land"),
            "waarschuwingen": data.get("actief"),
        }


class SevereSensor(CoordinatorEntity[MeteoCoordinator], SensorEntity):
    """Kans op rotatie of hagel, afgeleid uit de omgeving.

    Nadrukkelijk geen detectie: rotatie vraagt dopplerradar en hagel vraagt
    dual-polarisatie, en die data is niet vrij beschikbaar. Wat hier staat is
    of de atmosfeer het toelaat. De opbouw van de score staat in de
    attributen, zodat je kunt zien waar een getal vandaan komt.
    """

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: MeteoCoordinator,
        entry: ConfigEntry,
        sleutel: str,
        waardeveld: str,
        detailveld: str,
    ) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator)
        self._waardeveld = waardeveld
        self._detailveld = detailveld
        self._attr_translation_key = sleutel
        self._attr_unique_id = f"{entry.entry_id}_{sleutel}"
        self._attr_device_info = _device(entry)

    @property
    def native_value(self) -> int | None:
        """De score van 0 tot 100."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._waardeveld)

    @property
    def extra_state_attributes(self) -> dict:
        """Hoe de score is opgebouwd."""
        if self.coordinator.data is None:
            return {}
        return self.coordinator.data.get(self._detailveld) or {}
