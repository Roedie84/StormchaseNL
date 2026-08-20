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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Zet de binary sensors op."""
    storm: StormCoordinator = hass.data[DOMAIN][entry.entry_id]["storm"]
    async_add_entities(
        [
            StormNearbyBinarySensor(storm, entry),
            StormApproachingBinarySensor(storm, entry),
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
