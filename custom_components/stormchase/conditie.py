"""Huidige weersgesteldheid: Open-Meteo, bijgestuurd door de radar.

Open-Meteo geeft per kwartier een modelcode voor het hele gebied. Een bui van
een half uur valt daar makkelijk tussendoor: op 8 oktober regende het van
11:50 tot 12:21 (Buienradar tot 1,0 mm/u, `regen_verwacht` aan) terwijl de
weerentiteit op "sunny" bleef staan. Regent het volgens de radar nu, dan
wint de radar.

Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

# Vanaf deze intensiteit (mm/u) regent het volgens de radar.
RADAR_REGEN_MMU = 0.1
# Vanaf deze intensiteit (mm/u) is het een stortbui.
RADAR_STORTBUI_MMU = 4.0
# Ouder dan dit (seconden) zegt de radarwaarde niets meer over "nu". De
# regencoordinator haalt elke vijf minuten op; bij een storing houdt hij de
# laatste waarde tot drie uur vast, en die mag de conditie niet sturen.
RADAR_MAX_LEEFTIJD_S = 15 * 60

# Condities waarin de radar alleen "er valt iets" zegt en het model meer weet.
_NEERSLAG_SOORT = {"snowy", "snowy-rainy", "hail"}


def wmo_conditie(
    code: int | None, wmo: dict[int, str], is_dag: bool = True
) -> str | None:
    """Vertaal een WMO-weercode naar een Home Assistant-conditie."""
    if code is None:
        return None
    try:
        conditie = wmo.get(int(code))
    except (TypeError, ValueError):
        return None
    # Een heldere nacht is geen zon.
    if conditie == "sunny" and not is_dag:
        return "clear-night"
    return conditie


def huidige_conditie(
    model: str | None,
    intensiteit: float | None,
    onweer_dichtbij: bool = False,
) -> str | None:
    """Combineer de modelconditie met de radarintensiteit van nu.

    - Geen bruikbare radarwaarde of droog volgens de radar: de modelconditie.
    - Regen (>= 0,1 mm/u): "rainy", vanaf 4 mm/u "pouring".
    - Regen met onweer dichtbij, of een onweerscode van het model:
      "lightning-rainy".
    - Sneeuw of hagel van het model blijft staan; de radar ziet alleen dát
      er iets valt, niet wat.
    """
    try:
        mm = float(intensiteit) if intensiteit is not None else None
    except (TypeError, ValueError):
        mm = None
    if mm is None or mm < RADAR_REGEN_MMU:
        return model

    if onweer_dichtbij or model == "lightning-rainy":
        return "lightning-rainy"
    if model in _NEERSLAG_SOORT:
        return model
    if mm >= RADAR_STORTBUI_MMU:
        return "pouring"
    return "rainy"


def radar_intensiteit(
    regendata: dict | None, leeftijd_s: float | None
) -> float | None:
    """De radarintensiteit van nu, of None als die er niet (meer) is."""
    if not isinstance(regendata, dict):
        return None
    if leeftijd_s is None or leeftijd_s > RADAR_MAX_LEEFTIJD_S:
        return None
    return regendata.get("intensiteit")
