"""0.58.3 (L-SC-015): naderingsreeks opnieuw na een afstandsprong.

22-10 17:24-17:32: de dichtstbijzijnde inslag (~20 km) viel uit het venster,
de afstand sprong naar 90 km en de regressie gaf 7 minuten -124..-219 km/u.
17:44: een nieuwe, dichtere inslag van een andere bui (45,2 -> 38,0 km in 20 s)
gaf +108 km/u en een vals nadert-alarm van 17:41 tot 18:00. Nu begint de reeks
opnieuw bij meer dan 15 km verschil of meer dan 120 km/u tussen twee
opeenvolgende afstanden; de snelheid is dan onbekend tot er weer 3 punten zijn.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

from nadering import (  # noqa: E402
    MAX_STAPSNELHEID_KMH,
    SPRONG_KM,
    Naderingstrend,
    is_sprong,
)

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
VENSTER = 15 * 60
DEADZONE = 1.0


def _trend():
    return Naderingstrend(VENSTER, 3)


def _voer(trend, t0, reeks, stap=10.0):
    """Elke ronde (stap s) een nieuwe inslag met de gegeven afstand."""
    t = t0
    for afstand in reeks:
        trend.bij(t, afstand, inslag=t)
        t += stap
    return t


def test_grenzen():
    assert SPRONG_KM == 15.0
    assert MAX_STAPSNELHEID_KMH == 120.0


def test_sprong_omhoog_20_naar_90_km():
    tr = _trend()
    t = _voer(tr, 0.0, [20.0] * 30)          # 5 min stil op 20 km
    assert tr.snelheid(t) == 0.0
    tr.bij(t, 90.3, inslag=t)                # oude inslag valt uit het venster
    assert tr.sprongen == 1
    assert list(tr.metingen) == [(t, 90.3)]
    assert tr.snelheid(t) is None            # niet -64 .. -219 km/u
    # Met de echte vervolgstappen van 22-10 komt er geen -124..-219 meer
    t += 10
    tr.bij(t, 70.3, inslag=t)                # 20 km: weer een sprong
    assert tr.sprongen == 2
    t = _voer(tr, t + 10, [70.3] * 12)
    s = tr.snelheid(t)
    assert s is not None and abs(s) < 1.0


def test_sprong_omlaag_45_naar_38_km_geen_vals_alarm():
    tr = _trend()
    # 17:41:19-17:43:35 46,0 km; 17:43:45 45,2; 17:44:05 38,0 (echte reeks)
    t = _voer(tr, 0.0, [46.0] * 15)
    tr.bij(t, 45.2, inslag=t)
    assert tr.sprongen == 0                  # 0,8 km in 150 s: ~19 km/u
    t += 20
    tr.bij(t, 38.0, inslag=t)                # 7,2 km in 20 s: 1296 km/u
    assert tr.sprongen == 1
    assert tr.snelheid(t) is None
    # Daarna stil op 38 km: geen nadering, dus geen nadert-alarm
    t = _voer(tr, t + 10, [38.0] * 20)
    s = tr.snelheid(t)
    assert s is not None and s <= DEADZONE


def test_na_sprong_pas_snelheid_bij_minimum_punten():
    tr = _trend()
    t = _voer(tr, 0.0, [20.0] * 10)
    tr.bij(t, 60.0, inslag=t)
    assert tr.snelheid(t) is None
    tr.bij(t + 10, 59.9, inslag=t + 10)
    assert tr.snelheid(t + 10) is None       # 2 punten: te weinig
    tr.bij(t + 20, 59.8, inslag=t + 20)
    assert tr.snelheid(t + 20) is not None   # 3 punten: genoeg


def test_15_km_grens():
    punten = [(0.0, 20.0)]
    # Na een uur stil: 15 km is geen sprong (15 km/u), 15,1 wel
    assert not is_sprong(punten, 3600.0, 35.0)
    assert is_sprong(punten, 3600.0, 35.1)
    assert is_sprong(punten, 3600.0, 4.9)


def test_120_kmh_grens():
    punten = [(0.0, 40.0), (30.0, 40.0)]
    # 2 km in 60 s sinds de eerste 40,0 = precies 120 km/u: geen sprong
    assert not is_sprong(punten, 60.0, 38.0)
    # 2,1 km in 60 s = 126 km/u: sprong
    assert is_sprong(punten, 60.0, 37.9)
    # Ook verwijderend
    assert is_sprong(punten, 60.0, 42.1)


def test_120_kmh_grens_in_de_reeks():
    tr = _trend()
    t = _voer(tr, 0.0, [40.0] * 6)           # 0..50 s
    tr.bij(60.0, 38.0, inslag=60.0)          # 120 km/u: blijft
    assert tr.sprongen == 0
    tr2 = _trend()
    _voer(tr2, 0.0, [40.0] * 6)
    tr2.bij(60.0, 37.9, inslag=60.0)         # 126 km/u: opnieuw
    assert tr2.sprongen == 1
    assert len(tr2.metingen) == 1


def test_stapsnelheid_vanaf_eerste_punt_van_de_vorige_afstand():
    # De afstand blijft vaak minuten gelijk en zakt dan in een stap: dat is
    # niet 0,8 km in 10 s (288 km/u) maar 0,8 km sinds die afstand begon.
    punten = [(float(t), 46.0) for t in range(0, 150, 10)]
    assert not is_sprong(punten, 150.0, 45.2)


def test_normale_nadering_in_stappen_werkt_nog():
    # Bui op 40 km/u: elke 3 minuten 2 km dichter, nieuwe inslagen elke 10 s
    tr = _trend()
    reeks = []
    for stap in range(5):
        reeks += [50.0 - 2.0 * stap] * 18
    t = _voer(tr, 0.0, reeks)
    assert tr.sprongen == 0
    s = tr.snelheid(t)
    assert s is not None and 30.0 < s < 50.0


def test_normale_vloeiende_nadering_werkt_nog():
    # 0,1 km per 10 s = 36 km/u
    tr = _trend()
    t = _voer(tr, 0.0, [60.0 - 0.1 * i for i in range(60)])
    assert tr.sprongen == 0
    s = tr.snelheid(t)
    assert s is not None and abs(s - 36.0) < 1.0


def test_snelle_maar_echte_nadering_onder_120_blijft():
    # 100 km/u (rijdend naar de bui): 0,5 km per 18 s
    tr = _trend()
    t = _voer(tr, 0.0, [60.0 - 0.5 * i for i in range(20)], stap=18.0)
    assert tr.sprongen == 0
    s = tr.snelheid(t)
    assert s is not None and abs(s - 100.0) < 1.0


def test_coordinator_gebruikt_dezelfde_reeks():
    bron = (ROOT / "coordinator.py").read_text(encoding="utf-8")
    assert "self._nadering.bij(nu_trend, distance, last_strike)" in bron


def test_versie():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert tuple(int(x) for x in manifest["version"].split(".")) >= (0, 58, 3)
    changelog = (ROOT.parents[1] / "CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.index("## [0.58.3]") < changelog.index("## [0.58.2]")
