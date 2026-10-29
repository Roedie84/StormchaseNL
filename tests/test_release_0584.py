"""0.58.4 (L-SC-016): een reservebron "hapert" niet zolang hij niet nodig is.

Leerronde 22-10: de bronstatus stond van 10:24 tot middernacht op
"buienradar hapert". Buienradar faalde tijdens een DNS-storing samen met de
KNMI-nowcast en werd daarna niet meer gevraagd, omdat de nowcast weer werkte;
`op_rij_mislukt` bleef staan tot de volgende storing. Hetzelfde voor Bright
Sky ("meting") als reserve voor de KNMI-waarnemingen.
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


def _storing_dan_herstel(stats):
    """KNMI faalt 2x met Buienradar mee; daarna slaagt KNMI weer."""
    t0 = datetime(2026, 10, 22, 8, 24, tzinfo=timezone.utc)
    knmi, br = stats.bronnen["knmi_nowcast"], stats.bronnen["buienradar"]
    for i in range(2):
        knmi.fout("dns")
        knmi.laatste_fout_op = t0 + timedelta(minutes=i)
        br.fout("dns")
        br.laatste_fout_op = t0 + timedelta(minutes=i, seconds=5)
    knmi.succes()
    knmi.laatste_succes = t0 + timedelta(minutes=16)
    return knmi, br, t0


def test_reservebronnen_zijn_gekoppeld():
    stats = Statistieken()
    assert RESERVE_VOOR["buienradar"] == "knmi_nowcast"
    assert RESERVE_VOOR["meting"] == "knmi_edr"
    assert stats.bronnen["buienradar"].hoofdbron is stats.bronnen["knmi_nowcast"]
    assert stats.bronnen["meting"].hoofdbron is stats.bronnen["knmi_edr"]
    assert stats.bronnen["radar"].hoofdbron is None


def test_reserve_hapert_niet_na_herstel_van_de_hoofdbron():
    stats = Statistieken()
    knmi, br, t0 = _storing_dan_herstel(stats)
    nu = t0 + timedelta(hours=2)
    assert br.op_rij_mislukt == 2
    assert not br.hapert(nu)
    assert br.toestand(nu) == "reserve (niet nodig)"
    assert br.als_dict()["laatste_fout_op"] is not None  # de fout blijft zichtbaar


def test_reserve_hapert_tijdens_de_storing():
    stats = Statistieken()
    knmi, br = stats.bronnen["knmi_nowcast"], stats.bronnen["buienradar"]
    knmi.fout("dns")
    br.fout("dns")
    knmi.fout("dns")
    br.fout("dns")
    assert br.hapert()  # hoofdbron faalt ook: reserve is nodig en faalt


def test_reserve_hapert_weer_als_hij_opnieuw_gevraagd_wordt_en_faalt():
    stats = Statistieken()
    knmi, br, t0 = _storing_dan_herstel(stats)
    later = t0 + timedelta(hours=3)
    knmi.fout("time-out")
    knmi.laatste_fout_op = later
    br.fout("time-out")
    br.laatste_fout_op = later + timedelta(seconds=5)
    assert br.hapert(later + timedelta(minutes=1))


def test_hoofdbron_zelf_ongewijzigd():
    stats = Statistieken()
    knmi = stats.bronnen["knmi_nowcast"]
    knmi.fout("x")
    knmi.fout("x")
    assert knmi.hapert()
    assert knmi.toestand() == "hapert"


def test_meting_reserve_niet_in_gebruik_als_knmi_edr_werkt():
    stats = Statistieken()
    t0 = datetime(2026, 10, 22, 8, 24, tzinfo=timezone.utc)
    meting, edr = stats.bronnen["meting"], stats.bronnen["knmi_edr"]
    meting.succes()
    meting.laatste_succes = t0
    edr.succes()
    edr.laatste_succes = t0 + timedelta(minutes=10)
    assert meting.toestand(t0 + timedelta(hours=1)) == "reserve (niet nodig)"
