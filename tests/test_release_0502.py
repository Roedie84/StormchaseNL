"""0.50.2: validatievenster per soort en bron per regenvoorspelling (L-SC-006)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

from validatie import MAX_UITKOMSTEN, Validatie  # noqa: E402

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"


def _regen(val: Validatie, t: float, bron: str | None = "knmi", te_laat_min: float = -5) -> None:
    extra = {"verwachte_piek": 0.3}
    if bron is not None:
        extra["bron"] = bron
    val.voorspel("regen", t, 30, extra)
    val.uitgekomen("regen", t + (30 + te_laat_min) * 60)


def _passage(val: Validatie, t: float) -> None:
    val.voorspel("passage", t, 10, {"verwachte_afstand": 8.0})
    val.passage_afgerond(t + 11 * 60, 12.0)


class TestVensterPerSoort:
    def test_regen_verdringt_geen_onweer(self):
        """De situatie van 09-10: venster vol, regen erbij -> onweer blijft."""
        val = Validatie()
        for i in range(21):
            _passage(val, i * 10_000.0)
        for i in range(5):
            val.voorspel("aankomst", 500_000.0 + i * 10_000, 10, {})
            val.uitgekomen("aankomst", 500_000.0 + i * 10_000 + 600)
        for i in range(MAX_UITKOMSTEN + 25):
            _regen(val, 1_000_000.0 + i * 10_000)
        per = val.aantal_per_soort()
        assert per == {"aankomst": 5, "passage": 21, "regen": MAX_UITKOMSTEN}

    def test_oudste_van_dezelfde_soort_valt_weg(self):
        val = Validatie()
        _passage(val, 0.0)
        for i in range(MAX_UITKOMSTEN + 1):
            _regen(val, 100_000.0 + i * 10_000)
        regen = [r for r in val.uitkomsten if r["soort"] == "regen"]
        assert len(regen) == MAX_UITKOMSTEN
        assert regen[0]["gemaakt_op"] == 100_000.0 + 10_000  # de eerste ging eruit
        assert val.uitkomsten[0]["soort"] == "passage"

    def test_volgorde_blijft_chronologisch(self):
        val = Validatie()
        for i in range(MAX_UITKOMSTEN + 3):
            _regen(val, i * 10_000.0)
            if i % 7 == 0:
                _passage(val, i * 10_000.0 + 5_000)
        tijden = [r["gemaakt_op"] for r in val.uitkomsten]
        assert tijden == sorted(tijden)

    def test_teller_telt_ook_bij_vol_venster(self):
        val = Validatie([{"soort": "regen"}] * MAX_UITKOMSTEN)
        _regen(val, 0.0)
        assert val.afgerond == MAX_UITKOMSTEN + 1
        assert val.aantal_per_soort()["regen"] == MAX_UITKOMSTEN


class TestBronPerVoorspelling:
    def test_bron_komt_in_de_uitkomst(self):
        val = Validatie()
        _regen(val, 0.0, bron="knmi")
        assert val.uitkomsten[-1]["bron"] == "knmi"

    def test_bron_overleeft_een_herstart(self):
        val = Validatie()
        val.voorspel("regen", 0.0, 30, {"verwachte_piek": 0.3, "bron": "buienradar"})
        bewaard = json.loads(json.dumps(val.naar_opslag()))
        terug = Validatie(bewaard["uitkomsten"], bewaard["open"], bewaard["afgerond"])
        terug.uitgekomen("regen", 25 * 60)
        assert terug.uitkomsten[-1]["bron"] == "buienradar"

    def test_samenvatting_per_bron(self):
        val = Validatie([{"soort": "regen", "uitgekomen": True, "afwijking_min": -30}])
        _regen(val, 0.0, bron="knmi", te_laat_min=10)
        _regen(val, 10_000.0, bron="knmi", te_laat_min=-4)
        _regen(val, 20_000.0, bron="buienradar", te_laat_min=-20)
        per = val.regen_per_bron()
        assert per["knmi"]["aantal"] == 2
        assert per["knmi"]["te_laat"] == 1 and per["knmi"]["te_vroeg"] == 1
        assert per["knmi"]["gemiddelde_afwijking_min"] == 7.0
        assert per["buienradar"]["te_vroeg"] == 1
        assert per["onbekend"]["aantal"] == 1  # van voor 0.50.2

    def test_passage_zonder_bron_blijft_zonder_bron(self):
        val = Validatie()
        _passage(val, 0.0)
        assert "bron" not in val.uitkomsten[-1]

    def test_diagnostiek_toont_vensters_en_bronnen(self):
        val = Validatie()
        _regen(val, 0.0, bron="knmi")
        d = val.als_dict()
        assert d["aantal_per_soort"] == {"regen": 1}
        assert d["max_per_soort"] == MAX_UITKOMSTEN
        assert d["regen_per_bron"]["knmi"]["aantal"] == 1

    def test_regenmodule_geeft_de_bron_mee(self):
        bron = (BRON / "rain.py").read_text(encoding="utf-8")
        assert '{"verwachte_piek": piek, "bron": bron}' in bron
