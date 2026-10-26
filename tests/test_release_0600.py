"""0.60.0: geel alleen bij echte nabijheid (L-SC-024) en windstoten tijdens een
front met de verhouding van dat front (L-SC-022).

L-SC-024: 25-10 stond het waarschuwingsniveau 11 minuten op geel door
"nadert" bij een bui op 91 km met een aankomst over 6,6 uur (396 min).

L-SC-022: tijdens een front liep de verwachting 4 dagen op rij achter bij op-
en aflopende wind (tot +-6 km/u), omdat de algemene geleerde factor bleef
gelden terwijl de verhouding in het front anders lag.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

from const import WINDCORRECTIE_FRONT_MIN_PAREN  # noqa: E402
from indices import (  # noqa: E402
    NADERT_MAX_AANKOMST_MIN,
    gemeten_onweer,
    gemeten_uit_storm,
    niveau_met_metingen,
)
from windcorrectie import Windcorrectie  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BRON = ROOT / "custom_components" / "stormchase"
T0 = 1_760_000_000.0
STAP = 600.0


# ---- L-SC-024 ----

class TestGeelAlleenDichtbij:
    def test_25_10_bui_op_91_km_geeft_geen_geel(self):
        storm = SimpleNamespace(speed=13.8, distance=91.0, eta=396)
        gemeten = gemeten_uit_storm(storm, 1.0, 15.0)
        assert gemeten is False
        assert niveau_met_metingen("groen", gemeten) == "groen"

    def test_aankomst_binnen_120_minuten_wel_geel(self):
        storm = SimpleNamespace(speed=30.0, distance=55.0, eta=110)
        assert gemeten_uit_storm(storm, 1.0, 15.0)
        storm = SimpleNamespace(speed=30.0, distance=60.0, eta=NADERT_MAX_AANKOMST_MIN)
        assert gemeten_uit_storm(storm, 1.0, 15.0)
        storm = SimpleNamespace(speed=30.0, distance=61.0, eta=121)
        assert not gemeten_uit_storm(storm, 1.0, 15.0)

    def test_binnen_de_meldafstand_wel_geel(self):
        # Meldafstand groter dan 25 km: nadert binnen die afstand telt
        assert gemeten_onweer(True, 35.0, 400, meldafstand=40.0)
        assert not gemeten_onweer(True, 45.0, 400, meldafstand=40.0)

    def test_nabijheid_ongewijzigd(self):
        # Inslagen binnen 25 km geven geel, ook zonder nadering of met verre aankomst
        assert gemeten_onweer(False, 23.0)
        assert gemeten_onweer(True, 24.0, 900, meldafstand=15.0)
        assert not gemeten_onweer(False, 25.1, 30, meldafstand=15.0)
        # Hoger dan geel door de waarschuwing zelf blijft staan
        assert niveau_met_metingen("oranje", True) == "oranje"
        assert niveau_met_metingen("rood", False) == "rood"

    def test_zonder_aankomsttijd_blijft_nadert_gelden(self):
        assert gemeten_onweer(True, None)
        assert gemeten_onweer(True, 40.0, None, meldafstand=15.0)

    def test_aanroepers_geven_de_meldafstand_mee(self):
        for naam in ("sensor.py", "binary_sensor.py", "briefing.py"):
            tekst = (BRON / naam).read_text(encoding="utf-8")
            assert '"warn_distance"' in tekst, naam


# ---- L-SC-022 ----

def _rustig(wc, t, uren, model=60.0, ratio=0.7):
    for _ in range(int(uren * 3600 / STAP)):
        assert wc.bij(t, round(model * ratio, 1), model, t)
        t += STAP
    return t


def _front(wc, t, n, model=40.0, gemeten=40.0):
    for _ in range(n):
        assert wc.bij(t, gemeten, model, t, druk_1u=1.6)
        t += STAP
    return t


class TestFrontfactor:
    def test_frontfactor_tijdens_het_front(self):
        wc = Windcorrectie()
        t = _rustig(wc, T0, 8.0)  # geleerde factor 0,7
        t = _front(wc, t, 6, model=40.0, gemeten=36.0)  # front: 0,9
        nu = t - STAP
        uit = wc.corrigeer(40.0, nu)
        assert uit["front"] is True
        assert uit["factor"] == 0.7  # de geleerde factor zelf blijft
        assert uit["factor_front"] == 0.9
        assert uit["factor_toegepast"] == 0.9
        assert uit["paren_lopend_front"] == 6
        # 40 x 0,9 = 36, laatste fout 0: geen bijsturing
        assert uit["waarde"] == 36.0
        assert uit["bijsturing"] == 0.0

    def test_oude_methode_liep_achter(self):
        """Met de geleerde factor stond de verwachting 8 km/u te laag; de
        bijsturing (halve fout) haalde maar de helft terug."""
        wc = Windcorrectie()
        t = _rustig(wc, T0, 8.0)
        t = _front(wc, t, 6, model=40.0, gemeten=36.0)
        nu = t - STAP
        oud = 40.0 * 0.7 + 0.5 * (36.0 - 40.0 * 0.7)
        nieuw = wc.corrigeer(40.0, nu)["waarde"]
        assert abs(nieuw - 36.0) < abs(oud - 36.0)

    def test_te_weinig_frontparen_huidig_gedrag(self):
        wc = Windcorrectie()
        t = _rustig(wc, T0, 8.0)
        t = _front(wc, t, WINDCORRECTIE_FRONT_MIN_PAREN - 1, gemeten=36.0)
        nu = t - STAP
        uit = wc.corrigeer(40.0, nu)
        assert uit["front"] is True
        assert uit["factor_front"] is None
        assert uit["factor_toegepast"] == uit["factor"] == 0.7
        # zoals 0.59.x: model x factor + halve fout
        assert uit["waarde"] == round(40.0 * 0.7 + 0.5 * (36.0 - 28.0), 1)

    def test_alleen_het_lopende_front_telt(self):
        """Een eerder front met een andere verhouding telt niet mee."""
        wc = Windcorrectie()
        t = _rustig(wc, T0, 8.0)
        t = _front(wc, t, 8, gemeten=20.0)  # oud front: 0,5
        t = _rustig(wc, t, 4.0)
        t = _front(wc, t, 5, gemeten=44.0)  # nieuw front: 1,1
        uit = wc.corrigeer(40.0, t - STAP)
        assert uit["factor_front"] == 1.1
        assert uit["paren_lopend_front"] == 5

    def test_buiten_het_front_geen_frontfactor(self):
        wc = Windcorrectie()
        t = _rustig(wc, T0, 8.0)
        t = _front(wc, t, 6, gemeten=36.0)
        # ruim na de naloop weer rustig
        t = _rustig(wc, t, 3.0)
        uit = wc.corrigeer(40.0, t - STAP)
        assert uit["front"] is False
        assert uit["factor_front"] is None
        assert uit["factor_toegepast"] == uit["factor"]

    def test_zonder_geleerde_factor_kaal_model(self):
        """Bij de start (nog niets geleerd) blijft het kale model staan."""
        wc = Windcorrectie()
        t = _rustig(wc, T0, 2.0)
        t = _front(wc, t, 10, gemeten=36.0)
        uit = wc.corrigeer(40.0, t - STAP)
        assert uit["factor"] is None and uit["factor_front"] is None
        assert uit["waarde"] == 40.0

    def test_grenzen(self):
        wc = Windcorrectie()
        t = _rustig(wc, T0, 8.0)
        t = _front(wc, t, 6, model=20.0, gemeten=40.0)  # 2,0
        assert wc.corrigeer(20.0, t - STAP)["factor_front"] == 1.3

    def test_komende_uren_met_frontfactor(self):
        wc = Windcorrectie()
        t = _rustig(wc, T0, 8.0)
        t = _front(wc, t, 6, model=40.0, gemeten=36.0)
        nu = t - STAP
        uit = wc.corrigeer(40.0, nu)
        uren = wc.bijgestuurde_uren([(nu + 3600, 50.0)], nu, uit["factor_toegepast"])
        assert uren == [(nu + 3600, 45.0)]
        coord = (BRON / "coordinator.py").read_text(encoding="utf-8")
        assert 'wind.get("factor_toegepast"' in coord

    def test_attributen_op_de_sensor(self):
        tekst = (BRON / "sensor.py").read_text(encoding="utf-8")
        for sleutel in ('"factor_front"', '"factor_toegepast"', '"paren_lopend_front"'):
            assert sleutel in tekst


def test_versie():
    manifest = json.loads((BRON / "manifest.json").read_text(encoding="utf-8"))
    assert tuple(int(x) for x in manifest["version"].split(".")) >= (0, 60, 0)
    assert "## [0.60.0]" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
