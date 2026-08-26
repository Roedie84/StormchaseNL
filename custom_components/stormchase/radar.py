"""Radarbeelden van RainViewer.

Er is een eindpunt dat op coordinaten centreert in plaats van op kaarttegels.
Daarmee is een radarbeeld te maken dat je eigen positie volgt, als gewone
entiteit in Home Assistant: geen ingesloten webpagina, geen cookiemelding,
geen advertenties.

Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

# Het hoogste zoomniveau dat RainViewer aanbiedt
MAX_ZOOM = 7
MIN_ZOOM = 1

# Alleen deze twee formaten worden geleverd
FORMATEN = (256, 512)

# Kleurschema's lopen van 0 tot en met 8
MAX_KLEUR = 8


def laatste_frame(payload: dict | None) -> dict | None:
    """Pak het meest recente radarbeeld uit het overzicht.

    De reeks loopt van oud naar nieuw, dus het laatste element is het meest
    actuele. Ontbreekt de reeks, dan komt er niets terug en blijft het beeld
    op zijn vorige waarde staan.
    """
    if not payload:
        return None

    frames = ((payload.get("radar") or {}).get("past")) or []
    if not frames:
        return None

    laatste = frames[-1]
    if not laatste.get("path"):
        return None

    return {
        "host": payload.get("host") or "https://tilecache.rainviewer.com",
        "path": laatste["path"],
        "tijd": laatste.get("time"),
    }


def bouw_url(
    frame: dict | None,
    latitude: float,
    longitude: float,
    zoom: int = 7,
    formaat: int = 512,
    kleur: int = 2,
    vloeiend: bool = True,
    sneeuw: bool = True,
) -> str | None:
    """Stel de URL van een radarbeeld samen, gecentreerd op een positie.

    De coordinaten moeten een punt bevatten, ook als ze rond zijn; daarom
    worden ze altijd met decimalen geschreven.
    """
    if frame is None:
        return None

    zoom = max(MIN_ZOOM, min(int(zoom), MAX_ZOOM))
    formaat = formaat if formaat in FORMATEN else 512
    kleur = max(0, min(int(kleur), MAX_KLEUR))

    opties = f"{1 if vloeiend else 0}_{1 if sneeuw else 0}"

    return (
        f"{frame['host']}{frame['path']}/{formaat}/{zoom}"
        f"/{latitude:.4f}/{longitude:.4f}/{kleur}/{opties}.png"
    )
