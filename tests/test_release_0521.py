"""0.52.1: afstandsreeks alleen bij een nieuwe afstand, en over een herstart."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

try:
    import homeassistant.util.dt  # noqa: F401
except ModuleNotFoundError:  # zonder HA-installatie: alleen utcnow is nodig
    import types

    _dt = types.ModuleType("homeassistant.util.dt")
    _dt.utcnow = lambda: datetime.now(timezone.utc)
    for naam, mod in (
        ("homeassistant", types.ModuleType("homeassistant")),
        ("homeassistant.util", types.ModuleType("homeassistant.util")),
        ("homeassistant.util.dt", _dt),
    ):
        sys.modules.setdefault(naam, mod)
    sys.modules["homeassistant.util"].dt = _dt

import stats as stats_mod  # noqa: E402
from stats import GESCHIEDENIS, Statistieken  # noqa: E402

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
START = datetime(2026, 10, 10, 18, 29, 48, tzinfo=timezone.utc)


class _Klok:
    def __init__(self, monkeypatch):
        self.nu = START
        monkeypatch.setattr(stats_mod.dt_util, "utcnow", lambda: self.nu)

    def verder(self, seconden: float) -> None:
        self.nu += timedelta(seconds=seconden)


def _json(data):
    return json.loads(json.dumps(data))


class TestAlleenNieuweAfstand:
    def test_herhaling_van_10_s_geeft_geen_nieuw_punt(self, monkeypatch):
        # 10-10 22:29-22:59: elke tien seconden 73,6 km, dan 74,3 km.
        klok = _Klok(monkeypatch)
        s = Statistieken()
        for _ in range(180):
            s.noteer_meting(73.6, None)
            klok.verder(10)
        s.noteer_meting(74.3, None)
        reeks = list(s.afstandsreeks)
        assert [p["afstand"] for p in reeks] == [73.6, 74.3]
        # 'tot' laat zien hoe lang de afstand bleef staan
        assert reeks[0]["op"] == START.isoformat()
        assert reeks[0]["tot"] == (START + timedelta(seconds=1790)).isoformat()

    def test_nieuwe_snelheid_is_wel_een_punt(self, monkeypatch):
        _Klok(monkeypatch)
        s = Statistieken()
        s.noteer_meting(80.0, None)
        s.noteer_meting(80.0, 9.5)
        s.noteer_meting(80.0, 9.5)
        assert [(p["afstand"], p["snelheid"]) for p in s.afstandsreeks] == [
            (80.0, None),
            (80.0, 9.5),
        ]

    def test_geen_afstand_of_rommel_geen_punt(self, monkeypatch):
        _Klok(monkeypatch)
        s = Statistieken()
        s.noteer_meting(None, 3.0)
        s.noteer_meting(True, None)
        assert not s.afstandsreeks
        s.noteer_meting(50.0, "snel")
        assert list(s.afstandsreeks)[0]["snelheid"] is None

    def test_reeks_beslaat_nu_een_hele_cel(self, monkeypatch):
        # 180 plaatsen gaan niet meer op aan een half uur herhalingen
        klok = _Klok(monkeypatch)
        s = Statistieken()
        for i in range(400):
            s.noteer_meting(round(93 - i * 0.05, 1), None)
            klok.verder(10)
        assert len(s.afstandsreeks) <= GESCHIEDENIS
        assert len({p["afstand"] for p in s.afstandsreeks}) == len(s.afstandsreeks)

    def test_nieuw_punt_plant_het_bewaren(self, monkeypatch):
        _Klok(monkeypatch)
        s = Statistieken()
        gepland = []
        s._bij_wijziging = lambda: gepland.append(1)
        s.noteer_meting(60.0, None)
        s.noteer_meting(60.0, None)
        s.noteer_meting(59.0, None)
        assert len(gepland) == 2


class TestOverEenHerstart:
    def test_heen_en_terug(self, monkeypatch):
        klok = _Klok(monkeypatch)
        s = Statistieken()
        for afstand in (93.0, 88.2, 81.0):
            s.noteer_meting(afstand, 57.0)
            klok.verder(60)
        terug = Statistieken()
        terug.herstel_reeks(_json(s.reeks_naar_opslag()))
        assert list(terug.afstandsreeks) == list(s.afstandsreeks)

    def test_bewaard_komt_voor_wat_na_de_start_binnenkwam(self, monkeypatch):
        klok = _Klok(monkeypatch)
        oud = Statistieken()
        oud.noteer_meting(80.0, None)
        bewaard = _json(oud.reeks_naar_opslag())
        klok.verder(120)
        nieuw = Statistieken()
        nieuw.noteer_meting(46.0, None)
        nieuw.herstel_reeks(bewaard)
        assert [p["afstand"] for p in nieuw.afstandsreeks] == [80.0, 46.0]

    def test_rommel_wordt_overgeslagen(self):
        s = Statistieken()
        s.herstel_reeks(
            [
                {"op": "x", "afstand": 5.0},
                {"op": START.isoformat(), "afstand": "ver"},
                {"op": START.isoformat(), "afstand": False},
                "punt",
                {"op": START.isoformat(), "afstand": 12.5, "snelheid": "hard"},
            ]
        )
        assert list(s.afstandsreeks) == [
            {"op": START.isoformat(), "afstand": 12.5, "snelheid": None, "tot": START.isoformat()}
        ]
        s.herstel_reeks({"geen": "lijst"})
        assert len(s.afstandsreeks) == 1

    def test_reeks_staat_in_de_opslag(self):
        init = (BRON / "__init__.py").read_text(encoding="utf-8")
        assert '"afstandsreeks": stats.reeks_naar_opslag()' in init
        assert 'stats.herstel_reeks(bewaarde_bron.get("afstandsreeks"))' in init
        assert init.index("stats.herstel_reeks(") < init.index("stats.koppel_historie(")
