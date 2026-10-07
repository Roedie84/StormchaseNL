"""0.42.0: bronstatus pas "hapert" bij een echte storing, en de laatst
bekende trackerpositie na een herstart.

Live op 7 oktober: de radar sloeg af en toe één minuut over en de
bronstatus sprong dan op "radar hapert". En bij elke herstart viel de
locatie ~10 s terug op thuis, omdat de tracker nog niet bestond.
"""

import ast
from datetime import timedelta
from pathlib import Path

import pytest

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"

try:
    import homeassistant.util.dt  # noqa: F401
except ModuleNotFoundError:  # zonder HA-installatie: alleen utcnow is nodig
    import sys
    import types
    from datetime import datetime, timezone

    _dt = types.ModuleType("homeassistant.util.dt")
    _dt.utcnow = lambda: datetime.now(timezone.utc)
    for naam, mod in (
        ("homeassistant", types.ModuleType("homeassistant")),
        ("homeassistant.util", types.ModuleType("homeassistant.util")),
        ("homeassistant.util.dt", _dt),
    ):
        sys.modules.setdefault(naam, mod)
    sys.modules["homeassistant.util"].dt = _dt

from stats import HAPERT_NA_MINUTEN, BronStatus  # noqa: E402


def test_een_gemiste_ronde_is_geen_storing():
    bron = BronStatus()
    bron.succes()
    bron.fout("time-out")
    assert not bron.hapert()


def test_twee_op_rij_wel():
    bron = BronStatus()
    bron.succes()
    bron.fout("time-out")
    bron.fout("time-out")
    assert bron.hapert()


def test_een_succes_zet_de_teller_terug():
    bron = BronStatus()
    bron.fout("a")
    bron.fout("b")
    bron.succes()
    assert bron.op_rij_mislukt == 0
    assert not bron.hapert()


def test_een_fout_na_lange_stilte_telt_meteen():
    bron = BronStatus()
    bron.succes()
    bron.fout("time-out")
    later = bron.laatste_succes + timedelta(minutes=HAPERT_NA_MINUTEN + 1)
    assert bron.hapert(later)


def test_nooit_gelukt_en_een_fout_hapert():
    bron = BronStatus()
    bron.fout("dns")
    assert bron.hapert()


def _functie(bestand, naam):
    boom = ast.parse((BRON / bestand).read_text(encoding="utf-8"))
    for knoop in ast.walk(boom):
        if isinstance(knoop, ast.FunctionDef) and knoop.name == naam:
            return ast.unparse(knoop)
    raise AssertionError(naam)


def test_de_tracker_valt_eerst_terug_op_de_laatst_bekende_positie():
    code = _functie("coordinator.py", "resolve_location")
    assert "laatst_bekende_positie" in code
    assert code.index("laatst_bekende_positie") < code.index("Tracker %s zonder coordinaten")


def test_de_positie_wordt_bewaard_over_een_herstart():
    init = (BRON / "__init__.py").read_text(encoding="utf-8")
    assert "POSITIE_SLEUTEL" in init and "async_load" in init
