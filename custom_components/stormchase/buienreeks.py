"""Uit een neerslagreeks halen wanneer het regent, stopt en weer begint.

De reeks is een lijst van (minuten vanaf nu, mm per uur), oplopend in tijd.
Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations


def lees_reeks(reeks: list[tuple[int, float]], drempel: float) -> dict:
    """Bepaal intensiteit nu, regent, begint_over, stopt_over en volgende_bui_over.

    `begint_over` blijft zoals het altijd was: alleen gevuld als het nu droog
    is. Meldingen, `regen_verwacht` en de validatie hangen daaraan.

    `volgende_bui_over` is nieuw (0.46.0): regent het nu en houdt het binnen
    de reeks op, dan is dit het begin van de eerstvolgende bui daarna. Op 8
    oktober 08:10 stopte de regen over 16 minuten en kwam er vanaf +91 minuten
    een nieuwe bui aan, terwijl de sensor 'regen begint over' onbekend bleef.
    """
    # Wat valt er nu? Neem het zwaarste tijdvak rond dit moment in plaats
    # van een enkel vakje van vijf minuten. Een bui met een dipje erin zou
    # anders als droog gelden terwijl je nat wordt.
    rondom = [mm for minuten, mm in reeks if -10 <= minuten <= 10]
    intensiteit = max(rondom) if rondom else 0.0
    regent = intensiteit >= drempel

    # Wanneer begint het? Alleen relevant als het nu droog is.
    begint_over = None
    if not regent:
        begint_over = next(
            (minuten for minuten, mm in reeks if minuten > 0 and mm >= drempel),
            None,
        )

    # Wanneer stopt het? Alleen relevant als het nu regent.
    stopt_over = None
    if regent:
        stopt_over = next(
            (minuten for minuten, mm in reeks if minuten > 0 and mm < drempel),
            None,
        )

    # En komt er na het droge stuk weer een bui?
    volgende_bui_over = None
    if regent and stopt_over is not None:
        volgende_bui_over = next(
            (
                minuten
                for minuten, mm in reeks
                if minuten > stopt_over and mm >= drempel
            ),
            None,
        )

    return {
        "intensiteit": intensiteit,
        "regent": regent,
        "begint_over": begint_over,
        "stopt_over": stopt_over,
        "volgende_bui_over": volgende_bui_over,
    }


def begin_weergave(data: dict) -> int | None:
    """Wat de sensor 'regen begint over' toont.

    Droog: het begin van de eerstvolgende regen (ongewijzigd). Regent het:
    het begin van de volgende bui na het droge stuk, als die in de reeks zit;
    anders onbekend zoals voorheen.
    """
    if data.get("begint_over") is not None:
        return data["begint_over"]
    if data.get("regent"):
        return data.get("volgende_bui_over")
    return None


def gaat_om_volgende_bui(data: dict) -> bool:
    """True als de sensor het begin van de volgende bui toont."""
    return (
        data.get("begint_over") is None
        and bool(data.get("regent"))
        and data.get("volgende_bui_over") is not None
    )
