"""0.58.1: windtijdvak leesbaar, en briefing en Weerwaarschuwing volgen metingen.

Live za 24-10: boven_drempel_van 00:00, tot 00:00, 4 uur. Een tot-tijd van
middernacht en losse uren lazen als "van 00:00 tot 00:00". En het weerbericht
en binary_sensor Weerwaarschuwing keken na 0.58.0 nog alleen naar het model en
de officiele waarschuwingen.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

import windvooruitblik as W  # noqa: E402
from indices import gemeten_uit_storm  # noqa: E402

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
TZ = ZoneInfo("Europe/Amsterdam")
NU = datetime(2026, 10, 22, 9, 30, tzinfo=TZ)   # donderdag


def _open_meteo(stoten: dict, standaard: float = 30.0):
    begin = datetime(2026, 10, 22, 0, 0)
    tijden, waarden = [], []
    for i in range(96):
        m = begin + timedelta(hours=i)
        tijden.append(m.strftime("%Y-%m-%dT%H:%M"))
        waarden.append(stoten.get(((m.date() - begin.date()).days, m.hour), standaard))
    return {"time": tijden, "wind_gusts_10m": waarden}


def _dag(om, offset=2):
    dagen = W.dagen(W.per_uur(om, None, TZ), NU, 60)
    datum = (NU + timedelta(days=offset)).date().isoformat()
    return next(d for d in dagen if d["datum"] == datum)


def test_losse_uren_geen_van_tot():
    # za 24-10 live: 00:00 en 23:00 boven, plus nog twee losse uren
    om = _open_meteo({(2, 0): 62.0, (2, 5): 61.0, (2, 12): 63.0, (2, 23): 72.0})
    d = _dag(om)
    assert d["uren_boven_drempel"] == 4
    assert d["aaneengesloten"] is False
    assert d["boven_drempel_van"] is None and d["boven_drempel_tot"] is None
    assert d["tijdvak"] == "4 uur boven 60 km/u"
    titel, tekst = W.bericht({**d, "dag": "vandaag"}, 60)
    assert "00:00 tot 00:00" not in tekst
    assert "tot 72 km/u rond 23:00, 4 uur boven 60 km/u" in tekst


def test_tot_middernacht():
    om = _open_meteo({(2, 20): 62.0, (2, 21): 65.0, (2, 22): 66.0, (2, 23): 64.0})
    d = _dag(om)
    assert d["aaneengesloten"] is True
    assert (d["boven_drempel_van"], d["boven_drempel_tot"]) == ("20:00", "24:00")
    assert d["tijdvak"] == "boven 60 km/u van 20:00 tot middernacht"


def test_hele_dag():
    om = _open_meteo({(2, h): 70.0 for h in range(24)})
    d = _dag(om)
    assert d["hele_dag"] is True
    assert d["tijdvak"] == "boven 60 km/u de hele dag"
    assert "de hele dag" in W.bericht(d, 60)[1]


def test_gewoon_tijdvak_blijft():
    om = _open_meteo({(1, 13): 62.0, (1, 14): 78.0, (1, 15): 65.0})
    d = _dag(om, 1)
    assert d["tijdvak"] == "boven 60 km/u van 13:00 tot 16:00"
    assert d["boven_drempel_tot"] == "16:00"


def test_geen_uren_geen_tijdvak():
    d = _dag(_open_meteo({}), 1)
    assert d["tijdvak"] is None
    assert W.tijdvak({"uren_boven_drempel": 0}, 60) is None


def test_briefing_en_dashboard_gebruiken_tijdvak():
    bron = (ROOT / "briefing.py").read_text(encoding="utf-8")
    assert "dag['tijdvak']" in bron
    assert "boven_drempel_van']}-" not in bron
    js = (ROOT / "www" / "stormchase-strategy.js").read_text(encoding="utf-8")
    assert "d.tijdvak" in js
    assert "esc(d.boven_drempel_van)" not in js


# --- briefing en Weerwaarschuwing volgen metingen -------------------------


def test_gemeten_uit_storm():
    assert gemeten_uit_storm(SimpleNamespace(speed=5.0, distance=40.0))
    assert gemeten_uit_storm(SimpleNamespace(speed=None, distance=23.0))
    assert not gemeten_uit_storm(SimpleNamespace(speed=0.5, distance=40.0))
    assert not gemeten_uit_storm(SimpleNamespace(speed=None, distance=None))
    assert not gemeten_uit_storm(None)


def test_weerwaarschuwing_volgt_metingen():
    bron = (ROOT / "binary_sensor.py").read_text(encoding="utf-8")
    assert '"alerts"], entry, storm' in bron
    assert 'bool(self.coordinator.data.get("aantal")) or self._gemeten()' in bron
    assert '"gemeten_onweer": self._gemeten()' in bron
    assert '"officieel": bool(data.get("aantal"))' in bron


def test_briefing_volgt_metingen():
    bron = (ROOT / "briefing.py").read_text(encoding="utf-8")
    assert "def _gemeten(self)" in bron
    assert "Waarschuwingsniveau geel: onweer gemeten" in bron
    assert "verwachting_met_metingen(" in bron and "TEKST_GEMETEN" in bron


def test_dashboard_onderscheidt_gemeten_geel():
    js = (ROOT / "www" / "stormchase-strategy.js").read_text(encoding="utf-8")
    assert js.count("const gemetenAlleen") == 2
    assert "Gemeten onweer" in js


def test_versie():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "0.58.1"
