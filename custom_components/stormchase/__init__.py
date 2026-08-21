"""De Stormchase integratie.

Bouwt een afgeleide laag bovenop een bestaande Blitzortung-integratie:
naderingssnelheid, aankomsttijd, afstandsringen en onweersparameters uit
Open-Meteo. De coordinaten komen uit de Home Assistant configuratie.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from homeassistant.loader import async_get_integration

from .const import DOMAIN, SERVICE_TEST_NOTIFICATION
from .coordinator import MeteoCoordinator, StormCoordinator
from .alerts import AlertCoordinator
from .frontend import async_register_frontend
from .notifier import StormNotifier
from .rain import RainCoordinator
from .stats import Statistieken

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.WEATHER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Zet de integratie op vanuit een config entry."""
    integration = await async_get_integration(hass, DOMAIN)
    await async_register_frontend(hass, integration.version or "0")

    # De statistieken worden door alle onderdelen gevuld en komen terug in
    # het diagnosebestand.
    stats = Statistieken()

    storm = StormCoordinator(hass, entry)
    meteo = MeteoCoordinator(hass, entry)
    regen = RainCoordinator(hass, entry)
    waarschuwingen = AlertCoordinator(hass, entry)

    # De notifier luistert naar de events die de coordinator afvuurt en
    # stuurt daar meldingen over. Zit in de integratie zelf, zodat er geen
    # losse automatisering nodig is.
    notifier = StormNotifier(hass, entry)

    # Statistieken koppelen voor de eerste ophaalronde, anders mist die ronde
    # in de diagnostiek en zie je een gefaalde start niet terug.
    for onderdeel in (storm, meteo, regen, waarschuwingen, notifier):
        onderdeel.stats = stats

    # De storm-coordinator mag de meteo-coordinator laten verversen zodra
    # de locatie flink verschuift.
    storm.meteo = meteo

    await storm.async_config_entry_first_refresh()
    # Open-Meteo mag falen zonder de hele integratie te blokkeren; de
    # bliksemsensoren zijn het belangrijkste deel.
    await meteo.async_refresh()
    # Regen mag net als de weerparameters falen zonder de rest te blokkeren.
    await regen.async_refresh()
    await waarschuwingen.async_refresh()

    notifier.start()

    gegevens = hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})
    gegevens.update(
        {
            "storm": storm,
            "meteo": meteo,
            "rain": regen,
            "alerts": waarschuwingen,
            "notifier": notifier,
            "stats": stats,
        }
    )

    await _async_register_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def _async_register_services(hass: HomeAssistant) -> None:
    """Registreer de proefmelding-service, eenmalig."""
    if hass.services.has_service(DOMAIN, SERVICE_TEST_NOTIFICATION):
        return

    async def _test(call: ServiceCall) -> None:
        """Stuur een proefmelding via alle ingestelde diensten."""
        for gegevens in hass.data.get(DOMAIN, {}).values():
            notifier = gegevens.get("notifier")
            if notifier is not None:
                await notifier.async_test()

    hass.services.async_register(DOMAIN, SERVICE_TEST_NOTIFICATION, _test)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Ruim de integratie op."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        gegevens = hass.data[DOMAIN].pop(entry.entry_id, {})
        notifier = gegevens.get("notifier")
        if notifier is not None:
            notifier.stop()
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
            hass.services.async_remove(DOMAIN, SERVICE_TEST_NOTIFICATION)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Herlaad na een wijziging in de opties."""
    await hass.config_entries.async_reload(entry.entry_id)
