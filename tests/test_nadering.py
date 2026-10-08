"""0.45.0 (L-SC-001): naderingssnelheid alleen uit nieuwe inslagafstanden.

Live op 7 oktober 21:15-22:37: onweer op 95 → 69 km, nooit binnen 50 km.
`onweer_nadert` ging 4× aan, waarvan 3× precies 15 minuten (het trendvenster),
en de aankomsttijd sprong zonder nieuwe inslag van 45 naar 1214 minuten. De
oude code gaf de regressie elke ronde van tien seconden een punt, ook zonder
nieuwe inslag. De replay hieronder gebruikt de echte reeksen uit de recorder.
"""

import ast
from datetime import datetime
from pathlib import Path

import pytest

from nadering import Naderingstrend, regressiesnelheid

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
VENSTER = 15 * 60
DEADZONE = 1.0
DAG = "2026-10-07T"


def _ts(hms: str) -> float:
    return datetime.fromisoformat(f"{DAG}{hms}+02:00").timestamp()


# sensor.stormchase_afstand (dichtstbijzijnde inslag, herberekend), None = unknown
AFSTAND = [
    ("21:15:47", 94.6), ("21:20:47", 83.2), ("21:39:53", None), ("21:40:33", 94.5),
    ("21:54:03", 90.3), ("22:09:11", 82.8), ("22:13:23", None), ("22:14:33", 81.5),
    ("22:21:53", 69.0), ("22:22:03", 68.8), ("22:49:28", None),
]
# Elke nieuwe inslag (wijziging van de Blitzortung-afstandssensor)
INSLAGEN = [
    "21:15:38", "21:15:39", "21:20:38", "21:40:23", "21:40:23.9", "21:54:01",
    "21:54:02", "22:01:46", "22:09:05", "22:11:50", "22:14:28", "22:14:30",
    "22:14:32", "22:14:33", "22:14:34", "22:14:35", "22:21:51", "22:21:52",
    "22:21:53", "22:21:55", "22:21:56", "22:21:57", "22:21:57.5", "22:21:58",
    "22:21:58.9", "22:21:59",
]


def _rondes():
    """Rondes van 10 s met (tijd, afstand, tijd nieuwste inslag)."""
    afst = [(_ts(t), d) for t, d in AFSTAND]
    slag = [_ts(t) for t in INSLAGEN]
    t, eind = afst[0][0], _ts("22:50:00")
    while t <= eind:
        d = [x for s, x in afst if s <= t][-1]
        k = max((s for s in slag if s <= t), default=None)
        yield t, d, k
        t += 10


def _oud(geschiedenis, nu, min_samples=4):
    """De berekening tot en met 0.44.0, letterlijk."""
    samples = [(t, d) for t, d in geschiedenis if t >= nu - VENSTER]
    if len(samples) < min_samples:
        return None
    return regressiesnelheid(samples)


def _replay(nieuw: bool):
    trend = Naderingstrend(VENSTER, 3)
    geschiedenis = []
    reeks = []
    for t, d, k in _rondes():
        if d is None:
            # Elke "unknown" in de reeks was een herstart van HA (de
            # Blitzortung-sensor ging tegelijk naar unavailable): lege reeks.
            trend.wis()
            geschiedenis.clear()
            reeks.append((t, d, k, None, None))
            continue
        if nieuw:
            trend.bij(t, d, k)
            v = trend.snelheid(t)
        else:
            if d is not None:
                geschiedenis.append((t, d))
            v = _oud(geschiedenis, t)
        eta = round(d / v * 60) if v and v > DEADZONE and d else None
        reeks.append((t, d, k, v, eta))
    return reeks


def _perioden(reeks):
    """Nadert-perioden als (begin, eind)."""
    uit, begin = [], None
    for t, _, _, v, _ in reeks:
        aan = v is not None and v > DEADZONE
        if aan and begin is None:
            begin = t
        elif not aan and begin is not None:
            uit.append((begin, t))
            begin = None
    if begin is not None:
        uit.append((begin, reeks[-1][0]))
    return uit


def _sprongen_zonder_inslag(reeks):
    """Aankomstwijzigingen tussen rondes zonder nieuwe inslag of afstand."""
    n = 0
    for (_, d0, k0, _, e0), (_, d1, k1, _, e1) in zip(reeks, reeks[1:]):
        if k0 == k1 and d0 == d1 and e0 is not None and e1 is not None and e0 != e1:
            n += 1
    return n


# --- de replay ------------------------------------------------------------


def test_replay_oud_reproduceert_wat_ha_toonde():
    """Controle op de replay zelf: dezelfde zaagtand als in de recorder."""
    reeks = _replay(nieuw=False)
    eta = {t: e for t, _, _, _, e in reeks}
    assert eta[_ts("21:20:47")] == 201
    assert eta[_ts("21:22:47")] == 41
    assert _sprongen_zonder_inslag(reeks) > 100
    # 3 van de 4 perioden duren het hele venster (± één ronde)
    duur = [round(e - b) for b, e in _perioden(reeks)]
    assert sum(1 for x in duur if abs(x - VENSTER) <= 10) >= 3


def test_replay_nieuw_geen_zaagtand():
    reeks = _replay(nieuw=True)
    assert _sprongen_zonder_inslag(reeks) == 0


def test_replay_nieuw_geen_15_minuten_artefact():
    duur = [round(e - b) for b, e in _perioden(_replay(nieuw=True))]
    assert not any(abs(x - VENSTER) <= 10 for x in duur)


def test_replay_nieuw_minder_nadert_tijd():
    oud = sum(e - b for b, e in _perioden(_replay(nieuw=False)))
    nieuw = sum(e - b for b, e in _perioden(_replay(nieuw=True)))
    assert nieuw < oud


# --- het gedrag van Naderingstrend ----------------------------------------


def test_herhaling_zonder_nieuwe_inslag_telt_niet():
    tr = Naderingstrend(VENSTER, 3)
    assert tr.bij(0, 50.0, "a") is True
    for t in range(10, 300, 10):
        assert tr.bij(t, 50.0, "a") is False
    assert len(tr.metingen) == 1


def test_nieuwe_inslag_op_dezelfde_afstand_telt_wel():
    tr = Naderingstrend(VENSTER, 3)
    tr.bij(0, 50.0, "a")
    assert tr.bij(60, 50.0, "b") is True


def test_verplaatsing_telt_ruis_niet():
    tr = Naderingstrend(VENSTER, 3)
    tr.bij(0, 50.0, "a")
    assert tr.bij(10, 50.2, "a") is False
    assert tr.bij(20, 50.6, "a") is True


def test_zonder_inslagtijd_telt_elke_afstandswijziging():
    tr = Naderingstrend(VENSTER, 3)
    tr.bij(0, 50.0)
    assert tr.bij(10, 50.0) is False
    assert tr.bij(20, 49.9) is True


def test_drie_nieuwe_metingen_geven_een_snelheid():
    tr = Naderingstrend(VENSTER, 3)
    tr.bij(0, 60.0, 1)
    tr.bij(120, 59.0, 2)
    assert tr.snelheid(120) is None
    tr.bij(240, 58.0, 3)
    assert tr.snelheid(240) == pytest.approx(30.0)


def test_snelheid_verandert_niet_als_oude_punten_uit_het_venster_vallen():
    tr = Naderingstrend(VENSTER, 3)
    for i, t in enumerate([0, 300, 600, 700]):
        tr.bij(t, 60.0 - i, i)
    v = tr.snelheid(700)
    waarden = {tr.snelheid(t) for t in range(700, 1500, 10)}
    # vastgehouden of vervallen, nooit een andere waarde
    assert waarden <= {v, None}


def test_snelheid_vervalt_als_er_te_weinig_steun_over_is():
    tr = Naderingstrend(VENSTER, 3)
    tr.bij(0, 60.0, 1)
    tr.bij(60, 59.0, 2)
    tr.bij(120, 58.0, 3)
    assert tr.snelheid(120 + 0) is not None
    assert tr.snelheid(VENSTER) is not None
    assert tr.snelheid(VENSTER + 1) is None


def test_geen_afstand_laat_de_reeks_ongemoeid():
    tr = Naderingstrend(VENSTER, 3)
    assert tr.bij(0, None, 1) is False
    assert not tr.metingen


def test_vlakke_reeks_is_nul_en_niet_min_nul():
    v = regressiesnelheid([(0, 50.0), (60, 50.0), (120, 50.0)])
    assert str(v) == "0.0"


def test_coordinator_gebruikt_naderingstrend_met_inslagtijd():
    tekst = (BRON / "coordinator.py").read_text(encoding="utf-8")
    assert "_speed_from_history" not in tekst
    assert "self._nadering.bij(nu_trend, distance, last_strike)" in tekst
    boom = ast.parse(tekst)
    assert boom is not None


def test_versie_0450():
    import json

    assert json.loads((BRON / "manifest.json").read_text())["version"] == "0.45.0"
