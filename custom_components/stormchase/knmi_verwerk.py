"""Antwoorden van de KNMI-bronnen omzetten naar de vorm van Stormchase.

Alles hier werkt op gewone dicts en lijsten, zodat de bestaande sensoren,
de buienreeks, de conditielogica en de weerentiteit ongewijzigd verder
kunnen. De vorm van de antwoorden volgt die van de KNMI-app-API en de EDR
van het KNMI Data Platform.

Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta, timezone

try:
    from .knmi_grid import afstand_km
except ImportError:  # in de tests zonder pakketstructuur
    from knmi_grid import afstand_km

# ---------------------------------------------------------------------
# Waarschuwingen
# ---------------------------------------------------------------------

# Niveau in de KNMI-app naar de kleuren en rangen van Stormchase (zelfde
# schaal als bij MeteoAlarm: geel 1, oranje 2, rood 3).
KNMI_NIVEAUS: dict[str, tuple[str, int]] = {
    "yellow": ("geel", 1),
    "orange": ("oranje", 2),
    "red": ("rood", 3),
}

# Hoeveel uur vooruit het niveau per uur in de attributen komt
UREN_VOORUIT = 24

# Trefwoorden in de Nederlandse waarschuwingstekst, van specifiek naar
# algemeen (zelfde soortnamen als de vertaling van MeteoAlarm in taal.py).
SOORT_TREFWOORDEN: tuple[tuple[str, str], ...] = (
    ("zwaar onweer", "zwaar onweer"),
    ("onweer", "onweer"),
    ("ijzel", "ijzel"),
    ("gladheid", "gladheid"),
    ("sneeuw", "sneeuw"),
    ("zeer zware windstoten", "zeer zware windstoten"),
    ("zware windstoten", "zware windstoten"),
    ("windstoten", "windstoten"),
    ("storm", "storm"),
    ("wind", "wind"),
    ("hagel", "hagel"),
    ("veel regen", "veel regen"),
    ("zware regen", "zware regen"),
    ("regen", "regen"),
    ("mist", "mist"),
    ("extreme hitte", "extreme hitte"),
    ("hitte", "hitte"),
    ("kou", "kou"),
    ("vorst", "vorst"),
)


def soort_uit_tekst(tekst: str | None) -> str | None:
    """Het soort waarschuwing uit de omschrijving, of None."""
    if not tekst:
        return None
    klein = tekst.lower()
    for woord, soort in SOORT_TREFWOORDEN:
        if woord in klein:
            return soort
    return None


def _als_tijd(waarde) -> datetime | None:
    """ISO-tijd naar datetime met tijdzone (UTC als die ontbreekt)."""
    if not isinstance(waarde, str) or not waarde:
        return None
    try:
        moment = datetime.fromisoformat(waarde.replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


def _uren(payload: dict | None) -> list[dict]:
    """De uurverwachting uit een weer-antwoord."""
    uren = ((payload or {}).get("hourly") or {}).get("forecast") or []
    return [u for u in uren if isinstance(u, dict)]


def niveau_per_uur(payload: dict | None, nu: datetime, uren: int = UREN_VOORUIT) -> list[dict]:
    """Waarschuwingsniveau per uur, vanaf het lopende uur."""
    begin = nu.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    eind = begin + timedelta(hours=uren)
    uit: list[dict] = []
    for uur in _uren(payload):
        moment = _als_tijd(uur.get("dateTime"))
        if moment is None or not (begin <= moment < eind):
            continue
        niveau = KNMI_NIVEAUS.get(str(uur.get("alertLevel") or "").lower())
        uit.append(
            {
                "tijd": moment.isoformat(),
                "niveau": niveau[0] if niveau else "geen",
            }
        )
    return uit


def _periode(per_uur: list[dict], rang: int) -> tuple[str | None, str | None]:
    """Begin en einde van de aaneengesloten uren op of boven deze rang."""
    rangen = {kleur: r for kleur, r in KNMI_NIVEAUS.values()}
    vanaf = tot = None
    for uur in per_uur:
        if rangen.get(uur["niveau"], 0) >= rang:
            if vanaf is None:
                vanaf = uur["tijd"]
            tot = uur["tijd"]
        elif vanaf is not None:
            break
    if tot is not None:
        moment = _als_tijd(tot)
        tot = (moment + timedelta(hours=1)).isoformat() if moment else None
    return vanaf, tot


def waarschuwingen(
    payload: dict | None, regio: int, regionaam: str, nu: datetime
) -> dict:
    """Zet het weer-antwoord om naar de vorm van de waarschuwingscoordinator.

    Dezelfde sleutels als bij MeteoAlarm, zodat sensoren, meldingen en het
    weerbericht niets hoeven te weten van de bron. Begin en einde zijn
    afgeleid uit het niveau per uur (de app-API geeft ze niet per
    waarschuwing).
    """
    per_uur = niveau_per_uur(payload, nu)
    actief: list[dict] = []

    for item in (payload or {}).get("alerts") or []:
        if not isinstance(item, dict):
            continue
        niveau = KNMI_NIVEAUS.get(str(item.get("level") or "").lower())
        if niveau is None:
            continue
        omschrijving = item.get("description")
        omschrijving = omschrijving.strip() if isinstance(omschrijving, str) else ""
        kleur, rang = niveau
        soort = soort_uit_tekst(omschrijving) or "weerwaarschuwing"
        vanaf, tot = _periode(per_uur, rang)
        actief.append(
            {
                "titel": item.get("title") or f"Code {kleur}",
                "soort": soort,
                "soort_origineel": omschrijving or None,
                "omschrijving": omschrijving or None,
                "niveau": kleur,
                "rang": rang,
                "gebied": regionaam,
                "vanaf": vanaf,
                "tot": tot,
                "zekerheid": None,
                "urgentie": None,
                # Op regio, kleur en soort: een herschreven tekst is geen
                # nieuwe waarschuwing en wordt niet opnieuw gemeld.
                "id": f"knmi|{regio}|{kleur}|{soort}",
                "bron": "knmi",
            }
        )

    # Een niveau voor het lopende uur zonder losse waarschuwing: toch tonen
    if not actief and per_uur and per_uur[0]["niveau"] != "geen":
        kleur = per_uur[0]["niveau"]
        rang = {k: r for k, r in KNMI_NIVEAUS.values()}[kleur]
        vanaf, tot = _periode(per_uur, rang)
        actief.append(
            {
                "titel": f"Code {kleur}",
                "soort": "weerwaarschuwing",
                "soort_origineel": None,
                "omschrijving": None,
                "niveau": kleur,
                "rang": rang,
                "gebied": regionaam,
                "vanaf": vanaf,
                "tot": tot,
                "zekerheid": None,
                "urgentie": None,
                "id": f"knmi|{regio}|{kleur}|weerwaarschuwing",
                "bron": "knmi",
            }
        )

    actief.sort(key=lambda w: w["rang"], reverse=True)
    zwaarste = actief[0] if actief else None
    return {
        "actief": actief,
        "aantal": len(actief),
        "niveau": zwaarste["niveau"] if zwaarste else None,
        "rang": zwaarste["rang"] if zwaarste else 0,
        "soort": zwaarste["soort"] if zwaarste else None,
        "gebied": zwaarste["gebied"] if zwaarste else None,
        "land": "netherlands",
        "gefilterd_op": regionaam,
        "aantal_in_land": None,
        "gebieden_in_land": [],
        "bron": "knmi",
        "regio": regionaam,
        "regio_id": regio,
        "niveau_per_uur": per_uur,
    }


# ---------------------------------------------------------------------
# Neerslag per vijf minuten
# ---------------------------------------------------------------------


def nowcast_reeks(grafiek: dict | None, nu: datetime) -> list[tuple[int, float]]:
    """Zet de neerslaggrafiek om naar (minuten vanaf nu, mm/u).

    De tijden komen als ISO-tijdstempels in UTC en worden exact gebruikt; geen
    reconstructie uit een klokuur. Waarden zijn mm per uur.
    """
    blok = (grafiek or {}).get("precipitation") or {}
    tijden = blok.get("times") or []
    waarden = blok.get("amounts") or []
    reeks: list[tuple[int, float]] = []
    for stempel, waarde in zip(tijden, waarden):
        moment = _als_tijd(stempel)
        if moment is None or waarde is None:
            continue
        try:
            mm = max(float(waarde), 0.0)
        except (TypeError, ValueError):
            continue
        minuten = int((moment - nu).total_seconds() // 60)
        if -30 <= minuten <= 180:
            reeks.append((minuten, round(mm, 2)))
    if not reeks:
        raise ValueError("lege neerslaggrafiek van het KNMI")
    return sorted(reeks)


# ---------------------------------------------------------------------
# Waarnemingen (EDR)
# ---------------------------------------------------------------------

# Altijd opgevraagd
EDR_PARAMETERS = ("ta", "rh", "td", "pp", "ff", "gff", "dd", "zm", "nhc", "hc", "ww")
# Opgevraagd als de bron ze kent; bij een 400 wordt zonder deze herhaald
EDR_EXTRA = ("rg", "R1H")

# WMO-tabel 4680 (weercode van een automatisch station)
WW_ONWEER = set(range(90, 97)) | {12}
WW_ONWEER_RECENT = {26}
WW_HAGEL = {89, 93, 96}

# Beaufortgrenzen in m/s (bovengrens per kracht)
BEAUFORT = (0.3, 1.6, 3.4, 5.5, 8.0, 10.8, 13.9, 17.2, 20.8, 24.5, 28.5, 32.7)


def beaufort(ms: float | None) -> int | None:
    """Windkracht in Beaufort uit m/s."""
    if ms is None:
        return None
    for kracht, grens in enumerate(BEAUFORT):
        if ms < grens:
            return kracht
    return 12


def _laatste_waarde(coverage: dict, parameter: str) -> tuple[float | None, str | None]:
    """De laatste waarde (niet leeg) van een parameter en het tijdstip erbij."""
    reeks = ((coverage.get("ranges") or {}).get(parameter) or {}).get("values") or []
    tijden = (
        ((coverage.get("domain") or {}).get("axes") or {}).get("t") or {}
    ).get("values") or []
    for index in range(len(reeks) - 1, -1, -1):
        waarde = reeks[index]
        if waarde is None:
            continue
        try:
            getal = float(waarde)
        except (TypeError, ValueError):
            continue
        tijd = tijden[index] if index < len(tijden) else (tijden[-1] if tijden else None)
        return getal, tijd
    return None, None


def _positie(coverage: dict) -> tuple[float, float] | None:
    assen = ((coverage.get("domain") or {}).get("axes") or {})
    try:
        return (
            float((assen.get("y") or {}).get("values")[0]),
            float((assen.get("x") or {}).get("values")[0]),
        )
    except (TypeError, IndexError, ValueError):
        return None


def metingen(
    coverages: list, breedte: float, lengte: float, namen: dict[str, str] | None = None
) -> dict:
    """Per parameter de waarde van het dichtstbijzijnde station dat hem meet.

    Niet elk station meet alles: bij Eibergen komen temperatuur en wind van
    Hupsel, maar zicht of bewolking soms van Twenthe. Welk station wat
    leverde staat in `stations`.
    """
    namen = namen or {}
    gesorteerd = []
    for coverage in coverages or []:
        if not isinstance(coverage, dict):
            continue
        positie = _positie(coverage)
        if positie is None:
            continue
        gesorteerd.append((afstand_km(breedte, lengte, *positie), coverage))
    gesorteerd.sort(key=lambda paar: paar[0])

    waarden: dict[str, float] = {}
    per_parameter: dict[str, dict] = {}
    for parameter in EDR_PARAMETERS + EDR_EXTRA:
        for afstand, coverage in gesorteerd:
            waarde, tijd = _laatste_waarde(coverage, parameter)
            if waarde is None:
                continue
            station = str(coverage.get("eumetnet:locationId") or "?")
            waarden[parameter] = waarde
            per_parameter[parameter] = {
                "station": namen.get(station, station),
                "station_id": station,
                "afstand_km": round(afstand, 1),
                "tijd": tijd,
            }
            break

    if not waarden:
        raise ValueError("geen enkele waarneming in het antwoord")

    # Het station dat de meeste waarden leverde geldt als 'het' station
    telling = Counter(p["station_id"] for p in per_parameter.values())
    hoofd_id = telling.most_common(1)[0][0]
    hoofd = next(p for p in per_parameter.values() if p["station_id"] == hoofd_id)
    tijden = Counter(p["tijd"] for p in per_parameter.values() if p.get("tijd"))

    def kmh(ms):
        return round(ms * 3.6, 1) if ms is not None else None

    ff = waarden.get("ff")
    gff = waarden.get("gff")
    nhc = waarden.get("nhc")
    ww = waarden.get("ww")
    rg = waarden.get("rg")
    hc = waarden.get("hc")
    code = int(ww) if ww is not None else None
    weerstation = per_parameter.get("ww") or {}

    return {
        "temperatuur": waarden.get("ta"),
        "luchtvochtigheid": waarden.get("rh"),
        "dauwpunt": waarden.get("td"),
        "luchtdruk": waarden.get("pp"),
        "wind": kmh(ff),
        "wind_ms": ff,
        "windstoten": kmh(gff),
        "windstoten_ms": gff,
        "windstoten_bft": beaufort(gff),
        "windrichting": waarden.get("dd"),
        "zicht": waarden.get("zm"),
        # Okta naar procent; 9 betekent 'hemel onzichtbaar' (mist)
        "bewolking": (
            None if nhc is None else (100 if nhc >= 9 else round(nhc / 8 * 100))
        ),
        # Wolkenbasis komt in voet
        "wolkenbasis": round(hc * 0.3048) if hc is not None else None,
        "neerslag": round(rg / 6, 2) if rg is not None else None,
        "neerslag_intensiteit": rg,
        "neerslag_1u": waarden.get("R1H"),
        "weercode": code,
        "onweer": code in WW_ONWEER if code is not None else None,
        "onweer_afgelopen_uur": code in WW_ONWEER_RECENT if code is not None else None,
        "hagel": code in WW_HAGEL if code is not None else None,
        "weer_station": weerstation.get("station"),
        "weer_station_afstand_km": weerstation.get("afstand_km"),
        "windstoten_station": (per_parameter.get("gff") or {}).get("station"),
        "windstoten_station_afstand_km": (per_parameter.get("gff") or {}).get("afstand_km"),
        "luchtdruk_station": (per_parameter.get("pp") or {}).get("station"),
        "luchtdruk_station_id": (per_parameter.get("pp") or {}).get("station_id"),
        "waargenomen_op": tijden.most_common(1)[0][0] if tijden else None,
        "station": hoofd["station"],
        "station_afstand_km": hoofd["afstand_km"],
        "stations": {
            parameter: {k: v for k, v in info.items() if k != "station_id"}
            for parameter, info in per_parameter.items()
        },
        "bron": "knmi_edr",
    }


# ---------------------------------------------------------------------
# Luchtdrukverloop, zelf bijgehouden (herstartbestendig)
# ---------------------------------------------------------------------

DRUK_BEWAAR_S = 4 * 3600


class Drukhistorie:
    """Gemeten luchtdruk per tijdstip, om de verandering te berekenen.

    Alleen waarden van hetzelfde station worden vergeleken: onderweg wisselt
    het dichtstbijzijnde station, en het verschil tussen twee stations zegt
    niets over het verloop.
    """

    def __init__(self) -> None:
        self.punten: list[tuple[float, float, str]] = []

    def bij(self, stempel: float | None, druk: float | None, station: str | None) -> bool:
        """Voeg een meting toe. True als er iets veranderd is."""
        if stempel is None or druk is None:
            return False
        station = station or "?"
        if self.punten and self.punten[-1][0] >= stempel:
            return False
        self.punten.append((float(stempel), float(druk), station))
        grens = stempel - DRUK_BEWAAR_S
        self.punten = [p for p in self.punten if p[0] >= grens]
        return True

    def verandering(self, minuten: int, marge_minuten: int) -> float | None:
        """Druk nu min druk `minuten` geleden (hPa), of None.

        Negatief is dalend. Het vergelijkingspunt moet binnen de marge van
        het gevraagde moment liggen en van hetzelfde station komen.
        """
        if not self.punten:
            return None
        nu, druk_nu, station = self.punten[-1]
        doel = nu - minuten * 60
        kandidaten = [
            p
            for p in self.punten[:-1]
            if p[2] == station and abs(p[0] - doel) <= marge_minuten * 60
        ]
        if not kandidaten:
            return None
        oud = min(kandidaten, key=lambda p: abs(p[0] - doel))
        return round(druk_nu - oud[1], 1)

    def naar_opslag(self) -> list:
        return [list(p) for p in self.punten]

    def herstel(self, bewaard, nu: float) -> None:
        """Bewaarde punten terugzetten; te oude of rare vallen weg."""
        punten = []
        for rij in bewaard or []:
            try:
                stempel, druk, station = float(rij[0]), float(rij[1]), str(rij[2])
            except (TypeError, ValueError, IndexError):
                continue
            if nu - DRUK_BEWAAR_S <= stempel <= nu + 60:
                punten.append((stempel, druk, station))
        self.punten = sorted(punten)


def tendens(verandering: float | None) -> str | None:
    """Woord bij een drukverandering."""
    if verandering is None:
        return None
    if verandering <= -0.5:
        return "dalend"
    if verandering >= 0.5:
        return "stijgend"
    return "gelijk"


# ---------------------------------------------------------------------
# Weersverwachting (KNMI-app)
# ---------------------------------------------------------------------

# Weercodes van de KNMI-app naar Home Assistant-condities. Opgesteld aan de
# hand van de indeling in de KNMI-app (KNMI-OSS), via ha-nl-weather.
KNMI_CONDITIE_GROEPEN: dict[str, tuple[int, ...]] = {
    "sunny": (1372, 1365),
    "clear-night": (1373, 1376),
    "partlycloudy": (1380, 1381, 1375, 1387, 1388),
    "cloudy": (1386, 1374),
    "fog": (1420, 1421, 1422, 1370),
    "hail": (1416, 1417, 1418),
    "lightning": (1368, 1448),
    "lightning-rainy": (1389, 1390, 1391, 1392, 1393, 1394, 1395, 1396, 1397),
    "pouring": (1379, 1384, 1385, 1366, 1371),
    "rainy": (1377, 1382, 1383, 1378),
    "snowy": (
        1398, 1399, 1401, 1402, 1404, 1405, 1406, 1407, 1408, 1409, 1410,
        1411, 1412, 1367,
    ),
    "snowy-rainy": (1413, 1414, 1415, 1419, 1364),
    "windy": (1423, 1424, 1425),
    "windy-variant": (1369,),
}
KNMI_CONDITIES: dict[int, str] = {
    code: conditie
    for conditie, codes in KNMI_CONDITIE_GROEPEN.items()
    for code in codes
}


def knmi_conditie(code) -> str | None:
    """KNMI-weercode naar conditie, of None als hij onbekend is."""
    try:
        return KNMI_CONDITIES.get(int(code))
    except (TypeError, ValueError):
        return None


def _kans(waarde) -> float | None:
    """Neerslagkans als procent; de app levert een fractie (0..1)."""
    if waarde is None:
        return None
    try:
        getal = float(waarde)
    except (TypeError, ValueError):
        return None
    return round(getal * 100) if getal <= 1 else round(getal)


def _veld(blok, sleutel):
    return blok.get(sleutel) if isinstance(blok, dict) else None


def verwachting(payload: dict | None, details: dict | None, nu: datetime) -> dict:
    """Uur- en dagverwachting in de vorm van een HA-Forecast.

    Uren die voorbij zijn vallen weg. Details per dag (neerslagkans, wind)
    komen uit weather/detail, als die er zijn.
    """
    details = details or {}
    huidig_uur = nu.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)

    uren: list[dict] = []
    for uur in _uren(payload):
        moment = _als_tijd(uur.get("dateTime"))
        if moment is None or moment < huidig_uur:
            continue
        neerslag = uur.get("precipitation") or {}
        wind = uur.get("wind") or {}
        uren.append(
            {
                "datetime": moment.isoformat(),
                "condition": knmi_conditie(uur.get("weatherType")),
                "weercode": uur.get("weatherType"),
                "native_temperature": uur.get("temperature"),
                "native_precipitation": _veld(neerslag, "amount"),
                "precipitation_probability": _kans(_veld(neerslag, "chance")),
                "native_wind_speed": _veld(wind, "speed"),
                "native_wind_gust_speed": _veld(wind, "gusts"),
                "wind_bearing": _veld(wind, "degree"),
            }
        )

    dagen: list[dict] = []
    for dag in ((payload or {}).get("daily") or {}).get("forecast") or []:
        if not isinstance(dag, dict) or not dag.get("date"):
            continue
        detail = details.get(dag["date"]) or {}
        temperatuur = dag.get("temperature") or {}
        neerslag = dag.get("precipitation") or {}
        wind = detail.get("wind") or dag.get("wind") or {}
        kans = _veld(detail.get("precipitationChance"), "chance")
        if kans is None:
            kans = _veld(neerslag, "chance")
        dagen.append(
            {
                "datetime": dag["date"],
                "condition": knmi_conditie(dag.get("weatherType")),
                "weercode": dag.get("weatherType"),
                "native_temperature": _veld(temperatuur, "max"),
                "native_templow": _veld(temperatuur, "min"),
                "native_precipitation": _veld(neerslag, "amount"),
                "precipitation_probability": _kans(kans),
                "native_wind_speed": _veld(wind, "speed"),
                "native_wind_gust_speed": _veld(wind, "gusts"),
                "wind_bearing": _veld(wind, "degree"),
                "uv_index": _veld(detail.get("uvIndex"), "value"),
            }
        )

    return {"uren": uren, "dagen": dagen, "opgehaald": nu.isoformat()}


# ---------------------------------------------------------------------
# Meldingen van de Notification Service
# ---------------------------------------------------------------------

_STEMPEL = re.compile(r"(\d{12})")


def tijd_uit_bestandsnaam(naam: str | None) -> datetime | None:
    """Tijd (UTC) uit een bestandsnaam als ..._202610081210.nc of .h5."""
    if not naam:
        return None
    gevonden = _STEMPEL.findall(str(naam))
    if not gevonden:
        return None
    try:
        return datetime.strptime(gevonden[-1], "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
