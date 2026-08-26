"""Registratie van de dashboardstrategie in de frontend."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DOMAIN, STRATEGY_FILE, STRATEGY_URL

_LOGGER = logging.getLogger(__name__)

_REGISTERED = f"{DOMAIN}_frontend_registered"


async def _async_register_resource(hass: HomeAssistant, versioned_url: str) -> bool:
    """Zet het script in de Lovelace-bronnenlijst, of werk het bij.

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
        # Gebeurt bij Lovelace in YAML-modus, en soms als de integratie eerder
        # laadt dan Lovelace zelf.
        _LOGGER.warning(
            "Lovelace-bronnen niet beschikbaar; de dashboardstrategie moet "
            "handmatig als bron worden toegevoegd."
        )
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
        _LOGGER.warning(
            "Kon de dashboardstrategie niet als bron vastleggen: %s", err
        )
        return False


async def async_register_frontend(hass: HomeAssistant, version: str) -> None:
    """Serveer de strategie en zorg dat de frontend hem laadt.

    Het versienummer zit in de URL. Bij een update van de integratie wijzigt
    die URL, waardoor browsers het bestand opnieuw ophalen in plaats van een
    oude versie uit de cache te gebruiken.
    """
    source = Path(__file__).parent / "www" / STRATEGY_FILE
    if not source.is_file():
        _LOGGER.warning("Strategiebestand niet gevonden op %s", source)
        return

    # Het pad mag maar een keer geregistreerd worden. Bij een herlaad van de
    # integratie zonder herstart is dat al gebeurd; dat is geen fout en mag de
    # rest niet tegenhouden.
    if not hass.data.get(_REGISTERED):
        try:
            await hass.http.async_register_static_paths(
                [
                    StaticPathConfig(
                        STRATEGY_URL,
                        str(source),
                        # Cachen mag: de versie in de query zorgt voor
                        # verversing.
                        cache_headers=True,
                    )
                ]
            )
            hass.data[_REGISTERED] = True
        except (RuntimeError, ValueError) as err:
            _LOGGER.debug("Pad stond er al: %s", err)
            hass.data[_REGISTERED] = True

    # Versienummer plus starttijd. Het versienummer alleen bleek niet genoeg:
    # bij een update via HACS bleef de oude URL soms in de bronnenlijst staan,
    # waardoor de browser het oude script uit de cache bleef gebruiken. Met de
    # starttijd erbij wijzigt de URL bij elke herstart en is een herlaad
    # onvermijdelijk.
    stempel = int(dt_util.utcnow().timestamp())
    versioned_url = f"{STRATEGY_URL}?v={version}&t={stempel}"

    # Beide routes: de bron is leidend, add_extra_js_url vangt YAML-modus af.
    # Het script registreert zichzelf maar één keer, dus dubbel laden kan geen
    # kwaad.
    # Beide routes worden bij elke start opnieuw geprobeerd. Eerder werd dit
    # overgeslagen zodra het een keer gelukt leek, waardoor een mislukte
    # registratie nooit meer werd hersteld en het dashboard leeg bleef.
    via_resource = await _async_register_resource(hass, versioned_url)

    try:
        add_extra_js_url(hass, versioned_url)
    except Exception as err:  # noqa: BLE001 - mag de opstart niet blokkeren
        _LOGGER.debug("Kon het script niet aan de frontend meegeven: %s", err)

    if via_resource:
        _LOGGER.info("Dashboardstrategie geregistreerd op %s", versioned_url)
    else:
        _LOGGER.warning(
            "De dashboardstrategie kon niet als Lovelace-bron worden "
            "vastgelegd. Voeg %s handmatig toe onder Instellingen > "
            "Dashboards > Bronnen, als type JavaScript-module, en ververs "
            "daarna hard met Ctrl+Shift+R.",
            STRATEGY_URL,
        )
