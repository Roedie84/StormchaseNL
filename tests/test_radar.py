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
