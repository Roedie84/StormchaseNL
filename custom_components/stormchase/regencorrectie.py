"""Wanneer begint de regen echt? De nowcast bijstellen met de eigen uitkomsten (0.56.0, L-SC-011).

Gemeten 19-10 (validatie, KNMI-nowcast): van 43 uitgekomen voorspellingen
begon de regen er 31 keer eerder dan voorspeld, mediaan 7 minuten, en hoe
verder vooruit hoe meer (15-45 min gemiddeld 10, verder 15 minuten). Met een
vooraankondiging van 10 minuten kwam de melding zo vaak pas als het al regende.

Hier leert Stormchase uit zijn eigen afgeronde voorspellingen (per bron) een
bijstelling, op dezelfde manier als de windstootcorrectie: niets aangenomen,
alles uit de metingen. Twee vormen worden getoetst:

    verschuiving   werkelijk = voorspeld + mediaan(werkelijk - voorspeld),
                   per horizon (tot 15 / 15-45 / verder), anders over alles
    verhouding     werkelijk = voorspeld x mediaan(werkelijk / voorspeld)

Elke vorm wordt getoetst met leave-one-out: voor elke uitkomst de
bijstelling uit alle andere, en dan de gemiddelde afwijking. Alleen een vorm
die de afwijking minstens MIN_WINST beter maakt dan de kale nowcast wordt
gebruikt; anders blijft het de kale nowcast.

De validatie blijft de KALE voorspelling vastleggen, anders leert de
correctie van zichzelf.

Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

try:
    from .validatie import horizon
except ImportError:  # in de tests zonder pakketstructuur
    from validatie import horizon

#: Pas vanaf zoveel uitgekomen voorspellingen van dezelfde bron.
MIN_UITKOMSTEN = 15
#: Per horizon een eigen verschuiving vanaf zoveel uitkomsten in die horizon.
MIN_PER_HORIZON = 6
#: De bijstelling moet de gemiddelde afwijking minstens zoveel beter maken.
MIN_WINST = 0.10
#: Grenzen: nooit meer dan dit verschuiven, nooit buiten deze verhouding.
MAX_VERSCHUIVING_MIN = 30.0
VERHOUDING_GRENZEN = (0.4, 1.3)
#: Voorspellingen korter dan dit doen niet mee aan een verhouding.
MIN_VOORSPELD_VOOR_VERHOUDING = 5


def _mediaan(waarden: list[float]) -> float:
    rij = sorted(waarden)
    m = len(rij) // 2
    return rij[m] if len(rij) % 2 else (rij[m - 1] + rij[m]) / 2


def paren(uitkomsten: list[dict], bron: str) -> list[tuple[float, float]]:
    """(voorspeld, werkelijk) in minuten, alleen uitgekomen regen van deze bron."""
    uit = []
    for r in uitkomsten or []:
        if r.get("soort") != "regen" or not r.get("uitgekomen") or r.get("bron") != bron:
            continue
        v, w = r.get("voorspeld_over_min"), r.get("werkelijk_over_min")
        if isinstance(v, (int, float)) and isinstance(w, (int, float)) and v >= 0 and w >= 0:
            uit.append((float(v), float(w)))
    return uit


def _begrens(x: float, laag: float, hoog: float) -> float:
    return max(laag, min(hoog, x))


def _verschuivingen(rij: list[tuple[float, float]]) -> dict:
    """Mediaan (werkelijk - voorspeld) per horizon en over alles."""
    alles = [w - v for v, w in rij]
    uit = {"alles": _begrens(_mediaan(alles), -MAX_VERSCHUIVING_MIN, MAX_VERSCHUIVING_MIN)} if alles else {}
    per: dict[str, list[float]] = {}
    for v, w in rij:
        per.setdefault(horizon(v), []).append(w - v)
    for h, verschil in per.items():
        if len(verschil) >= MIN_PER_HORIZON:
            uit[h] = _begrens(_mediaan(verschil), -MAX_VERSCHUIVING_MIN, MAX_VERSCHUIVING_MIN)
    return uit


def _verhouding(rij: list[tuple[float, float]]) -> float | None:
    r = [w / v for v, w in rij if v >= MIN_VOORSPELD_VOOR_VERHOUDING]
    return _begrens(_mediaan(r), *VERHOUDING_GRENZEN) if r else None


def _pas_toe(vorm: str, model, voorspeld: float) -> float:
    if vorm == "verschuiving":
        schuif = model.get(horizon(voorspeld), model.get("alles", 0.0))
        return max(0.0, voorspeld + schuif)
    if vorm == "verhouding" and model is not None:
        return max(0.0, voorspeld * model)
    return voorspeld


def _maak(vorm: str, rij: list[tuple[float, float]]):
    return _verschuivingen(rij) if vorm == "verschuiving" else _verhouding(rij)


def leer(uitkomsten: list[dict], bron: str) -> dict:
    """Welke bijstelling geldt nu voor deze bron, met de onderbouwing."""
    rij = paren(uitkomsten, bron)
    basis = {"bron": bron, "uitkomsten": len(rij), "vorm": "geen", "toegepast": False}
    if len(rij) < MIN_UITKOMSTEN:
        return {**basis, "reden": f"{len(rij)} van de {MIN_UITKOMSTEN} uitkomsten nodig"}
    kaal = sum(abs(w - v) for v, w in rij) / len(rij)
    toets = {"geen": round(kaal, 1)}
    for vorm in ("verschuiving", "verhouding"):
        fout = 0.0
        for i, (v, w) in enumerate(rij):
            model = _maak(vorm, rij[:i] + rij[i + 1:])
            fout += abs(w - _pas_toe(vorm, model, v))
        toets[vorm] = round(fout / len(rij), 1)
    beste = min(("verschuiving", "verhouding"), key=lambda vorm: toets[vorm])
    uit = {**basis, "afwijking_min": toets}
    if toets[beste] > kaal * (1 - MIN_WINST):
        return {**uit, "reden": "geen vorm maakt de afwijking genoeg kleiner"}
    model = _maak(beste, rij)
    uit.update(vorm=beste, toegepast=True, reden=None)
    if beste == "verschuiving":
        uit["verschuiving_min"] = {h: round(s, 1) for h, s in model.items()}
    else:
        uit["verhouding"] = round(model, 2)
    return uit


def corrigeer(begint_over: int | None, correctie: dict | None) -> int | None:
    """De bijgestelde start van de regen (hele minuten), of de kale als er niets geldt."""
    if begint_over is None or not correctie or not correctie.get("toegepast"):
        return begint_over
    if correctie["vorm"] == "verschuiving":
        model = correctie.get("verschuiving_min") or {}
    else:
        model = correctie.get("verhouding")
    return int(round(_pas_toe(correctie["vorm"], model, float(begint_over))))
