"""Terugval op oude gegevens bij een storing.

Een leeg dashboard midden in een onweer omdat een server hikt is de
verkeerde uitkomst. Een waarde van een uur oud met een melding erbij is
bruikbaarder.
"""

import sys
import types
from datetime import datetime, timedelta, timezone

import pytest

# Home Assistant nabootsen voor deze ene module
NU = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
KLOK = {"nu": NU}


class UpdateFailed(Exception):
    """Zoals Home Assistant hem gooit."""


def _stub():
    for naam in (
        "homeassistant",
        "homeassistant.helpers",
        "homeassistant.helpers.update_coordinator",
        "homeassistant.util",
        "homeassistant.util.dt",
    ):
        sys.modules.setdefault(naam, types.ModuleType(naam))
    sys.modules["homeassistant.helpers.update_coordinator"].UpdateFailed = UpdateFailed
    dt = sys.modules["homeassistant.util.dt"]
    dt.utcnow = lambda: KLOK["nu"]
    sys.modules["homeassistant.util"].dt = dt


_stub()

from verouderd import VerouderdMixin  # noqa: E402


class Bron(VerouderdMixin):
    name = "testbron"


@pytest.fixture
def bron():
    KLOK["nu"] = NU
    return Bron()


def test_zonder_eerdere_gegevens_geeft_op(bron):
    """Is er nooit iets geweest, dan valt er niets terug te vallen."""
    with pytest.raises(UpdateFailed):
        bron.val_terug(RuntimeError("server weg"))


def test_terugval_op_verse_gegevens(bron):
    bron.onthoud({"cape": 1900})
    KLOK["nu"] = NU + timedelta(minutes=20)

    uitkomst = bron.val_terug(RuntimeError("server weg"))
    assert uitkomst["cape"] == 1900
    assert uitkomst["verouderd_minuten"] == 20


def test_te_oud_geeft_alsnog_op(bron):
    """Boven de maximale ouderdom is onbeschikbaar eerlijker."""
    bron.onthoud({"cape": 1900})
    KLOK["nu"] = NU + timedelta(hours=4)

    with pytest.raises(UpdateFailed):
        bron.val_terug(RuntimeError("server weg"))


def test_geslaagde_ronde_zet_de_klok_terug(bron):
    """Na herstel telt de ouderdom weer vanaf nul."""
    bron.onthoud({"cape": 1900})
    KLOK["nu"] = NU + timedelta(hours=2)
    bron.onthoud({"cape": 2100})
    KLOK["nu"] = NU + timedelta(hours=2, minutes=5)

    uitkomst = bron.val_terug(RuntimeError("hik"))
    assert uitkomst["cape"] == 2100
    assert uitkomst["verouderd_minuten"] == 5


def test_niet_dict_wordt_ongewijzigd_teruggegeven(bron):
    bron.onthoud([1, 2, 3])
    KLOK["nu"] = NU + timedelta(minutes=5)
    assert bron.val_terug(RuntimeError("hik")) == [1, 2, 3]


# ---- 0.47.0: laatste gegevens over een herstart ----


def test_bewaarde_gegevens_dienen_als_terugval_na_herstart(bron):
    """Mislukt de eerste ronde na een herstart, dan de bewaarde waarde."""
    bron.onthoud({"cape": 1900})
    bewaard = bron.laatste_naar_opslag()

    na_herstart = Bron()
    na_herstart.herstel_laatste(bewaard)
    KLOK["nu"] = NU + timedelta(minutes=3)
    uitkomst = na_herstart.val_terug(RuntimeError("server weg"))
    assert uitkomst["cape"] == 1900
    assert uitkomst["verouderd_minuten"] == 3


def test_bewaarde_gegevens_houden_zich_aan_de_maximale_ouderdom(bron):
    bron.onthoud({"cape": 1900})
    na_herstart = Bron()
    na_herstart.herstel_laatste(bron.laatste_naar_opslag())
    KLOK["nu"] = NU + timedelta(hours=4)
    with pytest.raises(UpdateFailed):
        na_herstart.val_terug(RuntimeError("server weg"))


def test_herstel_overschrijft_geen_verse_gegevens(bron):
    bron.onthoud({"cape": 2100})
    bron.herstel_laatste({"op": NU.isoformat(), "gegevens": {"cape": 1}})
    assert bron.val_terug(RuntimeError("hik"))["cape"] == 2100


@pytest.mark.parametrize(
    "bewaard",
    [None, [], {}, {"op": "gisteren", "gegevens": {}}, {"op": NU.isoformat(), "gegevens": [1]},
     {"op": "2026-08-22T11:00:00", "gegevens": {}}],
)
def test_onbruikbare_opslag_wordt_genegeerd(bron, bewaard):
    bron.herstel_laatste(bewaard)
    with pytest.raises(UpdateFailed):
        bron.val_terug(RuntimeError("server weg"))


def test_onthoud_plant_het_bewaren(bron):
    geteld = []
    bron.bij_onthoud = lambda: geteld.append(1)
    bron.onthoud({"cape": 1})
    assert geteld == [1]
    assert bron.laatste_naar_opslag()["gegevens"] == {"cape": 1}
