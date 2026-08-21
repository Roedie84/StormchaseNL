"""Binary sensors voor Stormchase."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_WARN_DISTANCE,
    DEFAULT_WARN_DISTANCE,
    DOMAIN,
    SPEED_DEADZONE,
)
from .coordinator import StormCoordinator
from .alerts import AlertCoordinator
from .rain import RainCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Zet de binary sensors op."""
    storm: StormCoordinator = hass.data[DOMAIN][entry.entry_id]["storm"]
    regen: RainCoordinator = hass.data[DOMAIN][entry.entry_id]["rain"]
    async_add_entities(
        [
            StormNearbyBinarySensor(storm, entry),
            StormApproachingBinarySensor(storm, entry),
            RainExpectedBinarySensor(regen, entry),
            AlertActiveBinarySensor(
                hass.data[DOMAIN][entry.entry_id]["alerts"], entry
            ),
            MovingBinarySensor(storm, entry),
        ]
    )


def _device(entry: ConfigEntry) -> DeviceInfo:
    """Hetzelfde apparaat als de sensoren."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Stormchase",
        manufacturer="Stormchase",
        model="Onweersmonitor",
    )


class StormNearbyBinarySensor(CoordinatorEntity[StormCoordinator], BinarySensorEntity):
    """Aan zodra de laatste inslag binnen de waarschuwingsafstand valt."""

    _attr_has_entity_name = True
    _attr_translation_key = "nearby"
    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(self, coordinator: StormCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_nearby"
        self._attr_device_info = _device(entry)

    @property
    def _threshold(self) -> float:
        """Actuele waarschuwingsafstand."""
        return float(
            self._entry.options.get(
                CONF_WARN_DISTANCE,
                self._entry.data.get(CONF_WARN_DISTANCE, DEFAULT_WARN_DISTANCE),
            )
        )

    @property
    def is_on(self) -> bool | None:
        """True bij onweer binnen de drempel."""
        if not self.coordinator.data or self.coordinator.data.distance is None:
            return None
        return self.coordinator.data.distance < self._threshold

    @property
    def extra_state_attributes(self) -> dict:
        """Context voor automatiseringen."""
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "afstand": data.distance,
            "azimut": data.azimuth,
            "drempel": self._threshold,
            "trend": data.trend,
            "aankomst_minuten": data.eta,
        }


class StormApproachingBinarySensor(
    CoordinatorEntity[StormCoordinator], BinarySensorEntity
):
    """Aan wanneer de afstand structureel afneemt."""

    _attr_has_entity_name = True
    _attr_translation_key = "approaching"

    def __init__(self, coordinator: StormCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_approaching"
        self._attr_device_info = _device(entry)

    @property
    def is_on(self) -> bool | None:
        """True als het onweer dichterbij komt."""
        if not self.coordinator.data or self.coordinator.data.speed is None:
            return None
        return self.coordinator.data.speed > SPEED_DEADZONE

    @property
    def extra_state_attributes(self) -> dict:
        """Snelheid en verwachte aankomst."""
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "snelheid_kmh": data.speed,
            "aankomst_minuten": data.eta,
            "trend": data.trend,
        }


class RainExpectedBinarySensor(CoordinatorEntity[RainCoordinator], BinarySensorEntity):
    """Aan wanneer er binnen de ingestelde tijd regen wordt verwacht."""

    _attr_has_entity_name = True
    _attr_translation_key = "rain_expected"
    _attr_device_class = BinarySensorDeviceClass.MOISTURE

    def __init__(self, coordinator: RainCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_rain_expected"
        self._attr_device_info = _device(entry)

    @property
    def is_on(self) -> bool | None:
        """True bij regen nu of binnenkort."""
        data = self.coordinator.data
        if not data:
            return None
        if data.get("regent"):
            return True
        begint = data.get("begint_over")
        return begint is not None and begint <= self.coordinator.vooruit

    @property
    def extra_state_attributes(self) -> dict:
        """Context voor automatiseringen."""
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "regent_nu": data.get("regent"),
            "begint_over_minuten": data.get("begint_over"),
            "stopt_over_minuten": data.get("stopt_over"),
            "intensiteit_mm_u": data.get("intensiteit"),
            "piek_mm_u": data.get("piek"),
        }


class AlertActiveBinarySensor(CoordinatorEntity[AlertCoordinator], BinarySensorEntity):
    """Aan zolang er een officiele waarschuwing van kracht is."""

    _attr_has_entity_name = True
    _attr_translation_key = "alert_active"
    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(self, coordinator: AlertCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_alert_active"
        self._attr_device_info = _device(entry)

    @property
    def is_on(self) -> bool | None:
        """True bij een of meer actieve waarschuwingen."""
        if self.coordinator.data is None:
            return None
        return bool(self.coordinator.data.get("aantal"))

    @property
    def extra_state_attributes(self) -> dict:
        """De zwaarste waarschuwing kort samengevat."""
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "niveau": data.get("niveau"),
            "soort": data.get("soort"),
            "gebied": data.get("gebied"),
            "aantal": data.get("aantal"),
        }


class MovingBinarySensor(CoordinatorEntity[StormCoordinator], BinarySensorEntity):
    """Aan wanneer je onderweg bent, uit wanneer je ergens staat.

    Bepaalt of meldingen over het weer ter plaatse zinvol zijn: tijdens het
    rijden is een bericht over regen hier alweer achterhaald voor je het
    leest.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "moving"
    _attr_device_class = BinarySensorDeviceClass.MOVING

    def __init__(self, coordinator: StormCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_moving"
        self._attr_device_info = _device(entry)

    @property
    def is_on(self) -> bool | None:
        """True als je in beweging bent."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.onderweg

    @property
    def extra_state_attributes(self) -> dict:
        """Hoe lang je al op dezelfde plek staat."""
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "stil_sinds_minuten": data.stil_sinds,
            "locatie_bron": data.location_source,
        }
