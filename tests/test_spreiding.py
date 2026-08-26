"""Spreiding tussen weermodellen."""

import pytest

from spreiding import beoordeel, mediaan, samenvatting


class TestMediaan:
    def test_oneven_aantal(self):
        assert mediaan([3, 1, 2]) == 2

    def test_even_aantal(self):
        assert mediaan([1, 2, 3, 4]) == 2.5

    def test_ongevoelig_voor_uitschieter(self):
        """Een enkel model dat er ver naast zit trekt de mediaan niet mee."""
        normaal = mediaan([1900, 1950, 1880, 1920])
        met_uitschieter = mediaan([1900, 1950, 1880, 1920, 9000])
        assert abs(met_uitschieter - normaal) < 60


class TestBeoordeling:
    def test_modellen_eens(self):
        oordeel = beoordeel(
            {"a": 1980, "b": 2050, "c": 1870, "d": 2110, "e": 1930, "f": 2000}
        )
        assert oordeel["overeenstemming"] == "modellen zijn het eens"
        assert oordeel["aantal_modellen"] == 6

    def test_modellen_verdeeld(self):
        oordeel = beoordeel(
            {"a": 240, "b": 2600, "c": 1800, "d": 420, "e": 2300, "f": 900}
        )
        assert oordeel["overeenstemming"] == "modellen zijn verdeeld"

    def test_lage_waarden_heten_niet_verdeeld(self):
        """Van 0 naar 60 J/kg is relatief enorm maar praktisch niets.

        Zonder ondergrens zou elke rustige dag als verdeeld gelden.
        """
        oordeel = beoordeel({"a": 10, "b": 40, "c": 0, "d": 60, "e": 25})
        assert oordeel["overeenstemming"] == "modellen zijn het eens"

    def test_te_weinig_modellen(self):
        oordeel = beoordeel({"a": 1900, "b": None, "c": None})
        assert oordeel["overeenstemming"] == "onbekend"
        assert oordeel["aantal_modellen"] == 1

    def test_lege_modellen_tellen_niet_mee(self):
        oordeel = beoordeel({"a": 1000, "b": None, "c": 1100, "d": 1050})
        assert oordeel["aantal_modellen"] == 3
        assert "b" not in oordeel["modellen"]

    def test_bereik_klopt(self):
        oordeel = beoordeel({"a": 100, "b": 500, "c": 300})
        assert oordeel["laagste"] == 100
        assert oordeel["hoogste"] == 500
        assert oordeel["spreiding"] == 400

    def test_alles_leeg(self):
        oordeel = beoordeel({"a": None, "b": None})
        assert oordeel["overeenstemming"] == "onbekend"
        assert oordeel["mediaan"] is None


class TestSamenvatting:
    def test_leesbare_regel(self):
        tekst = samenvatting(beoordeel({"a": 1900, "b": 2000, "c": 2100}))
        assert "2000 J/kg mediaan" in tekst
        assert "1900 tot 2100" in tekst
        assert "3 modellen" in tekst

    def test_zonder_gegevens(self):
        assert "Te weinig" in samenvatting(beoordeel({"a": None}))


class TestEnsemble:
    """Kansen uit ensembleleden zeggen iets anders dan een mediaan."""

    def test_eensgezind_hoog(self):
        from spreiding import ensemble

        uitkomst = ensemble([1900, 2100, 1850, 2000, 1950, 2200, 1800, 1990])
        assert uitkomst["kans_onweer"] == 100
        assert uitkomst["kans_zwaar"] == 100
        assert uitkomst["duiding"] == "vrijwel zeker"

    def test_verdeelde_leden(self):
        """Een nette mediaan kan een sterk verdeeld ensemble verbergen.

        Hier ligt de mediaan boven de onweersdrempel, terwijl de helft van de
        leden er ruim onder zit. Dat is precies het geval waarin een enkel
        getal misleidt.
        """
        from spreiding import ensemble

        leden = [200, 2400, 600, 1800, 300, 2100, 150, 1900, 400, 2200]
        uitkomst = ensemble(leden)

        assert uitkomst["mediaan_piek"] > 500
        assert uitkomst["kans_onweer"] == 60
        assert uitkomst["duiding"] == "waarschijnlijk"

    def test_rustige_dag(self):
        from spreiding import ensemble

        uitkomst = ensemble([20, 40, 10, 60, 30, 15, 50, 25])
        assert uitkomst["kans_onweer"] == 0
        assert uitkomst["duiding"] == "vrijwel uitgesloten"

    def test_te_weinig_leden(self):
        from spreiding import ensemble

        uitkomst = ensemble([1900, 2000])
        assert uitkomst["kans_onweer"] is None
        assert uitkomst["duiding"] == "onbekend"

    def test_lege_leden_tellen_niet_mee(self):
        from spreiding import ensemble

        uitkomst = ensemble([1900, None, 2000, None, 1800, 1950, 2100])
        assert uitkomst["leden"] == 5

    def test_kans_boven_drempel(self):
        from spreiding import kans_boven

        assert kans_boven([100, 200, 300, 400, 500], 300) == 60
        assert kans_boven([100, 200], 150) is None

    def test_duiding_loopt_op(self):
        from spreiding import duiding_kans

        oordelen = [duiding_kans(k) for k in (5, 20, 45, 70, 95)]
        assert oordelen == [
            "vrijwel uitgesloten",
            "kleine kans",
            "reele kans",
            "waarschijnlijk",
            "vrijwel zeker",
        ]
