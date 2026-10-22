"""0.57.1 (L-SC-014): onmogelijke celsnelheden niet gebruiken.

22-10 14:20-15:34: de celsnelheid lag 37 % van de tijd boven 120 km/u (max
407) terwijl de bui werkelijk ~67 km/u ging. Het zwaartepunt van een snel
groeiende cel versprong en de regressie startte al na 2 minuten.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

from cel import (  # noqa: E402
    MAX_CELSNELHEID,
    MIN_SPOORDUUR,
    naar_graden,
    volg_cel,
    volg_cellen,
)

IK = (52.06, 6.64)


def _rij(snelheid_kmh, stappen, interval=10.0, start_km=-40.0):
    """Een cel die met vaste snelheid naar het oosten trekt, elke ronde een punt."""
    geschiedenis: list = []
    cel = None
    for stap in range(stappen):
        t = stap * interval
        x = start_km + snelheid_kmh * t / 3600
        cel = volg_cel([naar_graden(x, 0, *IK)], geschiedenis, *IK, t)
        geschiedenis = cel.pop("geschiedenis")
    return cel


def test_gewone_bui_blijft_gemeten():
    cel = _rij(67, 35)  # 340 s spoor
    assert cel["snelheid"] == pytest.approx(67, abs=1)
    assert cel["snelheid_ruw"] == cel["snelheid"]
    assert cel["richting"] == "O"
    assert cel["passage_over"] is not None


def test_te_kort_spoor_is_onbekend():
    cel = _rij(67, 20)  # 190 s: vroeger al een snelheid, nu niet
    assert cel["spoorduur"] < MIN_SPOORDUUR
    assert cel["snelheid"] is None
    assert cel["richting"] is None
    assert cel["passage_over"] is None


def test_boven_120_is_onbekend_maar_ruw_zichtbaar():
    # 150 km/u = 0,42 km per ronde: geen sprong, wel te snel
    cel = _rij(150, 35)
    assert cel["snelheid"] is None
    assert cel["richting"] is None
    assert cel["passage_over"] is None
    assert cel["snelheid_ruw"] == pytest.approx(150, abs=2)
    assert cel["snelheid_ruw"] > MAX_CELSNELHEID


def test_sprong_van_zwaartepunt_start_reeks_opnieuw():
    geschiedenis: list = []
    for stap in range(35):
        t = stap * 10.0
        x = -40 + 67 * t / 3600 + (15 if stap == 34 else 0)
        cel = volg_cel([naar_graden(x, 0, *IK)], geschiedenis, *IK, t)
        geschiedenis = cel.pop("geschiedenis")
    assert len(geschiedenis) == 1
    assert cel["snelheid"] is None
    assert cel["spoorduur"] == 0


def test_meerdere_cellen_houden_kenmerk_bij_sprong():
    sporen: list = []
    volgend = 1
    for stap in range(35):
        t = stap * 10.0
        x = -40 + 67 * t / 3600 + (15 if stap == 34 else 0)
        punt = naar_graden(x, 0, *IK)
        cellen, sporen, volgend = volg_cellen([punt], sporen, *IK, t, volgend)
        if stap == 33:
            assert cellen[0]["snelheid"] == pytest.approx(67, abs=1)
    assert cellen[0]["id"] == 1  # zelfde cel, nameting passage blijft kloppen
    assert len(sporen[0]["punten"]) == 1
    assert cellen[0]["snelheid"] is None
    assert cellen[0]["passage_over"] is None


def test_meerdere_cellen_te_snel_onbekend():
    sporen: list = []
    volgend = 1
    for stap in range(35):
        t = stap * 10.0
        punt = naar_graden(-40 + 200 * t / 3600, 0, *IK)
        cellen, sporen, volgend = volg_cellen([punt], sporen, *IK, t, volgend)
    assert cellen[0]["snelheid"] is None
    assert cellen[0]["richting"] is None
    assert cellen[0]["snelheid_ruw"] == pytest.approx(200, abs=3)


def test_lange_pauze_is_geen_sprong():
    """Na een stille periode mag een bui verder zijn getrokken dan 10 km."""
    from cel import is_sprong

    vorige = (0.0, IK[0], IK[1])
    lat, lon = naar_graden(25, 0, *IK)
    assert is_sprong(vorige, 60.0, lat, lon)
    assert not is_sprong(vorige, 1800.0, lat, lon)  # 25 km in 30 min = 50 km/u


def test_sensor_toont_ruwe_snelheid():
    bron = (Path(__file__).resolve().parents[1] / "custom_components" / "stormchase" / "sensor.py").read_text()
    assert '"snelheid_ruw": cel.get("snelheid_ruw")' in bron
    assert '"spoorduur_s": cel.get("spoorduur")' in bron


def test_versie():
    import json

    manifest = json.loads(
        (Path(__file__).resolve().parents[1] / "custom_components" / "stormchase" / "manifest.json").read_text()
    )
    assert tuple(int(x) for x in manifest["version"].split(".")) >= (0, 57, 1)
