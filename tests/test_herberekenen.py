"""0.41.0: inslagen vanaf de actieve locatie en binaire sensoren zonder unknown.

Live op 7 oktober: actieve locatie de iPhone-tracker, Blitzortung meet vanaf
vaste coordinaten 13,6 km verderop. Zonder geo_location-entiteiten werd de
afstand van de bronsensor ongewijzigd overgenomen. En onweer_nabij en
onweer_nadert stonden op unknown zolang er geen inslag was.
"""

import ast
from pathlib import Path

import pytest

from indices import herbereken_vanaf, peiling, verplaats

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"

EIBERGEN = (52.10, 6.65)


def test_verplaats_en_peiling_zijn_elkaars_omgekeerde():
    punt = verplaats(*EIBERGEN, 90.0, 20.0)
    assert peiling(*EIBERGEN, *punt) == pytest.approx(90.0, abs=0.2)


def test_zelfde_punt_geeft_de_bronwaarde_terug():
    km, richting = herbereken_vanaf(EIBERGEN, EIBERGEN, 12.0, 45.0)
    assert km == pytest.approx(12.0, abs=0.1)
    assert richting == pytest.approx(45.0, abs=0.3)


def test_inslag_bij_de_tracker_is_dichtbij_ook_als_de_bron_ver_meet():
    """Bron 13,6 km naar het westen; de inslag ligt precies op de tracker."""
    tracker = verplaats(*EIBERGEN, 270.0, 13.6)
    km, _ = herbereken_vanaf(EIBERGEN, tracker, 13.6, 270.0)
    assert km < 0.2


def test_inslag_aan_de_andere_kant_telt_de_afwijking_op():
    tracker = verplaats(*EIBERGEN, 270.0, 13.6)
    km, richting = herbereken_vanaf(EIBERGEN, tracker, 10.0, 90.0)
    assert km == pytest.approx(23.6, abs=0.2)
    assert richting == pytest.approx(90.0, abs=1.0)


def _is_on(klasse: str) -> str:
    boom = ast.parse((BRON / "binary_sensor.py").read_text(encoding="utf-8"))
    for knoop in ast.walk(boom):
        if isinstance(knoop, ast.ClassDef) and knoop.name == klasse:
            for f in knoop.body:
                if isinstance(f, ast.FunctionDef) and f.name == "is_on":
                    return ast.unparse(f)
    raise AssertionError(klasse)


@pytest.mark.parametrize(
    "klasse,veld",
    [("StormNearbyBinarySensor", "distance"), ("StormApproachingBinarySensor", "speed")],
)
def test_geen_inslag_is_off_en_niet_unknown(klasse, veld):
    bron = _is_on(klasse)
    assert f"data.{veld} is None:\n        return False" in bron
