"""0.60.1: correctie-attributen van L-SC-011 op *Regen begint over*.

0.56.0 zette `_regen_attributen` in de MeteoSensor, maar *Regen begint over*
(key rain_starts) is een RainSensor: de attributen `zonder_correctie`,
`gecorrigeerd`, `correctie_vorm`, ... verschenen nooit (gemeten 28-10).
"""

import ast
from pathlib import Path

from buienreeks import gaat_om_volgende_bui

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
BRON = (ROOT / "sensor.py").read_text(encoding="utf-8")
BOOM = ast.parse(BRON)


def _functies():
    ns = {"gaat_om_volgende_bui": gaat_om_volgende_bui}
    nodes = [n for n in BOOM.body if isinstance(n, ast.FunctionDef)
             and n.name in ("_regen_attributen", "_regen_start_attributen")]
    assert len(nodes) == 2
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "sensor.py", "exec"), ns)
    return ns


def _klasse(naam):
    return next(n for n in BOOM.body if isinstance(n, ast.ClassDef) and n.name == naam)


def test_rainsensor_gebruikt_de_start_attributen():
    rain = ast.get_source_segment(BRON, _klasse("RainSensor"))
    assert "_regen_start_attributen(data)" in rain


def test_meteosensor_heeft_geen_dode_regentak_meer():
    meteo = ast.get_source_segment(BRON, _klasse("MeteoSensor"))
    assert "rain_starts" not in meteo


def test_attributen_met_correctie():
    f = _functies()["_regen_start_attributen"]
    data = {
        "bron": "knmi", "regent": False, "begint_over": 25, "begint_over_kaal": 32,
        "regencorrectie": {"vorm": "verschuiving", "toegepast": True,
                           "verschuiving_min": {"15-45": -7}, "uitkomsten": 51,
                           "afwijking_min": 8.1},
        "totaal": 0.4, "verwachting": [{"minuten": 0, "mm_per_uur": 0}],
    }
    a = f(data)
    assert a["zonder_correctie"] == 32
    assert a["gecorrigeerd"] is True
    assert a["correctie_vorm"] == "verschuiving"
    assert a["uitkomsten"] == 51
    assert a["bron"] == "knmi"
    assert a["totaal_mm_2u"] == 0.4
    assert a["verwachting"] == data["verwachting"]
    assert list(a)[-1] == "verwachting"


def test_attributen_zonder_correctie():
    f = _functies()["_regen_start_attributen"]
    a = f({"bron": "knmi", "regent": True, "begint_over": None, "volgende_bui_over": 40,
           "regencorrectie": {"vorm": "geen", "toegepast": False, "reden": "14 van de 15 uitkomsten nodig"}})
    assert a["gecorrigeerd"] is False
    assert a["correctie_vorm"] == "geen"
    assert a["uitleg"] == "14 van de 15 uitkomsten nodig"
    assert a["volgende_bui"] is True
