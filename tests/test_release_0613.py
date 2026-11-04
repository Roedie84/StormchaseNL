"""0.61.3 (L-SC-031): de ringen tonen geen 0 als Blitzortung eruit ligt.

03-11: teller onbeschikbaar, ringen 0/0/0. De sensoren worden onbekend; de
waarschuwingslogica blijft `data.rings` lezen.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
COORD = (BRON / "coordinator.py").read_text(encoding="utf-8")
SENSOR = (BRON / "sensor.py").read_text(encoding="utf-8")


def _functie(bron: str, naam: str) -> str:
    boom = ast.parse(bron)
    for knoop in ast.walk(boom):
        if isinstance(knoop, (ast.FunctionDef, ast.AsyncFunctionDef)) and knoop.name == naam:
            return ast.get_source_segment(bron, knoop)
    raise AssertionError(naam)


def _blitz_meet(staat, teller="sensor.teller", afstand=None):
    code = _functie(COORD, "_blitz_meet")
    regels = code.splitlines()
    code = "\n".join([regels[0]] + [r[4:] for r in regels[1:]])
    ruimte = {
        "CONF_COUNTER_SENSOR": "t",
        "CONF_DISTANCE_SENSOR": "a",
        "blitzortung_fout": lambda t: None
        if t != "unavailable" and t is not None
        else "fout",
    }
    exec(code, ruimte)

    class S:
        state = staat

    class Z:
        def __init__(self):
            self.hass = type("H", (), {"states": type("St", (), {"get": staticmethod(lambda e: None if staat is None else S)})})()

        def _opt(self, sleutel):
            return {"t": teller, "a": afstand}[sleutel]

    return ruimte["_blitz_meet"](Z())


def test_teller_onbeschikbaar_meet_niet():
    assert _blitz_meet("unavailable") is False
    assert _blitz_meet(None) is False


def test_teller_op_0_of_unknown_meet():
    assert _blitz_meet("0") is True
    assert _blitz_meet("unknown") is True


def test_zonder_ingestelde_teller_niets_te_zeggen():
    assert _blitz_meet("unavailable", teller=None, afstand=None) is True


def test_afstandssensor_is_de_terugval():
    assert _blitz_meet("unavailable", teller=None, afstand="sensor.afstand") is False


def test_inslagmarkers_gaan_voor_de_teller():
    assert "ringen_gemeten=bool(markers) or self._blitz_meet()" in COORD


def test_ringsensor_wordt_onbekend_en_rings_blijven():
    code = SENSOR[SENSOR.index("Aantal inslagen binnen deze ring"):]
    code = code[: code.index("class MeteoSensor")]
    assert re.search(r"if not self\.coordinator\.data\.ringen_gemeten:\s+return None", code)
    assert "self.coordinator.data.rings.get(self._bound)" in code
    assert "geen meting" in code


def test_waarschuwingslogica_leest_ringen_ongewijzigd():
    assert '"inslagen": data.rings' in COORD
    assert "self._storm.data.rings.get(far, 0)" in SENSOR
