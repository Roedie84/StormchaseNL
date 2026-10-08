"""Wat er over een herstart of herlaadbeurt bewaard blijft (0.47.0).

Home Assistant wordt hier vaak herstart. Tot 0.47.0 begon de integratie dan
deels opnieuw: open voorspellingen, de 30/30-schuilregel, de celsporen, de
naderingsreeks, de wachttijden van de meldingen en de al gemelde officiële
waarschuwingen zaten alleen in het geheugen. Een herstart kon daardoor een
melding opnieuw laten versturen of een lopende schuilperiode laten vergeten.

Deze module zet die toestand om naar iets wat in een Store past en terug,
met opschoning bij het laden: wat te oud is, valt weg, zodat een lange
onderbreking geen oude cellen of vlaggen terugbrengt.

Bewust vrij van Home Assistant-imports, zodat het zonder HA te testen is.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

# Versie van het opslagformaat, voor een eventuele latere migratie
OPSLAG_VERSIE = 1

# Celsporen, inslagpunten, naderingspunten en de overgangsvlaggen (nabij,
# nadert, schuilen) die ouder zijn dan dit vallen bij het laden weg. Een
# herstart duurt een minuut of twee; na een half uur stil is het een andere
# situatie en hoort de integratie opnieuw te beginnen.
MAX_LEEFTIJD_S = 1800

# Een al gemelde waarschuwing zonder einddatum blijft hooguit zo lang bewaard
GEMELD_ZONDER_EINDE_S = 2 * 24 * 3600

# Kenmerken in de attributen van een geo_location-inslag die de tijd van de
# inslag zelf dragen. De Blitzortung-integratie gebruikt publication_date.
INSLAGTIJD_KENMERKEN = ("publication_date", "time", "timestamp")


def _getal(waarde) -> float | None:
    """Een eindig getal uit de opslag, anders None (ook niet voor bools)."""
    if isinstance(waarde, bool) or not isinstance(waarde, (int, float)):
        return None
    if waarde != waarde or waarde in (float("inf"), float("-inf")):
        return None
    return float(waarde)


def als_tijdstempel(waarde) -> float | None:
    """Een datetime, ISO-tekst of epoch (s, ms of ns) als epoch-seconden."""
    if waarde is None or isinstance(waarde, bool):
        return None
    if isinstance(waarde, datetime):
        if waarde.tzinfo is None:
            return None
        return waarde.timestamp()
    if isinstance(waarde, (int, float)):
        getal = float(waarde)
        # Nanoseconden en milliseconden terugbrengen naar seconden
        if getal > 1e17:
            getal /= 1e9
        elif getal > 1e11:
            getal /= 1e3
        return getal if getal > 0 else None
    if isinstance(waarde, str):
        tekst = waarde.strip()
        if not tekst:
            return None
        try:
            return als_tijdstempel(float(tekst))
        except ValueError:
            pass
        try:
            moment = datetime.fromisoformat(tekst.replace("Z", "+00:00"))
        except ValueError:
            return None
        return als_tijdstempel(moment)
    return None


def inslagtijd(attributen: dict | None, terugval: float, nu: float) -> float:
    """De tijd van de inslag zelf, niet die van het eerste zien.

    Tot 0.47.0 kreeg elke inslag het tijdstip waarop de integratie hem voor
    het eerst zag. Na een herlaadbeurt zag ze alle bestaande inslagen
    opnieuw voor het eerst, en telden oude inslagen als nieuw in de
    frequentie en de cellen. Nu de eigen tijd uit de attributen, anders de
    terugval (last_changed van de entiteit). Nooit later dan nu.
    """
    for kenmerk in INSLAGTIJD_KENMERKEN:
        stempel = als_tijdstempel((attributen or {}).get(kenmerk))
        if stempel is not None:
            return min(stempel, nu)
    return min(terugval, nu)


def puntsleutel(stempel: float, breedte: float, lengte: float) -> tuple:
    """Vergelijkbare sleutel voor een inslagpunt, ongevoelig voor afronding."""
    return (round(stempel, 1), round(breedte, 4), round(lengte, 4))


def _punt(rij, nu: float, grens: float) -> tuple[float, float, float] | None:
    """Een (tijd, breedte, lengte) uit de opslag, of None als het niet deugt."""
    if not isinstance(rij, (list, tuple)) or len(rij) != 3:
        return None
    t, lat, lon = (_getal(w) for w in rij)
    if t is None or lat is None or lon is None:
        return None
    if t < grens or t > nu + 60:
        return None
    return (t, lat, lon)


def _vlag(waarde) -> bool | None:
    return waarde if isinstance(waarde, bool) else None


def snoei_storm(
    bewaard: dict | None,
    nu: float,
    max_leeftijd: float = MAX_LEEFTIJD_S,
    inslag_leeftijd: float | None = None,
) -> dict[str, Any]:
    """Maak de bewaarde onweerstoestand schoon voor gebruik na een herstart.

    Geeft altijd alle sleutels terug, met lege waarden als er niets (of niets
    bruikbaars) bewaard was.
    """
    uit: dict[str, Any] = {
        "punten": [],
        "inslagen": [],
        "celspoor": [],
        "celsporen": [],
        "volgend_celkenmerk": 1,
        "min_per_cel": {},
        "nadering": None,
        "laatste_dichtbij": None,
        "was_schuilen": None,
        "was_nearby": None,
        "was_approaching": None,
    }
    if not isinstance(bewaard, dict):
        return uit

    grens = nu - max_leeftijd
    opgeslagen = _getal(bewaard.get("opgeslagen_op"))
    vers = opgeslagen is not None and nu - max_leeftijd <= opgeslagen <= nu + 60

    for rij in bewaard.get("punten") or []:
        punt = _punt(rij, nu, grens)
        if punt is not None:
            uit["punten"].append(punt)
    uit["punten"].sort(key=lambda p: p[0])

    inslag_grens = nu - (inslag_leeftijd if inslag_leeftijd is not None else max_leeftijd)
    for rij in bewaard.get("inslagen") or []:
        if not isinstance(rij, (list, tuple)) or len(rij) != 2:
            continue
        t, afstand = _getal(rij[0]), _getal(rij[1])
        if t is None or afstand is None or t < inslag_grens or t > nu + 60:
            continue
        uit["inslagen"].append((t, afstand))
    uit["inslagen"].sort(key=lambda p: p[0])

    spoor = [_punt(r, nu, float("-inf")) for r in bewaard.get("celspoor") or []]
    spoor = [p for p in spoor if p is not None]
    if spoor and spoor[-1][0] >= grens:
        uit["celspoor"] = spoor

    hoogste = 0
    for item in bewaard.get("celsporen") or []:
        if not isinstance(item, dict):
            continue
        kenmerk = item.get("id")
        if isinstance(kenmerk, bool) or not isinstance(kenmerk, int):
            continue
        hoogste = max(hoogste, kenmerk)
        punten = [_punt(r, nu, float("-inf")) for r in item.get("punten") or []]
        punten = [p for p in punten if p is not None]
        # Een spoor waarvan het laatste punt te oud is, is een andere cel
        if not punten or punten[-1][0] < grens:
            continue
        uit["celsporen"].append({"id": kenmerk, "punten": punten})

    # Het volgende kenmerk loopt altijd door, ook als de sporen wegvallen:
    # anders zou een nieuwe cel het kenmerk van een open voorspelling krijgen.
    volgend = bewaard.get("volgend_celkenmerk")
    if isinstance(volgend, bool) or not isinstance(volgend, int):
        volgend = 1
    uit["volgend_celkenmerk"] = max(volgend, hoogste + 1, 1)

    behouden = {s["id"] for s in uit["celsporen"]}
    behouden |= {
        k for k in bewaard.get("behoud_cellen") or []
        if isinstance(k, int) and not isinstance(k, bool)
    }
    for sleutel, afstand in (bewaard.get("min_per_cel") or {}).items():
        try:
            kenmerk = int(sleutel)
        except (TypeError, ValueError):
            continue
        waarde = _getal(afstand)
        if waarde is not None and kenmerk in behouden:
            uit["min_per_cel"][kenmerk] = waarde

    if isinstance(bewaard.get("nadering"), dict):
        uit["nadering"] = bewaard["nadering"]

    # De schuilregel rekent zelf af tegen SCHUILNALOOP; de tijd zelf blijft
    # dus staan zolang hij niet in de toekomst ligt.
    dichtbij = _getal(bewaard.get("laatste_dichtbij"))
    if dichtbij is not None and dichtbij <= nu + 60:
        uit["laatste_dichtbij"] = dichtbij

    # De overgangsvlaggen alleen bij een korte onderbreking. Zo komt "veilig"
    # nog na een herstart midden in een schuilperiode, maar niet uren later.
    if vers:
        for naam in ("was_schuilen", "was_nearby", "was_approaching"):
            uit[naam] = _vlag(bewaard.get(naam))

    return uit


# ---- Al gemelde officiële waarschuwingen ----


def gemeld_naar_opslag(gemeld: dict[str, dict]) -> dict[str, dict]:
    """De al gemelde waarschuwingen, met tot wanneer ze gelden."""
    return {
        str(sleutel): {"tot": info.get("tot"), "gemeld_op": info.get("gemeld_op")}
        for sleutel, info in gemeld.items()
    }


def gemeld_uit_opslag(bewaard, nu: float) -> dict[str, dict]:
    """Gemelde waarschuwingen terughalen; verlopen exemplaren vallen weg.

    Ook de vorm van voor 0.47.0 (een lijst met sleutels) wordt gelezen; dan
    is er geen einddatum bekend en geldt de bewaartermijn zonder einde.
    """
    uit: dict[str, dict] = {}
    if isinstance(bewaard, list):
        bewaard = {s: {"tot": None, "gemeld_op": nu} for s in bewaard if isinstance(s, str)}
    if not isinstance(bewaard, dict):
        return uit
    for sleutel, info in bewaard.items():
        if not isinstance(sleutel, str) or not isinstance(info, dict):
            continue
        tot = _getal(info.get("tot"))
        gemeld_op = _getal(info.get("gemeld_op"))
        if tot is not None:
            if tot < nu:
                continue
        elif gemeld_op is None or gemeld_op < nu - GEMELD_ZONDER_EINDE_S:
            continue
        uit[sleutel] = {"tot": tot, "gemeld_op": gemeld_op}
    return uit


# ---- Wachttijden van de meldingen ----


def tijden_naar_opslag(tijden: dict[str, datetime | None]) -> dict[str, float]:
    """Wachttijden als epoch-seconden (wandkloktijd, geen monotone klok)."""
    uit = {}
    for naam, moment in tijden.items():
        stempel = als_tijdstempel(moment)
        if stempel is not None:
            uit[naam] = stempel
    return uit


def tijden_uit_opslag(bewaard, nu: float) -> dict[str, float]:
    """Wachttijden terughalen; een tijd in de toekomst (klok verzet) valt weg."""
    if not isinstance(bewaard, dict):
        return {}
    uit = {}
    for naam, waarde in bewaard.items():
        stempel = _getal(waarde)
        if isinstance(naam, str) and stempel is not None and stempel <= nu + 60:
            uit[naam] = stempel
    return uit


# ---- Wegschrijven zonder de Store eindeloos op te schuiven ----


class Bewaarplan:
    """Plant een uitgestelde schrijfactie, maar niet opnieuw zolang er een klaarstaat.

    Dezelfde rem als in BronHistorie.plan_opslag: de Store schuift een
    uitgestelde schrijfactie bij elke nieuwe aanvraag op, en de
    onweersronde loopt elke tien seconden.
    """

    def __init__(self, plannen: Callable[[], None] | None = None) -> None:
        self.plannen = plannen
        self.gepland = False

    def plan(self) -> None:
        if self.gepland or self.plannen is None:
            return
        self.gepland = True
        self.plannen()

    def geschreven(self) -> None:
        """Roep aan vanuit de datafunctie van de Store."""
        self.gepland = False
