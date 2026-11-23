"""0.64.0: een mistmelding alleen als een meting de mist bevestigt.

Ruud 23-11 17:24: "Mist melding terwijl er geen mist is?" Het model gaf
weercode 45/48; het station 87 % vocht, dauwpunt -1,4 bij 0,4 graden en
ruim 80 km zicht.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from mistcheck import beoordeel

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
NU = datetime(2026, 11, 23, 16, 24, tzinfo=timezone.utc).timestamp()
VERS = "2026-11-23T16:20:00Z"


def test_de_melding_van_23_november_was_er_niet_gekomen():
    uit = beoordeel({"waargenomen_op": VERS, "zicht": 83700, "luchtvochtigheid": 87.0,
                     "temperatuur": 0.4, "dauwpunt": -1.4}, NU)
    assert uit["bevestigd"] is False
    assert "87" in uit["reden"] and "84 km" in uit["reden"]


def test_weinig_zicht_bevestigt():
    assert beoordeel({"waargenomen_op": VERS, "zicht": 400, "luchtvochtigheid": 90}, NU)["bevestigd"] is True
    assert beoordeel({"waargenomen_op": VERS, "zicht": 1000}, NU)["bevestigd"] is False


def test_vocht_en_dauwpunt_bevestigen_ook_bij_ruim_zicht_van_een_ver_station():
    basis = {"waargenomen_op": VERS, "zicht": 20000, "temperatuur": 2.0}
    assert beoordeel({**basis, "luchtvochtigheid": 98, "dauwpunt": 1.7}, NU)["bevestigd"] is True
    assert beoordeel({**basis, "luchtvochtigheid": 98, "dauwpunt": 0.5}, NU)["bevestigd"] is False
    assert beoordeel({**basis, "luchtvochtigheid": 94, "dauwpunt": 1.9}, NU)["bevestigd"] is False
    # zonder dauwpunt (DWD-station) telt het vocht alleen
    assert beoordeel({"waargenomen_op": VERS, "luchtvochtigheid": 97}, NU)["bevestigd"] is True


def test_geen_of_oude_meting_bevestigt_niet():
    assert beoordeel(None, NU)["bevestigd"] is False
    assert beoordeel({}, NU)["bevestigd"] is False
    oud = {"waargenomen_op": "2026-11-23T14:00:00Z", "zicht": 100}
    assert beoordeel(oud, NU) == {"bevestigd": False, "reden": "stationsmeting te oud"}
    assert beoordeel({"waargenomen_op": "onzin", "zicht": 100}, NU)["bevestigd"] is False


def test_de_coordinator_vraagt_de_meting_voor_de_mistmelding():
    bron = (BRON / "coordinator.py").read_text()
    blok = bron[bron.index("if code in CODES_MIST:"):][:500]
    assert "mistcheck.beoordeel(" in blok and 'if oordeel["bevestigd"]:' in blok
    assert "meteo.stationsmeting = lambda: meting.data" in (BRON / "__init__.py").read_text()
