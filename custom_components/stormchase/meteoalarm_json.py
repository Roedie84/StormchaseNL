"""MeteoAlarm via de JSON-API, en landelijke waarschuwingen (0.62.0).

Ruud 10-11 06:53: "Het KNMI geeft momenteel code geel, ik zie dat niet terug
op dashboard tablet". Code geel voor dichte mist gold van 09-11 23:30 tot
10-11 12:00 voor "Nederland met uitzondering van Zeeland, Waddeneilanden,
IJsselmeergebied en Waddenzeegebied en delen van: Limburg". Stormchase zag
niets:

- de KNMI-app-API gaf voor de regio Gelderland geen waarschuwing en per uur
  het niveau "geen";
- de terugval op MeteoAlarm las de oude Atom-feed (meteoalarm-legacy-atom),
  die sinds 09-11 19:35 leeg is; de JSON-API (api/v1/warnings) had de
  waarschuwing wel;
- en ook dan noemt het gebied geen provincie: het filter op gebiedsnamen
  ("gelderland" in het gebied) vond hem niet.

Daarnaast telde de Atom-vertaling de MeteoAlarm-ernst een kleur te hoog
("Minor" = groen werd geel, "Moderate" = geel werd oranje). Hier telt het
awareness_level van MeteoAlarm zelf ("2; yellow; Moderate").

Alleen pure functies, zonder Home Assistant, zodat het los te testen is.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

try:
    from .taal import vertaal_soort
except ImportError:  # in de tests zonder pakketstructuur
    from taal import vertaal_soort

JSON_URL = "https://feeds.meteoalarm.org/api/v1/warnings/feeds-"

# awareness_level "2; yellow; Moderate" -> kleur en rang van Stormchase
KLEUREN: dict[str, tuple[str, int]] = {
    "yellow": ("geel", 1),
    "orange": ("oranje", 2),
    "red": ("rood", 3),
}
# Zonder awareness_level: de CAP-ernst (Minor is groen: geen waarschuwing)
ERNST: dict[str, tuple[str, int]] = {
    "Moderate": ("geel", 1),
    "Severe": ("oranje", 2),
    "Extreme": ("rood", 3),
}

# Namen waaronder MeteoAlarm (nl en en) de Nederlandse gebieden noemt
SYNONIEMEN: dict[str, tuple[str, ...]] = {
    "noord-holland": ("noord-holland", "north holland", "north-holland"),
    "zuid-holland": ("zuid-holland", "south holland", "south-holland"),
    "noord-brabant": ("noord-brabant", "north brabant", "north-brabant"),
    "waddeneilanden": ("waddeneilanden", "wadden islands"),
    "waddenzee": ("waddenzee", "wadden sea"),
    "ijsselmeergebied": ("ijsselmeergebied", "ijsselmeer"),
    "friesland": ("friesland", "fryslân", "fryslan"),
}

_LAND = re.compile(r"^\s*(the\s+)?(nederland|netherlands)\b", re.IGNORECASE)
_UITZONDERING = re.compile(r"\b(met uitzondering van|except|behalve)\b", re.IGNORECASE)
_DELEN = re.compile(r"\b(delen van|parts of)\b:?", re.IGNORECASE)


def _tijd(waarde) -> datetime | None:
    if not isinstance(waarde, str) or not waarde:
        return None
    try:
        moment = datetime.fromisoformat(waarde.replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _namen(naam: str) -> tuple[str, ...]:
    klein = naam.lower().strip()
    return SYNONIEMEN.get(klein, (klein,))


def landelijk(gebied: str | None) -> bool:
    """Gaat deze waarschuwing over heel Nederland (eventueel met uitzonderingen)?"""
    return bool(gebied) and bool(_LAND.match(gebied))


def landelijk_geldt(gebied: str | None, namen: list[str] | tuple[str, ...]) -> bool:
    """Geldt een landelijke waarschuwing voor jouw gebied?

    "Nederland met uitzondering van Zeeland, ... en delen van: Limburg":
    geldt overal behalve in de volledig uitgezonderde gebieden. Een gebied
    dat alleen "deels" is uitgezonderd (delen van Limburg) telt wel mee:
    voor de rest van dat gebied geldt de waarschuwing.
    """
    if not landelijk(gebied):
        return False
    tekst = gebied.lower()
    deel = _UITZONDERING.split(tekst, maxsplit=1)
    if len(deel) < 3:
        return True  # heel Nederland
    uitzondering = deel[2]
    volledig = _DELEN.split(uitzondering, maxsplit=1)[0]
    for naam in namen:
        for variant in _namen(naam):
            if variant and variant in volledig:
                return False
    return True


def _parameter(info: dict, naam: str) -> str | None:
    for p in info.get("parameter") or []:
        if isinstance(p, dict) and p.get("valueName") == naam:
            waarde = p.get("value")
            return waarde if isinstance(waarde, str) else None
    return None


def _niveau(info: dict) -> tuple[str, int] | None:
    bewust = _parameter(info, "awareness_level")
    if bewust:
        delen = [d.strip().lower() for d in bewust.split(";")]
        if len(delen) >= 2:
            return KLEUREN.get(delen[1])  # groen of onbekend -> None
    return ERNST.get(str(info.get("severity") or ""))


def _kies_info(infos: list) -> dict | None:
    infos = [i for i in infos if isinstance(i, dict)]
    for taal in ("nl", "en"):
        for info in infos:
            if str(info.get("language") or "").lower().startswith(taal):
                return info
    return infos[0] if infos else None


def waarschuwingen(data, nu: datetime) -> list[dict]:
    """Alle lopende en komende waarschuwingen uit het JSON-antwoord, in de
    vorm van Stormchase (zelfde sleutels als de Atom-feed gaf).
    Groen, verlopen, ingetrokken en "all clear" vallen weg."""
    if isinstance(data, dict):
        items = data.get("warnings") or []
    elif isinstance(data, list):
        items = data
    else:
        return []
    uit: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        alert = item.get("alert") if isinstance(item.get("alert"), dict) else item
        if str(alert.get("msgType") or "").lower() == "cancel":
            continue
        infos = alert.get("info") or []
        info = _kies_info(infos)
        if info is None:
            continue
        niveau = _niveau(info)
        if niveau is None:
            continue
        if str(info.get("urgency") or "").lower() == "past":
            continue
        if any(str(r).lower() == "allclear" for r in (info.get("responseType") or [])):
            continue
        tot = _tijd(info.get("expires"))
        if tot is not None and tot < nu:
            continue
        gebieden = [a.get("areaDesc") for a in (info.get("area") or []) if isinstance(a, dict)]
        gebied = "; ".join(g for g in gebieden if g) or None
        # Het soort uit de Engelse tekst (de vertaling kent de Engelse
        # MeteoAlarm-termen), de rest in het Nederlands.
        engels = next((i for i in infos if isinstance(i, dict)
                       and str(i.get("language") or "").lower().startswith("en")), info)
        oorspronkelijk = engels.get("event") or info.get("event")
        kleur, rang = niveau
        uit.append({
            "titel": info.get("headline") or oorspronkelijk,
            "soort": vertaal_soort(oorspronkelijk),
            "soort_origineel": oorspronkelijk,
            "omschrijving": info.get("headline") or info.get("description"),
            "niveau": kleur,
            "rang": rang,
            "gebied": gebied,
            "vanaf": info.get("onset") or info.get("effective"),
            "tot": info.get("expires"),
            "zekerheid": info.get("certainty"),
            "urgentie": info.get("urgency"),
            # Op kleur, soort en begin: een bijgewerkte versie (nieuw
            # identifier) is geen nieuwe waarschuwing en wordt niet opnieuw gemeld.
            "id": f"meteoalarm|{kleur}|{vertaal_soort(oorspronkelijk)}|{info.get('onset') or ''}",
            "landelijk": landelijk(gebied),
        })
    return uit


def vul_per_uur(per_uur: list[dict] | None, lijst: list[dict]) -> list[dict] | None:
    """Het niveau per uur (van het KNMI) aangevuld met deze waarschuwingen:
    een uur binnen vanaf-tot krijgt minstens hun kleur."""
    if not per_uur:
        return per_uur
    rang_van = {k: r for k, r in KLEUREN.values()}
    uit = []
    for uur in per_uur:
        moment = _tijd(uur.get("tijd"))
        niveau = uur.get("niveau") or "geen"
        for w in lijst:
            van, tot = _tijd(w.get("vanaf")), _tijd(w.get("tot"))
            if moment is None or (van is not None and moment < van.replace(minute=0, second=0, microsecond=0)):
                continue
            if tot is not None and moment >= tot:
                continue
            if w["rang"] > rang_van.get(niveau, 0):
                niveau = w["niveau"]
        uit.append(dict(uur, niveau=niveau))
    return uit
