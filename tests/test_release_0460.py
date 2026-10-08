"""0.46.0: passage-trefkans op afstand (L-SC-003) en het begin van de volgende bui.

1. `passage_afgerond` telde elke gemeten afstand als uitgekomen: passage 21/21,
   terwijl van de 12 bewaarde uitkomsten maar 5 binnen 10 km en 7 binnen 20 km
   zaten (uitschieters -56, -31, -31, -25 km).
2. 8 oktober 08:10: regen stopt over 16 min, nieuwe bui vanaf +91 min, maar
   'regen begint over' bleef onbekend zolang het regende.
"""

import ast
from pathlib import Path

import pytest

from buienreeks import begin_weergave, gaat_om_volgende_bui, lees_reeks
from validatie import Validatie

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"

# Afwijkingen (km) zoals in de bewaarde uitkomsten: 5 binnen 10 km, 2 tussen
# 10 en 20 km, 5 daarbuiten met als grootste -56,2.
AFWIJKINGEN = [-2.1, 4.0, -7.5, 9.8, 0.6, -14.2, 18.9, -25.0, -31.0, -31.3, 22.4, -56.2]


def _uitkomst(afwijking, horizon="tot 15 min"):
    return {
        "soort": "passage",
        "voorspeld_over_min": 10,
        "horizon": horizon,
        "gemaakt_op": 0.0,
        "uitgekomen": True,
        "verwachte_afstand_km": 30.0,
        "werkelijke_afstand_km": round(30.0 + afwijking, 1),
        "afwijking_km": afwijking,
    }


class TestPassageTrefkans:
    def test_oude_uitkomsten_geven_eerlijke_trefkans(self):
        """Reproductie: 'uitgekomen' blijft 12/12, maar raak is 5/12 en 7/12."""
        val = Validatie([_uitkomst(a) for a in AFWIJKINGEN])
        s = val.samenvatting()["passage (tot 15 min)"]

        assert s["aantal"] == 12
        assert s["uitgekomen"] == 12  # oude betekenis: afstand gemeten
        assert s["uitgekomen_betekent"] == "afstand gemeten"
        assert s["raak"] == 5
        assert s["binnen_10_km"] == 5
        assert s["binnen_20_km"] == 7
        assert s["trefkans_10_km_pct"] == 42
        assert s["trefkans_20_km_pct"] == 58
        assert s["grootste_afwijking_km"] == 56.2
        assert s["mediane_afwijking_km"] == pytest.approx(16.55, abs=0.06)

    @pytest.mark.parametrize(
        "werkelijk, raak, ruim",
        [(31.0, True, True), (20.0, True, True), (19.9, False, True),
         (10.0, False, True), (9.9, False, False), (-26.2 + 30, False, False)],
    )
    def test_nieuwe_uitkomst_krijgt_raak_per_straal(self, werkelijk, raak, ruim):
        val = Validatie()
        val.voorspel("passage", 0.0, 10, {"verwachte_afstand": 30.0})
        val.passage_afgerond(10 * 60, werkelijk)

        u = val.uitkomsten[-1]
        assert u["uitgekomen"] is True
        assert u["raak"] is raak
        assert u["binnen_10_km"] is raak
        assert u["binnen_20_km"] is ruim
        assert u["afwijking_km"] == round(werkelijk - 30.0, 1)

    def test_zonder_gemeten_afstand_is_mis(self):
        val = Validatie()
        val.voorspel("passage", 0.0, 10, {"verwachte_afstand": 30.0})
        val.passage_afgerond(10 * 60, None)

        u = val.uitkomsten[-1]
        assert u["uitgekomen"] is False
        assert u["raak"] is False and u["binnen_20_km"] is False
        s = val.samenvatting()["passage (tot 15 min)"]
        assert s["raak"] == 0 and s["trefkans_10_km_pct"] == 0

    def test_andere_soorten_ongewijzigd(self):
        val = Validatie()
        val.voorspel("regen", 0.0, 10, {})
        val.uitgekomen("regen", 12 * 60)
        s = val.samenvatting()["regen (tot 15 min)"]
        assert "raak" not in s and "trefkans_10_km_pct" not in s

    def test_diagnostiek_toont_trefkans(self):
        val = Validatie([_uitkomst(a) for a in AFWIJKINGEN])
        assert val.als_dict()["samenvatting"]["passage (tot 15 min)"]["binnen_10_km"] == 5


def _reeks_0810():
    """Regen nu, droog vanaf +16 min, nieuwe bui vanaf +91 min (5-min stappen)."""
    minuten = [-10, -5, 0, 5, 10] + list(range(16, 121, 5))
    return [(m, 1.8 if m < 16 else (0.0 if m < 91 else 2.4)) for m in minuten]


class TestVolgendeBui:
    def test_reproductie_0810(self):
        data = lees_reeks(_reeks_0810(), 0.1)

        assert data["regent"] is True
        assert data["stopt_over"] == 16
        assert data["begint_over"] is None  # meldingen/regen_verwacht ongewijzigd
        assert data["volgende_bui_over"] == 91
        assert begin_weergave(data) == 91
        assert gaat_om_volgende_bui(data) is True

    def test_regent_zonder_volgende_bui_blijft_onbekend(self):
        reeks = [(m, 1.5 if m < 20 else 0.0) for m in range(-10, 121, 5)]
        data = lees_reeks(reeks, 0.1)
        assert data["stopt_over"] == 20
        assert data["volgende_bui_over"] is None
        assert begin_weergave(data) is None
        assert gaat_om_volgende_bui(data) is False

    def test_regent_de_hele_reeks(self):
        data = lees_reeks([(m, 2.0) for m in range(-10, 121, 5)], 0.1)
        assert data["stopt_over"] is None
        assert data["volgende_bui_over"] is None
        assert begin_weergave(data) is None

    def test_droog_zoals_voorheen(self):
        reeks = [(m, 0.0 if m < 40 else 1.0) for m in range(-10, 121, 5)]
        data = lees_reeks(reeks, 0.1)
        assert data["regent"] is False
        assert data["begint_over"] == 40
        assert data["volgende_bui_over"] is None
        assert begin_weergave(data) == 40
        assert gaat_om_volgende_bui(data) is False

    def test_droog_zonder_regen(self):
        data = lees_reeks([(m, 0.0) for m in range(-10, 121, 5)], 0.1)
        assert begin_weergave(data) is None

    def test_oude_data_zonder_nieuw_veld(self):
        """Bewaarde data van voor 0.46.0 heeft geen volgende_bui_over."""
        assert begin_weergave({"regent": True, "begint_over": None, "stopt_over": 10}) is None


class TestAansluiting:
    def _bron(self, naam):
        return (BRON / naam).read_text(encoding="utf-8")

    def test_sensor_gebruikt_weergave(self):
        bron = self._bron("sensor.py")
        assert "value=begin_weergave" in bron
        assert '"volgende_bui": gaat_om_volgende_bui(data)' in bron

    def test_rain_gebruikt_lees_reeks(self):
        bron = self._bron("rain.py")
        assert "lees_reeks(reeks, drempel)" in bron
        assert '"volgende_bui_over": gelezen["volgende_bui_over"]' in bron

    def test_meldingen_en_validatie_blijven_op_begint_over(self):
        """Meldgedrag niet wijzigen: _vuur_event, validatie, regen_verwacht en
        briefing kijken alleen naar begint_over."""
        for naam in ("rain.py", "binary_sensor.py", "briefing.py", "notifier.py", "alerts.py"):
            assert "volgende_bui" not in self._bron(naam).replace(
                'gelezen["volgende_bui_over"]', ""
            ).replace('"volgende_bui_over": ', ""), naam

        boom = ast.parse(self._bron("rain.py"))
        vuur = next(
            n for n in ast.walk(boom)
            if isinstance(n, ast.FunctionDef) and n.name == "_vuur_event"
        )
        assert 'data["begint_over"]' in ast.get_source_segment(self._bron("rain.py"), vuur)


def test_versie_0460():
    import json

    versie = json.loads((BRON / "manifest.json").read_text())["version"]
    assert tuple(int(d) for d in versie.split(".")) >= (0, 46, 0)
