"""0.55.0: geen dubbele inslagen in de ringen; reservebron in rust.

Gevonden op het analysedashboard: 10-10 17:31 telden beide
Blitzortung-instanties dezelfde 8 inslagen, waardoor de 50 km-ring naar 16
sprong; na een herstart bleef hij op 4 staan zonder inslagen. En Meteoalarm
stond op 100 % terwijl hij al dagen niet meer gevraagd werd.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import homeassistant.util.dt  # noqa: F401
except ModuleNotFoundError:
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

from herstart import puntsleutel  # noqa: E402
import stats as _stats  # noqa: E402
from stats import RUST_NA_UREN, BronStatus  # noqa: E402

BRON = (Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
        / "coordinator.py").read_text(encoding="utf-8")


def test_zelfde_inslag_van_twee_instanties_een_sleutel():
    a = puntsleutel(1791651060.04, 52.1234, 6.6512)
    b = puntsleutel(1791651060.01, 52.12341, 6.65118)
    assert a == b


def test_coordinator_ontdubbelt_en_telt_ringen_binnen_het_venster():
    blok = BRON[BRON.index("def _uit_geo_location"): BRON.index("def _count_rings")]
    assert "gezien_sleutels" in blok and "if sleutel_nu in gezien_sleutels" in blok
    assert "self._ring_km.append" in blok and "venster" in blok
    assert 'getattr(self, "_ring_km", None)' in BRON


def test_reservebron_in_rust_is_geen_100_procent():
    bron = BronStatus()
    bron.succes()
    assert bron.toestand() == "in gebruik"
    nu = _stats.dt_util.utcnow()
    later = nu + timedelta(hours=RUST_NA_UREN + 1)
    assert bron.toestand(later) == "rust (niet nodig)"
    bron.laatste_succes = nu - timedelta(hours=RUST_NA_UREN + 1)
    assert bron.als_dict()["slaagpercentage"] is None
    assert bron.als_dict()["toestand"] == "rust (niet nodig)"


def test_haperende_bron_blijft_haperen():
    bron = BronStatus()
    bron.fout("time-out")
    bron.fout("time-out")
    assert bron.toestand() == "hapert"
