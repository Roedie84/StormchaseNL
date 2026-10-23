"""Registratie van de dashboardstrategie in de frontend."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url

try:  # bestaat in alle recente versies; oudere hebben hem niet
    from homeassistant.components.frontend import remove_extra_js_url
except ImportError:  # pragma: no cover - afhankelijk van de HA-versie
    remove_extra_js_url = None
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DASHBOARD_URL, DOMAIN, FRONTEND_FILES, STRATEGY_URL

_LOGGER = logging.getLogger(__name__)

_REGISTERED = f"{DOMAIN}_frontend_registered"
_EXTRA_JS = f"{DOMAIN}_frontend_extra_js"

# Alles onder dit pad is van ons. Een bron daaronder die niet (meer) bij een
# van onze bestanden hoort, is verweesd en wordt opgeruimd.
_EIGEN_PREFIX = f"/{DOMAIN}/"


def _basis(url: str) -> str:
    """De URL zonder query (?v=...&t=...)."""
    return str(url or "").split("?")[0]


async def _async_register_resource(hass: HomeAssistant, *versioned_urls: str) -> bool:
    """Zet de scripts in de Lovelace-bronnenlijst, of werk ze bij.

    Dit is de betrouwbaarste route: bronnen worden geladen op het moment dat
    een dashboard opstart, precies wanneer de strategie nodig is.
    add_extra_js_url alleen bleek in de praktijk niet altijd op tijd te
    landen, wat een 'Timeout waiting for strategy element' opleverde.

    Per bestand blijft precies een bron over: de eerste wordt bijgewerkt,
    dubbele worden verwijderd. Bronnen onder /stormchase/ die bij geen enkel
    bestand meer horen (verweesd) worden ook verwijderd.

    Werkt niet als Lovelace in YAML-modus draait; dan moet de gebruiker de
    bronnen zelf toevoegen.
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

        gewenst = {_basis(url): url for url in versioned_urls}
        items = list(resources.async_items())

        # Verweesd: onder ons pad, maar geen van onze bestanden.
        for item in items:
            basis = _basis(item.get("url"))
            if basis.startswith(_EIGEN_PREFIX) and basis not in gewenst:
                await resources.async_delete_item(item["id"])
                _LOGGER.debug("Verweesde Lovelace-bron verwijderd: %s", item.get("url"))

        for basis, versioned_url in gewenst.items():
            bestaand = [item for item in items if _basis(item.get("url")) == basis]

            # Een exacte treffer houden we; anders de eerste bijwerken.
            houden = next(
                (item for item in bestaand if item.get("url") == versioned_url),
                bestaand[0] if bestaand else None,
            )
            for item in bestaand:
                if item is not houden:
                    await resources.async_delete_item(item["id"])
                    _LOGGER.debug("Dubbele Lovelace-bron verwijderd: %s", item.get("url"))

            if houden is None:
                await resources.async_create_item(
                    {"res_type": "module", "url": versioned_url}
                )
                _LOGGER.debug("Lovelace-bron aangemaakt: %s", versioned_url)
            elif houden.get("url") != versioned_url or houden.get("type", "module") != "module":
                # Versie in de URL bijwerken, zodat browsers het nieuwe script
                # ophalen in plaats van een oude uit de cache.
                await resources.async_update_item(
                    houden["id"], {"res_type": "module", "url": versioned_url}
                )
                _LOGGER.debug("Lovelace-bron bijgewerkt naar %s", versioned_url)

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
    www = Path(__file__).parent / "www"
    ontbreekt = [naam for naam, _url in FRONTEND_FILES if not (www / naam).is_file()]
    if ontbreekt:
        _LOGGER.warning("Dashboardbestand(en) niet gevonden in %s: %s", www, ontbreekt)
        return

    # Elk pad mag maar een keer geregistreerd worden. Bij een herlaad van de
    # integratie zonder herstart is dat al gebeurd; dat is geen fout en mag de
    # rest niet tegenhouden. Per URL bijhouden: na een update zonder herstart
    # staat het oude pad er al, het nieuwe (stormchase-dashboard.js) nog niet.
    # Oudere versies bewaarden hier True (alleen het grote bestand).
    geregistreerd = hass.data.get(_REGISTERED)
    if not isinstance(geregistreerd, set):
        geregistreerd = {STRATEGY_URL} if geregistreerd else set()
        hass.data[_REGISTERED] = geregistreerd
    for naam, url in FRONTEND_FILES:
        if url in geregistreerd:
            continue
        try:
            await hass.http.async_register_static_paths(
                [
                    StaticPathConfig(
                        url,
                        str(www / naam),
                        # Cachen mag: de versie in de query zorgt voor
                        # verversing.
                        cache_headers=True,
                    )
                ]
            )
        except (RuntimeError, ValueError) as err:
            _LOGGER.debug("Pad stond er al: %s", err)
        geregistreerd.add(url)

    # Versienummer plus starttijd. Het versienummer alleen bleek niet genoeg:
    # bij een update via HACS bleef de oude URL soms in de bronnenlijst staan,
    # waardoor de browser het oude script uit de cache bleef gebruiken. Met de
    # starttijd erbij wijzigt de URL bij elke herstart en is een herlaad
    # onvermijdelijk.
    stempel = int(dt_util.utcnow().timestamp())
    versioned_url = f"{STRATEGY_URL}?v={version}&t={stempel}"
    # De kleine strategie eerst: die moet binnen de time-out registreren.
    dashboard_url = f"{DASHBOARD_URL}?v={version}&t={stempel}"
    urls = [dashboard_url, versioned_url]

    # Beide routes: de bron is leidend, add_extra_js_url vangt YAML-modus af.
    # Het script registreert zichzelf maar één keer, dus dubbel laden kan geen
    # kwaad.
    # Beide routes worden bij elke start opnieuw geprobeerd. Eerder werd dit
    # overgeslagen zodra het een keer gelukt leek, waardoor een mislukte
    # registratie nooit meer werd hersteld en het dashboard leeg bleef.
    via_resource = await _async_register_resource(hass, *urls)

    # URL's van een vorige start (herlaad zonder herstart) eerst weghalen,
    # anders stapelen ze op in de lijst die de frontend meekrijgt.
    if remove_extra_js_url is not None:
        for oud in hass.data.get(_EXTRA_JS, []):
            try:
                remove_extra_js_url(hass, oud)
            except Exception:  # noqa: BLE001 - opruimen is bijzaak
                pass
    try:
        add_extra_js_url(hass, dashboard_url)
        add_extra_js_url(hass, versioned_url)
        hass.data[_EXTRA_JS] = list(urls)
    except Exception as err:  # noqa: BLE001 - mag de opstart niet blokkeren
        _LOGGER.debug("Kon het script niet aan de frontend meegeven: %s", err)

    if via_resource:
        _LOGGER.info("Dashboardstrategie geregistreerd op %s en %s", dashboard_url, versioned_url)
    else:
        _LOGGER.warning(
            "De dashboardstrategie kon niet als Lovelace-bron worden "
            "vastgelegd. Voeg %s en %s handmatig toe onder Instellingen > "
            "Dashboards > Bronnen, als type JavaScript-module, en ververs "
            "daarna hard met Ctrl+Shift+R.",
            DASHBOARD_URL,
            STRATEGY_URL,
        )
