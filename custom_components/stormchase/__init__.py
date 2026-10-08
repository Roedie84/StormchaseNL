"""De Stormchase integratie.

Bouwt een afgeleide laag bovenop een bestaande Blitzortung-integratie:
naderingssnelheid, aankomsttijd, afstandsringen en onweersparameters uit
Open-Meteo. De coordinaten komen uit de Home Assistant configuratie.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, ServiceCall

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.restore_state import async_get as async_get_restore_state
from homeassistant.helpers.storage import Store
from homeassistant.loader import async_get_integration

from .const import (
    DATA_NOTIFY_ENABLED,
    DOMAIN,
    SERVICE_SEND_BRIEFING,
    SERVICE_TEST_NOTIFICATION,
)
from .coordinator import POSITIE_SLEUTEL, MeteoCoordinator, StormCoordinator
from .meting import MetingCoordinator
from .radarbron import RadarCoordinator
from .alerts import AlertCoordinator
from .briefing import Briefing
from .bronhistorie import BronHistorie
from .frontend import async_register_frontend
from .notifier import StormNotifier
from .rain import RainCoordinator
from .stats import Statistieken
from .validatie import Validatie
from .herstart import OPSLAG_VERSIE, Bewaarplan

_LOGGER = logging.getLogger(__name__)

# L-SC-002: de dagtellers per bron gaan hooguit eens per zoveel seconden naar
# schijf. Bij het afsluiten van Home Assistant schrijft de Store een nog
# openstaande wijziging zelf weg; bij het ontladen doen we dat hieronder.
BRONSTATISTIEK_SLEUTEL = "stormchase_bronstatistiek"
BRONSTATISTIEK_VERTRAGING = 300

# 0.47.0: toestand die een herstart moet overleven (open voorspellingen staan
# in de validatie-opslag; schuilregel, cellen, nadering, gemelde
# waarschuwingen en wachttijden hier). Per config entry een eigen bestand.
STAAT_SLEUTEL = f"{DOMAIN}_staat"
STAAT_VERTRAGING = 120

# 0.47.0: de laatst geslaagde gegevens per bron, zodat de sensoren na een
# herstart niet onbeschikbaar zijn als de eerste ophaalronde mislukt.
LAATSTE_SLEUTEL = f"{DOMAIN}_laatste"
LAATSTE_VERTRAGING = 60

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.WEATHER,
    Platform.IMAGE,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Zet de integratie op vanuit een config entry."""
    integration = await async_get_integration(hass, DOMAIN)
    await async_register_frontend(hass, integration.version or "0")

    # De statistieken worden door alle onderdelen gevuld en komen terug in
    # het diagnosebestand.
    stats = Statistieken()

    # L-SC-002: gelukt/mislukt per bron per dag terughalen, zodat de
    # betrouwbaarheid van een bron over dagen te volgen is en niet bij elke
    # herstart opnieuw begint. Koppelen voor de eerste ophaalronde.
    bron_opslag = Store(hass, 1, BRONSTATISTIEK_SLEUTEL)
    bewaarde_bron = await bron_opslag.async_load()
    bronhistorie = BronHistorie(bewaarde_bron)
    # 0.47.0: de totaaltellers (bronnen, events, meldingen) staan naast de
    # dagtellers, zodat ook die een herstart overleven.
    if isinstance(bewaarde_bron, dict):
        stats.herstel_tellers(bewaarde_bron.get("tellers"))

    def _bron_data() -> dict:
        return {**bronhistorie.naar_opslag(), "tellers": stats.tellers_naar_opslag()}

    stats.koppel_historie(
        bronhistorie,
        lambda: bronhistorie.plan_opslag(
            lambda: bron_opslag.async_delay_save(
                _bron_data, BRONSTATISTIEK_VERTRAGING
            )
        ),
    )

    storm = StormCoordinator(hass, entry)
    meteo = MeteoCoordinator(hass, entry)
    regen = RainCoordinator(hass, entry)
    waarschuwingen = AlertCoordinator(hass, entry)
    meting = MetingCoordinator(hass, entry)
    radar = RadarCoordinator(hass, entry)

    # De notifier luistert naar de events die de coordinator afvuurt en
    # stuurt daar meldingen over. Zit in de integratie zelf, zodat er geen
    # losse automatisering nodig is.
    notifier = StormNotifier(hass, entry)

    # Statistieken koppelen voor de eerste ophaalronde, anders mist die ronde
    # in de diagnostiek en zie je een gefaalde start niet terug.
    for onderdeel in (storm, meteo, regen, waarschuwingen, meting, radar, notifier):
        onderdeel.stats = stats

    # De notifier heeft de storm-coordinator nodig om te zien of je stilstaat
    notifier.storm = storm

    # Luister op elke verandering van de afstandssensor, zodat we inslagen
    # tussen twee ophaalrondes door niet missen.
    afmelden = storm.volg_bronsensor()
    if afmelden is not None:
        entry.async_on_unload(afmelden)

    # De storm-coordinator mag de meteo-coordinator laten verversen zodra
    # de locatie flink verschuift.
    storm.meteo = meteo
    storm.alerts = waarschuwingen

    # Uitkomsten van eerdere voorspellingen terughalen. Zonder dit begint de
    # zelfcontrole bij elke herstart opnieuw, en dan verzamelt hij nooit
    # genoeg om iets over de nauwkeurigheid te kunnen zeggen.
    # 0.42.0: de laatst bekende trackerpositie, zodat de locatie na een
    # herstart niet even naar thuis springt.
    if POSITIE_SLEUTEL not in hass.data:
        positie_opslag = Store(hass, 1, POSITIE_SLEUTEL)
        bewaarde_posities = await positie_opslag.async_load() or {}
        hass.data[POSITIE_SLEUTEL] = {
            "posities": dict(bewaarde_posities.get("posities") or {}),
            "opslag": positie_opslag,
        }

    opslag = Store(hass, 1, f"{DOMAIN}_validatie")
    bewaard = await opslag.async_load() or {}
    # 0.47.0: ook de open voorspellingen en de teller van afgeronde
    storm.validatie = Validatie(
        bewaard.get("uitkomsten"), bewaard.get("open"), bewaard.get("afgerond")
    )
    storm.opslag = opslag
    # Regen en onweer delen dezelfde lijst met voorspellingen
    regen.validatie = storm.validatie

    # 0.47.0: de toestand van voor de herstart terugzetten, voor de eerste
    # ophaalronde en voordat de notifier luistert, zodat er niets dubbel gemeld
    # wordt en de schuilregel gewoon doorloopt.
    staat_opslag = Store(hass, 1, f"{STAAT_SLEUTEL}_{entry.entry_id}")
    staat = await staat_opslag.async_load() or {}
    staatplan = Bewaarplan()

    def _staat_data() -> dict:
        staatplan.geschreven()
        return {
            "versie": OPSLAG_VERSIE,
            "storm": storm.naar_opslag(),
            "gemeld": waarschuwingen.gemeld_naar_opslag(),
            "notifier": notifier.naar_opslag(),
        }

    staatplan.plannen = lambda: staat_opslag.async_delay_save(
        _staat_data, STAAT_VERTRAGING
    )
    storm.herstel(staat.get("storm"))
    waarschuwingen.herstel_gemeld(staat.get("gemeld"))
    notifier.herstel(staat.get("notifier"))
    storm.bewaarplan = staatplan
    waarschuwingen.bewaarplan = staatplan
    notifier.bewaarplan = staatplan

    laatste_opslag = Store(hass, 1, f"{LAATSTE_SLEUTEL}_{entry.entry_id}")
    laatste = await laatste_opslag.async_load() or {}
    laatsteplan = Bewaarplan()
    terugvallers = {
        "meteo": meteo,
        "rain": regen,
        "alerts": waarschuwingen,
        "meting": meting,
    }

    def _laatste_data() -> dict:
        laatsteplan.geschreven()
        return {
            naam: onderdeel.laatste_naar_opslag()
            for naam, onderdeel in terugvallers.items()
        }

    laatsteplan.plannen = lambda: laatste_opslag.async_delay_save(
        _laatste_data, LAATSTE_VERTRAGING
    )
    for naam, onderdeel in terugvallers.items():
        onderdeel.herstel_laatste(laatste.get(naam))
        onderdeel.bij_onthoud = laatsteplan.plan

    # 0.47.0: de stand van de meldingenschakelaar voordat de notifier luistert. De
    # schakelaar zelf herstelt pas bij het aanmaken van de platformen, na de
    # eerste ophaalrondes; tot dan gold "aan" en gingen er meldingen uit
    # terwijl de schakelaar uit stond.
    gegevens = hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})
    stand = _bewaarde_meldingenstand(hass, entry)
    if stand is not None:
        gegevens[DATA_NOTIFY_ENABLED] = stand

    # Luisteraars aanzetten voor de eerste ophaalronde. Anders vuren de
    # gebeurtenissen uit die ronde in het niets: bij een herstart midden in
    # een onweer zou je de eerste melding van elke soort mislopen.
    notifier.start()

    await storm.async_config_entry_first_refresh()
    # Open-Meteo mag falen zonder de hele integratie te blokkeren; de
    # bliksemsensoren zijn het belangrijkste deel.
    await meteo.async_refresh()
    # Regen mag net als de weerparameters falen zonder de rest te blokkeren.
    await regen.async_refresh()
    await waarschuwingen.async_refresh()
    # Metingen zijn een aanvulling; falen mag de rest niet blokkeren.
    await meting.async_refresh()
    await radar.async_refresh()

    gegevens = hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})
    gegevens.update(
        {
            "storm": storm,
            "meteo": meteo,
            "rain": regen,
            "alerts": waarschuwingen,
            "meting": meting,
            "radar": radar,
            "notifier": notifier,
            "stats": stats,
            "bron_opslag": bron_opslag,
            # 0.47.0: alles wat bij ontladen en afsluiten meteen weg moet
            "opslagen": [
                ("validatie", opslag, storm.validatie.naar_opslag),
                ("staat", staat_opslag, _staat_data),
                ("laatste", laatste_opslag, _laatste_data),
                ("bronstatistiek", bron_opslag, _bron_data),
            ],
            "plannen": [staatplan, laatsteplan],
        }
    )

    async def _bij_stoppen(_event: Event) -> None:
        """Bij het afsluiten alles meteen wegschrijven (0.47.0)."""
        await _async_bewaar_alles(hass, gegevens)

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _bij_stoppen)
    )

    # Het dagelijkse weerbericht plannen. Pas hierna, want het leest de
    # gegevens van de coordinators uit hass.data.
    briefing = Briefing(hass, entry)
    briefing.start()
    gegevens["briefing"] = briefing

    await _async_register_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


def _bewaarde_meldingenstand(hass: HomeAssistant, entry: ConfigEntry) -> bool | None:
    """De laatst bekende stand van de meldingenschakelaar, of None."""
    entity_id = er.async_get(hass).async_get_entity_id(
        "switch", DOMAIN, f"{entry.entry_id}_notifications"
    )
    if entity_id is None:
        return None
    try:
        opgeslagen = async_get_restore_state(hass).last_states.get(entity_id)
    except Exception:  # noqa: BLE001 - zonder herstelgegevens geldt de standaard
        opgeslagen = None
    staat = opgeslagen.state if opgeslagen is not None else hass.states.get(entity_id)
    if staat is None or staat.state not in ("on", "off"):
        return None
    return staat.state == "on"


async def _async_bewaar_alles(hass: HomeAssistant, gegevens: dict) -> None:
    """Schrijf alle opslag meteen weg, zonder te wachten op de vertraging.

    Bij een herlaadbeurt maakt de nieuwe instantie eigen Store-objecten aan;
    een uitgestelde schrijfactie van de oude kon daarna nog oude gegevens
    over de nieuwe heen zetten. async_save annuleert die uitgestelde actie.
    """
    for naam, opslag, data in gegevens.get("opslagen", []):
        try:
            await opslag.async_save(data())
        except Exception:  # noqa: BLE001 - ontladen mag hier niet op stuklopen
            _LOGGER.warning("Opslag %s niet weggeschreven", naam, exc_info=True)
    posities = hass.data.get(POSITIE_SLEUTEL)
    if posities and posities.get("opslag") is not None:
        try:
            await posities["opslag"].async_save({"posities": posities["posities"]})
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Trackerposities niet weggeschreven", exc_info=True)


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

    async def _briefing(call: ServiceCall) -> None:
        """Stuur het weerbericht nu, los van het schema."""
        for gegevens in hass.data.get(DOMAIN, {}).values():
            onderdeel = gegevens.get("briefing")
            if onderdeel is not None:
                await onderdeel.async_send()

    hass.services.async_register(DOMAIN, SERVICE_SEND_BRIEFING, _briefing)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Ruim de integratie op."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        gegevens = hass.data[DOMAIN].pop(entry.entry_id, {})
        notifier = gegevens.get("notifier")
        if notifier is not None:
            notifier.stop()
        briefing = gegevens.get("briefing")
        if briefing is not None:
            briefing.stop()
        # L-SC-002 / 0.47.0: alle nog uitgestelde schrijfacties meteen doen
        # (validatie, toestand, laatste gegevens, bronstatistiek, posities),
        # anders mist een herlaadbeurt (opties gewijzigd) de laatste minuut.
        await _async_bewaar_alles(hass, gegevens)
        # Daarna mag de oude instantie niets meer plannen: anders kan een
        # late ronde alsnog oude gegevens over die van de nieuwe zetten.
        for plan in gegevens.get("plannen", []):
            plan.plannen = None
        storm = gegevens.get("storm")
        if storm is not None:
            storm.opslag = None
        stats = gegevens.get("stats")
        if stats is not None:
            stats._bij_wijziging = None
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
            hass.services.async_remove(DOMAIN, SERVICE_TEST_NOTIFICATION)
            hass.services.async_remove(DOMAIN, SERVICE_SEND_BRIEFING)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Herlaad na een wijziging in de opties."""
    await hass.config_entries.async_reload(entry.entry_id)
