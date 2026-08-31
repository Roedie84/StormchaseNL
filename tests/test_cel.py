"""Celtracking: clusteren, richting bepalen en de passage uitrekenen."""

import pytest

from cel import (
    frequentie,
    frequentietrend,
    kompasrichting,
    naar_graden,
    naar_km,
    volg_cel,
    zoek_cellen,
)

IK = (49.65, 6.81)


def spoor_van_beweging(startafstand_km, zijdelings_km, snelheid_kmh, stappen=10):
    """Bouw een reeks waarnemingen van een cel die langs een rechte lijn gaat.

    De cel begint westelijk van ons en beweegt naar het oosten. Met
    zijdelings_km schuift de baan noordelijk op, zodat hij ernaast passeert.
    """
    resultaat = None
    geschiedenis = []

    for stap in range(stappen):
        t = stap * 60.0
        x = -startafstand_km + snelheid_kmh * t / 3600
        lat, lon = naar_graden(x, zijdelings_km, *IK)
        resultaat = volg_cel([(lat, lon)], geschiedenis, *IK, t)
        geschiedenis = resultaat["geschiedenis"]

    return resultaat


class TestOmrekenen:
    def test_heen_en_terug(self):
        lat, lon = naar_graden(30, -20, *IK)
        x, y = naar_km(lat, lon, *IK)
        assert x == pytest.approx(30, abs=0.1)
        assert y == pytest.approx(-20, abs=0.1)

    @pytest.mark.parametrize(
        "graden,verwacht", [(0, "N"), (45, "NO"), (90, "O"), (180, "Z"), (350, "N")]
    )
    def test_kompasrichting(self, graden, verwacht):
        assert kompasrichting(graden) == verwacht


class TestClusteren:
    def test_twee_buien_gescheiden(self):
        punten = [(49.9, 6.6), (49.92, 6.62), (49.88, 6.58),
                  (50.6, 7.4), (50.62, 7.42), (50.58, 7.38)]
        cellen = zoek_cellen(punten, *IK)
        assert len(cellen) == 2
        assert cellen[0]["afstand"] < cellen[1]["afstand"]
        assert all(c["inslagen"] == 3 for c in cellen)

    def test_dichtstbijzijnde_eerst(self):
        cellen = zoek_cellen([(49.9, 6.6), (50.6, 7.4)], *IK)
        assert cellen == sorted(cellen, key=lambda c: c["afstand"])

    def test_geen_inslagen(self):
        assert zoek_cellen([], *IK) == []


class TestBeweging:
    def test_richting_en_snelheid(self):
        cel = spoor_van_beweging(60, 0, 50)
        assert cel["richting"] == "O"
        assert cel["snelheid"] == pytest.approx(50, abs=2)

    def test_recht_erop_af(self):
        """Een cel die je middenop raakt passeert op nul kilometer.

        Op dertig kilometer bij vijftig per uur duurt dat 36 minuten, binnen
        het venster waarin de voorspelling betrouwbaar is gebleken.
        """
        cel = spoor_van_beweging(30, 0, 50)
        assert cel["passage_afstand"] == pytest.approx(0, abs=0.5)
        assert cel["passage_over"] > 0

    def test_schampt_erlangs(self):
        """Vijftien kilometer ernaast blijft vijftien kilometer."""
        cel = spoor_van_beweging(30, 15, 50)
        assert cel["passage_afstand"] == pytest.approx(15, abs=0.5)

    def test_trekt_weg(self):
        """Een cel die al voorbij is krijgt geen passagetijd."""
        geschiedenis = []
        cel = None
        for stap in range(10):
            t = stap * 60.0
            lat, lon = naar_graden(20 + 50 * t / 3600, 0, *IK)
            cel = volg_cel([(lat, lon)], geschiedenis, *IK, t)
            geschiedenis = cel["geschiedenis"]
        assert cel["passage_over"] is None

    def test_te_kort_geen_uitspraak(self):
        """Onder de twee minuten valt er niets te zeggen over de richting."""
        cel = spoor_van_beweging(60, 0, 50, stappen=2)
        assert cel["richting"] is None

    def test_spoor_breekt_bij_andere_cel(self):
        """Springt het zwaartepunt te ver, dan begint het spoor opnieuw."""
        geschiedenis = [(0.0, 49.9, 6.6), (60.0, 49.92, 6.62)]
        ver_weg = naar_graden(200, 0, *IK)
        cel = volg_cel([ver_weg], geschiedenis, *IK, 120.0)
        assert len(cel["geschiedenis"]) == 1


class TestFrequentie:
    def test_inslagen_per_minuut(self):
        nu = 1000.0
        stempels = [nu - 300 + i * 10 for i in range(30)]
        assert frequentie(stempels, nu) == pytest.approx(6.0, abs=0.2)

    def test_toename(self):
        nu = 1000.0
        stempels = [nu - 500 + i * 25 for i in range(8)] + [nu - 250 + i * 5 for i in range(45)]
        assert "toe" in frequentietrend(stempels, nu)

    def test_afname(self):
        nu = 1000.0
        stempels = [nu - 500 + i * 5 for i in range(50)] + [nu - 200 + i * 40 for i in range(4)]
        assert "af" in frequentietrend(stempels, nu)

    def test_te_weinig(self):
        assert frequentietrend([1.0, 2.0], 1000.0) == "te weinig gegevens"


class TestMeerdereCellen:
    """Elke bui apart volgen, zoals op professionele stormkaarten.

    Een enkele cel volgen zegt niets over de bui die van de andere kant
    komt. Elke cel houdt daarom een eigen spoor bij.
    """

    def bouw(self, opzet, stappen=8, snelheid=45):
        """Laat een aantal cellen naar het oosten trekken."""
        from cel import naar_graden, volg_cellen

        sporen = []
        cellen = []
        for stap in range(stappen):
            t = stap * 60.0
            punten = []
            for dx, dy, aantal in opzet:
                lat, lon = naar_graden(dx + snelheid * t / 3600, dy, *IK)
                punten += [(lat + i * 0.008, lon + i * 0.008) for i in range(aantal)]
            cellen, sporen = volg_cellen(punten, sporen, *IK, t)
        return cellen

    def test_elke_cel_wordt_gevonden(self):
        cellen = self.bouw([(-70, -20, 35), (20, 30, 12), (60, -60, 3)])
        assert len(cellen) == 3

    def test_elke_cel_heeft_een_eigen_koers(self):
        cellen = self.bouw([(-70, -20, 35), (20, 30, 12)])
        for cel in cellen:
            assert cel["richting"] == "O"
            assert cel["snelheid"] == pytest.approx(45, abs=3)

    def test_intensiteit_volgt_de_activiteit(self):
        cellen = self.bouw([(-70, -20, 35), (20, 30, 12), (60, -60, 3)])
        naar_aantal = {c["inslagen"]: c["intensiteit"] for c in cellen}

        assert naar_aantal[35] == "rood"
        assert naar_aantal[12] == "oranje"
        assert naar_aantal[3] == "geel"

    def test_drempels(self):
        from cel import intensiteit

        assert intensiteit(0) == "geel"
        assert intensiteit(7) == "geel"
        assert intensiteit(8) == "oranje"
        assert intensiteit(24) == "oranje"
        assert intensiteit(25) == "rood"

    def test_sporen_blijven_gekoppeld(self):
        """Twee cellen mogen elkaars spoor niet overnemen."""
        cellen = self.bouw([(-70, -40, 20), (-70, 40, 20)])
        assert len(cellen) == 2
        for cel in cellen:
            assert len(cel["spoor"]) >= 4

    def test_zonder_inslagen(self):
        from cel import volg_cellen

        cellen, sporen = volg_cellen([], [], *IK, 0.0)
        assert cellen == []
        assert sporen == []


class TestPassagegrens:
    """Ver vooruit is de passage niet meer betrouwbaar.

    Gemeten over echte buien: tot een kwartier vooruit 0,2 kilometer ernaast,
    tot drie kwartier 3,8 kilometer, en daarboven 16,9 kilometer met een
    trefkans van een op drie.
    """

    def test_binnen_de_grens(self):
        from cel import passage

        uitkomst = passage((-30, 0), (50, 0))
        assert uitkomst is not None
        assert uitkomst[0] == 36

    def test_te_ver_vooruit_geeft_niets(self):
        from cel import passage

        assert passage((-80, 0), (50, 0)) is None

    def test_grens_is_op_metingen_gebaseerd(self):
        from cel import MAX_PASSAGE_MINUTEN

        assert MAX_PASSAGE_MINUTEN == 45

    def test_eigen_grens_meegeven(self):
        from cel import passage

        assert passage((-80, 0), (50, 0), grens=120) is not None

    def test_wegtrekkende_cel_blijft_leeg(self):
        from cel import passage

        assert passage((30, 0), (50, 0)) is None


class TestVoorrand:
    """Bij een buienlijn ligt het zwaartepunt ver van de voorrand.

    Gemeten geval: dichtstbijzijnde inslag op 4,3 kilometer terwijl het
    zwaartepunt van dezelfde cel op 53 kilometer lag. De passage meldde toen
    34 minuten terwijl de bui er al was.
    """

    def buienlijn(self, stappen=8, snelheid=90):
        from cel import naar_graden, volg_cellen

        sporen = []
        cellen = []
        for stap in range(stappen):
            t = stap * 60.0
            punten = []
            for km in range(4, 100, 4):
                lat, lon = naar_graden(-km + snelheid * t / 3600, (km - 50) * 0.3, *IK)
                punten.append((lat, lon))
            cellen, sporen = volg_cellen(punten, sporen, *IK, t)
        return cellen[0]

    def test_voorrand_ligt_dichterbij_dan_het_zwaartepunt(self):
        """Ook binnen een enkele cel scheelt de rand met het midden.

        Sinds buienlijnen worden opgeknipt is dat verschil kleiner, maar het
        blijft bestaan: een cel van veertig kilometer heeft een rand die
        merkbaar dichterbij ligt dan zijn zwaartepunt.
        """
        cel = self.buienlijn()
        assert cel["rand_afstand"] < cel["afstand"]

    def test_passage_rekent_vanaf_de_voorrand(self):
        """Anders meldt hij een half uur terwijl de bui er al is."""
        cel = self.buienlijn()
        assert cel["passage_over"] < 10

    def test_compacte_bui_verandert_nauwelijks(self):
        """Bij een kleine cel liggen rand en zwaartepunt dicht bij elkaar."""
        from cel import naar_graden, volg_cellen

        sporen = []
        cellen = []
        for stap in range(8):
            t = stap * 60.0
            lat, lon = naar_graden(-30 + 50 * t / 3600, 0, *IK)
            punten = [(lat + i * 0.01, lon + i * 0.01) for i in range(10)]
            cellen, sporen = volg_cellen(punten, sporen, *IK, t)

        cel = cellen[0]
        assert abs(cel["afstand"] - cel["rand_afstand"]) < 10

    def test_sorteren_op_voorrand(self):
        """Een lange bui met de rand vlakbij komt voor een compacte verderop."""
        from cel import naar_graden, zoek_cellen

        punten = []
        # Lange lijn: rand op 10 km, zwaartepunt ver weg
        for km in range(10, 90, 4):
            punten.append(naar_graden(-km, 40, *IK))
        # Compacte bui op 30 km
        for i in range(5):
            punten.append(naar_graden(30 + i * 0.5, -40, *IK))

        cellen = zoek_cellen(punten, *IK)
        assert cellen[0]["rand_afstand"] < cellen[1]["rand_afstand"]


class TestBuienlijnOpknippen:
    """Een buienlijn is geen cel.

    Het zwaartepunt van een lange lijn schuift heen en weer naarmate er
    inslagen bijkomen en afvallen, en die verschuiving werd als beweging
    gelezen. Een lijn van Arnhem tot Duisburg leverde zo een koers pal naar
    het zuiden op, terwijl de buien naar het oosten trokken.
    """

    def lijn(self, lengte=50, stap=2):
        from cel import naar_graden

        return [naar_graden(-40 + i * stap, 60 - i * stap, *IK) for i in range(lengte)]

    def test_lange_lijn_wordt_opgeknipt(self):
        from cel import zoek_cellen

        assert len(zoek_cellen(self.lijn(), *IK)) > 3

    def test_compacte_bui_blijft_een_cel(self):
        from cel import naar_graden, zoek_cellen

        compact = [naar_graden(-30 + i * 0.3, 5 + i * 0.3, *IK) for i in range(20)]
        assert len(zoek_cellen(compact, *IK)) == 1

    def test_omvang_wordt_goed_gemeten(self):
        from cel import MAX_CELGROOTTE_KM, _omvang

        assert _omvang(self.lijn(), *IK) > MAX_CELGROOTTE_KM

    def test_koers_wijst_de_goede_kant_op(self):
        """Na het opknippen volgt elk stuk de werkelijke verplaatsing."""
        from cel import naar_graden, volg_cellen

        sporen = []
        cellen = []
        for stap in range(10):
            t = stap * 60.0
            punten = [
                naar_graden(-50 + i * 2 + 60 * t / 3600, 50 - i * 2.5, *IK)
                for i in range(40)
            ]
            cellen, sporen = volg_cellen(punten, sporen, *IK, t)

        richtingen = {c["richting"] for c in cellen if c["richting"]}

        # Oostwaarts, dus geen enkele cel mag naar het zuiden of westen wijzen
        assert richtingen
        assert not richtingen & {"Z", "ZW", "W", "ZZW", "WZW"}
