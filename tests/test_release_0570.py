"""0.57.0: windvooruitblik - harde wind van tevoren melden.

21-10, met storm Austen op komst voor vrijdag: "hoe gaat de storm chase app
daarmee om". De windmelding keek alleen naar nu; een stormdag kwam pas binnen
via een KNMI-code of op het moment zelf.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

import windvooruitblik as W  # noqa: E402

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
TZ = ZoneInfo("Europe/Amsterdam")
NU = datetime(2026, 10, 22, 9, 30, tzinfo=TZ)   # donderdag


def _open_meteo(stoten: dict):
    """Uren vanaf donderdag 22-10 00:00 lokaal; stoten {(dag offset, uur): km/u}, rest 30."""
    begin = datetime(2026, 10, 22, 0, 0)
    tijden, waarden = [], []
    for i in range(72):
        m = begin + timedelta(hours=i)
        tijden.append(m.strftime("%Y-%m-%dT%H:%M"))
        waarden.append(stoten.get(((m.date() - begin.date()).days, m.hour), 30.0))
    return {"time": tijden, "wind_gusts_10m": waarden}


def test_hoogste_van_open_meteo_en_knmi():
    om = _open_meteo({(1, 14): 55.0})
    knmi = [{"datetime": "2026-10-23T12:00:00+00:00", "native_wind_gust_speed": 72}]   # 14:00 lokaal
    uren = W.per_uur(om, knmi, TZ)
    assert uren[datetime(2026, 10, 23, 14, tzinfo=TZ)] == (72.0, "knmi")
    om = _open_meteo({(1, 14): 80.0})
    assert W.per_uur(om, knmi, TZ)[datetime(2026, 10, 23, 14, tzinfo=TZ)] == (80.0, "open-meteo")


def test_dagoverzicht_met_tijdvak_boven_de_drempel():
    om = _open_meteo({(1, 13): 62.0, (1, 14): 78.0, (1, 15): 65.0})
    dagen = W.dagen(W.per_uur(om, None, TZ), NU, 60)
    morgen = next(d for d in dagen if d["dag"] == "morgen")
    assert morgen["max_kmh"] == 78 and morgen["piek_om"] == "14:00"
    assert (morgen["boven_drempel_van"], morgen["boven_drempel_tot"]) == ("13:00", "16:00")
    assert morgen["uren_boven_drempel"] == 3 and morgen["klasse"] == 2
    # vandaag: alleen de uren die nog komen
    vandaag = dagen[0]
    assert vandaag["dag"] == "vandaag" and vandaag["klasse"] == 0


def test_klassen():
    assert W.klasse(59, 60) == 0
    assert W.klasse(60, 60) == 1
    assert W.klasse(75, 60) == 2
    assert W.klasse(105, 60) == 3
    assert W.klasse(85, 80) == 1     # drempel boven 75: geen tussenklasse


def test_morgen_pas_de_avond_ervoor():
    om = _open_meteo({(1, 14): 78.0})
    dagen = W.dagen(W.per_uur(om, None, TZ), NU, 60)
    assert W.te_melden(dagen, NU, {}) is None
    avond = NU.replace(hour=18, minute=5)
    dagen = W.dagen(W.per_uur(om, None, TZ), avond, 60)
    melding = W.te_melden(dagen, avond, {})
    assert melding["dag"] == "morgen"


def test_vandaag_direct_en_een_keer_per_klasse():
    om = _open_meteo({(0, 15): 66.0})
    dagen = W.dagen(W.per_uur(om, None, TZ), NU, 60)
    melding = W.te_melden(dagen, NU, {})
    assert melding["dag"] == "vandaag" and melding["klasse"] == 1
    gemeld = {melding["datum"]: melding["klasse"]}
    assert W.te_melden(dagen, NU, gemeld) is None
    # opgeschaald naar 80: opnieuw
    om = _open_meteo({(0, 15): 80.0})
    dagen = W.dagen(W.per_uur(om, None, TZ), NU, 60)
    assert W.te_melden(dagen, NU, gemeld)["klasse"] == 2


def test_overmorgen_nooit():
    om = _open_meteo({(2, 14): 90.0})
    avond = NU.replace(hour=20)
    dagen = W.dagen(W.per_uur(om, None, TZ), avond, 60)
    assert W.te_melden(dagen, avond, {}) is None


def test_berichttekst():
    d = {"datum": "2026-10-23", "dag": "morgen", "max_kmh": 78, "piek_om": "14:00", "bron": "knmi",
         "boven_drempel_van": "13:00", "boven_drempel_tot": "16:00", "klasse": 2}
    titel, tekst = W.bericht(d, 60)
    assert titel == "Storm op komst"
    assert tekst == ("Krachtige windstoten verwacht morgen (vr 23-10): tot 78 km/u rond 14:00, "
                     "boven 60 km/u van 13:00 tot 16:00 (KNMI).")


def test_gemeld_opschonen():
    assert W.gemeld_opschonen({"2026-10-21": 2, "2026-10-22": 1, "2026-10-23": 1}, NU) == {
        "2026-10-22": 1, "2026-10-23": 1}


def test_ingebouwd():
    coord = (ROOT / "coordinator.py").read_text(encoding="utf-8")
    assert '"windvooruitblik": self._windvooruitblik(hourly),' in coord
    assert "EVENT_WIND_OUTLOOK" in coord
    notifier = (ROOT / "notifier.py").read_text(encoding="utf-8")
    assert "async_listen(EVENT_WIND_OUTLOOK, self._handle_wind_outlook)" in notifier
    init = (ROOT / "__init__.py").read_text(encoding="utf-8")
    assert '"windvooruitblik": dict(meteo.windvooruitblik_gemeld)' in init
    assert "meteo.knmi_bron = waarschuwingen" in init
    assert 'key="wind_outlook"' in (ROOT / "sensor.py").read_text(encoding="utf-8")
    assert "_regel_wind_vooruit()" in (ROOT / "briefing.py").read_text(encoding="utf-8")
