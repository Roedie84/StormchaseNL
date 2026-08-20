"""Registratie van de dashboardstrategie in de frontend."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, STRATEGY_FILE, STRATEGY_URL

_LOGGER = logging.getLogger(__name__)

_REGISTERED = f"{DOMAIN}_frontend_registered"


async def async_register_frontend(hass: HomeAssistant, version: str) -> None:
    """Serveer de strategie en laad hem in de frontend.

    Het versienummer zit in de URL. Bij een update van de integratie wijzigt
    die URL, waardoor browsers het bestand opnieuw ophalen in plaats van een
    oude versie uit de cache te gebruiken. Zonder dat zou een nieuwe tegel
    pas verschijnen na een harde ververs.
    """
    if hass.data.get(_REGISTERED):
        return

    source = Path(__file__).parent / "www" / STRATEGY_FILE
    if not source.is_file():
        _LOGGER.warning("Strategiebestand niet gevonden op %s", source)
        return

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                STRATEGY_URL,
                str(source),
                # Cachen mag: de versie in de query zorgt voor verversing.
                cache_headers=True,
            )
        ]
    )

    add_extra_js_url(hass, f"{STRATEGY_URL}?v={version}")
    hass.data[_REGISTERED] = True

    _LOGGER.debug("Dashboardstrategie geregistreerd op %s (v%s)", STRATEGY_URL, version)
