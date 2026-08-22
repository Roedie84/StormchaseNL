"""Voorspellingen vastleggen en achteraf nakijken."""

import pytest

from validatie import MAX_UITKOMSTEN, Validatie


@pytest.fixture
def val():
    return Validatie()


class TestVastleggen:
    def test_een_voorspelling_per_soort(self, val):
        """Elke ronde een nieuwe zou het gemiddelde betekenisloos maken."""
        val.voorspel("regen", 0.0, 20, {})
        val.voorspel("regen", 10.0, 15, {})
        assert val.open["regen"]["verwacht_over"] == 20

    def test_verschillende_soorten_naast_elkaar(self, val):
        val.voorspel("regen", 0.0, 20, {})
        val.voorspel("aankomst", 0.0, 45, {})
        assert set(val.open) == {"regen", "aankomst"}


class TestNakijken:
    def test_precies_op_tijd(self, val):
        val.voorspel("regen", 0.0, 20, {})
        val.uitgekomen("regen", 20 * 60)

        uitkomst = val.uitkomsten[-1]
        assert uitkomst["uitgekomen"] is True
        assert uitkomst["afwijking_min"] == 0.0

    def test_te_vroeg(self, val):
        """Kwam het eerder dan gedacht, dan is de afwijking negatief."""
        val.voorspel("regen", 0.0, 20, {})
        val.uitgekomen("regen", 12 * 60)
        assert val.uitkomsten[-1]["afwijking_min"] == -8.0

    def test_te_laat(self, val):
        val.voorspel("regen", 0.0, 20, {})
        val.uitgekomen("regen", 27 * 60)
        assert val.uitkomsten[-1]["afwijking_min"] == 7.0

    def test_niet_uitgekomen(self, val):
        """Ruim over tijd telt als gemist, niet als geslaagd."""
        val.voorspel("regen", 0.0, 20, {})
        val.verlopen((20 + 45 + 1) * 60)

        uitkomst = val.uitkomsten[-1]
        assert uitkomst["uitgekomen"] is False
        assert "regen" not in val.open

    def test_geduld_voor_het_verlopen(self, val):
        val.voorspel("regen", 0.0, 20, {})
        val.verlopen(30 * 60)
        assert "regen" in val.open

    def test_uitgekomen_zonder_voorspelling(self, val):
        """Mag geen fout geven, er valt alleen niets af te rekenen."""
        val.uitgekomen("regen", 100.0)
        assert val.uitkomsten == []


class TestPassage:
    def test_afstand_vergelijken(self, val):
        val.voorspel("passage", 0.0, 30, {"verwachte_afstand": 12.0})
        val.passage_afgerond(30 * 60, 8.5)

        uitkomst = val.uitkomsten[-1]
        assert uitkomst["afwijking_km"] == -3.5
        assert uitkomst["werkelijke_afstand_km"] == 8.5

    def test_nog_niet_aan_de_beurt(self, val):
        val.voorspel("passage", 0.0, 30, {"verwachte_afstand": 12.0})
        val.passage_afgerond(10 * 60, 8.5)
        assert "passage" in val.open


class TestSamenvatting:
    def test_gemiddelde_afwijking(self, val):
        for gemaakt, werkelijk in ((0.0, 22), (100.0, 18), (200.0, 25)):
            val.voorspel("regen", gemaakt, 20, {})
            val.uitgekomen("regen", gemaakt + werkelijk * 60)

        samenvatting = val.samenvatting()["regen (15 tot 45 min)"]
        assert samenvatting["aantal"] == 3
        assert samenvatting["uitgekomen"] == 3
        assert samenvatting["gemiddelde_afwijking_min"] == pytest.approx(3.0, abs=0.1)
        assert samenvatting["grootste_afwijking_min"] == 5.0

    def test_gemiste_tellen_mee_in_aantal(self, val):
        val.voorspel("regen", 0.0, 20, {})
        val.uitgekomen("regen", 20 * 60)
        val.voorspel("regen", 1000.0, 20, {})
        val.verlopen(1000.0 + (20 + 46) * 60)

        samenvatting = val.samenvatting()["regen (15 tot 45 min)"]
        assert samenvatting["aantal"] == 2
        assert samenvatting["uitgekomen"] == 1

    def test_lijst_blijft_begrensd(self, val):
        for i in range(MAX_UITKOMSTEN + 20):
            val.voorspel("regen", float(i * 1000), 5, {})
            val.uitgekomen("regen", i * 1000 + 300)
        assert len(val.uitkomsten) == MAX_UITKOMSTEN

    def test_dict_bevat_alles(self, val):
        val.voorspel("aankomst", 0.0, 45, {"afstand_bij_voorspelling": 60})
        uit = val.als_dict()
        assert "aankomst" in uit["open"]
        assert uit["open"]["aankomst"]["verwacht_over_min"] == 45


class TestHorizon:
    """Voorspellingen ver vooruit horen niet op een hoop met dichtbij."""

    def test_indeling(self):
        from validatie import horizon

        assert horizon(8) == "tot 15 min"
        assert horizon(15) == "tot 15 min"
        assert horizon(30) == "15 tot 45 min"
        assert horizon(90) == "meer dan 45 min"

    def test_samenvatting_splitst(self, val):
        """Een misser ver vooruit mag het dichtbijgemiddelde niet verpesten."""
        val.voorspel("regen", 0.0, 12, {})
        val.uitgekomen("regen", 5 * 60)

        val.voorspel("regen", 10000.0, 57, {})
        val.uitgekomen("regen", 10000.0 + 90 * 60)

        samenvatting = val.samenvatting()
        assert samenvatting["regen (tot 15 min)"]["gemiddelde_afwijking_min"] == 7.0
        assert samenvatting["regen (meer dan 45 min)"]["gemiddelde_afwijking_min"] == 33.0

    def test_samenvoegen_kan_ook(self, val):
        val.voorspel("regen", 0.0, 12, {})
        val.uitgekomen("regen", 5 * 60)
        val.voorspel("regen", 10000.0, 57, {})
        val.uitgekomen("regen", 10000.0 + 90 * 60)

        samen = val.samenvatting(per_horizon=False)
        assert samen["regen"]["aantal"] == 2
        assert samen["regen"]["gemiddelde_afwijking_min"] == 20.0
