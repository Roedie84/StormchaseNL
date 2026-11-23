"""Bevestigt een meting de mist die het model aangeeft? (0.64.0)

Ruud 23-11 17:24: "Mist melding terwijl er geen mist is?" De melding kwam
uit de weercode van het rekenmodel (45/48) terwijl het station 87 %
luchtvochtigheid, een dauwpunt 1,8 graden onder de temperatuur en ruim
80 km zicht gaf. Een modelcode alleen is geen mist.

Vrij van Home Assistant, zodat het los te toetsen is.
"""

from __future__ import annotations

from datetime import datetime

#: Onder dit zicht (m) is het mist.
ZICHT_MIST_M = 1000.0
#: Zonder zichtmeting: zo vochtig en het dauwpunt zo dicht bij de temperatuur.
VOCHT_MIST_PROCENT = 95.0
SPREIDING_MIST_GRADEN = 1.0
#: Een oudere meting zegt niets over nu.
MAX_LEEFTIJD_S = 90 * 60


def _getal(waarde) -> float | None:
    try:
        return None if waarde is None else float(waarde)
    except (TypeError, ValueError):
        return None


def _epoch(stempel) -> float | None:
    if stempel is None:
        return None
    try:
        tijd = datetime.fromisoformat(str(stempel).replace("Z", "+00:00"))
    except ValueError:
        return None
    return tijd.timestamp() if tijd.tzinfo is not None else None


def beoordeel(meting: dict | None, nu: float) -> dict:
    """{"bevestigd": bool, "reden": tekst} voor de stationsmeting op `nu` (epoch)."""
    if not isinstance(meting, dict) or not meting:
        return {"bevestigd": False, "reden": "geen stationsmeting"}
    tijd = _epoch(meting.get("waargenomen_op"))
    if tijd is None or nu - tijd > MAX_LEEFTIJD_S:
        return {"bevestigd": False, "reden": "stationsmeting te oud"}
    zicht = _getal(meting.get("zicht"))
    if zicht is not None and zicht < ZICHT_MIST_M:
        return {"bevestigd": True, "reden": f"zicht {zicht:.0f} m"}
    vocht = _getal(meting.get("luchtvochtigheid"))
    temp, dauw = _getal(meting.get("temperatuur")), _getal(meting.get("dauwpunt"))
    spreiding = None if temp is None or dauw is None else temp - dauw
    if vocht is not None and vocht >= VOCHT_MIST_PROCENT and (
        spreiding is None or spreiding <= SPREIDING_MIST_GRADEN
    ):
        # een zichtmeting die ruim zicht geeft, komt vaak van een verder
        # station; vocht en dauwpunt van dichtbij wegen dan zwaarder
        return {"bevestigd": True, "reden": f"luchtvochtigheid {vocht:.0f} %"}
    delen = []
    if zicht is not None:
        delen.append(f"zicht {zicht / 1000:.0f} km" if zicht >= 1000 else f"zicht {zicht:.0f} m")
    if vocht is not None:
        delen.append(f"luchtvochtigheid {vocht:.0f} %")
    return {"bevestigd": False, "reden": ", ".join(delen) or "geen zicht of vocht gemeten"}
