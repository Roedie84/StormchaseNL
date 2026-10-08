"""0.49.0: officiële KNMI-bronnen, aanvullend in Nederland.

Waarschuwingen en neerslag van de KNMI-app, waarnemingen via EDR,
pushmeldingen via MQTT, de radarkaart via WMS en de verwachting voor de
weerentiteit. Live testen kan hier niet (de sandbox bereikt het KNMI niet);
de fixtures volgen de vorm van de antwoorden zoals de KNMI-app-API en het
KNMI Data Platform ze geven (zie ha-nl-weather als referentie).
"""

import asyncio
import json
import threading
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

import pytest

try:
    import homeassistant.util.dt  # noqa: F401
except ModuleNotFoundError:  # zonder HA-installatie: alleen utcnow is nodig
    import sys
    import types

    _dt = types.ModuleType("homeassistant.util.dt")
    _dt.utcnow = lambda: datetime.now(timezone.utc)
    for naam, mod in (
        ("homeassistant", types.ModuleType("homeassistant")),
        ("homeassistant.util", types.ModuleType("homeassistant.util")),
        ("homeassistant.util.dt", _dt),
    ):
        sys.modules.setdefault(naam, mod)
    sys.modules["homeassistant.util"].dt = _dt

import knmi_api  # noqa: E402
from knmi_api import (  # noqa: E402
    Afremming,
    KnmiApp,
    KnmiBronnen,
    KnmiEdr,
    KnmiFout,
    KnmiWms,
    NietGevonden,
    OngeldigVerzoek,
    SleutelGeweigerd,
    TeVeelVerzoeken,
    laatste_tijd_uit_capabilities,
    poging,
    tijd_z,
    vijf_minuten_slot,
)
from knmi_grid import (  # noqa: E402
    KNMI_REGIOS,
    Landbepaling,
    afstand_km,
    bbox_webmercator,
    in_nederland_grof,
    naar_webmercator,
    radarcel,
    regio_uit_geocode,
    stereografisch,
    verwachtingscel,
)
from knmi_push import KnmiPush, lees_melding  # noqa: E402
from knmi_verwerk import (  # noqa: E402
    Drukhistorie,
    beaufort,
    knmi_conditie,
    metingen,
    niveau_per_uur,
    nowcast_reeks,
    soort_uit_tekst,
    tendens,
    tijd_uit_bestandsnaam,
    verwachting,
    waarschuwingen,
)
from buienreeks import lees_reeks  # noqa: E402
from stats import Statistieken  # noqa: E402
from vooruitblik import (  # noqa: E402
    FrameCache,
    frame_tijden,
    framelabel,
    framesleutel,
    stel_gif_samen,
)

ROOT = Path(__file__).resolve().parents[1]
BRON = ROOT / "custom_components" / "stormchase"
NU = datetime(2026, 10, 8, 14, 7, 30, tzinfo=timezone.utc)
UUR = NU.replace(minute=0, second=0)


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------
# Nep-sessie in de vorm van aiohttp (async context manager)
# ---------------------------------------------------------------------


class _Antwoord:
    def __init__(self, status=200, body=b"", headers=None):
        self.status = status
        self._body = body if isinstance(body, bytes) else (
            json.dumps(body).encode() if isinstance(body, (dict, list)) else str(body).encode()
        )
        self.headers = headers or {}

    async def text(self):
        return self._body.decode()

    async def read(self):
        return self._body


class _Verzoek:
    def __init__(self, antwoord):
        self.antwoord = antwoord

    async def __aenter__(self):
        if isinstance(self.antwoord, Exception):
            raise self.antwoord
        return self.antwoord

    async def __aexit__(self, *_):
        return False


class _Sessie:
    def __init__(self, antwoord):
        self.antwoord = antwoord
        self.verzoeken = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.verzoeken.append({"url": url, "params": params, "headers": headers})
        antwoord = self.antwoord(url, params) if callable(self.antwoord) else self.antwoord
        return _Verzoek(antwoord)


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------
# 1. Rastercellen en projectie (gecontroleerd tegen pyproj in de referentie)
# ---------------------------------------------------------------------

# Waarden berekend met de rasterdefinities van ha-nl-weather (pyproj)
REFERENTIE = [
    # naam, breedte, lengte, verwachtingscel, radarcel, x (km), y (km)
    ("eibergen", 52.1, 6.65, "A858", "B79855", 474.1796, -4067.1259),
    ("hupsel", 52.0675, 6.6567, "A858", "B80209", 475.0925, -4070.8168),
    ("debilt", 52.1, 5.18, "A508", "B43010", 369.6875, -4077.9518),
    ("amsterdam", 52.37, 4.89, "A434", "B34908", 346.3737, -4048.5772),
    ("maastricht", 50.85, 5.69, "A628", "B61053", 420.4055, -4219.3716),
    ("groningen", 53.22, 6.57, "A844", "B72356", 453.6774, -3939.0825),
    ("den_helder", 52.96, 4.76, "A392", "B29576", 331.5239, -3981.3442),
    ("vlissingen", 51.44, 3.6, "A96", "B5188", 261.9251, -4163.1802),
    ("enschede", 52.22, 6.89, "A926", "B85104", 489.5418, -4051.2841),
    ("brussel", 50.85, 4.35, "A313", "B26313", 321.6194, -4228.049),
    ("schiermonnikoog", 53.48, 6.16, "A736", "B61448", 422.264, -3912.4438),
    ("gronau", 52.21, 7.02, "A961", "B88263", 498.8744, -4051.3139),
]


class TestRaster:
    @pytest.mark.parametrize("naam,br,le,a,b,x,y", REFERENTIE, ids=[r[0] for r in REFERENTIE])
    def test_cellen_gelijk_aan_referentie(self, naam, br, le, a, b, x, y):
        assert verwachtingscel(br, le) == a
        assert radarcel(br, le) == b

    @pytest.mark.parametrize("naam,br,le,a,b,x,y", REFERENTIE, ids=[r[0] for r in REFERENTIE])
    def test_projectie_gelijk_aan_pyproj(self, naam, br, le, a, b, x, y):
        px, py = stereografisch(br, le)
        assert px == pytest.approx(x, abs=1e-3)
        assert py == pytest.approx(y, abs=1e-3)

    def test_buiten_de_rasters(self):
        assert verwachtingscel(51.96, 7.63) is None  # Münster
        assert radarcel(51.96, 7.63) is None
        assert verwachtingscel(48.85, 2.35) is None  # Parijs
        assert radarcel(48.85, 2.35) is None

    def test_webmercator(self):
        x, y = naar_webmercator(0, 0)
        assert (x, y) == pytest.approx((0, 0), abs=1e-6)
        # Referentie: pyproj EPSG:4326 -> EPSG:3857
        x, y = naar_webmercator(52.1, 6.65)
        assert x == pytest.approx(740274.614, abs=0.01)
        assert y == pytest.approx(6818226.972, abs=0.01)
        minx, miny, maxx, maxy = (float(v) for v in bbox_webmercator((51.0, 5.0, 53.0, 7.0)).split(","))
        assert minx < maxx and miny < maxy

    def test_afstand(self):
        # Eibergen - Hupsel ongeveer 3,6 km
        assert afstand_km(52.1, 6.65, 52.068, 6.657) == pytest.approx(3.6, abs=0.2)


# ---------------------------------------------------------------------
# 2. In Nederland of niet
# ---------------------------------------------------------------------


class TestNederland:
    @pytest.mark.parametrize(
        "br,le,binnen",
        [
            (52.1, 6.65, True),   # Eibergen
            (51.97, 6.72, True),  # Winterswijk
            (52.22, 6.89, True),  # Enschede
            (50.85, 5.69, True),  # Maastricht
            (53.08, 4.80, True),  # Texel
            (53.48, 6.16, True),  # Schiermonnikoog
            (51.44, 3.60, True),  # Vlissingen
            (52.21, 7.02, False),  # Gronau (DE)
            (51.84, 6.61, False),  # Bocholt (DE)
            (51.96, 7.63, False),  # Münster
            (50.85, 4.35, False),  # Brussel
            (51.22, 4.40, False),  # Antwerpen
            (50.78, 6.08, False),  # Aken
        ],
    )
    def test_grove_grens(self, br, le, binnen):
        assert in_nederland_grof(br, le) is binnen

    def test_geocodering_gaat_voor_in_de_buurt(self):
        land = Landbepaling()
        # Gronau valt buiten de grove grens; met een NL-geocodering vlakbij
        # (bijv. Glanerbrug) zou hij binnen tellen
        land.noteer(52.21, 7.0, "NL")
        assert land.in_nederland(52.21, 7.02) is True
        land.noteer(52.21, 7.02, "DE")
        assert land.in_nederland(52.21, 7.02) is False

    def test_ver_van_de_geocodering_de_grove_grens(self):
        land = Landbepaling()
        land.noteer(51.96, 7.63, "DE")  # Münster
        assert land.in_nederland(52.1, 6.65) is True  # Eibergen, ver weg


# ---------------------------------------------------------------------
# 3. Waarschuwingsregio uit de geocodering
# ---------------------------------------------------------------------


class TestRegio:
    def test_provinciecode(self):
        geo = {"principalSubdivisionCode": "NL-GE", "principalSubdivision": "Gelderland"}
        assert regio_uit_geocode(geo, 52.1, 6.65) == (4, "provincie")

    def test_engelse_naam(self):
        geo = {"principalSubdivision": "North Holland"}
        assert regio_uit_geocode(geo, 52.37, 4.89)[0] == 9

    @pytest.mark.parametrize("gemeente,code", [("Texel", "NL-NH"), ("Terschelling", "NL-FR"), ("Schiermonnikoog", "NL-FR")])
    def test_waddeneilanden(self, gemeente, code):
        geo = {
            "principalSubdivisionCode": code,
            "localityInfo": {"administrative": [{"name": "Netherlands"}, {"name": gemeente}]},
        }
        assert regio_uit_geocode(geo, 53.3, 5.2) == (12, "gemeente")

    def test_open_water(self):
        geo = {"localityInfo": {"informative": [{"name": "IJsselmeer"}]}}
        assert regio_uit_geocode(geo, 52.8, 5.3) == (6, "water")

    def test_zonder_geocodering_dichtstbijzijnd(self):
        assert regio_uit_geocode(None, 50.85, 5.69) == (7, "dichtstbijzijnd")
        assert regio_uit_geocode({}, 51.45, 3.6)[0] == 14

    def test_alle_regios_bestaan(self):
        assert sorted(KNMI_REGIOS) == list(range(1, 16))


# ---------------------------------------------------------------------
# 4. Waarschuwingen
# ---------------------------------------------------------------------


def _weer(alerts, niveaus, start=UUR - timedelta(hours=1)):
    return {
        "alerts": alerts,
        "hourly": {
            "forecast": [
                {
                    "dateTime": _iso(start + timedelta(hours=i)),
                    "weatherType": 1377,
                    "temperature": 14 + i,
                    "precipitation": {"amount": 0.2, "chance": 0.4},
                    "wind": {"speed": 25, "gusts": 60, "degree": 230},
                    "alertLevel": niveau,
                }
                for i, niveau in enumerate(niveaus)
            ]
        },
        "daily": {
            "forecast": [
                {
                    "date": "2026-10-08",
                    "weatherType": 1389,
                    "temperature": {"min": 9, "max": 16},
                    "precipitation": {"amount": 4.2},
                }
            ]
        },
    }


class TestWaarschuwingen:
    def test_code_geel_met_periode(self):
        payload = _weer(
            [{"level": "yellow", "description": "Code geel: zware windstoten tot 80 km/u."}],
            ["yellow", "yellow", "yellow", "orange", "yellow", "none", "none"],
        )
        data = waarschuwingen(payload, 4, "Gelderland", NU)
        assert data["bron"] == "knmi"
        assert data["niveau"] == "geel" and data["rang"] == 1
        assert data["regio"] == "Gelderland" and data["gebied"] == "Gelderland"
        w = data["actief"][0]
        assert w["soort"] == "zware windstoten"
        # Het lopende uur (14:00) tot en met 17:00 op geel of hoger
        assert w["vanaf"] == UUR.isoformat()
        assert w["tot"] == (UUR + timedelta(hours=4)).isoformat()
        assert w["id"] == "knmi|4|geel|zware windstoten"
        # Niveau per uur vanaf het lopende uur, het vorige uur valt weg
        assert data["niveau_per_uur"][0] == {"tijd": UUR.isoformat(), "niveau": "geel"}
        assert data["niveau_per_uur"][2]["niveau"] == "oranje"
        assert data["niveau_per_uur"][4]["niveau"] == "geen"

    def test_zwaarste_eerst(self):
        payload = _weer(
            [
                {"level": "yellow", "description": "Code geel: gladheid"},
                {"level": "orange", "description": "Code oranje: zware onweersbuien"},
            ],
            ["orange"] * 3,
        )
        data = waarschuwingen(payload, 10, "Overijssel", NU)
        assert data["niveau"] == "oranje"
        assert [w["soort"] for w in data["actief"]] == ["onweer", "gladheid"]

    def test_herschreven_tekst_zelfde_kenmerk(self):
        een = waarschuwingen(_weer([{"level": "yellow", "description": "Code geel: onweer"}], ["yellow"]), 4, "Gelderland", NU)
        twee = waarschuwingen(_weer([{"level": "yellow", "description": "Code geel: kans op onweer met hagel"}], ["yellow"]), 4, "Gelderland", NU)
        assert een["actief"][0]["id"] == twee["actief"][0]["id"]

    def test_niveau_zonder_losse_waarschuwing(self):
        data = waarschuwingen(_weer([], ["none", "yellow", "yellow", "none"]), 4, "Gelderland", NU)
        assert data["niveau"] == "geel"
        assert data["actief"][0]["soort"] == "weerwaarschuwing"

    def test_niets_aan_de_hand(self):
        data = waarschuwingen(_weer([], ["none"] * 5), 4, "Gelderland", NU)
        assert data["aantal"] == 0 and data["niveau"] is None and data["rang"] == 0

    def test_onbekend_niveau_en_rommel(self):
        data = waarschuwingen({"alerts": [{"level": "purple"}, "tekst", None]}, 4, "Gelderland", NU)
        assert data["aantal"] == 0

    def test_zelfde_sleutels_als_meteoalarm(self):
        data = waarschuwingen(_weer([{"level": "red", "description": "Code rood: storm"}], ["red"]), 9, "Noord-Holland", NU)
        for sleutel in ("actief", "aantal", "niveau", "rang", "soort", "gebied", "land", "gefilterd_op", "aantal_in_land", "gebieden_in_land"):
            assert sleutel in data
        for sleutel in ("titel", "soort", "niveau", "rang", "gebied", "vanaf", "tot", "id"):
            assert sleutel in data["actief"][0]

    def test_soort_uit_tekst(self):
        assert soort_uit_tekst("Code oranje: zeer zware windstoten") == "zeer zware windstoten"
        assert soort_uit_tekst("Code geel: extreme hitte") == "extreme hitte"
        assert soort_uit_tekst("Code geel: ijzel") == "ijzel"
        assert soort_uit_tekst("") is None

    def test_niveau_per_uur_maximaal_24(self):
        payload = _weer([], ["none"] * 60)
        assert len(niveau_per_uur(payload, NU)) == 24


# ---------------------------------------------------------------------
# 5. Neerslag per vijf minuten
# ---------------------------------------------------------------------


class TestNowcast:
    def test_exacte_tijdstempels(self):
        slot = vijf_minuten_slot(NU)
        assert slot == datetime(2026, 10, 8, 14, 5, tzinfo=timezone.utc)
        grafiek = {"precipitation": {
            "times": [_iso(slot + timedelta(minutes=5 * i)) for i in range(4)],
            "amounts": [0, 0.4, 2.0, None],
        }}
        reeks = nowcast_reeks(grafiek, NU)
        # 14:05 is 2,5 minuut geleden: -3 (afgerond naar beneden zoals bij Buienradar)
        assert reeks == [(-3, 0.0), (2, 0.4), (7, 2.0)]

    def test_over_middernacht_en_met_tijdzone(self):
        nu = datetime(2026, 10, 8, 21, 58, tzinfo=timezone.utc)
        grafiek = {"precipitation": {
            "times": ["2026-10-09T00:00:00+02:00", "2026-10-09T00:05:00+02:00"],
            "amounts": [1.0, 0.0],
        }}
        assert nowcast_reeks(grafiek, nu) == [(2, 1.0), (7, 0.0)]

    def test_lege_grafiek_is_een_fout(self):
        with pytest.raises(ValueError):
            nowcast_reeks({"precipitation": {"times": [], "amounts": []}}, NU)
        with pytest.raises(ValueError):
            nowcast_reeks(None, NU)

    def test_zelfde_reeksvorm_voor_buienreeks(self):
        slot = vijf_minuten_slot(NU)
        grafiek = {"precipitation": {
            "times": [_iso(slot + timedelta(minutes=5 * i)) for i in range(6)],
            "amounts": [0, 0, 0, 0.5, 1.0, 0],
        }}
        gelezen = lees_reeks(nowcast_reeks(grafiek, NU), 0.1)
        assert gelezen["regent"] is False
        assert gelezen["begint_over"] == 12

    def test_nu_venster_ongewijzigd(self):
        """L-SC-005: het venster -10..+10 in lees_reeks blijft zoals het is."""
        bron = (BRON / "buienreeks.py").read_text(encoding="utf-8")
        assert "-10 <= minuten <= 10" in bron


# ---------------------------------------------------------------------
# 6. Waarnemingen (EDR)
# ---------------------------------------------------------------------


def _coverage(station, br, le, **waarden):
    tijden = [_iso(UUR - timedelta(minutes=20)), _iso(UUR - timedelta(minutes=10))]
    return {
        "type": "Coverage",
        "eumetnet:locationId": station,
        "domain": {"axes": {"x": {"values": [le]}, "y": {"values": [br]}, "t": {"values": tijden}}},
        "ranges": {p: {"type": "NdArray", "values": v} for p, v in waarden.items()},
    }


KUBUS = [
    _coverage("0-20000-0-06283", 52.068, 6.657, ta=[14.0, 14.2], rh=[80, 82], td=[10.0, 10.4],
              pp=[1008.0, 1007.6], ff=[5.0, 6.0], gff=[11.0, 17.5], dd=[230, 235],
              ww=[61, 95], rg=[0.5, 1.2], zm=[None, None]),
    _coverage("0-20000-0-06290", 52.274, 6.891, ta=[13.0, 13.1], zm=[20000, 18000],
              nhc=[6, 9], hc=[3000, 2500], ww=[0, 0]),
    _coverage("0-20000-0-06275", 52.06, 5.87, ta=[15.0, 15.0], pp=[1009.0, 1009.0]),
]
NAMEN = {"0-20000-0-06283": "Hupsel", "0-20000-0-06290": "Twenthe", "0-20000-0-06275": "Deelen"}


class TestMetingen:
    def test_dichtstbijzijnde_per_parameter(self):
        data = metingen(KUBUS, 52.1, 6.65, NAMEN)
        assert data["bron"] == "knmi_edr"
        assert data["temperatuur"] == 14.2
        assert data["station"] == "Hupsel"
        assert data["station_afstand_km"] == pytest.approx(3.6, abs=0.2)
        # Zicht en bewolking meet Hupsel niet: die komen van Twenthe
        assert data["zicht"] == 18000
        assert data["stations"]["zm"]["station"] == "Twenthe"
        assert data["bewolking"] == 100  # okta 9
        assert data["wolkenbasis"] == round(2500 * 0.3048)

    def test_wind_en_beaufort(self):
        data = metingen(KUBUS, 52.1, 6.65, NAMEN)
        assert data["windstoten_ms"] == 17.5
        assert data["windstoten"] == 63.0  # km/u
        assert data["windstoten_bft"] == 8
        assert data["wind"] == pytest.approx(21.6)

    def test_onweer_en_hagel_uit_weercode(self):
        data = metingen(KUBUS, 52.1, 6.65, NAMEN)
        assert data["weercode"] == 95 and data["onweer"] is True and data["hagel"] is False
        assert data["weer_station"] == "Hupsel"
        hagel = [_coverage("x", 52.07, 6.66, ww=[0, 96])]
        assert metingen(hagel, 52.1, 6.65)["hagel"] is True
        recent = [_coverage("x", 52.07, 6.66, ww=[26, 26])]
        uit = metingen(recent, 52.1, 6.65)
        assert uit["onweer"] is False and uit["onweer_afgelopen_uur"] is True

    def test_neerslag(self):
        data = metingen(KUBUS, 52.1, 6.65, NAMEN)
        assert data["neerslag_intensiteit"] == 1.2
        assert data["neerslag"] == 0.2  # mm per tien minuten

    def test_zonder_namen_het_nummer(self):
        assert metingen(KUBUS, 52.1, 6.65)["station"] == "0-20000-0-06283"

    def test_leeg_is_een_fout(self):
        with pytest.raises(ValueError):
            metingen([], 52.1, 6.65)
        with pytest.raises(ValueError):
            metingen([_coverage("x", 52.0, 6.0, ta=[None, None])], 52.1, 6.65)

    @pytest.mark.parametrize("ms,bft", [(0.0, 0), (0.3, 1), (5.4, 3), (10.8, 6), (20.0, 8), (24.4, 9), (33.0, 12), (None, None)])
    def test_beaufort(self, ms, bft):
        assert beaufort(ms) == bft


class TestDrukhistorie:
    def test_verandering_een_en_drie_uur(self):
        h = Drukhistorie()
        t0 = 1_791_000_000.0
        for i in range(19):  # drie uur, elke tien minuten
            h.bij(t0 + i * 600, 1012.0 - i * 0.3, "06283")
        assert h.verandering(60, 10) == pytest.approx(-1.8)
        assert h.verandering(180, 15) == pytest.approx(-5.4)
        assert tendens(h.verandering(60, 10)) == "dalend"

    def test_ander_station_telt_niet(self):
        h = Drukhistorie()
        h.bij(1000.0, 1010.0, "A")
        h.bij(1000.0 + 3600, 1005.0, "B")
        assert h.verandering(60, 10) is None

    def test_te_weinig_geschiedenis(self):
        h = Drukhistorie()
        h.bij(1000.0, 1010.0, "A")
        assert h.verandering(60, 10) is None
        assert tendens(None) is None

    def test_zelfde_tijdstip_niet_dubbel(self):
        h = Drukhistorie()
        assert h.bij(1000.0, 1010.0, "A") is True
        assert h.bij(1000.0, 1010.0, "A") is False
        assert h.bij(None, 1010.0, "A") is False

    def test_herstartbestendig(self):
        h = Drukhistorie()
        t0 = 1_791_000_000.0
        for i in range(7):
            h.bij(t0 + i * 600, 1010.0 + i * 0.2, "06283")
        bewaard = json.loads(json.dumps(h.naar_opslag()))
        nieuw = Drukhistorie()
        nieuw.herstel(bewaard, t0 + 3700)
        assert nieuw.verandering(60, 10) == h.verandering(60, 10) == pytest.approx(1.2)

    def test_oude_en_rare_punten_vallen_weg(self):
        nieuw = Drukhistorie()
        nieuw.herstel([[0, 1000, "A"], ["x"], None, [5 * 3600, 1001, "A"]], 5 * 3600 + 10)
        assert nieuw.punten == [(5 * 3600.0, 1001.0, "A")]


# ---------------------------------------------------------------------
# 7. Weersverwachting
# ---------------------------------------------------------------------


class TestVerwachting:
    def test_uren_en_dagen(self):
        payload = _weer([], ["none"] * 6)
        details = {"2026-10-08": {"precipitationChance": {"chance": 0.7}, "uvIndex": {"value": 3},
                                  "wind": {"speed": 30, "gusts": 70, "degree": 240}}}
        uit = verwachting(payload, details, NU)
        # Het vorige uur valt weg
        assert uit["uren"][0]["datetime"] == UUR.isoformat()
        uur = uit["uren"][0]
        assert uur["condition"] == "rainy"
        assert uur["precipitation_probability"] == 40
        assert uur["native_wind_gust_speed"] == 60
        dag = uit["dagen"][0]
        assert dag["condition"] == "lightning-rainy"
        assert dag["native_temperature"] == 16 and dag["native_templow"] == 9
        assert dag["precipitation_probability"] == 70
        assert dag["native_wind_gust_speed"] == 70 and dag["uv_index"] == 3

    @pytest.mark.parametrize(
        "code,conditie",
        [(1372, "sunny"), (1373, "clear-night"), (1380, "partlycloudy"), (1386, "cloudy"),
         (1420, "fog"), (1389, "lightning-rainy"), (1384, "pouring"), (1377, "rainy"),
         (1398, "snowy"), (1413, "snowy-rainy"), (1416, "hail"), (1423, "windy"),
         ("1377", "rainy"), (9999, None), (None, None)],
    )
    def test_weercodes(self, code, conditie):
        assert knmi_conditie(code) == conditie

    def test_zonder_details(self):
        uit = verwachting(_weer([], ["none"]), None, NU)
        assert uit["dagen"][0]["precipitation_probability"] is None


# ---------------------------------------------------------------------
# 8. Verbindingen: fouten, sleutels, afremmen
# ---------------------------------------------------------------------


class TestApi:
    def test_app_zonder_sleutel_met_juiste_parameters(self):
        sessie = _Sessie(_Antwoord(200, {"alerts": []}))
        _run(KnmiApp(sessie).weer("A858", 4))
        verzoek = sessie.verzoeken[0]
        assert verzoek["url"] == "https://api.app.knmi.cloud/weather"
        assert verzoek["params"] == {"location": "A858", "region": "4"}
        assert verzoek["headers"] is None

    def test_neerslaggrafiek_met_z_tijd(self):
        sessie = _Sessie(_Antwoord(200, {"precipitation": {}}))
        _run(KnmiApp(sessie).neerslaggrafiek("B79855", datetime(2026, 10, 8, 14, 5, tzinfo=timezone.utc)))
        assert sessie.verzoeken[0]["params"] == {"location": "B79855", "time": "2026-10-08T14:05:00Z"}

    def test_edr_kubus(self):
        sessie = _Sessie(_Antwoord(200, {"coverages": KUBUS}))
        uit = _run(KnmiEdr(sessie, "geheime-sleutel").kubus(NU, ("ta", "pp")))
        assert len(uit) == 3
        verzoek = sessie.verzoeken[0]
        assert verzoek["url"].endswith("/10-minute-in-situ-meteorological-observations/cube")
        assert verzoek["headers"] == {"Authorization": "geheime-sleutel"}
        assert verzoek["params"]["parameter-name"] == "ta,pp"
        assert verzoek["params"]["datetime"] == "2026-10-08T13:37:30Z/2026-10-08T14:07:30Z"

    def test_stationsnamen(self):
        sessie = _Sessie(_Antwoord(200, {"features": [{"id": "06283", "properties": {"name": "HUPSEL"}}, {"id": None}]}))
        assert _run(KnmiEdr(sessie, "s").stations(NU)) == {"06283": "HUPSEL"}

    @pytest.mark.parametrize(
        "status,soort",
        [(403, SleutelGeweigerd), (401, SleutelGeweigerd), (429, TeVeelVerzoeken),
         (404, NietGevonden), (400, OngeldigVerzoek), (503, knmi_api.ServerFout)],
    )
    def test_statusfouten(self, status, soort):
        sessie = _Sessie(_Antwoord(status, "geheime-sleutel in de body", {"Retry-After": "120"}))
        with pytest.raises(soort) as fout:
            _run(KnmiEdr(sessie, "geheime-sleutel").kubus(NU, ("ta",)))
        assert fout.value.status == status
        assert "geheime-sleutel" not in str(fout.value)

    def test_timeout_en_verbindingsfout(self):
        with pytest.raises(KnmiFout):
            _run(KnmiApp(_Sessie(asyncio.TimeoutError())).weer("A1", 1))
        import aiohttp

        with pytest.raises(KnmiFout) as fout:
            _run(KnmiEdr(_Sessie(aiohttp.ClientConnectionError("x")), "geheim").kubus(NU, ("ta",)))
        assert "geheim" not in str(fout.value)

    def test_onleesbare_json(self):
        with pytest.raises(KnmiFout):
            _run(KnmiApp(_Sessie(_Antwoord(200, "<html>"))).weer("A1", 1))

    def test_wms_kaart_en_parameters(self):
        png = b"\x89PNG\r\n\x1a\nrest"
        sessie = _Sessie(_Antwoord(200, png))
        wms = KnmiWms(sessie, "wms-sleutel", per_seconde=1000)
        ref = datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc)
        params = KnmiWms.kaartparameters("1,2,3,4", 768, 768, "radar/nearest", ref + timedelta(minutes=30), ref)
        assert _run(wms.kaart(params)) == png
        p = sessie.verzoeken[0]["params"]
        assert p["CRS"] == "EPSG:3857" and p["DATASET"] == "radar_forecast_2.0"
        assert p["LAYERS"] == "precipitation_nowcast"
        assert p["DIM_REFERENCE_TIME"] == "2026-10-08T14:00:00Z"
        assert p["TIME"] == "2026-10-08T14:30:00Z"
        actueel = KnmiWms.kaartparameters("1,2,3,4", 10, 10, "s", ref)
        assert actueel["DATASET"] == "nl_rdr_data_rtcor_5m" and "DIM_REFERENCE_TIME" not in actueel
        assert sessie.verzoeken[0]["headers"] == {"Authorization": "wms-sleutel"}

    def test_wms_tekst_in_plaats_van_beeld(self):
        wms = KnmiWms(_Sessie(_Antwoord(200, b"ADAGUC Server: fout")), "s", per_seconde=1000)
        with pytest.raises(OngeldigVerzoek):
            _run(wms.kaart({}))

    def test_wms_tempo(self, monkeypatch):
        gewacht = []

        async def slaap(s):
            gewacht.append(s)

        monkeypatch.setattr(knmi_api.asyncio, "sleep", slaap)
        wms = KnmiWms(_Sessie(_Antwoord(200, b"\x89PNG")), "s", per_seconde=5)

        async def drie():
            for _ in range(3):
                await wms.kaart({})

        _run(drie())
        assert len(gewacht) >= 2 and all(0 < w <= 0.2 for w in gewacht)

    def test_capabilities(self):
        tekst = """<?xml version="1.0"?>
        <WMS_Capabilities xmlns="http://www.opengis.net/wms"><Capability><Layer>
        <Layer><Name>precipitation_real_time</Name>
        <Dimension name="time" units="ISO8601">2026-09-08T00:00:00Z/2026-10-08T14:00:00Z/PT5M</Dimension>
        </Layer></Layer></Capability></WMS_Capabilities>"""
        assert laatste_tijd_uit_capabilities(tekst) == datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc)
        lijst = '<a><Dimension name="time">2026-10-08T13:55:00Z,2026-10-08T14:05:00Z</Dimension></a>'
        assert laatste_tijd_uit_capabilities(lijst) == datetime(2026, 10, 8, 14, 5, tzinfo=timezone.utc)
        assert laatste_tijd_uit_capabilities("geen xml") is None

    def test_tijd_z(self):
        assert tijd_z(datetime(2026, 10, 8, 16, 5, tzinfo=timezone(timedelta(hours=2)))) == "2026-10-08T14:05:00Z"


class TestAfremming:
    def test_storing_verdubbelt(self):
        rem = Afremming()
        assert rem.fout(KnmiFout("x", 503), nu=0) == 120
        assert rem.fout(KnmiFout("x", 503), nu=0) == 240
        assert rem.mag(100) is False and rem.mag(240) is True
        for _ in range(10):
            rem.fout(KnmiFout("x"), nu=0)
        assert rem.tot == 1800
        rem.succes()
        assert rem.mag(0) and rem.op_rij == 0

    def test_429_volgt_retry_after(self):
        rem = Afremming()
        assert rem.fout(TeVeelVerzoeken("x", 429, {"Retry-After": "3600"}), nu=0) == 3600
        rem = Afremming()
        assert rem.fout(TeVeelVerzoeken("x", 429, {}), nu=0) == 600
        assert rem.reden == "afgeremd (429)"

    def test_sleutel_geweigerd_een_uur(self):
        rem = Afremming()
        assert rem.fout(SleutelGeweigerd("x", 403), nu=0) == 3600
        assert rem.reden == "sleutel geweigerd of quotum op"

    def test_poging_slaat_over_zolang_afgeremd(self):
        stats = Statistieken()
        rem = Afremming()
        aanroepen = []

        async def faalt():
            aanroepen.append(1)
            raise SleutelGeweigerd("HTTP 403", 403)

        uit, reden = _run(poging(rem, stats.bronnen["knmi_edr"], "test", faalt))
        assert uit is None and "403" in reden
        assert stats.bronnen["knmi_edr"].mislukt == 1
        uit, _ = _run(poging(rem, stats.bronnen["knmi_edr"], "test", faalt))
        assert uit is None and len(aanroepen) == 1  # tweede keer niet gevraagd

    def test_poging_succes(self):
        stats = Statistieken()

        async def lukt():
            return {"ok": 1}

        uit, reden = _run(poging(Afremming(), stats.bronnen["knmi_nowcast"], "test", lukt))
        assert uit == {"ok": 1} and reden is None
        assert stats.bronnen["knmi_nowcast"].gelukt == 1

    def test_geweigerde_sleutel_eenmalig_gelogd(self, caplog):
        rem = Afremming()

        async def faalt():
            raise SleutelGeweigerd("HTTP 403: sleutel geweigerd of quotum op", 403)

        with caplog.at_level("DEBUG"):
            _run(poging(rem, None, "test", faalt))
            rem.tot = 0  # wachttijd voorbij, nog steeds fout
            _run(poging(rem, None, "test", faalt))
        waarschuwingen_log = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(waarschuwingen_log) == 1


class TestBronnen:
    def test_zonder_sleutels_geen_verbinding(self):
        knmi = KnmiBronnen(object())
        assert knmi.edr is None and knmi.wms is None and knmi.notificatie_sleutel is None
        assert len(knmi.ontbrekende_functies()) == 3
        assert knmi.als_dict()["sleutels"] == {"wms": False, "edr": False, "notificatie": False}

    def test_als_dict_bevat_geen_sleutels(self):
        knmi = KnmiBronnen(object(), "wms-geheim-123", "edr-geheim-456", "mqtt-geheim-789")
        tekst = json.dumps(knmi.als_dict())
        for geheim in ("wms-geheim-123", "edr-geheim-456", "mqtt-geheim-789"):
            assert geheim not in tekst
        assert knmi.ontbrekende_functies() == []


# ---------------------------------------------------------------------
# 9. Notification Service
# ---------------------------------------------------------------------


class _NepClient:
    def __init__(self, client_id):
        self.client_id = client_id
        self.aanroepen = []

    def __getattr__(self, naam):
        def opnemen(*args, **kwargs):
            self.aanroepen.append((naam, args, kwargs))

        return opnemen


class _Reden:
    def __init__(self, waarde):
        self.value = waarde


class TestPush:
    def test_lees_melding(self):
        bericht = json.dumps({"data": {"datasetName": "radar_forecast", "filename": "RAD_NL25_RAC_FM_202610081205.h5"}})
        assert lees_melding(bericht) == ("radar_forecast", "RAD_NL25_RAC_FM_202610081205.h5")
        assert lees_melding(b"geen json") is None
        assert lees_melding(json.dumps({"data": {}})) is None

    def test_tijd_uit_bestandsnaam(self):
        assert tijd_uit_bestandsnaam("KMDS__OPER_P___10M_OBS_L2_202610081210.nc") == datetime(2026, 10, 8, 12, 10, tzinfo=timezone.utc)
        assert tijd_uit_bestandsnaam("RAD_NL25_RAC_FM_202610081205.h5") == datetime(2026, 10, 8, 12, 5, tzinfo=timezone.utc)
        assert tijd_uit_bestandsnaam("zonder tijd") is None
        assert tijd_uit_bestandsnaam(None) is None

    def _push(self):
        meldingen = []
        clients = []

        def fabriek(client_id):
            client = _NepClient(client_id)
            clients.append(client)
            return client

        async def opzet():
            loop = asyncio.get_running_loop()
            push = KnmiPush("mqtt-geheim", loop, None, lambda d, b: meldingen.append((d, b)), fabriek)
            push.start()
            return push

        return opzet, meldingen, clients

    def test_verbinden_abonneren_en_melden(self):
        opzet, meldingen, clients = self._push()

        async def scenario():
            push = await opzet()
            client = clients[0]
            namen = [a[0] for a in client.aanroepen]
            assert namen[:1] == ["username_pw_set"]
            assert client.aanroepen[0][1] == ("token", "mqtt-geheim")
            assert "connect_async" in namen and "loop_start" in namen
            verbind = next(a for a in client.aanroepen if a[0] == "connect_async")
            assert verbind[1] == ("mqtt.dataplatform.knmi.nl", 443, 60)
            assert client.client_id.startswith("stormchase-")

            class Bericht:
                payload = json.dumps({"data": {"datasetName": "10-minute-in-situ-meteorological-observations", "filename": "KMDS__OPER_P___10M_OBS_L2_202610081210.nc"}}).encode()

            def draad():
                push._bij_verbinden(client, None, None, _Reden(0), None)
                push._bij_bericht(client, None, Bericht())

            t = threading.Thread(target=draad)
            t.start()
            t.join()
            await asyncio.sleep(0.05)
            onderwerpen = [a[1][0] for a in client.aanroepen if a[0] == "subscribe"]
            assert any("10-minute-in-situ" in o for o in onderwerpen)
            assert any("radar_forecast" in o for o in onderwerpen)
            assert push.status == "verbonden"
            assert meldingen == [("10-minute-in-situ-meteorological-observations", "KMDS__OPER_P___10M_OBS_L2_202610081210.nc")]
            assert "mqtt-geheim" not in json.dumps(push.als_dict())

        _run(scenario())

    def test_geweigerde_sleutel_stopt(self):
        opzet, _, clients = self._push()

        async def scenario():
            push = await opzet()
            push._bij_verbinden(clients[0], None, None, _Reden(135), None)
            await asyncio.sleep(0.1)
            assert push.status == "sleutel geweigerd"
            assert any(a[0] == "loop_stop" for a in clients[0].aanroepen)

        _run(scenario())

    def test_verbroken_daarna_opnieuw(self):
        opzet, _, clients = self._push()

        async def scenario():
            push = await opzet()
            push._bij_verbinden(clients[0], None, None, _Reden(0), None)
            push._bij_verbreken(clients[0], None, None, _Reden(7), None)
            await asyncio.sleep(0.05)
            assert push.status == "verbinding verbroken"
            push._bij_verbinden(clients[0], None, None, _Reden(0), None)
            await asyncio.sleep(0.05)
            assert push.status == "verbonden" and push.verbindingen == 2
            # paho regelt het herverbinden zelf, exponentieel tot 10 minuten
            vertraging = next(a for a in clients[0].aanroepen if a[0] == "reconnect_delay_set")
            assert vertraging[2] == {"min_delay": 5, "max_delay": 600}

        _run(scenario())

    def test_echte_paho_client(self):
        pytest.importorskip("paho.mqtt.client")
        from knmi_push import _maak_paho_client

        client = _maak_paho_client("stormchase-test")
        assert client is not None


# ---------------------------------------------------------------------
# 10. Radarvooruitblik
# ---------------------------------------------------------------------


def _png(kleur, maat=64):
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGBA", (maat, maat), kleur).save(buffer, "PNG")
    return buffer.getvalue()


class TestVooruitblik:
    def test_frametijden_op_het_raster(self):
        ref = datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc)
        tijden = frame_tijden(ref)
        assert len(tijden) == 19
        assert tijden[0] == (ref - timedelta(minutes=60), False)
        assert tijden[6] == (ref, False)
        assert tijden[7] == (ref + timedelta(minutes=10), True)
        assert tijden[-1] == (ref + timedelta(minutes=120), True)

    def test_frametijden_tussen_het_raster(self):
        ref = datetime(2026, 10, 8, 14, 5, tzinfo=timezone.utc)
        tijden = frame_tijden(ref)
        verleden = [t for t, verwachting in tijden if not verwachting]
        # 13:00 .. 14:00 op het raster, plus 14:05 als laatste gemeten beeld
        assert verleden[0] == datetime(2026, 10, 8, 13, 0, tzinfo=timezone.utc)
        assert verleden[-2:] == [datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc), ref]
        verwacht = [t for t, verwachting in tijden if verwachting]
        assert verwacht[0] == ref + timedelta(minutes=10) and verwacht[-1] == ref + timedelta(minutes=120)

    def test_volgende_ronde_hergebruikt_het_verleden(self):
        """Een nieuwe radarronde vraagt alleen het nieuwe beeld en de verwachting."""
        een = datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc)
        twee = een + timedelta(minutes=5)

        def sleutels(ref):
            return {framesleutel("b", 768, "s", t, ref if v else None) for t, v in frame_tijden(ref)}

        nieuw = sleutels(twee) - sleutels(een)
        assert len(nieuw) == 13  # 14:05 gemeten + 12 verwachtingsbeelden

    def test_cache_bovengrens(self):
        cache = FrameCache(maximum=3)
        for i in range(5):
            cache.zet((i,), b"x")
        assert len(cache) == 3 and (0,) not in cache and (4,) in cache

    def test_gemeten_frame_hergebruikt_bij_nieuwe_referentie(self):
        t = datetime(2026, 10, 8, 13, 30, tzinfo=timezone.utc)
        een = framesleutel("b", 768, "s", t, None)
        assert een == framesleutel("b", 768, "s", t, None)
        ref1 = datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc)
        ref2 = ref1 + timedelta(minutes=5)
        assert framesleutel("b", 768, "s", t, ref1) != framesleutel("b", 768, "s", t, ref2)

    def test_labels(self):
        ref = datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc)
        assert framelabel(ref, ref, 7200) == "KNMI-radar 16:00 (nu)"
        assert framelabel(ref + timedelta(minutes=30), ref, 7200) == "KNMI-verwachting 16:30 (+30 min)"
        assert framelabel(ref - timedelta(minutes=20), ref, 7200) == "KNMI-radar 15:40 (-20 min)"

    def test_gif_met_ontbrekend_frame(self):
        from PIL import Image

        achtergrond = Image.new("RGBA", (64, 64), (20, 20, 20, 255))
        frames = [("a", _png((0, 0, 255, 100))), ("b", None), ("c", _png((255, 0, 0, 100))), ("d", b"kapot")]
        gif = stel_gif_samen(achtergrond, frames, (0, 0, 64), (32, 32), 300)
        beeld = Image.open(BytesIO(gif))
        assert beeld.format == "GIF" and beeld.n_frames == 2

    def test_geen_frames_geen_gif(self):
        from PIL import Image

        assert stel_gif_samen(Image.new("RGBA", (8, 8)), [("a", None)], (0, 0, 8), (4, 4)) is None


# ---------------------------------------------------------------------
# 11. Herstartbestendigheid en bronstatus
# ---------------------------------------------------------------------


class TestBronstatistiek:
    def test_nieuwe_bronnen_in_de_statistiek(self):
        stats = Statistieken()
        for naam in ("knmi_waarschuwingen", "knmi_verwachting", "knmi_nowcast", "knmi_edr", "knmi_wms"):
            assert naam in stats.bronnen

    def test_tellers_overleven_een_herstart(self):
        stats = Statistieken()
        stats.bronnen["knmi_edr"].succes()
        stats.bronnen["knmi_edr"].fout(SleutelGeweigerd("HTTP 403", 403))
        stats.regen_via_knmi = 7
        bewaard = json.loads(json.dumps(stats.tellers_naar_opslag()))
        nieuw = Statistieken()
        nieuw.herstel_tellers(bewaard)
        assert nieuw.bronnen["knmi_edr"].gelukt == 1
        assert nieuw.bronnen["knmi_edr"].mislukt == 1
        assert nieuw.regen_via_knmi == 7
        assert nieuw.als_dict()["regenbron_gebruikt"]["knmi"] == 7

    def test_drukhistorie_in_de_toestandsopslag(self):
        bron = (BRON / "__init__.py").read_text(encoding="utf-8")
        assert '"meting_druk": meting.druk_naar_opslag()' in bron
        assert 'meting.herstel_druk(staat.get("meting_druk"))' in bron
        # Terugzetten voordat de eerste ophaalronde loopt
        assert bron.index("meting.herstel_druk") < bron.index("async_config_entry_first_refresh()")


# ---------------------------------------------------------------------
# 12. Configuratie, terugval en privacy (broncontroles)
# ---------------------------------------------------------------------


class TestConfiguratie:
    def test_optievelden_met_de_juiste_namen(self):
        for bestand in ("strings.json", "translations/nl.json"):
            vertaling = json.loads((BRON / bestand).read_text(encoding="utf-8"))
            for flow in ("config", "options"):
                velden = vertaling[flow]["step"]["knmi"]["data"]
                assert velden["knmi_wms_sleutel"] == "KNMI WMS-sleutel (radarkaart)"
                assert velden["knmi_notificatie_sleutel"] == "KNMI Notification Service-sleutel"
                assert velden["knmi_edr_sleutel"] == "KNMI EDR-sleutel (waarnemingen)"
                assert "knmi_radarstijl" in velden

    def test_wachtwoordvelden_zonder_standaard(self):
        bron = (BRON / "config_flow.py").read_text(encoding="utf-8")
        assert "TextSelectorType.PASSWORD" in bron
        assert '"suggested_value"' in bron
        # Beide flows krijgen de stap
        assert bron.count('step_id="knmi"') == 2

    def test_diagnostiek_verbergt_de_sleutels(self):
        bron = (BRON / "diagnostics.py").read_text(encoding="utf-8")
        assert "*KNMI_SLEUTELS" in bron

    def test_sleutels_niet_in_logregels(self):
        import re

        for naam in ("knmi_api.py", "knmi_push.py", "__init__.py", "meting.py", "alerts.py", "rain.py", "image.py", "radarbron.py"):
            bron = (BRON / naam).read_text(encoding="utf-8")
            for regel in re.findall(r"_LOGGER\.\w+\((?:[^()]|\([^()]*\))*\)", bron, re.S):
                assert "_sleutel" not in regel, f"{naam}: {regel[:80]}"

    def test_vooruitblik_alleen_met_wms_sleutel(self):
        bron = (BRON / "image.py").read_text(encoding="utf-8")
        assert "knmi is not None and knmi.wms is not None" in bron
        assert '_attr_content_type = "image/gif"' in bron

    def test_terugval_buiten_nederland(self):
        # Neerslag, metingen en radar vragen alleen in Nederland bij het KNMI
        for naam in ("rain.py", "meting.py", "radarbron.py"):
            assert "in_nederland(" in (BRON / naam).read_text(encoding="utf-8"), naam
        # Waarschuwingen alleen bij land 'netherlands'; anders MeteoAlarm
        alerts = (BRON / "alerts.py").read_text(encoding="utf-8")
        assert 'if land == "netherlands" and self.knmi is not None:' in alerts
        assert alerts.index("await self._knmi(latitude, longitude)") < alerts.index('url = f"{METEOALARM_URL}{land}"')

    def test_neerslagvolgorde(self):
        rain = (BRON / "rain.py").read_text(encoding="utf-8")
        assert rain.index("self._knmi_nowcast(") < rain.index("self._buienradar_of_open_meteo(")
        assert rain.index("await self._buienradar(latitude") < rain.index("await self._open_meteo(latitude")

    def test_manifest(self):
        manifest = json.loads((BRON / "manifest.json").read_text())
        assert any(r.startswith("paho-mqtt") for r in manifest["requirements"])
        assert not any("aiomqtt" in r or "pyproj" in r for r in manifest["requirements"])


def test_versie_0490():
    versie = json.loads((BRON / "manifest.json").read_text())["version"]
    assert tuple(int(d) for d in versie.split(".")) >= (0, 49, 0)
