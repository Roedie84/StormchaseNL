"""Bewolking van de kaartdienst, met herprojectie."""

import pytest

from radar import rastergrenzen, tegelraster
from wolken import STANDAARD_LAAG, STERKTE, mercatorrij, wms_url

RASTER = tegelraster(52.0964, 6.641, 7)
GRENZEN = rastergrenzen(RASTER)


class TestGrenzen:
    def test_noord_ligt_boven_zuid(self):
        zuid, west, noord, oost = GRENZEN
        assert noord > zuid
        assert oost > west

    def test_gebied_omsluit_de_locatie(self):
        zuid, west, noord, oost = GRENZEN
        assert zuid < 52.0964 < noord
        assert west < 6.641 < oost

    def test_heen_en_terug(self):
        """Van coordinaat naar tegel en terug moet uitkomen."""
        from radar import coordinaat_van_tegel, tegelpositie

        x, y = tegelpositie(52.0964, 6.641, 7)
        lat, lon = coordinaat_van_tegel(x, y, 7)

        assert lat == pytest.approx(52.0964, abs=0.001)
        assert lon == pytest.approx(6.641, abs=0.001)


class TestVerzoek:
    def test_hoekvolgorde(self):
        """In versie 1.3.0 komt de breedtegraad eerst bij EPSG:4326.

        Met de verkeerde volgorde komt er een leeg beeld terug, zonder
        foutmelding. Dat is lastig te vinden.
        """
        zuid, west, noord, oost = GRENZEN
        url = wms_url(GRENZEN, 768, 768)

        assert f"bbox={zuid},{west},{noord},{oost}" in url

    def test_bevat_de_vereiste_velden(self):
        url = wms_url(GRENZEN, 768, 768)

        for veld in ("service=WMS", "request=GetMap", "crs=EPSG:4326",
                     "width=768", "height=768", "transparent=true"):
            assert veld in url

    def test_standaardlaag(self):
        assert f"layers={STANDAARD_LAAG}" in wms_url(GRENZEN, 768, 768)

    def test_eigen_laag(self):
        assert "layers=msg_fes:cth" in wms_url(GRENZEN, 768, 768, "msg_fes:cth")


class TestHerprojectie:
    """Webmercator rekt de afstand tussen breedtegraden op.

    Een plat beeld ongewijzigd overleggen zou de bewolking tientallen
    kilometers verkeerd neerzetten.
    """

    def test_randen_vallen_samen(self):
        zuid, _, noord, _ = GRENZEN

        assert mercatorrij(0, 768, zuid, noord) == pytest.approx(0, abs=0.5)
        assert mercatorrij(767, 768, zuid, noord) == pytest.approx(767, abs=0.5)

    def test_midden_verschuift(self):
        """Het midden hoort niet op de helft te liggen."""
        zuid, _, noord, _ = GRENZEN
        midden = mercatorrij(384, 768, zuid, noord)

        assert midden != pytest.approx(383.5, abs=1)
        assert 360 < midden < 380

    def test_verloopt_monotoon(self):
        zuid, _, noord, _ = GRENZEN
        rijen = [mercatorrij(r, 768, zuid, noord) for r in range(0, 768, 32)]

        assert rijen == sorted(rijen)

    def test_sterkte_is_gedempt(self):
        assert 0.1 <= STERKTE <= 0.6


class TestAndereDiensten:
    """Dezelfde opbouw wordt voor meerdere kaartdiensten gebruikt."""

    def test_eigen_basisadres(self):
        url = wms_url(GRENZEN, 768, 768, "dwd:Niederschlagsradar",
                      "https://maps.dwd.de/geoserver/dwd/ows")

        assert url.startswith("https://maps.dwd.de/geoserver/dwd/ows?")
        assert "layers=dwd:Niederschlagsradar" in url

    def test_hoekvolgorde_geldt_ook_daar(self):
        """Dezelfde valkuil, dezelfde controle."""
        zuid, west, noord, oost = GRENZEN
        url = wms_url(GRENZEN, 512, 512, "dwd:Niederschlagsradar",
                      "https://maps.dwd.de/geoserver/dwd/ows")

        assert f"bbox={zuid},{west},{noord},{oost}" in url


class TestGrijstinten:
    """Bewolking in grijs, met vloeiende overgangen.

    De afgeleide producten komen met hun eigen palet: het wolkenmasker
    kleurt heldere gebieden groen en blauw, de wolktophoogte gebruikt een
    regenboogschaal met harde blokken. Over een kaart heen is dat
    onleesbaar, dus het beeld wordt zelf omgezet.
    """

    def test_heldere_lucht_verdwijnt(self):
        from wolken import DREMPEL, alfa_van_helderheid

        assert alfa_van_helderheid(0) == 0
        assert alfa_van_helderheid(DREMPEL) == 0

    def test_dichter_wordt_minder_doorzichtig(self):
        from wolken import alfa_van_helderheid

        waarden = [alfa_van_helderheid(v) for v in (100, 160, 220, 255)]
        assert waarden == sorted(waarden)
        assert waarden[0] > 0

    def test_nooit_volledig_dekkend(self):
        """De kaart eronder moet leesbaar blijven."""
        from wolken import alfa_van_helderheid

        assert alfa_van_helderheid(255) < 200

    def test_vervaging_maakt_de_overgang_zacht(self):
        from PIL import Image, ImageFilter

        from wolken import VERVAGING

        bron = Image.new("L", (400, 100), 30)
        bron.paste(Image.new("L", (200, 100), 210), (200, 0))
        zacht = bron.filter(ImageFilter.GaussianBlur(VERVAGING))

        def sprong(beeld):
            rij = [beeld.getpixel((x, 50)) for x in range(180, 220)]
            return max(abs(rij[i + 1] - rij[i]) for i in range(len(rij) - 1))

        assert sprong(bron) > 150
        assert sprong(zacht) < 50

    def test_wolk_blijft_staan_na_de_hele_bewerking(self):
        """Dezelfde stappen als in de verwerking: uitrekken, vervagen, drempel.

        De uitrekstap hoort erbij; zonder die stap blijft er boven heldere
        lucht een restje doorzicht staan.
        """
        from PIL import Image, ImageFilter, ImageOps

        from wolken import UITSNIJDING, VERVAGING, alfa_van_helderheid

        bron = Image.new("L", (400, 100), 30)
        bron.paste(Image.new("L", (200, 100), 210), (200, 0))

        bewerkt = ImageOps.autocontrast(bron, cutoff=UITSNIJDING).filter(
            ImageFilter.GaussianBlur(VERVAGING)
        )

        assert alfa_van_helderheid(bewerkt.getpixel((350, 50))) > 50
        assert alfa_van_helderheid(bewerkt.getpixel((50, 50))) == 0


class TestContrastUitrekken:
    """Het bereik van het bronbeeld verschilt per moment.

    Overdag lopen de gemeten temperaturen ver uiteen, 's nachts liggen ze
    dicht bij elkaar. Een vaste drempel op de ruwe waarden sneed daardoor
    's nachts vrijwel alle bewolking weg.
    """

    def maak(self, helder, bewolkt):
        from PIL import Image

        beeld = Image.new("L", (100, 100), helder)
        beeld.paste(Image.new("L", (50, 100), bewolkt), (50, 0))
        return beeld

    def test_nacht_zonder_uitrekken_geeft_nauwelijks_verschil(self):
        from wolken import alfa_van_helderheid

        # Waarden dicht bij elkaar, zoals in een nachtbeeld
        assert alfa_van_helderheid(130) - alfa_van_helderheid(90) < 40

    def test_nacht_na_uitrekken_geeft_wel_verschil(self):
        from PIL import ImageOps

        from wolken import UITSNIJDING, alfa_van_helderheid

        uitgerekt = ImageOps.autocontrast(self.maak(90, 130), cutoff=UITSNIJDING)

        helder = alfa_van_helderheid(uitgerekt.getpixel((10, 50)))
        bewolkt = alfa_van_helderheid(uitgerekt.getpixel((90, 50)))

        assert helder == 0
        assert bewolkt > 100

    def test_dag_en_nacht_komen_gelijk_uit(self):
        """Na uitrekken maakt het niet meer uit hoe het bereik eruitzag."""
        from PIL import ImageOps

        from wolken import UITSNIJDING, alfa_van_helderheid

        nacht = ImageOps.autocontrast(self.maak(90, 130), cutoff=UITSNIJDING)
        dag = ImageOps.autocontrast(self.maak(20, 230), cutoff=UITSNIJDING)

        assert alfa_van_helderheid(nacht.getpixel((90, 50))) == (
            alfa_van_helderheid(dag.getpixel((90, 50)))
        )

    def test_drempel_is_laag_genoeg(self):
        """Na uitrekken hoort de drempel alleen ruis weg te nemen."""
        from wolken import DREMPEL

        assert DREMPEL <= 40
