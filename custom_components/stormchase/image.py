"""Radarbeeld dat je eigen positie volgt.

Een gewone entiteit in plaats van een ingesloten webpagina: geen
cookiemelding, geen advertenties, en het beeld schuift mee met de locatie die
de integratie gebruikt.
"""

from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_RADAR_KLEUR,
    CONF_RADAR_ZOOM,
    DEFAULT_RADAR_KLEUR,
    DEFAULT_RADAR_ZOOM,
    DOMAIN,
)
from .radar import bouw_url
from .radarbron import RadarCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Zet het radarbeeld op."""
    gegevens = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [RadarImage(hass, gegevens["radar"], gegevens["storm"], entry)]
    )


class RadarImage(CoordinatorEntity[RadarCoordinator], ImageEntity):
    """Het meest recente radarbeeld rond je positie."""

    _attr_has_entity_name = True
    _attr_translation_key = "radar"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: RadarCoordinator,
        storm,
        entry: ConfigEntry,
    ) -> None:
        """Initialiseer het beeld."""
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)

        self._storm = storm
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_radar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Stormchase",
            manufacturer="Stormchase",
            model="Onweersmonitor",
        )
        self._vorige_url: str | None = None

    def _opt(self, sleutel: str, standaard):
        """Instelling ophalen."""
        return self._entry.options.get(
            sleutel, self._entry.data.get(sleutel, standaard)
        )

    @property
    def image_url(self) -> str | None:
        """De URL van het huidige beeld, gecentreerd op de actieve locatie."""
        gegevens = self._storm.data if self._storm else None
        latitude = getattr(gegevens, "latitude", None)
        longitude = getattr(gegevens, "longitude", None)

        if latitude is None or longitude is None:
            latitude = self.hass.config.latitude
            longitude = self.hass.config.longitude

        return bouw_url(
            self.coordinator.data,
            latitude,
            longitude,
            zoom=self._opt(CONF_RADAR_ZOOM, DEFAULT_RADAR_ZOOM),
            kleur=self._opt(CONF_RADAR_KLEUR, DEFAULT_RADAR_KLEUR),
        )

    def _handle_coordinator_update(self) -> None:
        """Ververs het beeld wanneer er een nieuw frame is.

        Home Assistant haalt het plaatje pas op als de tijdstempel wijzigt,
        dus die moet mee wanneer de URL verandert.
        """
        url = self.image_url
        if url != self._vorige_url:
            self._vorige_url = url
            self._attr_image_last_updated = dt_util.utcnow()

        super()._handle_coordinator_update()

    @property
    def extra_state_attributes(self) -> dict:
        """Wanneer het beeld gemaakt is en waar het op centreert."""
        frame = self.coordinator.data or {}
        gegevens = self._storm.data if self._storm else None
        return {
            "beeld_tijd": frame.get("tijd"),
            "zoom": self._opt(CONF_RADAR_ZOOM, DEFAULT_RADAR_ZOOM),
            "locatie_bron": getattr(gegevens, "location_source", None),
        }
