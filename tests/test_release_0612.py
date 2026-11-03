"""0.61.2: de bronstatus ziet Blitzortung.

03-11 21:53 (kaart claude-stormchase, live op 0.61.1): de bronstatus zei
"alles in orde" en de ringen 0/0/0, terwijl de bliksemteller onbeschikbaar
was. "Geen inslagen" was zo niet te onderscheiden van "geen meting".
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

try:
    import homeassistant.util.dt  # noqa: F401
except ModuleNotFoundError:  # zonder HA-installatie: alleen utcnow is nodig
    import sys
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

from stats import BLITZORTUNG_MELD_SECONDEN, Statistieken, blitzortung_fout  # noqa: E402

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"


def test_onbeschikbare_teller_is_een_fout():
    assert blitzortung_fout("unavailable") == "bliksemteller onbeschikbaar"
    assert blitzortung_fout(None) == "bliksemteller niet gevonden"


def test_meting_of_nog_geen_inslag_is_geen_fout():
    assert blitzortung_fout("0") is None
    assert blitzortung_fout("12") is None
    # na een herstart staat de teller op unknown tot de eerste inslag
    assert blitzortung_fout("unknown") is None


def test_blitzortung_staat_in_de_bronstatus_en_hapert():
    stats = Statistieken()
    bron = stats.bronnen["blitzortung"]
    bron.succes()
    assert bron.hapert() is False
    bron.fout(blitzortung_fout("unavailable"))
    bron.fout(blitzortung_fout("unavailable"))
    assert bron.hapert() is True
    assert bron.als_dict()["laatste_fout"] == "bliksemteller onbeschikbaar"
    bron.succes()
    assert bron.hapert() is False


def test_coordinator_meldt_elke_ronde_maar_telt_zuinig():
    code = (BRON / "coordinator.py").read_text(encoding="utf-8")
    assert "self._meld_blitzortung()" in code
    assert "def _meld_blitzortung" in code
    assert BLITZORTUNG_MELD_SECONDEN == 60
    # teller bij voorkeur, anders de afstandssensor
    assert "self._opt(CONF_COUNTER_SENSOR) or self._opt(CONF_DISTANCE_SENSOR)" in code
