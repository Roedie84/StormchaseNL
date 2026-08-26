"""Waarden opzoeken in een reeks tijdstempels.

Niet elk weermodel levert per uur. ICON-D2 geeft kwartierwaarden, GRAPES
stappen van drie uur, en een enkel model wijkt af van hele uren. Zoeken op een
exacte tijdstempel levert dan niets op, terwijl er een prima waarde vlak
ernaast staat.

Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

from datetime import datetime

# Hoe ver een tijdstip mag afwijken voordat de waarde niets meer zegt
MARGE_UUR = 5400  # anderhalf uur
MARGE_KWARTIER = 900


def _lees(tekst: str, tzinfo=None) -> datetime | None:
    """Lees een tijdstempel uit een weermodel."""
    try:
        moment = datetime.fromisoformat(tekst)
    except (ValueError, TypeError):
        return None

    if moment.tzinfo is None and tzinfo is not None:
        moment = moment.replace(tzinfo=tzinfo)
    return moment


def dichtstbijzijnde(
    tijden: list[str],
    waarden: list,
    doel: datetime,
    marge: int = MARGE_UUR,
):
    """Geef de waarde die het dichtst bij het doelmoment ligt.

    Lege waarden worden overgeslagen; die zeggen niets en zouden een bruikbare
    waarde iets verderop verdringen. Ligt alles buiten de marge, dan komt er
    niets terug.
    """
    beste = None

    for index, tekst in enumerate(tijden):
        if index >= len(waarden) or waarden[index] is None:
            continue

        moment = _lees(tekst, doel.tzinfo)
        if moment is None:
            continue

        verschil = abs((moment - doel).total_seconds())
        if verschil <= marge and (beste is None or verschil < beste[0]):
            beste = (verschil, waarden[index])

    return beste[1] if beste else None


def op_stempel(tijden: list[str], waarden: list, stempel: str):
    """Waarde bij een exacte tijdstempel, of niets."""
    if stempel in tijden:
        index = tijden.index(stempel)
        if index < len(waarden):
            return waarden[index]
    return None


def aantal_gevuld(waarden: list | None) -> int:
    """Hoeveel waarden er daadwerkelijk iets bevatten.

    Handig om onderscheid te maken tussen een model dat het veld niet levert
    en een opzoekactie die ernaast greep.
    """
    return sum(1 for w in (waarden or []) if w is not None)
