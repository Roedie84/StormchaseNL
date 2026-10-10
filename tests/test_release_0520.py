"""0.52.0 (L-SC-007): windstootcorrectie pas na zes uur en zonder fronten."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

import const  # noqa: E402
from windcorrectie import MIN_SPANNE_S, Windcorrectie  # noqa: E402

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"

# 9 oktober 22:04-23:34, KNMI Hupsel: gemeten stoot (km/u) en luchtdruk (hPa).
# Om 22:33 trok het koufront over: stoot 35 -> 55, druk +1,5 hPa.
NACHT = [
    (22 * 60 + 4, 38.8, 1004.64),
    (22 * 60 + 14, 32.8, 1004.44),
    (22 * 60 + 24, 35.3, 1004.04),
    (22 * 60 + 33, 54.7, 1005.56),
    (22 * 60 + 44, 28.8, 1005.66),
    (22 * 60 + 54, 29.8, 1005.86),
    (23 * 60 + 4, 25.1, 1005.76),
    (23 * 60 + 14, 19.5, 1005.96),
    (23 * 60 + 24, 18.5, 1005.76),
    (23 * 60 + 34, 13.7, 1005.66),
]


def _druk_1u(index: int) -> float | None:
    """Drukverandering over (ongeveer) een uur, zoals de meting die geeft."""
    minuut, _, druk = NACHT[index]
    eerder = [d for m, _, d in NACHT if 50 <= minuut - m <= 70]
    return round(druk - eerder[0], 1) if eerder else None


def _rustig(wc: Windcorrectie, start: float, uren: float, model=40.0, gemeten=22.0) -> float:
    """Rustig weer, elke tien minuten een paar met verhouding 0,55."""
    t = start
    for _ in range(int(uren * 6) + 1):
        wc.bij(t, gemeten, model, t - 120)
        t += 600
    return t - 600


class TestZesUur:
    def test_minder_dan_zes_uur_kaal_model(self):
        wc = Windcorrectie()
        t = _rustig(wc, 0.0, 5.5)
        uit = wc.corrigeer(40.0, t)
        assert uit["factor"] is None
        assert uit["waarde"] == 40.0 and not uit["toegepast"]
        assert uit["paren"] >= 30  # genoeg paren, te kort

    def test_na_zes_uur_factor(self):
        wc = Windcorrectie()
        t = _rustig(wc, 0.0, 6.0)
        uit = wc.corrigeer(40.0, t)
        assert uit["toegepast"] and uit["factor"] == 0.55
        assert uit["waarde"] == 22.0
        assert uit["uren"] == 6.0
        assert MIN_SPANNE_S == 6 * 3600 == const.WINDCORRECTIE_MIN_SPANNE_S


class TestFront:
    def test_koufront_van_9_oktober_herkend(self):
        """Stootsprong en druksprong om 22:33; daarna een uur naloop."""
        wc = Windcorrectie()
        basis = 1_000_000.0
        for i, (minuut, stoot, _) in enumerate(NACHT):
            t = basis + minuut * 60
            assert wc.bij(t, stoot, 40.0, t, druk_1u=_druk_1u(i))
        vlaggen = {round((p[0] - basis) / 60): p[3] for p in wc.paren}
        assert vlaggen[22 * 60 + 33] is True
        assert vlaggen[22 * 60 + 24] is False
        # De druk steeg over het uur tot 23:24 nog >= 1 hPa
        assert vlaggen[23 * 60 + 14] is True
        uit = wc.corrigeer(40.0, basis + NACHT[-1][0] * 60)
        assert uit["paren_front"] >= 6  # front plus naloop
        assert not uit["toegepast"]

    def test_front_leert_de_factor_niet(self):
        """Eén front van een paar uur met verhouding 0,40 tussen rustig
        weer met 0,55: de factor blijft 0,55."""
        wc = Windcorrectie()
        t = _rustig(wc, 0.0, 4.0)
        # Front: druk springt, model blijft hoog, wind valt weg
        for i in range(1, 19):
            t += 600
            wc.bij(t, 16.0, 40.0, t, druk_1u=1.6)
        t = _rustig(wc, t + 600, 4.0)
        uit = wc.corrigeer(40.0, t)
        assert uit["factor"] == 0.55
        assert uit["paren_front"] >= 18

    def test_onweer_bij_het_station(self):
        wc = Windcorrectie()
        assert wc.bij(1000.0, 30.0, 40.0, 1000.0, onweer=True)
        assert wc.paren[-1][3] is True
        assert wc.corrigeer(40.0, 1000.0)["front"] is True

    def test_gewone_tendens_is_geen_front(self):
        wc = Windcorrectie()
        assert wc.bij(1000.0, 30.0, 40.0, 1000.0, onweer=False, druk_1u=-0.6)
        assert wc.paren[-1][3] is False
        assert wc.bij(1600.0, 40.0, 40.0, 1600.0, druk_1u="rommel")
        assert wc.paren[-1][3] is False  # 10 km/u erbij: gewone vlaag

    def test_naloop_alleen_na_het_front(self):
        wc = Windcorrectie()
        t = _rustig(wc, 0.0, 7.0)
        wc.bij(t + 600, 22.0, 40.0, t + 600, druk_1u=2.0)
        uit = wc.corrigeer(40.0, t + 600)
        # De paren ervoor tellen gewoon; alleen het frontpaar valt weg
        assert uit["paren_front"] == 1 and uit["toegepast"]
        assert uit["front"] is True


class TestUpgrade:
    def test_opslag_uit_0511_zonder_frontvlag(self):
        """Paren van [tijd, gemeten, model] krijgen alsnog de stoottoets."""
        oud = [[1000.0 + 600 * i, 35.0, 50.0] for i in range(5)]
        oud.append([1000.0 + 600 * 5, 55.0, 50.0])  # sprong van 20 km/u
        oud.append([1000.0 + 600 * 6, 33.0, 50.0])
        wc = Windcorrectie(json.loads(json.dumps(oud)))
        assert len(wc.paren) == 7
        assert [p[3] for p in wc.paren] == [False] * 5 + [True, False]
        # en het rekent gewoon door
        uit = wc.corrigeer(50.0, 1000.0 + 3600)
        assert uit["waarde"] == 50.0 and uit["paren_front"] == 2

    def test_rommel_in_de_opslag(self):
        bewaard = [[1, 2, 3], [1, 2], "x", None, [4, 5, 6, True, 9], [7, "a", 9], [10, 20, 30, False]]
        wc = Windcorrectie(bewaard)
        assert [p[0] for p in wc.paren] == [1.0, 10.0]
        assert Windcorrectie({"paren": []}).paren == []
        assert Windcorrectie(None).paren == []

    def test_opslag_rondje(self):
        wc = Windcorrectie()
        t = _rustig(wc, 0.0, 6.5)
        wc.bij(t + 600, 22.0, 40.0, t + 600, onweer=True)
        opgeslagen = json.loads(json.dumps(wc.naar_opslag()))
        assert all(len(p) == 4 for p in opgeslagen)
        terug = Windcorrectie(opgeslagen)
        assert terug.paren == wc.paren
        assert terug.corrigeer(40.0, t + 600) == wc.corrigeer(40.0, t + 600)


class TestKoppeling:
    def test_constanten_in_const(self):
        assert const.FRONT_DRUK_1U_HPA == 1.0
        assert const.FRONT_STOOT_SPRONG_KMH == 15.0
        assert const.FRONT_NALOOP_S == 3600

    def test_meting_geeft_frontsignalen_door(self):
        init = (BRON / "__init__.py").read_text(encoding="utf-8")
        assert 'onweer=gemeten.get("onweer") or gemeten.get("onweer_afgelopen_uur")' in init
        assert 'druk_1u=gemeten.get("druk_verandering_1u")' in init

    def test_sensor_attributen(self):
        sensor = (BRON / "sensor.py").read_text(encoding="utf-8")
        for naam in ('"paren_front"', '"front"', '"uren_metingen"'):
            assert naam in sensor
        assert "zes uur" in sensor
