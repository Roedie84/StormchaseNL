"""Opbouw van de radar-URL's."""

import pytest

from radar import bouw_url, laatste_frame

OVERZICHT = {
    "version": "2.0",
    "host": "https://tilecache.rainviewer.com",
    "radar": {
        "past": [
            {"time": 1609401600, "path": "/v2/radar/1609401600"},
            {"time": 1609402200, "path": "/v2/radar/1609402200"},
        ]
    },
}


class TestFrame:
    def test_nieuwste_wint(self):
        """De reeks loopt van oud naar nieuw."""
        assert laatste_frame(OVERZICHT)["tijd"] == 1609402200

    def test_host_uit_het_overzicht(self):
        assert laatste_frame(OVERZICHT)["host"] == "https://tilecache.rainviewer.com"

    def test_terugval_op_standaardhost(self):
        zonder = {"radar": {"past": [{"time": 1, "path": "/v2/radar/1"}]}}
        assert "tilecache" in laatste_frame(zonder)["host"]

    @pytest.mark.parametrize(
        "payload", [None, {}, {"radar": {}}, {"radar": {"past": []}}]
    )
    def test_zonder_beelden(self, payload):
        assert laatste_frame(payload) is None

    def test_frame_zonder_pad(self):
        assert laatste_frame({"radar": {"past": [{"time": 1}]}}) is None


class TestUrl:
    def test_opbouw(self):
        url = bouw_url(laatste_frame(OVERZICHT), 49.6455, 6.8102)
        assert url == (
            "https://tilecache.rainviewer.com/v2/radar/1609402200"
            "/512/7/49.6455/6.8102/2/1_1.png"
        )

    def test_coordinaten_krijgen_altijd_decimalen(self):
        """RainViewer eist een punt in het getal, ook bij ronde waarden."""
        url = bouw_url(laatste_frame(OVERZICHT), 52.0, 6.0)
        assert "/52.0000/6.0000/" in url

    def test_zoom_wordt_afgekapt(self):
        """Boven zeven bestaat er geen zoomniveau."""
        url = bouw_url(laatste_frame(OVERZICHT), 52.1, 6.6, zoom=12)
        assert "/512/7/" in url

    def test_zoom_ondergrens(self):
        url = bouw_url(laatste_frame(OVERZICHT), 52.1, 6.6, zoom=0)
        assert "/512/1/" in url

    def test_onbekend_formaat_valt_terug(self):
        url = bouw_url(laatste_frame(OVERZICHT), 52.1, 6.6, formaat=1024)
        assert "/512/" in url

    def test_opties(self):
        url = bouw_url(
            laatste_frame(OVERZICHT), 52.1, 6.6, vloeiend=False, sneeuw=False
        )
        assert url.endswith("/0_0.png")

    def test_kleur_binnen_bereik(self):
        url = bouw_url(laatste_frame(OVERZICHT), 52.1, 6.6, kleur=99)
        assert "/8/1_1.png" in url

    def test_zonder_frame(self):
        assert bouw_url(None, 52.1, 6.6) is None


class TestTegels:
    """Kaarttegels rond een positie.

    RainViewer levert alleen de neerslaglaag. Zonder kaart eronder zweven er
    vlekken in het niets en is niet te zien waar de bui hangt.
    """

    def test_nulpunt(self):
        from radar import tegelpositie

        # Op zoom 1 ligt het snijpunt van evenaar en nulmeridiaan in het
        # midden van het raster van twee bij twee
        x, y = tegelpositie(0, 0, 1)
        assert x == pytest.approx(1.0)
        assert y == pytest.approx(1.0)

    def test_hoger_zoomniveau_verdubbelt(self):
        from radar import tegelpositie

        laag = tegelpositie(52.0, 6.0, 7)
        hoog = tegelpositie(52.0, 6.0, 8)
        assert hoog[0] == pytest.approx(laag[0] * 2)
        assert hoog[1] == pytest.approx(laag[1] * 2)

    def test_raster_is_compleet(self):
        from radar import tegelraster

        raster = tegelraster(52.0964, 6.641, 7)
        assert len(raster["tegels"]) == 9
        assert raster["afmeting"] == 768

    def test_middelpunt_ligt_in_het_raster(self):
        from radar import tegelraster

        raster = tegelraster(52.0964, 6.641, 7)
        assert 0 < raster["midden_x"] < raster["afmeting"]
        assert 0 < raster["midden_y"] < raster["afmeting"]

    def test_tegels_blijven_binnen_de_kaart(self):
        """Bij de polen mag de rij niet buiten het raster vallen."""
        from radar import tegelraster

        for breedtegraad in (84.0, -84.0):
            raster = tegelraster(breedtegraad, 6.0, 7)
            for tegel in raster["tegels"]:
                assert 0 <= tegel["y"] < 2 ** 7

    def test_rond_de_datumgrens(self):
        """Over de nulmeridiaan van 180 graden loopt de x-as door."""
        from radar import tegelraster

        raster = tegelraster(0.0, 179.9, 7)
        for tegel in raster["tegels"]:
            assert 0 <= tegel["x"] < 2 ** 7

    def test_urls(self):
        from radar import basiskaart_url, radartegel_url, tegelraster

        raster = tegelraster(52.0964, 6.641, 7)
        tegel = raster["tegels"][4]
        frame = {"host": "https://tilecache.rainviewer.com", "path": "/v2/radar/abc"}

        assert basiskaart_url(tegel, 7).endswith(f"/7/{tegel['x']}/{tegel['y']}.png")
        assert radartegel_url(frame, tegel, 7).endswith(
            f"/256/7/{tegel['x']}/{tegel['y']}/2/1_1.png"
        )

    def test_radartegel_zonder_frame(self):
        from radar import radartegel_url, tegelraster

        raster = tegelraster(52.0, 6.0, 7)
        assert radartegel_url(None, raster["tegels"][0], 7) is None


class TestBasiskaart:
    """De ondergrond mag geen sleutel vereisen.

    CARTO zette zijn donkere kaart achter een sleutel, wat een watermerk
    "API KEY REQUIRED" dwars over het radarbeeld opleverde.
    """

    def test_geen_sleutel_in_de_url(self):
        from radar import BASISKAART

        for verdacht in ("apikey", "api_key", "access_token", "key="):
            assert verdacht not in BASISKAART.lower()

    def test_url_bevat_de_tegelvelden(self):
        from radar import BASISKAART

        for veld in ("{z}", "{x}", "{y}"):
            assert veld in BASISKAART

    def test_herkenbare_naam_bij_het_ophalen(self):
        """OpenStreetMap vraagt om een herkenbare naam."""
        from radar import TEGEL_AGENT

        assert "Stormchase" in TEGEL_AGENT

    def test_demping_maakt_donkerder_maar_niet_zwart(self):
        from radar import KAART_HELDERHEID, KAART_KLEUR

        assert 0 < KAART_HELDERHEID < 1
        assert 0 < KAART_KLEUR <= 1


class TestInslagenOpHetBeeld:
    """Blikseminslagen op de juiste plek tekenen.

    De radar laat zien waar de neerslag hangt, de inslagen waar de bui echt
    actief is. Samen zie je of een cel aantrekt of uitdooft.
    """

    def test_eigen_positie_valt_op_het_middelpunt(self):
        from radar import pixelpositie, tegelraster

        raster = tegelraster(52.0964, 6.641, 7)
        px, py = pixelpositie(52.0964, 6.641, raster)

        assert px == pytest.approx(raster["midden_x"], abs=0.01)
        assert py == pytest.approx(raster["midden_y"], abs=0.01)

    def test_noordelijker_ligt_hoger_in_beeld(self):
        from radar import pixelpositie, tegelraster

        raster = tegelraster(52.0964, 6.641, 7)
        _, midden = pixelpositie(52.0964, 6.641, raster)
        _, noord = pixelpositie(53.0, 6.641, raster)

        assert noord < midden

    def test_oostelijker_ligt_rechter_in_beeld(self):
        from radar import pixelpositie, tegelraster

        raster = tegelraster(52.0964, 6.641, 7)
        midden, _ = pixelpositie(52.0964, 6.641, raster)
        oost, _ = pixelpositie(52.0964, 8.0, raster)

        assert oost > midden

    def test_buiten_beeld_geeft_niets(self):
        from radar import pixelpositie, tegelraster

        raster = tegelraster(52.0964, 6.641, 7)
        assert pixelpositie(41.0, 6.641, raster) is None

    def test_venster_is_een_kwartier(self):
        """Lang genoeg om verplaatsing te zien, kort genoeg om geen vlek te
        worden."""
        from radar import INSLAG_VENSTER

        assert 300 <= INSLAG_VENSTER <= 1800
