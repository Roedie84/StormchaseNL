"""0.61.1: regenuitkomst na verplaatsing telt niet mee (L-SC-030).

02-11 06:17: "over 57 min" in Eibergen, afgerekend om 06:42 toen de locatie
~13 km westwaarts reed: -31,7 min, en dat punt voedt `regencorrectie.leer`.
"""

from __future__ import annotations

import json
from pathlib import Path

from validatie import PLEK_VERVALT_KM, Validatie

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
EIBERGEN = (52.10, 6.65)
DRIE_KM = (52.10, 6.694)
DERTIEN_KM = (52.10, 6.46)


def _open(plek=EIBERGEN):
    val = Validatie()
    extra = {"bron": "knmi"}
    if plek is not None:
        extra["plek"] = list(plek)
    val.voorspel("regen", 0.0, 57, extra)
    return val


def test_verder_dan_de_grens_vervalt_zonder_uitkomst():
    val = _open()
    assert val.vervalt_na_verplaatsing("regen", DERTIEN_KM) is True
    assert val.open == {}
    assert val.uitkomsten == []
    assert val.afgerond == 0
    assert val.wijzigingen == 2


def test_binnen_de_grens_blijft_hij_staan_en_telt_de_uitkomst():
    val = _open()
    assert val.vervalt_na_verplaatsing("regen", DRIE_KM) is False
    val.uitgekomen("regen", 60 * 50.0, {"intensiteit": 1.0})
    assert val.uitkomsten[0]["uitgekomen"] is True
    assert val.uitkomsten[0]["afwijking_min"] == -7.0


def test_voorspelling_zonder_plek_of_zonder_locatie_loopt_gewoon_af():
    val = _open(plek=None)
    assert val.vervalt_na_verplaatsing("regen", DERTIEN_KM) is False
    assert "regen" in val.open
    val = _open()
    assert val.vervalt_na_verplaatsing("regen", None) is False
    assert "regen" in val.open


def test_vervallen_voorspelling_verloopt_niet_als_gemist():
    val = _open()
    val.vervalt_na_verplaatsing("regen", DERTIEN_KM)
    val.verlopen(60 * 300.0)
    assert val.uitkomsten == []


def test_plek_overleeft_de_opslag_maar_staat_niet_in_de_diagnostiek():
    val = _open()
    terug = Validatie(open_voorspellingen=val.naar_opslag()["open"])
    assert terug.vervalt_na_verplaatsing("regen", DERTIEN_KM) is True
    assert "plek" not in _open().als_dict()["open"]["regen"]


def test_rain_controleert_de_plek_voor_verlopen_en_bewaart_hem():
    bron = (BRON / "rain.py").read_text(encoding="utf-8")
    assert bron.index('vervalt_na_verplaatsing("regen", plek)') < bron.index(
        "self.validatie.verlopen(nu)"
    )
    assert 'extra["plek"] = [round(plek[0], 3), round(plek[1], 3)]' in bron
    assert "self._verwerk(reeks, bron, (latitude, longitude))" in bron


def test_grens_en_versie():
    assert PLEK_VERVALT_KM == 5.0
    versie = json.loads((BRON / "manifest.json").read_text())["version"]
    assert tuple(int(x) for x in versie.split(".")) >= (0, 61, 1)
