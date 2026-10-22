"""0.58.2: rust in de windmeldingen.

22-10 18:51 "Veel meldingen van storm nu ... oplossen": drie vooruitblik-
meldingen kort na elkaar (vandaag 60 precies op de drempel in het lopende uur,
morgen 63 Open-Meteo, morgen 77 KNMI).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

import windvooruitblik as W  # noqa: E402

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
TZ = ZoneInfo("Europe/Amsterdam")


def _om(stoten: dict):
    begin = datetime(2026, 10, 22, 0, 0)
    tijden, waarden = [], []
    for i in range(72):
        m = begin + timedelta(hours=i)
        tijden.append(m.strftime("%Y-%m-%dT%H:%M"))
        waarden.append(stoten.get(((m.date() - begin.date()).days, m.hour), 30.0))
    return {"time": tijden, "wind_gusts_10m": waarden}


def _melding(stoten, nu, gemeld, knmi=None):
    dagen = W.dagen(W.per_uur(_om(stoten), knmi, TZ), nu, 60)
    return W.te_melden(dagen, nu, gemeld, 60)


def test_vandaag_op_de_drempel_in_het_lopende_uur_niet():
    nu = datetime(2026, 10, 22, 17, 10, tzinfo=TZ)
    assert _melding({(0, 17): 60.0}, nu, {}) is None
    # ook met marge: het lopende uur telt niet
    assert _melding({(0, 17): 70.0}, nu, {}) is None
    # binnen het uur (18:00 is 50 minuten weg) ook niet
    assert _melding({(0, 18): 70.0}, nu, {}) is None
    assert _melding({(0, 19): 70.0}, nu, {})["dag"] == "vandaag"


def test_marge_boven_de_drempel():
    avond = datetime(2026, 10, 22, 18, 5, tzinfo=TZ)
    assert _melding({(1, 14): 63.0}, avond, {}) is None
    assert _melding({(1, 14): 64.4}, avond, {}) is None
    assert _melding({(1, 14): 65.0}, avond, {})["dag"] == "morgen"


def test_live_reeks_22_10_geeft_een_melding():
    nu = datetime(2026, 10, 22, 16, 30, tzinfo=TZ)
    gemeld = {}
    assert _melding({(0, 17): 60.0, (1, 14): 63.0}, nu, gemeld) is None
    avond = datetime(2026, 10, 22, 18, 5, tzinfo=TZ)
    assert _melding({(0, 17): 60.0, (1, 14): 63.0}, avond, gemeld) is None
    # KNMI 77 om 18:51: een melding
    laat = datetime(2026, 10, 22, 18, 51, tzinfo=TZ)
    knmi = [{"datetime": "2026-10-23T12:00:00+00:00", "native_wind_gust_speed": 77}]
    m = _melding({(1, 14): 63.0}, laat, gemeld, knmi)
    assert m["dag"] == "morgen" and m["max_kmh"] == 77 and m["bron"] == "knmi"
    gemeld[m["datum"]] = W.als_gemeld(m)
    assert gemeld == {"2026-10-23": {"klasse": 2, "kmh": 77}}
    # daarna 85: geen nieuwe melding (minder dan 15 meer)
    knmi[0]["native_wind_gust_speed"] = 85
    assert _melding({(1, 14): 63.0}, laat, gemeld, knmi) is None


def test_opschaling_15_kmh_of_klasse_3():
    avond = datetime(2026, 10, 22, 20, 0, tzinfo=TZ)
    gemeld = {"2026-10-23": {"klasse": 2, "kmh": 77}}
    assert _melding({(1, 14): 91.0}, avond, gemeld) is None
    assert _melding({(1, 14): 92.0}, avond, gemeld)["max_kmh"] == 92
    gemeld = {"2026-10-23": {"klasse": 2, "kmh": 90}}
    assert _melding({(1, 14): 100.0}, avond, gemeld)["klasse"] == 3
    gemeld = {"2026-10-23": {"klasse": 3, "kmh": 100}}
    assert _melding({(1, 14): 110.0}, avond, gemeld) is None


def test_vandaag_na_morgenmelding_alleen_bij_opschaling():
    ochtend = datetime(2026, 10, 23, 7, 0, tzinfo=TZ)
    gemeld = {"2026-10-23": {"klasse": 2, "kmh": 77}}
    assert _melding({(1, 14): 80.0}, ochtend, gemeld) is None
    assert _melding({(1, 14): 95.0}, ochtend, gemeld)["dag"] == "vandaag"


def test_oude_opslag_blijft_leesbaar():
    assert W.vorige({"2026-10-23": 2}, "2026-10-23", 60) == (2, 75.0)
    assert W.vorige({"2026-10-22": 1}, "2026-10-22", 60) == (1, 60.0)
    assert W.vorige({"2026-10-23": 3}, "2026-10-23", 60) == (3, 100.0)
    assert W.vorige({}, "2026-10-23", 60) is None
    # live opslag {'2026-10-22': 1, '2026-10-23': 2}: geen nieuwe melding bij 77-89
    avond = datetime(2026, 10, 22, 19, 0, tzinfo=TZ)
    live = {"2026-10-22": 1, "2026-10-23": 2}
    assert _melding({(1, 14): 77.0}, avond, live) is None
    assert _melding({(1, 14): 89.0}, avond, live) is None
    assert _melding({(1, 14): 90.0}, avond, live) is not None


def test_opslag_overleeft_json_herstart():
    gemeld = json.loads(json.dumps({"2026-10-23": W.als_gemeld(
        {"klasse": 2, "max_kmh": 77})}))
    avond = datetime(2026, 10, 22, 19, 0, tzinfo=TZ)
    assert _melding({(1, 14): 77.0}, avond, gemeld) is None
    assert W.gemeld_opschonen(gemeld, avond) == gemeld


def test_ingebouwd():
    coord = (ROOT / "coordinator.py").read_text(encoding="utf-8")
    assert "windvooruitblik.te_melden(overzicht, nu, self.windvooruitblik_gemeld, drempel)" in coord
    assert "windvooruitblik.als_gemeld(melding)" in coord
    assert "windstoten >= drempel - WIND_HYSTERESE" in coord
    notifier = (ROOT / "notifier.py").read_text(encoding="utf-8")
    assert "WIND_MIN_INTERVAL)" in notifier
    const = (ROOT / "const.py").read_text(encoding="utf-8")
    assert "WIND_HYSTERESE = 10.0" in const and "WIND_MIN_INTERVAL = 120" in const
    init = (ROOT / "__init__.py").read_text(encoding="utf-8")
    assert '"windvooruitblik": dict(meteo.windvooruitblik_gemeld)' in init


def _controleer_wind_los():
    """_controleer_wind uit coordinator.py, zonder Home Assistant uitgevoerd."""
    import ast
    import textwrap
    bron = (ROOT / "coordinator.py").read_text(encoding="utf-8")
    boom = ast.parse(bron)
    for knoop in ast.walk(boom):
        if isinstance(knoop, ast.FunctionDef) and knoop.name == "_controleer_wind":
            code = textwrap.dedent(ast.get_source_segment(bron, knoop))
            break
    ns = {"CONF_WIND_THRESHOLD": "x", "DEFAULT_WIND_THRESHOLD": 60, "WIND_HYSTERESE": 10.0,
          "EVENT_WIND": "stormchase_wind"}
    exec(code, ns)
    return ns["_controleer_wind"]


class _Coord:
    def __init__(self):
        self._was_winderig = False
        self.stats = None
        self.events = []
        self.hass = type("H", (), {})()
        self.hass.bus = type("B", (), {"async_fire": lambda _s, e, d: self.events.append(d)})()

    def _opt(self, _k, standaard):
        return standaard


def test_live_hysterese():
    controleer = _controleer_wind_los()
    c = _Coord()
    for stoot in (61, 58, 62, 55, 64, 59, 61):
        controleer(c, stoot, "model")
    assert len(c.events) == 1
    controleer(c, 49, "model")          # onder 60 - 10: weer rustig
    assert c._was_winderig is False
    controleer(c, 62, "model")
    assert len(c.events) == 2


def test_versie():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "0.58.2"
    changelog = (ROOT.parents[1] / "CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.index("## [0.58.2]") < changelog.index("## [0.58.1]")
