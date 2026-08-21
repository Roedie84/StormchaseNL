"""Diagnostiek voor Stormchase.

Levert de knop 'Diagnostische gegevens downloaden' bij de integratie. Het
bestand bevat de instellingen, de actuele waarden en de statistieken over hoe
de externe bronnen zich gedragen hebben.

Exacte coordinaten worden afgerond tot twee decimalen, ongeveer een
kilometer. Genoeg om te beoordelen of de juiste regio wordt gebruikt, te
grof om je adres uit af te leiden.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_MANUAL_LOCATION,
    CONF_NOTIFY_SERVICES,
    CONF_TRACKER_ENTITY,
    DOMAIN,
)

# Deze velden zeggen iets over wie je bent, niet over hoe de integratie werkt
TE_VERBERGEN = {CONF_MANUAL_LOCATION, CONF_TRACKER_ENTITY, CONF_NOTIFY_SERVICES}


def _grof(waarde: float | None) -> float | None:
    """Rond een coordinaat af tot ongeveer een kilometer."""
    return round(waarde, 2) if isinstance(waarde, (int, float)) else None


def _kort(data: dict | None, velden: tuple[str, ...]) -> dict:
    """Neem alleen de genoemde velden over."""
    if not data:
        return {}
    return {veld: data.get(veld) for veld in velden}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Stel het diagnosebestand samen."""
    gegevens = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})

    storm = gegevens.get("storm")
    meteo = gegevens.get("meteo")
    regen = gegevens.get("rain")
    waarschuwingen = gegevens.get("alerts")
    stats = gegevens.get("stats")

    # Welke entiteiten bestaan er, en wat is hun toestand? Zonder de
    # attributen, want daar zitten de coordinaten in.
    entiteiten = {}
    for state in hass.states.async_all():
        if f"{DOMAIN}" in state.entity_id:
            entiteiten[state.entity_id] = state.state

    # De bronsensoren van Blitzortung, want daar hangt alles aan
    bronsensoren = {}
    for sleutel in ("distance_sensor", "azimuth_sensor", "counter_sensor"):
        entity_id = entry.options.get(sleutel, entry.data.get(sleutel))
        if entity_id:
            state = hass.states.get(entity_id)
            bronsensoren[sleutel] = {
                "entity_id": entity_id,
                "bestaat": state is not None,
                "waarde": state.state if state else None,
            }

    # Hoeveel geo_location markers matchen het ingestelde patroon? Bij twee
    # Blitzortung-integraties naast elkaar telt dit dubbel, en dat is precies
    # het soort probleem dat je hier wil zien.
    patroon = entry.options.get("geo_pattern", entry.data.get("geo_pattern", ""))
    alle_geo = [s.entity_id for s in hass.states.async_all("geo_location")]
    passend = [e for e in alle_geo if patroon and patroon in e]

    storm_data = storm.data if storm else None
    regen_data = regen.data if regen else None
    alert_data = waarschuwingen.data if waarschuwingen else None
    meteo_data = meteo.data if meteo else None

    return {
        "versie": entry.version,
        "instellingen": async_redact_data(
            {**entry.data, **entry.options}, TE_VERBERGEN
        ),
        "locatie": {
            "bron": storm_data.location_source if storm_data else None,
            "latitude_grof": _grof(storm_data.latitude) if storm_data else None,
            "longitude_grof": _grof(storm_data.longitude) if storm_data else None,
            "ha_thuis_grof": [
                _grof(hass.config.latitude),
                _grof(hass.config.longitude),
            ],
        },
        "bronsensoren": bronsensoren,
        "blitzortung": {
            "gevonden": bool(storm_data.blitzortung) if storm_data else None,
            "meet_vanaf": (storm_data.blitzortung or {}).get("bron")
            if storm_data
            else None,
            "afwijking_km": storm_data.afwijking_km if storm_data else None,
        },
        "geo_location": {
            "patroon": patroon,
            "totaal_aanwezig": len(alle_geo),
            "passend_bij_patroon": len(passend),
            "voorbeelden": passend[:5],
        },
        "onweer": {
            "afstand": storm_data.distance if storm_data else None,
            "azimut": storm_data.azimuth if storm_data else None,
            "snelheid": storm_data.speed if storm_data else None,
            "aankomst": storm_data.eta if storm_data else None,
            "trend": storm_data.trend if storm_data else None,
            "markers": storm_data.markers if storm_data else None,
            "ringen": storm_data.rings if storm_data else None,
            "ringen_via": storm_data.ring_bron if storm_data else None,
            "onderweg": storm_data.onderweg if storm_data else None,
            "stil_sinds_minuten": storm_data.stil_sinds if storm_data else None,
        },
        "parameters": _kort(meteo_data, ("cape", "cape_peak", "lifted_index", "cin")),
        "neerslag": {
            **_kort(
                regen_data,
                ("bron", "intensiteit", "regent", "begint_over", "stopt_over", "piek"),
            ),
            # De volledige reeks, om te kunnen zien of het parsen klopte
            "verwachting": (regen_data or {}).get("verwachting"),
        },
        "waarschuwingen": {
            **_kort(alert_data, ("land", "niveau", "aantal", "soort", "gebied")),
            "gefilterd_op": (alert_data or {}).get("gefilterd_op"),
            "aantal_in_land": (alert_data or {}).get("aantal_in_land"),
            # Alleen de omschrijvingen, niet de volledige waarschuwingen
            "gebieden": [
                w.get("gebied") for w in ((alert_data or {}).get("actief") or [])
            ][:20],
        },
        "statistieken": stats.als_dict() if stats else None,
        "entiteiten": entiteiten,
    }
