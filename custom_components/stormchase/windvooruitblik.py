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

Bewust zonder Home Assistant, zodat het los te testen is.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, tzinfo

MELD_VANAF_UUR = 18
KLASSEN = (75.0, 100.0)
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
        uit.append({
            "datum": dag.isoformat(),
            "dag": "vandaag" if i == 0 else "morgen" if i == 1 else DAGNAMEN[dag.weekday()],
            "max_kmh": round(piek),
            "piek_om": piek_om.strftime("%H:%M"),
            "bron": bron,
            "boven_drempel_van": boven[0].strftime("%H:%M") if boven else None,
            "boven_drempel_tot": (boven[-1] + timedelta(hours=1)).strftime("%H:%M") if boven else None,
            "uren_boven_drempel": len(boven),
            "klasse": klasse(piek, drempel),
        })
    return uit


def te_melden(dagoverzicht: list[dict], nu: datetime, gemeld: dict) -> dict | None:
    """De dag die nu gemeld moet worden, of None. `gemeld`: {datum: klasse}."""
    vandaag = nu.date().isoformat()
    for d in dagoverzicht:
        if d["dag"] == "morgen" and nu.hour < MELD_VANAF_UUR:
            continue
        if d["datum"] != vandaag and d["dag"] != "morgen":
            continue
        if d["klasse"] > int(gemeld.get(d["datum"], 0)):
            return d
    return None


def bericht(d: dict, drempel: float) -> tuple[str, str]:
    """Titel en tekst voor de melding."""
    stoot = d["max_kmh"]
    zwaarte = "Zware windstoten" if stoot >= 100 else "Krachtige windstoten" if stoot >= 75 else "Harde windstoten"
    wanneer = d["dag"]
    if wanneer == "morgen":
        datum = date.fromisoformat(d["datum"])
        wanneer = f"morgen ({DAGNAMEN[datum.weekday()]} {datum.day}-{datum.month})"
    tekst = f"{zwaarte} verwacht {wanneer}: tot {stoot} km/u rond {d['piek_om']}"
    if d.get("boven_drempel_van"):
        tekst += f", boven {drempel:.0f} km/u van {d['boven_drempel_van']} tot {d['boven_drempel_tot']}"
    tekst += f" ({'KNMI' if d.get('bron') == 'knmi' else 'Open-Meteo'})."
    titel = "Storm op komst" if stoot >= 75 else "Harde wind op komst"
    return titel, tekst


def gemeld_opschonen(gemeld: dict, nu: datetime) -> dict:
    """Alleen vandaag en later bewaren."""
    vandaag = nu.date().isoformat()
    return {k: v for k, v in (gemeld or {}).items() if isinstance(k, str) and k >= vandaag}
