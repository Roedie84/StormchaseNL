"""0.59.4 (L-SC-023): GPS-ruis van de eigen locatie is geen nadering.

Live op 25-10: inslag op 29,2 km om 14:10, daarna geen dichtere. De afstand
bewoog alleen door de tracker (29,2 → 29,6 → 29,2 km, steeds < 0,5 km per
stap), terwijl er verder weg wel nieuwe inslagen kwamen. Elke nieuwe inslag
gaf een punt met de verschoven afstand: -6,2 km/u om 14:36 ("trekt snel weg")
en +1,1..+2,3 km/u van 15:04 tot 15:14 ("nadert", waarschuwingsniveau geel,
aankomst 762-1593 min). Reeksen uit de recorder (sensor.stormchase_afstand);
de nieuwe inslagen zijn de wijzigingen van sensor.stormchase_actieve_markers.
"""

from datetime import datetime

from nadering import VERPLAATSING_KM, Naderingstrend, regressiesnelheid

VENSTER = 15 * 60
DEADZONE = 1.0
DAG = "2026-10-25T"


def _ts(hms: str) -> float:
    return datetime.fromisoformat(f"{DAG}{hms}+01:00").timestamp()


AFSTAND = [
    ("14:10:33", 29.2), ("14:32:54", 29.3), ("14:33:24", 29.4), ("14:33:54", 29.5),
    ("14:34:04", 29.6), ("15:01:42", 29.4), ("15:02:12", 29.3), ("15:03:32", 29.2),
    ("15:12:58", 29.3),
]
INSLAGEN = [
    "14:32:54", "14:33:04", "14:36:04", "14:36:14", "14:36:24", "14:36:44",
    "14:36:54", "14:37:14", "14:39:08", "14:39:18", "14:39:41", "14:40:31",
    "14:40:41", "14:41:41", "14:42:01", "14:42:41", "14:42:51", "14:43:01",
    "14:43:22", "14:43:32", "14:45:58", "14:46:18", "14:46:28", "14:46:38",
    "14:46:48", "14:46:58", "14:47:08", "14:48:48", "14:48:58", "14:49:38",
    "14:49:48", "14:49:58", "14:51:01", "14:51:11", "14:51:21", "14:51:41",
    "14:52:41", "14:53:04", "14:54:19", "14:54:29", "14:54:39", "14:54:49",
    "14:54:59", "14:55:19", "14:56:01", "14:56:33", "14:56:57", "14:57:47",
    "14:58:41", "14:58:51", "14:59:01", "14:59:31", "15:01:02", "15:02:32",
    "15:02:42", "15:04:12", "15:04:22", "15:04:32", "15:04:42", "15:04:52",
    "15:05:22", "15:06:24", "15:06:34", "15:06:44", "15:06:54", "15:07:04",
    "15:07:14", "15:07:34", "15:07:44", "15:08:46", "15:09:32", "15:10:25",
    "15:12:18", "15:12:28", "15:12:38", "15:13:38", "15:13:48", "15:14:13",
]


def _rondes():
    afst = [(_ts(t), d) for t, d in AFSTAND]
    slag = [_ts(t) for t in INSLAGEN]
    t, eind = afst[0][0], _ts("15:20:00")
    while t <= eind:
        d = [x for s, x in afst if s <= t][-1]
        k = max((s for s in slag if s <= t), default=None)
        yield t, d, k
        t += 10


def _snelheden_nieuw():
    tr = Naderingstrend(VENSTER, 3)
    uit = []
    for t, d, k in _rondes():
        tr.bij(t, d, k)
        uit.append(tr.snelheid(t))
    return uit


def _snelheden_oud():
    """Tot 0.59.3: elk nieuw punt met de ruwe afstand (zonder sprongen)."""
    punten, vorige_k, uit = [], None, []
    for t, d, k in _rondes():
        nieuw = not punten or k != vorige_k or abs(d - punten[-1][1]) >= VERPLAATSING_KM
        vorige_k = k
        if nieuw:
            punten.append((t, d))
        recent = [(s, x) for s, x in punten if s >= t - VENSTER]
        uit.append(regressiesnelheid(recent) if len(recent) >= 3 else None)
    return uit


def test_replay_oud_gaf_nadert_en_trekt_snel_weg():
    v = [x for x in _snelheden_oud() if x is not None]
    assert max(v) > DEADZONE
    assert min(v) < -3


def test_replay_nieuw_geen_nadert_of_wegtrekken_door_ruis():
    v = [x for x in _snelheden_nieuw() if x is not None]
    assert v
    assert all(abs(x) <= DEADZONE for x in v)


def test_echte_nadering_in_kleine_stappen_telt_nog():
    """0,3 km per inslag, elke minuut: samen boven de drempel → nadert."""
    tr = Naderingstrend(VENSTER, 3)
    for i in range(10):
        tr.bij(i * 60, 40.0 - 0.3 * i, i)
    v = tr.snelheid(9 * 60)
    assert v is not None and v > DEADZONE


def test_ruispunt_krijgt_de_vorige_afstand():
    tr = Naderingstrend(VENSTER, 3)
    tr.bij(0, 29.6, "a")
    assert tr.bij(30, 29.3, "b") is True
    assert tr.metingen[-1][1] == 29.6
    assert tr.bij(60, 28.9, "c") is True
    assert tr.metingen[-1][1] == 28.9


def test_zonder_inslagtijd_ongewijzigd():
    tr = Naderingstrend(VENSTER, 3)
    tr.bij(0, 50.0)
    assert tr.bij(20, 49.9) is True
    assert tr.metingen[-1][1] == 49.9
