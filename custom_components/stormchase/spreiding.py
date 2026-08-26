"""Hoe eens zijn de weermodellen het met elkaar?

Een enkel getal uit een enkel model leest als zekerheid, en dat is het niet.
Zijn acht modellen het erover eens dat er 2000 J/kg aan energie zit, dan kun
je daar iets mee. Loopt de schatting uiteen van 200 tot 2600, dan zegt het
gemiddelde weinig en is wachten op de volgende modelrun verstandiger.

Dat onderscheid is voor een chaser het verschil tussen een dag vrijhouden en
afwachten. Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

# Minder dan dit aantal modellen met een waarde zegt niets over spreiding
MIN_MODELLEN = 3

# De spreiding wordt afgezet tegen de mediaan. Bij lage waarden zou een
# absolute maat onzin opleveren: van 20 naar 80 J/kg is verhoudingsgewijs
# enorm maar praktisch betekenisloos, dus we rekenen met een ondergrens.
BODEM = 200.0

EENS = 0.4
REDELIJK = 0.8


def mediaan(waarden: list[float]) -> float:
    """Middelste waarde; ongevoeliger voor een enkel uitschietend model."""
    gesorteerd = sorted(waarden)
    midden = len(gesorteerd) // 2

    if len(gesorteerd) % 2:
        return gesorteerd[midden]
    return (gesorteerd[midden - 1] + gesorteerd[midden]) / 2


def beoordeel(per_model: dict[str, float | None]) -> dict:
    """Vat de spreiding tussen modellen samen.

    Geeft de mediaan in plaats van het gemiddelde: een enkel model dat er
    ver naast zit trekt een gemiddelde scheef, en juist bij convectie komt
    dat voor.
    """
    waarden = [w for w in per_model.values() if w is not None]

    if len(waarden) < MIN_MODELLEN:
        return {
            "overeenstemming": "onbekend",
            "aantal_modellen": len(waarden),
            "mediaan": mediaan(waarden) if waarden else None,
            "laagste": min(waarden) if waarden else None,
            "hoogste": max(waarden) if waarden else None,
            "spreiding": None,
            "modellen": {k: v for k, v in per_model.items() if v is not None},
        }

    middelste = mediaan(waarden)
    laagste = min(waarden)
    hoogste = max(waarden)
    spreiding = hoogste - laagste

    verhouding = spreiding / max(middelste, BODEM)

    if verhouding < EENS:
        oordeel = "modellen zijn het eens"
    elif verhouding < REDELIJK:
        oordeel = "modellen wijken wat af"
    else:
        oordeel = "modellen zijn verdeeld"

    return {
        "overeenstemming": oordeel,
        "aantal_modellen": len(waarden),
        "mediaan": round(middelste, 1),
        "laagste": round(laagste, 1),
        "hoogste": round(hoogste, 1),
        "spreiding": round(spreiding, 1),
        "verhouding": round(verhouding, 2),
        "modellen": {k: round(v, 1) for k, v in per_model.items() if v is not None},
    }


def samenvatting(oordeel: dict, eenheid: str = "J/kg") -> str:
    """Een regel die zegt wat je eraan hebt."""
    if oordeel.get("overeenstemming") == "onbekend":
        return "Te weinig modellen met gegevens"

    return (
        f"{oordeel['mediaan']:.0f} {eenheid} mediaan, "
        f"{oordeel['laagste']:.0f} tot {oordeel['hoogste']:.0f} "
        f"over {oordeel['aantal_modellen']} modellen"
    )


# ---------------------------------------------------------------------
# Ensemble: hetzelfde model, meerdere keren gedraaid
#
# Een ensemble geeft geen spreiding tussen modellen maar een kans: hoeveel
# van de leden komen boven een drempel uit. Dat is een ander soort getal dan
# een mediaan, en bruikbaarder om een dag mee te plannen.
# ---------------------------------------------------------------------

# Vanaf deze waarden noemen we een dag onweersgeschikt respectievelijk zwaar
DREMPEL_ONWEER = 500.0
DREMPEL_ZWAAR = 1500.0

# Minder leden dan dit zegt niets over een kans
MIN_LEDEN = 5


def kans_boven(waarden: list[float], drempel: float) -> int | None:
    """Welk deel van de leden komt boven de drempel uit, in procenten."""
    bruikbaar = [w for w in waarden if w is not None]
    if len(bruikbaar) < MIN_LEDEN:
        return None
    return round(sum(1 for w in bruikbaar if w >= drempel) / len(bruikbaar) * 100)


def duiding_kans(kans: int | None) -> str:
    """Wat een kans praktisch betekent."""
    if kans is None:
        return "onbekend"
    if kans < 10:
        return "vrijwel uitgesloten"
    if kans < 30:
        return "kleine kans"
    if kans < 60:
        return "reele kans"
    if kans < 85:
        return "waarschijnlijk"
    return "vrijwel zeker"


def ensemble(pieken_per_lid: list[float]) -> dict:
    """Vat een ensemble samen in kansen en spreiding.

    Krijgt per lid de hoogste waarde over de beoordeelde periode; dat zegt
    meer over de dag dan een momentopname, want convectie piekt vaak maar
    een paar uur.
    """
    bruikbaar = [w for w in pieken_per_lid if w is not None]

    if len(bruikbaar) < MIN_LEDEN:
        return {
            "leden": len(bruikbaar),
            "kans_onweer": None,
            "kans_zwaar": None,
            "duiding": "onbekend",
            "mediaan_piek": mediaan(bruikbaar) if bruikbaar else None,
            "hoogste_lid": max(bruikbaar) if bruikbaar else None,
        }

    onweer = kans_boven(bruikbaar, DREMPEL_ONWEER)

    return {
        "leden": len(bruikbaar),
        "kans_onweer": onweer,
        "kans_zwaar": kans_boven(bruikbaar, DREMPEL_ZWAAR),
        "duiding": duiding_kans(onweer),
        "mediaan_piek": round(mediaan(bruikbaar)),
        "hoogste_lid": round(max(bruikbaar)),
        "laagste_lid": round(min(bruikbaar)),
    }
