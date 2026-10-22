"""0.56.1 (L-SC-012): passage afrekenen ook als de cel een nieuw kenmerk kreeg.

17-10: drie passagevoorspellingen (42,4 / 39,2 km) zonder gemeten afstand,
terwijl de inslagen op 36-42 km lagen: de cel was opgeknipt en had een nieuw
kenmerk, en de nameting zocht alleen het oude.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

from validatie import OPVOLGER_KM, Validatie  # noqa: E402

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
LAT, LON = 52.06, 6.64


def _cel(kenmerk, dlat=0.0, afstand=40.0):
    return {"id": kenmerk, "latitude": LAT + dlat, "longitude": LON, "afstand": afstand}


def _open_passage(val, kenmerk=7):
    val.voorspel("passage", 0.0, 10, {"verwachte_afstand": 42.4, "cel": kenmerk})


def test_zelfde_cel_blijft_voorgaan():
    val = Validatie()
    _open_passage(val)
    val.volg_passagecel([_cel(7), _cel(8, 0.05)], {7: (LAT, LON)})
    assert "opvolgers" not in val.open["passage"]
    assert val.passage_meting({7: 38.0, 8: 30.0}) == (38.0, "zelfde cel")


def test_opvolger_na_kenmerkwissel_levert_afstand():
    val = Validatie()
    _open_passage(val)
    laatste = {7: (LAT, LON)}
    # cel 7 is weg; cel 9 duikt ~5,5 km verder op, cel 10 ver weg (~55 km)
    val.volg_passagecel([_cel(9, 0.05), _cel(10, 0.5)], laatste)
    assert val.open["passage"]["opvolgers"] == [9]
    afstand, via = val.passage_meting({9: 39.0, 10: 12.0})
    assert (afstand, via) == (39.0, "opvolger")
    val.passage_afgerond(10 * 60, afstand, via)
    uitkomst = val.uitkomsten[-1]
    assert uitkomst["uitgekomen"] is True
    assert uitkomst["werkelijke_afstand_km"] == 39.0
    assert uitkomst["afwijking_km"] == -3.4
    assert uitkomst["gemeten_via"] == "opvolger"
    assert uitkomst["raak"] is True


def test_ver_weg_is_geen_opvolger():
    val = Validatie()
    _open_passage(val)
    val.volg_passagecel([_cel(10, 0.5)], {7: (LAT, LON)})
    assert "opvolgers" not in val.open["passage"]
    assert val.passage_meting({10: 12.0}) == (None, None)
    assert OPVOLGER_KM == 15.0


def test_opvolger_van_opvolger():
    val = Validatie()
    _open_passage(val)
    laatste = {7: (LAT, LON)}
    val.volg_passagecel([_cel(9, 0.05)], laatste)
    laatste[9] = (LAT + 0.10, LON)  # cel 9 is doorgetrokken
    val.volg_passagecel([_cel(11, 0.18)], laatste)
    assert val.open["passage"]["opvolgers"] == [9, 11]


def test_opvolgers_overleven_opslag():
    val = Validatie()
    _open_passage(val)
    val.volg_passagecel([_cel(9, 0.05)], {7: (LAT, LON)})
    bewaard = val.naar_opslag()
    terug = Validatie(bewaard["uitkomsten"], bewaard["open"], bewaard["afgerond"])
    assert terug.open["passage"]["opvolgers"] == [9]
    assert val.wijzigingen == 2  # vastleggen + opvolger: aanleiding om op te slaan


def test_zonder_cel_in_de_ronde_toch_afrekenen():
    """De coordinator rekent af buiten `if cel:` (bron gecontroleerd)."""
    bron = (ROOT / "coordinator.py").read_text(encoding="utf-8")
    blok = bron.split("def _controleer_voorspellingen", 1)[1].split("def plan_validatie_opslag", 1)[0]
    assert "val.volg_passagecel(cellen, self._laatste_pos_per_cel)" in blok
    assert "if cel or afstand_passage is not None:" in blok
