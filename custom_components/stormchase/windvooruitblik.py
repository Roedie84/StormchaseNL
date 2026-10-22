"""Windvooruitblik: harde wind van tevoren melden (0.57.0).

Gevraagd 21-10, met storm Austen op komst voor vrijdag: "hoe gaat de storm
chase app daarmee om". De windmelding keek alleen naar NU (de bijgestelde
modelwaarde of het station), de vooruitblik alleen naar onweer. Een stormdag
kwam dus pas binnen via een KNMI-code of op het moment zelf.

Hier per uur de hoogste verwachte windstoot uit Open-Meteo en de KNMI-
uurverwachting (de hoogste van de twee: dit is een vooraankondiging, en een
onderschatting kost meer dan een overschatting), per dag samengevat:
hoogste stoot, piekuur, en het tijdvak boven de drempel.

Melden:
* morgen: vanaf de avond (MELD_VANAF_UUR), de avond van tevoren;
* vandaag: de uren die nog komen, als dat nog niet gemeld was (de
  verwachting kan 's nachts zijn opgeschaald);
* elke dag één keer per zwaarteklasse (drempel, 75, 100 km/u): schaalt het op,
  dan opnieuw.

0.58.2 (22-10, "veel meldingen van storm nu"): drie meldingen op één middag
(vandaag 60 km/u precies op de drempel in het lopende uur, morgen 63 uit
Open-Meteo en daarna 77 uit KNMI). Nu:
* per dag in principe één melding; opnieuw alleen bij een echte opschaling:
  naar klasse 3 (100 km/u) of minstens OPSCHALING_KMH hoger dan gemeld;
* pas melden vanaf drempel + MARGE_KMH;
* vandaag alleen als het tijdvak boven de drempel minstens een uur in de
  toekomst begint (het lopende uur telt niet; dat is de live windmelding) en
  de dag nog niet als morgen gemeld was;
* `gemeld` is {datum: {"klasse", "kmh"}}; de oude vorm {datum: klasse} blijft
  leesbaar.

Bewust zonder Home Assistant, zodat het los te testen is.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, tzinfo

MELD_VANAF_UUR = 18
KLASSEN = (75.0, 100.0)
# 0.58.2: rust in de meldingen
MARGE_KMH = 5.0
OPSCHALING_KMH = 15.0
VOORLOOP = timedelta(hours=1)
DAGEN = 3
DAGNAMEN = ("ma", "di", "wo", "do", "vr", "za", "zo")


def _lokaal_uur(tekst, tz: tzinfo) -> datetime | None:
    try:
        moment = datetime.fromisoformat(str(tekst).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    moment = moment.replace(tzinfo=tz) if moment.tzinfo is None else moment.astimezone(tz)
    return moment.replace(minute=0, second=0, microsecond=0)


def per_uur(open_meteo: dict | None, knmi_uren: list | None, tz: tzinfo) -> dict:
    """{lokaal uur: (stoot km/u, bron)} - de hoogste van de bronnen."""
    uit: dict[datetime, tuple[float, str]] = {}

    def zet(moment, waarde, bron):
        if moment is None or waarde is None:
            return
        try:
            waarde = float(waarde)
        except (TypeError, ValueError):
            return
        if moment not in uit or waarde > uit[moment][0]:
            uit[moment] = (waarde, bron)

    tijden = (open_meteo or {}).get("time") or []
    stoten = (open_meteo or {}).get("wind_gusts_10m") or []
    for tekst, waarde in zip(tijden, stoten):
        zet(_lokaal_uur(tekst, tz), waarde, "open-meteo")
    for uur in knmi_uren or []:
        if isinstance(uur, dict):
            zet(_lokaal_uur(uur.get("datetime"), tz), uur.get("native_wind_gust_speed"), "knmi")
    return uit


def klasse(stoot: float | None, drempel: float) -> int:
    if stoot is None or stoot < drempel:
        return 0
    return 1 + sum(1 for k in KLASSEN if stoot >= k and k > drempel)


def _tot(laatste: datetime) -> str:
    """Eindtijd van het laatste uur; middernacht als 24:00."""
    eind = laatste + timedelta(hours=1)
    return "24:00" if eind.date() != laatste.date() else eind.strftime("%H:%M")


def tijdvak(d: dict, drempel: float) -> str | None:
    """Het tijdvak boven de drempel in gewone taal (0.58.1).

    "de hele dag", "van 20:00 tot middernacht", "van 13:00 tot 16:00", of bij
    losse uren geen van-tot maar het aantal: "4 uur boven 60 km/u".
    """
    uren = d.get("uren_boven_drempel") or 0
    if not uren and not d.get("boven_drempel_van"):
        return None
    grens = f"boven {drempel:.0f} km/u"
    if d.get("hele_dag"):
        return f"{grens} de hele dag"
    # Een dagoverzicht van voor 0.58.1 kent `aaneengesloten` niet; een van-tot
    # was daar alleen bruikbaar als het tijdvak klopte.
    if d.get("boven_drempel_van") and d.get("aaneengesloten", True):
        tot = d.get("boven_drempel_tot")
        tot = "middernacht" if tot == "24:00" else tot
        return f"{grens} van {d['boven_drempel_van']} tot {tot}"
    return f"{uren} uur {grens}"


def dagen(uren: dict, nu: datetime, drempel: float, aantal: int = DAGEN) -> list[dict]:
    """Per lokale dag vanaf vandaag (alleen uren die nog komen)."""
    huidig = nu.replace(minute=0, second=0, microsecond=0)
    uit = []
    for i in range(aantal):
        dag = (nu + timedelta(days=i)).date()
        reeks = sorted((m, w) for m, w in uren.items() if m.date() == dag and m >= huidig)
        if not reeks:
            continue
        piek_om, (piek, bron) = max(reeks, key=lambda mw: mw[1][0])
        boven = [m for m, (w, _b) in reeks if w >= drempel]
        # 0.58.1: alleen een van-tot bij aaneengesloten uren; tot middernacht
        # heet 24:00 (was 00:00, live za 24-10: "00:00 tot 00:00", 4 uur).
        aaneen = bool(boven) and all(
            b - a == timedelta(hours=1) for a, b in zip(boven, boven[1:])
        )
        uit.append({
            "datum": dag.isoformat(),
            "dag": "vandaag" if i == 0 else "morgen" if i == 1 else DAGNAMEN[dag.weekday()],
            "max_kmh": round(piek),
            "piek_om": piek_om.strftime("%H:%M"),
            "bron": bron,
            "boven_drempel_van": boven[0].strftime("%H:%M") if aaneen else None,
            "boven_drempel_tot": _tot(boven[-1]) if aaneen else None,
            "uren_boven_drempel": len(boven),
            "aaneengesloten": aaneen,
            # 0.58.2: het eerste uur boven de drempel (ook bij losse uren)
            "eerste_boven": boven[0].isoformat() if boven else None,
            "hele_dag": len(boven) == 24,
            "klasse": klasse(piek, drempel),
        })
        uit[-1]["tijdvak"] = tijdvak(uit[-1], drempel)
    return uit


def vorige(gemeld: dict, datum: str, drempel: float) -> tuple[int, float] | None:
    """(klasse, km/u) zoals gemeld, of None (0.58.2).

    De oude opslag {datum: klasse} kent geen km/u; dan de ondergrens van die
    klasse (drempel, 75, 100).
    """
    waarde = (gemeld or {}).get(datum)
    if waarde is None:
        return None
    if isinstance(waarde, dict):
        try:
            k = int(waarde.get("klasse") or 0)
            kmh = waarde.get("kmh")
            kmh = float(kmh) if kmh is not None else None
        except (TypeError, ValueError):
            return None
    else:
        try:
            k, kmh = int(waarde), None
        except (TypeError, ValueError):
            return None
    if k <= 0:
        return None
    if kmh is None:
        grenzen = (drempel, *[g for g in KLASSEN if g > drempel])
        kmh = grenzen[min(k, len(grenzen)) - 1]
    return k, kmh


def als_gemeld(d: dict) -> dict:
    """Wat er van een melding bewaard wordt (0.58.2)."""
    return {"klasse": int(d["klasse"]), "kmh": d["max_kmh"]}


def te_melden(dagoverzicht: list[dict], nu: datetime, gemeld: dict,
              drempel: float | None = None) -> dict | None:
    """De dag die nu gemeld moet worden, of None.

    `gemeld`: {datum: {"klasse", "kmh"}} (of de oude vorm {datum: klasse}).
    `drempel`: de winddrempel (standaard 60 km/u).
    """
    vandaag = nu.date().isoformat()
    for d in dagoverzicht:
        if d["dag"] == "morgen" and nu.hour < MELD_VANAF_UUR:
            continue
        if d["datum"] != vandaag and d["dag"] != "morgen":
            continue
        if not d.get("klasse"):
            continue
        grens = 60.0 if drempel is None else float(drempel)
        if d["max_kmh"] < grens + MARGE_KMH:
            continue
        eerder = vorige(gemeld, d["datum"], grens)
        if eerder is None:
            if d["datum"] == vandaag and not _komt_nog(d, nu):
                continue
            return d
        k, kmh = eerder
        if (d["klasse"] >= 3 and k < 3) or d["max_kmh"] >= kmh + OPSCHALING_KMH:
            return d
    return None


def _komt_nog(d: dict, nu: datetime) -> bool:
    """Begint het tijdvak boven de drempel minstens een uur na nu? (0.58.2)"""
    eerste = d.get("eerste_boven")
    if not eerste:
        return False
    try:
        moment = datetime.fromisoformat(eerste)
    except (TypeError, ValueError):
        return False
    if moment.tzinfo is None and nu.tzinfo is not None:
        moment = moment.replace(tzinfo=nu.tzinfo)
    return moment >= nu + VOORLOOP


def bericht(d: dict, drempel: float) -> tuple[str, str]:
    """Titel en tekst voor de melding."""
    stoot = d["max_kmh"]
    zwaarte = "Zware windstoten" if stoot >= 100 else "Krachtige windstoten" if stoot >= 75 else "Harde windstoten"
    wanneer = d["dag"]
    if wanneer == "morgen":
        datum = date.fromisoformat(d["datum"])
        wanneer = f"morgen ({DAGNAMEN[datum.weekday()]} {datum.day}-{datum.month})"
    tekst = f"{zwaarte} verwacht {wanneer}: tot {stoot} km/u rond {d['piek_om']}"
    vak = tijdvak(d, drempel)
    if vak:
        tekst += f", {vak}"
    tekst += f" ({'KNMI' if d.get('bron') == 'knmi' else 'Open-Meteo'})."
    titel = "Storm op komst" if stoot >= 75 else "Harde wind op komst"
    return titel, tekst


def gemeld_opschonen(gemeld: dict, nu: datetime) -> dict:
    """Alleen vandaag en later bewaren."""
    vandaag = nu.date().isoformat()
    return {k: v for k, v in (gemeld or {}).items() if isinstance(k, str) and k >= vandaag}
