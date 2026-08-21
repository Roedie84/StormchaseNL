"""Onweersindices: schering, stabiliteit en het samenvattend oordeel."""

import pytest

from indices import (
    duiding_cape,
    duiding_schering,
    duiding_stabiliteit,
    duiding_vriesniveau,
    hagelkans,
    onweersverwachting,
    peiling,
    rotatiekans,
    total_totals,
    windschering,
)


class TestWindschering:
    def test_zelfde_richting_harder(self):
        """Alleen sneller waaien levert het snelheidsverschil op."""
        assert windschering(20, 270, 60, 270) == pytest.approx(40, abs=0.5)

    def test_draaiende_wind_levert_schering(self):
        """Gelijke snelheid maar gedraaid geeft toch schering."""
        assert windschering(40, 180, 40, 270) == pytest.approx(56.6, abs=0.5)

    def test_geen_verschil(self):
        assert windschering(30, 200, 30, 200) == 0.0

    def test_ontbrekende_gegevens(self):
        assert windschering(None, 200, 30, 200) is None


class TestPeiling:
    @pytest.mark.parametrize(
        "lat,lon,verwacht",
        [(53.16, 6.41, 0), (52.16, 7.41, 90), (51.16, 6.41, 180), (52.16, 5.41, 270)],
    )
    def test_hoofdrichtingen(self, lat, lon, verwacht):
        assert peiling(52.16, 6.41, lat, lon) == pytest.approx(verwacht, abs=1)


class TestDuiding:
    @pytest.mark.parametrize(
        "cape,verwacht",
        [(40, "nauwelijks energie"), (300, "weinig energie"),
         (900, "matige energie"), (1900, "veel energie"), (2800, "zeer veel energie")],
    )
    def test_cape(self, cape, verwacht):
        assert duiding_cape(cape) == verwacht

    @pytest.mark.parametrize(
        "tt,verwacht",
        [(41, "stabiel"), (47, "licht onstabiel"), (53, "onstabiel"), (58, "sterk onstabiel")],
    )
    def test_stabiliteit_via_total_totals(self, tt, verwacht):
        assert duiding_stabiliteit(None, tt) == verwacht

    def test_lifted_index_gaat_voor(self):
        """Is de Lifted Index er, dan telt die en niet Total Totals."""
        assert duiding_stabiliteit(-7, 41) == "sterk onstabiel"

    @pytest.mark.parametrize(
        "schering,verwacht",
        [(12, "zwak"), (38, "matig"), (61, "sterk"), (88, "supercelwaardig")],
    )
    def test_schering(self, schering, verwacht):
        assert duiding_schering(schering) == verwacht

    @pytest.mark.parametrize(
        "hoogte,verwacht",
        [(1200, "laag"), (2800, "gunstig voor hagel"), (4600, "te hoog voor hagel")],
    )
    def test_vriesniveau(self, hoogte, verwacht):
        assert duiding_vriesniveau(hoogte) == verwacht


class TestTotalTotals:
    def test_onweersdag(self):
        assert total_totals(18, 14, -12) == 56

    def test_stabiele_dag(self):
        assert total_totals(10, 0, -15) == 40

    def test_ontbrekend(self):
        assert total_totals(None, 14, -12) is None


class TestKansen:
    def test_rotatie_vraagt_beide(self):
        """Energie zonder schering roteert niet, en andersom ook niet."""
        veel_beide, _ = rotatiekans(2400, 90)
        alleen_energie, _ = rotatiekans(2400, 15)
        alleen_schering, _ = rotatiekans(100, 90)

        assert veel_beide == 100
        assert alleen_energie < 25
        assert alleen_schering < 10

    def test_hagel_smelt_bij_hoog_vriesniveau(self):
        laag, _ = hagelkans(2600, 70, 2800)
        hoog, _ = hagelkans(2600, 70, 4600)
        assert laag > hoog * 2

    def test_model_meldt_hagel(self):
        """WMO-code 96 tilt de score op, ook bij weinig energie."""
        score, detail = hagelkans(400, 20, 3000, 96)
        assert score >= 60
        assert detail["model_meldt_hagel"] is True


class TestOnweersverwachting:
    def test_stabiele_lucht_geeft_niets(self):
        oordeel, _, rang = onweersverwachting(2400, None, 41, 80)
        assert oordeel == "Geen onweer verwacht"
        assert rang == 0

    def test_weinig_energie_geeft_niets(self):
        _, _, rang = onweersverwachting(50, None, 55, 80)
        assert rang == 0

    def test_oplopende_ernst(self):
        rangen = [
            onweersverwachting(600, None, 49, 20)[2],
            onweersverwachting(1900, None, 53, 55)[2],
            onweersverwachting(2900, None, 58, 90)[2],
        ]
        assert rangen == sorted(rangen)
        assert rangen[-1] == 4

    def test_toelichting_noemt_de_onderdelen(self):
        _, toelichting, _ = onweersverwachting(1900, None, 53, 55)
        assert "energie" in toelichting
        assert "schering" in toelichting
