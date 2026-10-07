"""0.43.0: een mislukte bron krijgt na 2 en 5 minuten een herkansing.

Live op 7 oktober: tijdens een DNS-storing om 16:45 bleven CAPE, Lifted
Index en windschering een uur oud, omdat Open-Meteo pas na het hele interval
van 30 minuten opnieuw werd geprobeerd.
"""

import ast
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"

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

from herpoging import (  # noqa: E402
    HERPOGINGEN,
    MAX_RETRY_AFTER,
    HerpogingMixin,
    is_beperkt,
    retry_after,
    volgende_interval,
)
from stats import Statistieken  # noqa: E402

HALF_UUR = timedelta(minutes=30)


class HttpFout(Exception):
    """Lijkt op aiohttp.ClientResponseError: status en headers."""

    def __init__(self, status, headers=None):
        super().__init__(f"HTTP {status}")
        self.status = status
        self.headers = headers or {}


# --- het schema ------------------------------------------------------------


def test_schema_twee_dan_vijf_dan_normaal():
    assert volgende_interval(HALF_UUR, 0) == HALF_UUR
    assert volgende_interval(HALF_UUR, 1) == timedelta(minutes=2)
    assert volgende_interval(HALF_UUR, 2) == timedelta(minutes=5)
    assert volgende_interval(HALF_UUR, 3) == HALF_UUR
    assert volgende_interval(HALF_UUR, 10) == HALF_UUR
    assert len(HERPOGINGEN) == 2


def test_herkansing_nooit_langer_dan_normaal():
    vijf = timedelta(minutes=5)
    assert volgende_interval(vijf, 1) == timedelta(minutes=2)
    assert volgende_interval(vijf, 2) == vijf
    minuut = timedelta(minutes=1)
    assert volgende_interval(minuut, 1) == minuut


def test_afgeremd_geen_herkansing():
    assert volgende_interval(HALF_UUR, 1, beperkt=True) == HALF_UUR
    assert volgende_interval(HALF_UUR, 1, True, timedelta(hours=1)) == timedelta(hours=1)
    assert volgende_interval(HALF_UUR, 1, True, timedelta(minutes=1)) == HALF_UUR


def test_429_en_retry_after_herkennen():
    assert is_beperkt(HttpFout(429))
    assert not is_beperkt(HttpFout(503))
    assert not is_beperkt(TimeoutError())
    assert retry_after(HttpFout(429, {"Retry-After": "120"})) == timedelta(minutes=2)
    assert retry_after(HttpFout(429, {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})) is None
    assert retry_after(HttpFout(429, {"Retry-After": "999999"})) == MAX_RETRY_AFTER
    assert retry_after(HttpFout(429)) is None
    assert retry_after(OSError("dns")) is None


def test_bronstatus_onthoudt_afremming_tot_succes():
    stats = Statistieken()
    bron = stats.bronnen["open_meteo"]
    bron.fout(HttpFout(429, {"Retry-After": "600"}))
    assert bron.beperkt and bron.retry_after == timedelta(minutes=10)
    assert bron.als_dict()["afgeremd"] is True
    bron.succes()
    assert not bron.beperkt and bron.retry_after is None


# --- de mixin ----------------------------------------------------------------


class NepCoordinator(HerpogingMixin):
    _herpoging_bronnen = ("open_meteo", "lifted_index")

    def __init__(self, stats):
        self.stats = stats
        self.update_interval = HALF_UUR
        self.uitkomst = {}

    async def _haal_op(self):
        for naam in self._herpoging_bronnen:
            fout = self.uitkomst.get(naam)
            if fout is None:
                self.stats.bronnen[naam].succes()
            else:
                self.stats.bronnen[naam].fout(fout)
        if self.uitkomst.get("open_meteo") is not None:
            raise RuntimeError("UpdateFailed")
        return {"ok": True}


def _ronde(coordinator):
    try:
        asyncio.run(coordinator._async_update_data())
    except RuntimeError:
        pass
    return coordinator.update_interval


def test_dns_storing_herstelt_binnen_minuten():
    c = NepCoordinator(Statistieken())
    assert _ronde(c) == HALF_UUR
    c.uitkomst = {"open_meteo": OSError("dns"), "lifted_index": OSError("dns")}
    assert _ronde(c) == timedelta(minutes=2)
    assert _ronde(c) == timedelta(minutes=5)
    assert _ronde(c) == HALF_UUR  # begrensd: daarna het gewone interval
    assert _ronde(c) == HALF_UUR
    c.uitkomst = {}
    assert _ronde(c) == HALF_UUR
    # Een nieuwe storing begint weer bij 2 minuten
    c.uitkomst = {"lifted_index": OSError("dns")}
    assert _ronde(c) == timedelta(minutes=2)


def test_een_deelbron_die_faalt_krijgt_ook_een_herkansing():
    c = NepCoordinator(Statistieken())
    c.uitkomst = {"lifted_index": OSError("dns")}
    assert _ronde(c) == timedelta(minutes=2)
    li = c.stats.bronnen["lifted_index"]
    om = c.stats.bronnen["open_meteo"]
    assert li.herkansing and not om.herkansing
    assert li.volgende_poging == om.volgende_poging
    assert li.als_dict()["volgende_poging"] is not None


def test_429_wacht_het_gewone_interval_af():
    c = NepCoordinator(Statistieken())
    c.uitkomst = {"open_meteo": HttpFout(429), "lifted_index": OSError("dns")}
    assert _ronde(c) == HALF_UUR
    assert not c.stats.bronnen["lifted_index"].herkansing


def test_429_met_retry_after_wacht_langer():
    c = NepCoordinator(Statistieken())
    c.uitkomst = {"open_meteo": HttpFout(429, {"Retry-After": "3600"})}
    assert _ronde(c) == timedelta(hours=1)


def test_volgende_poging_klopt():
    c = NepCoordinator(Statistieken())
    c.stats.bronnen["open_meteo"].fout(OSError("dns"))
    nu = datetime(2026, 10, 7, 16, 45, tzinfo=timezone.utc)
    interval = c._plan_volgende(c.stats, {"open_meteo": 0, "lifted_index": 0}, nu)
    assert interval == timedelta(minutes=2)
    assert c.stats.bronnen["open_meteo"].volgende_poging == nu + interval


def test_eerst_mislukt_dan_gelukt_in_dezelfde_ronde_is_geen_storing():
    """Het ensemble probeert twee modellen; lukt het tweede, dan niets mis."""
    stats = Statistieken()
    c = NepCoordinator(stats)
    voor = c._mislukt_tellers(stats)
    stats.bronnen["open_meteo"].fout(OSError("eerste model"))
    stats.bronnen["open_meteo"].succes()
    assert c._plan_volgende(stats, voor) == HALF_UUR


def test_zonder_statistieken_niets_aanpassen():
    c = NepCoordinator(None)
    c.stats = None

    async def stil():
        return {}

    c._haal_op = stil
    asyncio.run(c._async_update_data())
    assert c.update_interval == HALF_UUR


# --- de koppeling -------------------------------------------------------------


@pytest.mark.parametrize(
    ("bestand", "klasse", "bronnen"),
    [
        ("coordinator.py", "MeteoCoordinator", {"open_meteo", "icon_d2", "lifted_index", "ensemble", "ensemble_leden"}),
        ("alerts.py", "AlertCoordinator", {"meteoalarm", "geocodering"}),
        ("meting.py", "MetingCoordinator", {"meting"}),
        ("rain.py", "RainCoordinator", {"buienradar"}),
    ],
)
def test_coordinators_gebruiken_de_herkansing(bestand, klasse, bronnen):
    boom = ast.parse((BRON / bestand).read_text(encoding="utf-8"))
    knoop = next(
        k for k in ast.walk(boom) if isinstance(k, ast.ClassDef) and k.name == klasse
    )
    assert ast.unparse(knoop.bases[0]) == "HerpogingMixin"
    namen = {k.name for k in knoop.body if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert "_haal_op" in namen
    assert "_async_update_data" not in namen  # anders slaat de mixin over
    toewijzing = next(
        k for k in knoop.body
        if isinstance(k, ast.Assign) and k.targets[0].id == "_herpoging_bronnen"
    )
    assert set(ast.literal_eval(toewijzing.value)) == bronnen
    assert bronnen <= set(Statistieken().bronnen)
