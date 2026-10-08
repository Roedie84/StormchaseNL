"""L-SC-002: gelukt/mislukt per bron per dag, bewaard over herstarts.

Live op 7 oktober: zestien herstarts op een dag, en na elke herstart begonnen
de tellers in de diagnostiek weer bij nul. De betrouwbaarheid van een bron
over dagen viel zo alleen uit de recorder te halen.
"""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

try:
    import homeassistant.util.dt  # noqa: F401
except ModuleNotFoundError:  # zonder HA-installatie: alleen utcnow is nodig
    import sys
    import types

    _dt = types.ModuleType("homeassistant.util.dt")
    _dt.utcnow = lambda: datetime.now(timezone.utc)
    for naam, mod in (
        ("homeassistant", types.ModuleType("homeassistant")),
        ("homeassistant.util", types.ModuleType("homeassistant.util")),
        ("homeassistant.util.dt", _dt),
    ):
        sys.modules.setdefault(naam, mod)
    sys.modules["homeassistant.util"].dt = _dt

from bronhistorie import BEWAAR_DAGEN, BronHistorie  # noqa: E402
from stats import BronStatus, Statistieken  # noqa: E402

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
DAG = date(2026, 10, 7)


# --- tellen ----------------------------------------------------------------


def test_telt_per_bron_per_dag():
    h = BronHistorie()
    h.noteer("radar", True, DAG)
    h.noteer("radar", True, DAG)
    h.noteer("radar", False, DAG)
    h.noteer("open_meteo", True, DAG + timedelta(days=1))

    d = h.als_dict()
    assert d["per_dag"]["2026-10-07"]["radar"] == {
        "gelukt": 2,
        "mislukt": 1,
        "slaagpercentage": 66.7,
    }
    assert d["per_dag"]["2026-10-08"]["open_meteo"]["gelukt"] == 1
    assert d["totaal"]["radar"] == {
        "gelukt": 2,
        "mislukt": 1,
        "dagen": 1,
        "slaagpercentage": 66.7,
    }
    assert d["aantal_dagen"] == 2


def test_nieuwste_dag_eerst_in_de_diagnostiek():
    h = BronHistorie()
    for i in range(3):
        h.noteer("radar", True, DAG + timedelta(days=i))
    assert list(h.als_dict()["per_dag"]) == ["2026-10-09", "2026-10-08", "2026-10-07"]


# --- over herstarts --------------------------------------------------------


def test_overleeft_een_herstart_via_de_opslag():
    voor = BronHistorie()
    for _ in range(5):
        voor.noteer("buienradar", True, DAG)
    voor.noteer("buienradar", False, DAG)

    # Zoals de Store het bewaart: als JSON
    bewaard = json.loads(json.dumps(voor.naar_opslag()))
    na = BronHistorie(bewaard)
    na.noteer("buienradar", True, DAG)

    telling = na.als_dict()["per_dag"]["2026-10-07"]["buienradar"]
    assert (telling["gelukt"], telling["mislukt"]) == (6, 1)


def test_zestien_herstarts_op_een_dag_tellen_door():
    """Het patroon van 7 oktober: na elke herstart een nieuwe Statistieken."""
    bewaard = None
    for _ in range(17):  # 16 herstarts = 17 draaiperiodes
        stats = Statistieken()
        historie = BronHistorie(bewaard)
        stats.koppel_historie(historie, vandaag=lambda: DAG)
        stats.bronnen["radar"].succes()
        stats.bronnen["radar"].succes()
        stats.bronnen["open_meteo"].fout(OSError("DNS"))
        # de tellers van deze draaiperiode zelf beginnen bij nul
        assert stats.bronnen["radar"].gelukt == 2
        bewaard = json.loads(json.dumps(historie.naar_opslag()))

    dag = BronHistorie(bewaard).als_dict()["per_dag"]["2026-10-07"]
    assert dag["radar"]["gelukt"] == 34
    assert dag["open_meteo"]["mislukt"] == 17


# --- rollend venster -------------------------------------------------------


def test_houdt_hooguit_bewaar_dagen_vast():
    h = BronHistorie()
    for i in range(BEWAAR_DAGEN + 5):
        h.noteer("radar", True, DAG + timedelta(days=i))
    assert len(h.dagen) == BEWAAR_DAGEN
    laatste = DAG + timedelta(days=BEWAAR_DAGEN + 4)
    assert h.dagen[-1] == laatste.isoformat()
    assert h.dagen[0] == (laatste - timedelta(days=BEWAAR_DAGEN - 1)).isoformat()


def test_oude_dagen_uit_de_opslag_vallen_af_bij_een_nieuwe_dag():
    oud = (DAG - timedelta(days=BEWAAR_DAGEN)).isoformat()
    h = BronHistorie({"dagen": {oud: {"radar": {"gelukt": 9, "mislukt": 0}}}})
    h.noteer("radar", True, DAG)
    assert h.dagen == ["2026-10-07"]


def test_dag_in_de_toekomst_valt_af():
    """Een verzette klok mag geen dag achterlaten die nooit meer verdwijnt."""
    h = BronHistorie({"dagen": {"2027-01-01": {"radar": {"gelukt": 1, "mislukt": 0}}}})
    h.noteer("radar", True, DAG)
    assert h.dagen == ["2026-10-07"]


# --- beschadigde opslag ----------------------------------------------------


@pytest.mark.parametrize(
    "bewaard",
    [None, [], "onzin", {"dagen": None}, {"dagen": []}, {"dagen": {"geen-datum": {}}}],
)
def test_onbruikbare_opslag_geeft_lege_historie(bewaard):
    h = BronHistorie(bewaard)
    assert h.dagen == []
    assert h.als_dict()["per_dag"] == {}


def test_rare_tellingen_worden_nul():
    h = BronHistorie(
        {
            "dagen": {
                "2026-10-07": {
                    "radar": {"gelukt": -3, "mislukt": "veel"},
                    "meting": {"gelukt": True, "mislukt": 2},
                    "kapot": "geen dict",
                }
            }
        }
    )
    dag = h.als_dict()["per_dag"]["2026-10-07"]
    assert dag["radar"]["gelukt"] == 0 and dag["radar"]["mislukt"] == 0
    assert dag["meting"] == {"gelukt": 0, "mislukt": 2, "slaagpercentage": 0.0}
    assert "kapot" not in dag


# --- koppeling met de statistieken ----------------------------------------


def test_elke_ronde_plant_een_schrijfactie():
    stats = Statistieken()
    geplant = []
    stats.koppel_historie(BronHistorie(), lambda: geplant.append(1), vandaag=lambda: DAG)
    stats.bronnen["meteoalarm"].succes()
    stats.bronnen["meteoalarm"].fout(OSError("x"))
    assert len(geplant) == 2


def test_niet_opnieuw_plannen_zolang_er_een_klaarstaat():
    """De Store schuift een uitgestelde schrijfactie bij elke aanvraag op;
    met de radar elke minuut zou er anders nooit iets weggeschreven worden."""
    h = BronHistorie()
    stats = Statistieken()
    geplant = []
    stats.koppel_historie(
        h, lambda: h.plan_opslag(lambda: geplant.append(1)), vandaag=lambda: DAG
    )
    for _ in range(10):
        stats.bronnen["radar"].succes()
    assert len(geplant) == 1
    h.naar_opslag()  # de Store schrijft weg
    stats.bronnen["radar"].succes()
    assert len(geplant) == 2


def test_diagnostiek_toont_de_dagtellers():
    stats = Statistieken()
    stats.koppel_historie(BronHistorie(), vandaag=lambda: DAG)
    stats.bronnen["icon_d2"].succes()
    d = stats.als_dict()
    assert d["bronnen_per_dag"]["per_dag"]["2026-10-07"]["icon_d2"]["gelukt"] == 1
    # de bestaande tellers sinds de herstart blijven zoals ze waren
    assert d["bronnen"]["icon_d2"]["gelukt"] == 1


def test_zonder_historie_niets_anders_dan_voorheen():
    stats = Statistieken()
    stats.bronnen["radar"].succes()
    assert stats.als_dict()["bronnen_per_dag"] is None


def test_een_fout_in_de_dagtellers_breekt_de_bron_niet():
    bron = BronStatus()

    def stuk(_):
        raise RuntimeError("opslag weg")

    bron.bij_uitkomst = stuk
    bron.succes()
    bron.fout(OSError("x"))
    bron.fout(OSError("x"))
    assert (bron.gelukt, bron.mislukt, bron.op_rij_mislukt) == (1, 2, 2)
    assert bron.hapert()


def test_bronstatus_attributen_blijven_klein():
    """De dagtellers horen in de diagnostiek, niet in de sensorattributen:
    die komen bij elke verandering in de recorder."""
    bron = BronStatus()
    bron.bij_uitkomst = lambda _: None
    assert "bij_uitkomst" not in bron.als_dict()
    assert "per_dag" not in bron.als_dict()


# --- opzet in __init__ -----------------------------------------------------


class TestOpzet:
    @pytest.fixture
    def bron(self):
        return (BRON / "__init__.py").read_text(encoding="utf-8")

    def test_gekoppeld_voor_de_eerste_ronde(self, bron):
        assert bron.index("stats.koppel_historie(") < bron.index(
            "async_config_entry_first_refresh"
        )

    def test_vertraagd_wegschrijven(self, bron):
        assert "async_delay_save(" in bron
        assert "plan_opslag(" in bron
        assert "BRONSTATISTIEK_VERTRAGING = 300" in bron

    def test_wegschrijven_bij_ontladen(self, bron):
        ontladen = bron[bron.index("async def async_unload_entry") :]
        # 0.47.0: via _async_bewaar_alles, samen met de andere opslag
        assert "await _async_bewaar_alles(hass, gegevens)" in ontladen
        assert '("bronstatistiek", bron_opslag, _bron_data)' in bron
        assert "bronhistorie.naar_opslag()" in bron
