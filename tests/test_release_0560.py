"""0.56.0 (L-SC-011): de start van de regen bijstellen met de eigen uitkomsten.

19-10: van 43 uitgekomen KNMI-voorspellingen begon de regen 31 keer eerder
dan voorspeld (mediaan 7 min); verder vooruit meer.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

import regencorrectie as R  # noqa: E402
from validatie import Validatie  # noqa: E402

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"

# echte paren (voorspeld, werkelijk) uit de validatie van 14-19 okt
ECHT = [(57, 30), (25, 10), (47, 25), (60, 73), (27, 15), (57, 65), (27, 20), (47, 26),
        (42, 30), (32, 55), (57, 45), (32, 25), (17, 5)]


def _uitkomsten(rij, bron="knmi"):
    return [{"soort": "regen", "uitgekomen": True, "bron": bron,
             "voorspeld_over_min": v, "werkelijk_over_min": w} for v, w in rij]


def test_te_weinig_uitkomsten_geen_correctie():
    c = R.leer(_uitkomsten(ECHT[:10]), "knmi")
    assert c["toegepast"] is False and "15" in c["reden"]
    assert R.corrigeer(30, c) == 30


def test_systematisch_te_laat_wordt_bijgesteld():
    rij = [(v, v * 0.6) for v in range(10, 60, 2)]
    c = R.leer(_uitkomsten(rij), "knmi")
    assert c["toegepast"] and c["vorm"] == "verhouding" and c["verhouding"] == 0.6
    assert R.corrigeer(50, c) == 30
    assert c["afwijking_min"]["verhouding"] < c["afwijking_min"]["geen"]


def test_vaste_verschuiving_per_horizon():
    rij = [(v, v - 7) for v in range(10, 60, 2)]
    c = R.leer(_uitkomsten(rij), "knmi")
    assert c["toegepast"] and c["vorm"] == "verschuiving"
    assert R.corrigeer(40, c) == 33


def test_ruis_zonder_patroon_blijft_kaal():
    rij = [(30, 30 + d) for d in (-8, 8, -6, 6, -7, 7, -5, 5, -9, 9, -4, 4, -8, 8, -6, 6)]
    c = R.leer(_uitkomsten(rij), "knmi")
    assert c["toegepast"] is False and c["vorm"] == "geen"


def test_alleen_de_eigen_bron_en_uitgekomen():
    rij = [(v, v * 0.6) for v in range(10, 60, 2)]
    andere = _uitkomsten(rij, "buienradar") + [{"soort": "regen", "uitgekomen": False, "bron": "knmi",
                                               "voorspeld_over_min": 30}] * 20
    assert R.leer(andere, "knmi")["uitkomsten"] == 0


def test_echte_reeks_aangevuld_tot_genoeg():
    c = R.leer(_uitkomsten(ECHT * 2), "knmi")
    assert c["toegepast"]
    # de bijgestelde start van een voorspelling van 30 min ligt eerder
    assert R.corrigeer(30, c) < 30
    assert R.corrigeer(None, c) is None and R.corrigeer(0, c) == 0


def test_grenzen():
    rij = [(v, 0) for v in range(10, 60, 2)]
    c = R.leer(_uitkomsten(rij), "knmi")
    if c["vorm"] == "verhouding":
        assert c["verhouding"] >= R.VERHOUDING_GRENZEN[0]
    else:
        assert all(abs(s) <= R.MAX_VERSCHUIVING_MIN for s in c["verschuiving_min"].values())


def test_rain_legt_de_kale_voorspelling_vast_en_toont_de_bijgestelde():
    bron = (ROOT / "rain.py").read_text(encoding="utf-8")
    assert '"regen", nu, begint_kaal' in bron
    assert "begint_over = corrigeer(begint_kaal, correctie)" in bron
    assert '"begint_over_kaal": begint_kaal' in bron
    sensor = (ROOT / "sensor.py").read_text(encoding="utf-8")
    assert '"zonder_correctie": data.get("begint_over_kaal")' in sensor


def test_validatie_rondt_kale_waarde_af():
    val = Validatie()
    val.voorspel("regen", 0.0, 30, {"bron": "knmi"})
    val.uitgekomen("regen", 20 * 60.0)
    r = val.uitkomsten[-1]
    assert r["voorspeld_over_min"] == 30 and r["werkelijk_over_min"] == 20
    assert R.paren(val.uitkomsten, "knmi") == [(30.0, 20.0)]
