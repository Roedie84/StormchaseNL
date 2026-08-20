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


async def _async_register_resource(hass: HomeAssistant, versioned_url: str) -> bool:
    """Zet het script in de Lovelace-bronnenlijst.

    Dit is de betrouwbaarste route: bronnen worden geladen op het moment dat
    een dashboard opstart, precies wanneer de strategie nodig is.
    add_extra_js_url alleen bleek in de praktijk niet altijd op tijd te
    landen, wat een 'Timeout waiting for strategy element' opleverde.

    Werkt niet als Lovelace in YAML-modus draait; dan moet de gebruiker de
    bron zelf toevoegen.
    """
    lovelace = hass.data.get("lovelace")
    resources = getattr(lovelace, "resources", None)
    if resources is None:
        _LOGGER.debug("Lovelace-bronnen niet beschikbaar")
        return False

    try:
        if hasattr(resources, "async_get_info"):
            await resources.async_get_info()

        bestaand = [
            item
            for item in resources.async_items()
            if str(item.get("url", "")).split("?")[0] == STRATEGY_URL
        ]

        # Bestaat hij al met dezelfde versie, dan is er niets te doen.
        for item in bestaand:
            if item.get("url") == versioned_url:
                return True

        if bestaand:
            # Versie in de URL bijwerken, zodat browsers het nieuwe script
            # ophalen in plaats van een oude uit de cache.
            await resources.async_update_item(
                bestaand[0]["id"], {"res_type": "module", "url": versioned_url}
            )
            _LOGGER.debug("Lovelace-bron bijgewerkt naar %s", versioned_url)
        else:
            await resources.async_create_item(
                {"res_type": "module", "url": versioned_url}
            )
            _LOGGER.debug("Lovelace-bron aangemaakt: %s", versioned_url)

        return True

    except Exception as err:  # noqa: BLE001 - Lovelace-API varieert per versie
        _LOGGER.debug("Kon de Lovelace-bron niet registreren: %s", err)
        return False


async def async_register_frontend(hass: HomeAssistant, version: str) -> None:
    """Serveer de strategie en zorg dat de frontend hem laadt.

    Het versienummer zit in de URL. Bij een update van de integratie wijzigt
    die URL, waardoor browsers het bestand opnieuw ophalen in plaats van een
    oude versie uit de cache te gebruiken.
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

    versioned_url = f"{STRATEGY_URL}?v={version}"

    # Beide routes: de bron is leidend, add_extra_js_url vangt YAML-modus af.
    # Het script registreert zichzelf maar één keer, dus dubbel laden kan geen
    # kwaad.
    via_resource = await _async_register_resource(hass, versioned_url)
    add_extra_js_url(hass, versioned_url)

    hass.data[_REGISTERED] = True

    if not via_resource:
        _LOGGER.info(
            "Stormchase-strategie geladen via extra_js_url. Blijft je "
            "dashboard leeg met 'Timeout waiting for strategy element', voeg "
            "%s dan handmatig toe onder Instellingen > Dashboards > Bronnen "
            "als type JavaScript-module.",
            STRATEGY_URL,
        )
