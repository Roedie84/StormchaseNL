"""Schakelaar voor de meldingen van Stormchase."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DATA_NOTIFY_ENABLED, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Zet de schakelaar op."""
    async_add_entities([NotifySwitch(hass, entry)])


class NotifySwitch(SwitchEntity, RestoreEntity):
    """Zet de onweersmeldingen aan of uit.

    Handig om vanaf het dashboard tijdelijk stil te leggen zonder de
    instellingen te hoeven aanpassen. De stand blijft bewaard na een
    herstart.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "notifications"
    _attr_icon = "mdi:bell-ring"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiseer de schakelaar."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_notifications"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Stormchase",
            manufacturer="Stormchase",
            model="Onweersmonitor",
        )
        self._is_on = True

    async def async_added_to_hass(self) -> None:
        """Herstel de vorige stand."""
        await super().async_added_to_hass()
        vorige = await self.async_get_last_state()
        if vorige is not None:
            self._is_on = vorige.state == "on"
        self._bewaar()

    def _bewaar(self) -> None:
        """Deel de stand met de notifier."""
        gegevens = self.hass.data.setdefault(DOMAIN, {}).setdefault(
            self._entry.entry_id, {}
        )
        gegevens[DATA_NOTIFY_ENABLED] = self._is_on

    @property
    def is_on(self) -> bool:
        """Staan de meldingen aan?"""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Meldingen inschakelen."""
        self._is_on = True
        self._bewaar()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Meldingen uitschakelen."""
        self._is_on = False
        self._bewaar()
        self.async_write_ha_state()
