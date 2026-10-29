"""0.60.2: MeteoAlarm is in Nederland de reserve van de KNMI-waarschuwingen.

Leerronde 29-10 11:40: de bronstatus stond vanaf 11:33 op "meteoalarm hapert".
Om 11:32 faalden de KNMI-waarschuwingen één keer (DNS-storing), MeteoAlarm viel
in en kreeg een time-out; daarna werkte het KNMI weer en werd MeteoAlarm niet
meer gevraagd. `op_rij_mislukt` bleef 1 met een laatste succes van 23:45 de
avond ervoor, dus "hapert" tot de volgende KNMI-storing. De fouttekst was leeg
(str(TimeoutError()) == "").
"""

from datetime import datetime, timedelta, timezone

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

from stats import RESERVE_VOOR, Statistieken  # noqa: E402

T0 = datetime(2026, 10, 29, 10, 32, 54, tzinfo=timezone.utc)


def _situatie_29_10(stats):
    knmi = stats.bronnen["knmi_waarschuwingen"]
    ma = stats.bronnen["meteoalarm"]
    ma.succes()
    ma.laatste_succes = datetime(2026, 10, 28, 23, 45, 46, tzinfo=timezone.utc)
    knmi.succes()
    knmi.laatste_succes = T0 - timedelta(minutes=3)
    knmi.fout("verbindingsfout (ClientConnectorDNSError)")
    knmi.laatste_fout_op = T0
    ma.fout(TimeoutError())
    ma.laatste_fout_op = T0 + timedelta(seconds=20)
    knmi.succes()
    knmi.laatste_succes = T0 + timedelta(minutes=2, seconds=20)
    return knmi, ma


def test_meteoalarm_is_reserve_van_de_knmi_waarschuwingen():
    stats = Statistieken()
    assert RESERVE_VOOR["meteoalarm"] == "knmi_waarschuwingen"
    assert stats.bronnen["meteoalarm"].hoofdbron is stats.bronnen["knmi_waarschuwingen"]
    assert stats.bronnen["knmi_waarschuwingen"].hoofdbron is None


def test_meteoalarm_hapert_niet_als_het_knmi_weer_werkt():
    stats = Statistieken()
    _knmi, ma = _situatie_29_10(stats)
    nu = T0 + timedelta(minutes=12)
    assert ma.op_rij_mislukt == 1
    assert not ma.hapert(nu)
    assert ma.toestand(nu) == "reserve (niet nodig)"


def test_meteoalarm_hapert_wel_als_het_knmi_ook_faalt():
    stats = Statistieken()
    knmi, ma = _situatie_29_10(stats)
    knmi.fout("dns")
    knmi.laatste_fout_op = T0 + timedelta(minutes=10)
    ma.fout(TimeoutError())
    ma.laatste_fout_op = T0 + timedelta(minutes=10, seconds=20)
    assert ma.hapert(T0 + timedelta(minutes=11))


def test_buitenland_meteoalarm_is_gewone_bron():
    """Buiten Nederland wordt het KNMI niet gevraagd: MeteoAlarm hapert gewoon."""
    stats = Statistieken()
    knmi, ma = stats.bronnen["knmi_waarschuwingen"], stats.bronnen["meteoalarm"]
    knmi.succes()
    knmi.laatste_succes = T0 - timedelta(days=2)
    ma.succes()
    ma.laatste_succes = T0 - timedelta(hours=1)
    ma.fout(TimeoutError())
    ma.laatste_fout_op = T0
    ma.fout(TimeoutError())
    ma.laatste_fout_op = T0 + timedelta(minutes=15)
    assert ma.hapert(T0 + timedelta(minutes=16))


def test_lege_fouttekst_krijgt_de_soort_fout():
    stats = Statistieken()
    ma = stats.bronnen["meteoalarm"]
    ma.fout(TimeoutError())
    assert ma.laatste_fout == "TimeoutError"
    ma.fout("503 Service Unavailable")
    assert ma.laatste_fout == "503 Service Unavailable"
