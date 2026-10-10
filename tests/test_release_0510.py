"""0.51.0: windstoten bijgesteld met de stationsmeting en het regenbeeld in één zin."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

from buienreeks import bui_piek, lees_reeks, regenbeeld, sterkte  # noqa: E402
from windcorrectie import (  # noqa: E402
    FACTOR_MAX,
    FACTOR_MIN,
    MIN_PAREN,
    Windcorrectie,
)

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"

# 9 oktober 19:30-22:20: Open-Meteo tegen KNMI Hupsel (km/u)
MODEL_0910 = [47.2, 44.3, 44.3, 46.4, 46.4, 48.6, 48.6, 50.0, 50.0, 50.0, 52.2, 52.2, 52.2, 54.7, 54.7, 54.7, 54.7]
GEMETEN_0910 = [34.7, 32.4, 31.9, 31.2, 36.6, 37.0, 27.5, 35.5, 33.3, 30.3, 28.9, 36.5, 40.5, 35.7, 34.6, 28.2, 38.8]


# 0.52.0: de correctie telt pas na zes uur aan paren; deze tests vullen
# daarom per uur in plaats van per tien minuten.
def _vul(wc: Windcorrectie, model, gemeten, start=1_000_000.0, stap=3600.0) -> float:
    t = start
    for m, g in zip(model, gemeten):
        wc.bij(t, g, m, t - 120)
        t += stap
    return t - stap


class TestWindcorrectie:
    def test_avond_van_9_oktober(self):
        """Model 55 km/u, gemeten 28-40: de correctie zakt naar ~0,68."""
        wc = Windcorrectie()
        laatste = _vul(wc, MODEL_0910, GEMETEN_0910)
        factor, paren = wc.factor(laatste)
        assert paren == len(MODEL_0910)
        assert 0.62 <= factor <= 0.74
        uit = wc.corrigeer(54.7, laatste)
        assert uit["toegepast"]
        assert 34 <= uit["waarde"] <= 40  # in het gemeten bereik
        assert uit["model"] == 54.7

    def test_te_weinig_paren_laat_model_staan(self):
        wc = Windcorrectie()
        laatste = _vul(wc, MODEL_0910[: MIN_PAREN - 1], GEMETEN_0910[: MIN_PAREN - 1])
        uit = wc.corrigeer(50.0, laatste)
        assert uit["factor"] is None and uit["waarde"] == 50.0 and not uit["toegepast"]

    def test_minder_dan_een_uur_telt_niet(self):
        wc = Windcorrectie()
        laatste = _vul(wc, [50.0] * 10, [30.0] * 10, stap=300.0)  # 45 minuten
        assert wc.factor(laatste)[0] is None

    def test_grenzen(self):
        laag = Windcorrectie()
        t = _vul(laag, [50.0] * 8, [5.0] * 8)
        assert laag.factor(t)[0] == FACTOR_MIN
        hoog = Windcorrectie()
        t = _vul(hoog, [20.0] * 8, [60.0] * 8)
        assert hoog.factor(t)[0] == FACTOR_MAX

    def test_weinig_wind_telt_niet_mee(self):
        wc = Windcorrectie()
        assert not wc.bij(1000.0, 8.0, 4.0, 1000.0)

    def test_zelfde_meting_niet_dubbel(self):
        wc = Windcorrectie()
        assert wc.bij(1000.0, 30.0, 50.0, 1000.0)
        assert not wc.bij(1000.0, 30.0, 50.0, 1100.0)
        assert len(wc.paren) == 1

    def test_oude_modelwaarde_telt_niet(self):
        wc = Windcorrectie()
        assert not wc.bij(10_000.0, 30.0, 50.0, 10_000.0 - 46 * 60)

    def test_lege_waarden(self):
        wc = Windcorrectie()
        assert not wc.bij(None, 30.0, 50.0, 0.0)
        assert not wc.bij(0.0, None, 50.0, 0.0)
        assert not wc.bij(0.0, 30.0, None, 0.0)
        assert wc.corrigeer(None, 0.0)["waarde"] is None

    def test_mediaan_negeert_een_uitschieter(self):
        wc = Windcorrectie()
        t = _vul(wc, [50.0] * 9, [30.0] * 8 + [120.0])
        assert wc.factor(t)[0] == 0.6

    def test_oud_valt_buiten_venster(self):
        wc = Windcorrectie()
        _vul(wc, [50.0] * 8, [25.0] * 8, start=0.0)
        t = _vul(wc, [50.0] * 8, [40.0] * 8, start=30 * 3600.0)
        assert wc.factor(t)[0] == 0.8

    def test_over_een_herstart(self):
        wc = Windcorrectie()
        t = _vul(wc, MODEL_0910, GEMETEN_0910)
        opgeslagen = json.loads(json.dumps(wc.naar_opslag()))
        terug = Windcorrectie(opgeslagen)
        assert terug.factor(t) == wc.factor(t)
        assert Windcorrectie("rommel").paren == []
        assert Windcorrectie([[1, "x", 3], [1, 2, 3]]).paren == [(1.0, 2.0, 3.0, False)]


def _data_2227() -> dict:
    """De KNMI-nowcast van 9 oktober 22:27 (Eibergen)."""
    mm = [0, 0, 0.12, 0, 0, 0.84, 13.68, 6.72, 1.44, 0.72, 1.32, 0.72, 0.12, 0.48,
          1.68, 0, 0, 0, 0, 0, 0, 0, 0.48, 1.56, 0.84, 0.36, 1.08, 0.48, 0, 0]
    reeks = [(-28 + 5 * i, w) for i, w in enumerate(mm)]
    data = lees_reeks(reeks, 0.1)
    data["drempel"] = 0.1
    data["verwachting"] = [{"minuten": m, "mm_per_uur": w} for m, w in reeks]
    return data


class TestRegenbeeld:
    def test_bui_van_2226(self):
        data = _data_2227()
        assert data["regent"] and data["stopt_over"] == 47 and data["volgende_bui_over"] == 82
        zin = regenbeeld(data)
        assert zin == (
            "Regent nu, zwaar (13,7 mm/u), droog over 47 min; "
            "volgende bui over 82 min (licht, tot 1,6 mm/u)."
        )

    def test_droog_met_bui_op_komst(self):
        data = lees_reeks([(0, 0.0), (5, 0.0), (15, 0.5), (20, 4.0), (25, 0.0)], 0.1)
        data["verwachting"] = [{"minuten": m, "mm_per_uur": w} for m, w in
                               [(0, 0.0), (5, 0.0), (15, 0.5), (20, 4.0), (25, 0.0)]]
        assert regenbeeld(data) == "Droog, over 15 min een bui (matig, tot 4,0 mm/u)."

    def test_droog_zonder_regen(self):
        data = lees_reeks([(0, 0.0), (60, 0.0)], 0.1)
        data["verwachting"] = []
        assert regenbeeld(data) == "Droog, komende 2 uur geen regen."

    def test_regent_aanhoudend(self):
        data = lees_reeks([(0, 3.0), (60, 3.0), (115, 2.0)], 0.1)
        assert regenbeeld(data) == "Regent nu, matig (3,0 mm/u), houdt de komende 2 uur aan."

    def test_zonder_gegevens(self):
        assert regenbeeld(None) is None
        assert regenbeeld({}) is None

    def test_sterkte(self):
        assert [sterkte(x) for x in (0.2, 2.5, 9.9, 10.0, None)] == [
            "licht", "matig", "matig", "zwaar", "onbekend"
        ]

    def test_bui_piek_zonder_begin(self):
        assert bui_piek(_data_2227(), None) is None


class TestEntiteiten:
    def test_vertalingen(self):
        for bestand in ("translations/nl.json", "translations/en.json", "strings.json"):
            sensoren = json.loads((BRON / bestand).read_text(encoding="utf-8"))["entity"]["sensor"]
            assert "rain_stops" in sensoren and "rain_summary" in sensoren
        nl = json.loads((BRON / "translations/nl.json").read_text(encoding="utf-8"))["entity"]["sensor"]
        assert nl["rain_stops"]["name"] == "Regen stopt over"
        assert nl["rain_summary"]["name"] == "Regenbeeld"

    def test_dashboard_kent_ze(self):
        script = (BRON / "www" / "stormchase-strategy.js").read_text(encoding="utf-8")
        assert '"stormchase_regen_stopt_over"' in script
        assert '"stormchase_regenbeeld"' in script
        assert "volgende bui over" in script

    def test_windstoot_attributen_en_koppeling(self):
        sensor = (BRON / "sensor.py").read_text(encoding="utf-8")
        assert '"correctiefactor"' in sensor and '"model"' in sensor
        init = (BRON / "__init__.py").read_text(encoding="utf-8")
        assert "meting.async_add_listener(_koppel_wind)" in init
        assert '"windcorrectie": windcorrectie.naar_opslag()' in init
        coord = (BRON / "coordinator.py").read_text(encoding="utf-8")
        # De windmelding gaat op de bijgestelde waarde
        assert 'self._controleer_wind(wind["waarde"])' in coord
