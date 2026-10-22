"""0.58.0: naderingsreeks per cel (L-SC-013) en metingen boven het model.

22-10: de naderingssnelheid kwam op 138 km/u (eerder 222) tegen werkelijk
~35 km/u, doordat afstanden van twee cellen in een regressie belandden. En
14:22-15:56 stond het waarschuwingsniveau op groen en de verwachting op "Geen
onweer verwacht" terwijl onweer_nadert drie keer aan stond, de dichtstbijzijnde
inslag op 23,0 km lag en er 372 inslagen binnen 50 km vielen.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

from cel import naar_graden, volg_cellen  # noqa: E402
from indices import (  # noqa: E402
    RANG_GEEN,
    RANG_KLEIN,
    RANG_ONWEER,
    RANG_ZWAAR,
    TEKST_GEMETEN,
    gemeten_onweer,
    niveau_met_metingen,
    verwachting_met_metingen,
)
from nadering import Naderingstrend  # noqa: E402

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
IK = (52.06, 6.64)


def _trend():
    return Naderingstrend(900, 3)


# --- L-SC-013: naderingsreeks per cel ------------------------------------


def test_celwissel_begint_reeks_opnieuw():
    tr = _trend()
    # cel 1 nadert met ~36 km/u: 0,6 km per minuut
    for i in range(5):
        tr.volg_cel(1)
        tr.bij(i * 60.0, 40.0 - 0.6 * i, i)
    assert tr.snelheid(240.0) == pytest.approx(36, abs=0.5)
    # andere cel ligt 15 km dichterbij: zonder wissel gaf dat een enorme sprong
    assert tr.volg_cel(2) is True
    assert not tr.metingen
    assert tr.snelheid(300.0) is None
    tr.bij(300.0, 22.0, 5)
    tr.bij(360.0, 21.4, 6)
    assert tr.snelheid(360.0) is None   # te weinig punten van de nieuwe cel
    tr.bij(420.0, 20.8, 7)
    assert tr.snelheid(420.0) == pytest.approx(36, abs=0.5)
    assert tr.celwissels == 1


def test_zonder_wissel_222_kmh_niet_meer_mogelijk():
    """Vroeger: 40 -> 39,4 -> 25 km in twee minuten gaf honderden km/u."""
    tr = _trend()
    tr.volg_cel(1)
    tr.bij(0.0, 40.0, 0)
    tr.bij(60.0, 39.4, 1)
    tr.volg_cel(2)
    tr.bij(120.0, 25.0, 2)
    assert tr.snelheid(120.0) is None


def test_zelfde_cel_houdt_reeks():
    tr = _trend()
    for i in range(4):
        assert tr.volg_cel(7) is False
        tr.bij(i * 60.0, 30.0 - 0.5 * i, i)
    assert len(tr.metingen) == 4
    assert tr.snelheid(180.0) == pytest.approx(30, abs=0.5)


def test_zwaartepuntsprong_begint_reeks_opnieuw():
    tr = _trend()
    for i in range(4):
        tr.volg_cel(3)
        tr.bij(i * 60.0, 30.0 - 0.5 * i, i)
    assert tr.volg_cel(3, herstart=True) is True
    assert not tr.metingen and tr.snelheid(240.0) is None


def test_geen_cel_laat_reeks_staan():
    tr = _trend()
    for i in range(4):
        tr.volg_cel(1)
        tr.bij(i * 60.0, 30.0 - 0.5 * i, i)
    assert tr.volg_cel(None) is False
    assert len(tr.metingen) == 4
    assert tr.volg_cel(1) is False


def test_eerste_cel_wist_niets():
    tr = _trend()
    tr.bij(0.0, 30.0, 0)
    assert tr.volg_cel(5) is False
    assert len(tr.metingen) == 1


def test_cel_overleeft_herstart():
    tr = _trend()
    tr.volg_cel(4)
    tr.bij(0.0, 30.0, 0)
    opslag = tr.naar_opslag()
    assert opslag["cel"] == 4
    nieuw = _trend()
    nieuw.herstel(opslag, 10.0)
    assert nieuw.volg_cel(4) is False
    assert len(nieuw.metingen) == 1
    nieuw.herstel({"metingen": [], "cel": [1]}, 10.0)
    assert nieuw.volg_cel(9) is False   # ongeldige cel telt als geen


def test_volg_cellen_meldt_herstart():
    sporen: list = []
    volgend = 1
    for stap in range(35):
        t = stap * 10.0
        x = -40 + 67 * t / 3600 + (15 if stap == 34 else 0)
        cellen, sporen, volgend = volg_cellen([naar_graden(x, 0, *IK)], sporen, *IK, t, volgend)
        if stap == 0:
            assert cellen[0]["herstart"] is True    # nieuwe cel
        elif stap < 34:
            assert cellen[0]["herstart"] is False
    assert cellen[0]["id"] == 1 and cellen[0]["herstart"] is True   # sprong


def test_coordinator_volgt_cel_voor_reeks():
    bron = (ROOT / "coordinator.py").read_text(encoding="utf-8")
    i_cel = bron.index("self._nadering.volg_cel(")
    i_bij = bron.index("self._nadering.bij(nu_trend, distance, last_strike)")
    assert i_cel < i_bij
    assert 'cellen[0].get("id"), bool(cellen[0].get("herstart"))' in bron


# --- metingen boven het model --------------------------------------------


def test_gemeten_onweer():
    assert gemeten_onweer(True, None)
    assert gemeten_onweer(False, 23.0)          # 22-10: dichtstbij 23,0 km
    assert gemeten_onweer(None, 25.0)
    assert not gemeten_onweer(False, 25.1)
    assert not gemeten_onweer(False, None)


def test_niveau_minstens_geel():
    assert niveau_met_metingen("groen", True) == "geel"
    assert niveau_met_metingen(None, True) == "geel"
    assert niveau_met_metingen("oranje", True) == "oranje"
    assert niveau_met_metingen("rood", True) == "rood"
    assert niveau_met_metingen("groen", False) == "groen"
    assert niveau_met_metingen(None, False) == "groen"


def test_verwachting_wijkt_voor_metingen():
    assert verwachting_met_metingen("Geen onweer verwacht", RANG_GEEN, True) == (TEKST_GEMETEN, True)
    assert verwachting_met_metingen("Kleine kans op onweer", RANG_KLEIN, True) == (TEKST_GEMETEN, True)
    assert verwachting_met_metingen("Kans op onweer", RANG_ONWEER, True) == ("Kans op onweer", False)
    assert verwachting_met_metingen("Kans op zwaar onweer", RANG_ZWAAR, True)[1] is False
    assert verwachting_met_metingen("Geen onweer verwacht", RANG_GEEN, False) == ("Geen onweer verwacht", False)
    assert verwachting_met_metingen(None, None, True) == (None, False)
    assert TEKST_GEMETEN == "Onweer in de buurt (gemeten)"


def test_sensoren_luisteren_naar_storm():
    bron = (ROOT / "sensor.py").read_text(encoding="utf-8")
    assert "ForecastSensor(meteo, entry, storm)" in bron
    assert "AlertSensor(waarschuwingen, entry, storm)" in bron
    assert bron.count("self._storm.async_add_listener(self.async_write_ha_state)") >= 3
    assert '"overstemd_door_metingen": overstemd' in bron
    assert '"niveau_waarschuwingen"' in bron


def test_dashboard_kleurt_gemeten_geel():
    js = (ROOT / "www" / "stormchase-strategy.js").read_text(encoding="utf-8")
    assert 'l.includes("gemeten")' in js
    assert 'attr(vw, "overstemd_door_metingen")' in js


def test_versie():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert tuple(int(x) for x in manifest["version"].split(".")) >= (0, 58, 0)
