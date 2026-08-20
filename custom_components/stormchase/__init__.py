"""De Stormchase integratie.

Bouwt een afgeleide laag bovenop een bestaande Blitzortung-integratie:
naderingssnelheid, aankomsttijd, afstandsringen en onweersparameters uit
Open-Meteo. De coordinaten komen uit de Home Assistant configuratie.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from homeassistant.loader import async_get_integration

from .const import DOMAIN
from .coordinator import MeteoCoordinator, StormCoordinator
from .frontend import async_register_frontend

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Zet de integratie op vanuit een config entry."""
    integration = await async_get_integration(hass, DOMAIN)
    await async_register_frontend(hass, integration.version or "0")

    storm = StormCoordinator(hass, entry)
    meteo = MeteoCoordinator(hass, entry)

    # De storm-coordinator mag de meteo-coordinator laten verversen zodra
    # de locatie flink verschuift.
    storm.meteo = meteo

    await storm.async_config_entry_first_refresh()
    # Open-Meteo mag falen zonder de hele integratie te blokkeren; de
    # bliksemsensoren zijn het belangrijkste deel.
    await meteo.async_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "storm": storm,
        "meteo": meteo,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Ruim de integratie op."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Herlaad na een wijziging in de opties."""
    await hass.config_entries.async_reload(entry.entry_id)
