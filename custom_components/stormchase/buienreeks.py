"""Uit een neerslagreeks halen wanneer het regent, stopt en weer begint.

De reeks is een lijst van (minuten vanaf nu, mm per uur), oplopend in tijd.
Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

from datetime import datetime

try:
    from .const import STATION_REGEN_CODES, STATION_REGEN_MAX_KM, STATION_REGEN_MAX_S
except ImportError:  # in de tests zonder pakketstructuur
    from const import STATION_REGEN_CODES, STATION_REGEN_MAX_KM, STATION_REGEN_MAX_S


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


# ---- 0.61.0 (L-SC-029): motregen van het nabije station ----

def _epoch(stempel) -> float | None:
    if stempel is None:
        return None
    try:
        tijd = datetime.fromisoformat(str(stempel).replace("Z", "+00:00"))
    except ValueError:
        return None
    return tijd.timestamp() if tijd.tzinfo is not None else None


def _getal_of_niets(waarde) -> float | None:
    try:
        return None if waarde is None else float(waarde)
    except (TypeError, ValueError):
        return None


def station_regen(meting: dict | None, drempel: float, nu: float) -> dict | None:
    """Meet het nabije station nu neerslag? (0.61.0, L-SC-029)

    Op 01-11 mat Hupsel (3,4 km) ~130 min motregen (0,01-0,51 mm/u, weercode
    51/57) terwijl de KNMI-nowcast 0,0 gaf en het regenbeeld "droog" zei: de
    radar ziet lage motregen onder de bundel niet. Telt als regen als het
    station binnen STATION_REGEN_MAX_KM ligt, de meting hooguit
    STATION_REGEN_MAX_S oud is, en de neerslag minstens de regendrempel is
    of de weercode motregen/regen zegt (50-67). Elk van beide met de afstand
    van het station dat die waarde leverde. Anders None.
    """
    if not isinstance(meting, dict):
        return None
    tijd = _epoch(meting.get("waargenomen_op"))
    if tijd is None or not -300 <= nu - tijd <= STATION_REGEN_MAX_S:
        return None

    def dichtbij(afstand) -> bool:
        afstand = _getal_of_niets(afstand)
        return afstand is not None and afstand <= STATION_REGEN_MAX_KM

    # KNMI: intensiteit (mm/u); Bright Sky: neerslag per 10 minuten (mm)
    mm = _getal_of_niets(meting.get("neerslag_intensiteit"))
    mm_afstand = meting.get("neerslag_station_afstand_km")
    if mm is None and meting.get("bron") == "brightsky":
        per_10 = _getal_of_niets(meting.get("neerslag"))
        mm = None if per_10 is None else round(per_10 * 6, 2)
        mm_afstand = meting.get("station_afstand_km")
    code = meting.get("weercode")
    try:
        code = None if code is None else int(code)
    except (TypeError, ValueError):
        code = None

    door_mm = mm is not None and mm >= drempel and dichtbij(mm_afstand)
    door_code = (
        code is not None and code in STATION_REGEN_CODES
        and dichtbij(meting.get("weer_station_afstand_km"))
    )
    if not (door_mm or door_code):
        return None
    if door_code:
        station = meting.get("weer_station")
        afstand = meting.get("weer_station_afstand_km")
    else:
        station = meting.get("neerslag_station") or meting.get("station")
        afstand = mm_afstand
    return {
        "intensiteit": mm,
        "weercode": code,
        "motregen": code is None or code < 60,
        "station": station,
        "afstand_km": afstand,
        "waargenomen_op": meting.get("waargenomen_op"),
    }


def met_station_regen(data: dict, station: dict | None) -> dict:
    """Neerslaggegevens met de motregen van het station erin (0.61.0, L-SC-029).

    Zonder stationsregen: alleen `regen_bron` ("radar" bij radarregen, anders
    None) en `station_regen` None; verder ongewijzigd. Met: `regent` aan,
    `regen_bron` "station", `stopt_over` onbekend (de radar ziet niets om op
    te houden), en de bui die de radar ziet aankomen is de volgende bui.
    `begint_over` (meldingen, validatie) blijft wat de radar zegt.
    """
    uit = dict(data)
    if station is None or data.get("regent"):
        uit["regen_bron"] = "radar" if data.get("regent") else None
        uit["station_regen"] = None
        return uit
    uit.update(
        regent=True,
        regen_bron="station",
        station_regen=station,
        stopt_over=None,
        volgende_bui_over=data.get("begint_over"),
    )
    return uit


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


# ---- 0.51.0: het regenbeeld in één zin ----

def sterkte(mm_per_uur: float | None) -> str:
    """Licht, matig of zwaar (grenzen 2,5 en 10 mm/u)."""
    if mm_per_uur is None:
        return "onbekend"
    if mm_per_uur < 2.5:
        return "licht"
    if mm_per_uur < 10:
        return "matig"
    return "zwaar"


def _getal(waarde: float) -> str:
    return f"{waarde:.1f}".replace(".", ",")


def bui_piek(data: dict, vanaf: int | None) -> float | None:
    """Hoogste intensiteit van de bui die op `vanaf` minuten begint."""
    if vanaf is None:
        return None
    drempel = data.get("drempel") or 0.1
    piek = None
    for punt in data.get("verwachting") or []:
        minuten, mm = punt.get("minuten"), punt.get("mm_per_uur")
        if minuten is None or mm is None or minuten < vanaf:
            continue
        if mm < drempel:
            break
        piek = mm if piek is None else max(piek, mm)
    return piek


def _met_piek(data: dict, vanaf: int | None) -> str:
    piek = bui_piek(data, vanaf)
    if piek is None:
        return ""
    return f" ({sterkte(piek)}, tot {_getal(piek)} mm/u)"


def regenbeeld(data: dict | None) -> str | None:
    """Nu, wanneer het stopt en wanneer de volgende bui komt, in één zin.

    Op 9 oktober 22:26 viel er een korte, zware bui (14-16 mm/u). De sensor
    'regen begint over' stond toen op 82: dat was de volgende bui, maar zo
    las het niet. Deze zin zegt het allemaal.
    """
    if not data:
        return None
    # 0.61.0 (L-SC-029): het station meet motregen, de radar zegt droog
    station = data.get("station_regen")
    if data.get("regent") and data.get("regen_bron") == "station" and station:
        zin = "Lichte motregen" if station.get("motregen") else "Lichte regen"
        zin += f" (station {station.get('station') or 'dichtbij'}"
        if (station.get("intensiteit") or 0) >= 0.1:
            zin += f", {_getal(station['intensiteit'])} mm/u"
        zin += "), radar droog"
        volgende = data.get("volgende_bui_over")
        if volgende is not None:
            zin += f"; over {volgende} min een bui" + _met_piek(data, volgende)
        return zin + "."
    if data.get("regent"):
        nu = data.get("intensiteit")
        zin = f"Regent nu, {sterkte(nu)}"
        if nu is not None:
            zin += f" ({_getal(nu)} mm/u)"
        stopt = data.get("stopt_over")
        zin += (
            ", houdt de komende 2 uur aan"
            if stopt is None
            else f", droog over {stopt} min"
        )
        volgende = data.get("volgende_bui_over")
        if volgende is not None:
            zin += f"; volgende bui over {volgende} min" + _met_piek(data, volgende)
        return zin + "."
    begint = data.get("begint_over")
    if begint is not None:
        return f"Droog, over {begint} min een bui" + _met_piek(data, begint) + "."
    if data.get("verwachting") is not None:
        return "Droog, komende 2 uur geen regen."
    return None
