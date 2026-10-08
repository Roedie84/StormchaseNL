"""0.47.0: een herstart of herlaadbeurt verandert niets.

Home Assistant wordt hier vaak herstart (zestien keer op 7 oktober). Tot
0.47.0 gingen daarbij open voorspellingen, de 30/30-schuilregel, celsporen,
de naderingsreeks, tellers, wachttijden en de al gemelde waarschuwingen
verloren, en werd de validatie na 60 uitkomsten niet meer bewaard.
"""

import json
from datetime import datetime, timedelta, timezone
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

from herstart import (  # noqa: E402
    GEMELD_ZONDER_EINDE_S,
    MAX_LEEFTIJD_S,
    Bewaarplan,
    gemeld_naar_opslag,
    gemeld_uit_opslag,
    inslagtijd,
    puntsleutel,
    snoei_storm,
    tijden_naar_opslag,
    tijden_uit_opslag,
)
from nadering import Naderingstrend  # noqa: E402
from stats import Statistieken  # noqa: E402
from validatie import MAX_UITKOMSTEN, Validatie  # noqa: E402

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
NU = 1_791_000_000.0


def _json(data):
    """Zoals de Store het bewaart en teruggeeft."""
    return json.loads(json.dumps(data))


# ---- 1. Validatie wordt ook bewaard als de lijst vol is ----


class TestValidatie:
    def test_teller_loopt_door_als_de_lijst_vol_is(self):
        val = Validatie([{"soort": "regen"}] * MAX_UITKOMSTEN)
        assert val.afgerond == MAX_UITKOMSTEN
        voor = val.wijzigingen
        val.voorspel("regen", NU, 10, {})
        val.uitgekomen("regen", NU + 600)
        assert len(val.uitkomsten) == MAX_UITKOMSTEN
        assert val.afgerond == MAX_UITKOMSTEN + 1
        assert val.wijzigingen == voor + 2

    def test_coordinator_slaat_op_bij_elke_wijziging(self):
        bron = (BRON / "coordinator.py").read_text(encoding="utf-8")
        assert "len(val.uitkomsten) != self._bewaarde_uitkomsten" not in bron
        assert "self.validatie.wijzigingen != self._bewaarde_wijzigingen" in bron
        assert "async_delay_save(self.validatie.naar_opslag" in bron

    def test_open_voorspellingen_overleven_een_herstart(self):
        val = Validatie()
        val.voorspel("passage", NU, 20, {"verwachte_afstand": 8.0, "cel": 4})
        val.voorspel("regen", NU, 10, {"verwachte_piek": 1.2})
        bewaard = _json(val.naar_opslag())

        terug = Validatie(bewaard["uitkomsten"], bewaard["open"], bewaard["afgerond"])
        assert terug.open == val.open
        # En ze worden gewoon afgerekend
        terug.passage_afgerond(NU + 20 * 60, 9.0)
        assert terug.uitkomsten[-1]["raak"] is True
        assert terug.afgerond == 1

    def test_oude_opslag_zonder_open_en_teller(self):
        val = Validatie([{"soort": "regen"}] * 5, None, None)
        assert val.open == {}
        assert val.afgerond == 5

    def test_kapotte_open_voorspelling_valt_weg(self):
        val = Validatie([], {"regen": {"gemaakt_op": "x"}, "aankomst": [], 3: {}})
        assert val.open == {}

    def test_verlopen_open_voorspelling_wordt_na_herstart_afgerekend(self):
        val = Validatie()
        val.voorspel("aankomst", NU, 10, {})
        terug = Validatie([], _json(val.naar_opslag())["open"])
        terug.verlopen(NU + 3600)
        assert terug.open == {}
        assert terug.uitkomsten[-1]["uitgekomen"] is False


# ---- 7. Inslagen met hun eigen tijd ----


class TestInslagtijd:
    def test_eigen_tijd_als_datetime(self):
        moment = datetime.fromtimestamp(NU - 120, tz=timezone.utc)
        assert inslagtijd({"publication_date": moment}, NU - 5, NU) == NU - 120

    def test_eigen_tijd_als_tekst_en_nanoseconden(self):
        tekst = datetime.fromtimestamp(NU - 60, tz=timezone.utc).isoformat()
        assert inslagtijd({"publication_date": tekst}, NU, NU) == pytest.approx(NU - 60)
        assert inslagtijd({"time": int((NU - 30) * 1e9)}, NU, NU) == pytest.approx(NU - 30)

    def test_terugval_op_last_changed(self):
        assert inslagtijd({"latitude": 52}, NU - 400, NU) == NU - 400
        assert inslagtijd(None, NU - 400, NU) == NU - 400
        assert inslagtijd({"publication_date": "onzin"}, NU - 400, NU) == NU - 400

    def test_nooit_in_de_toekomst(self):
        assert inslagtijd({"timestamp": NU + 999}, NU, NU) == NU

    def test_coordinator_gebruikt_de_eigen_tijd(self):
        bron = (BRON / "coordinator.py").read_text(encoding="utf-8")
        blok = bron[bron.index("def _uit_geo_location") : bron.index("def _count_rings")]
        assert "inslagtijd(" in blok
        assert "stempel = dt_util.utcnow().timestamp()" not in blok
        assert "_herstelde_punten" in blok


# ---- 6, 8. Schuilregel, cellen en nadering ----


def _bewaard(opgeslagen_op=NU - 60, **extra):
    data = {
        "opgeslagen_op": opgeslagen_op,
        "punten": [[NU - 100, 52.0, 6.5], [NU - 5000, 52.1, 6.6]],
        "inslagen": [[NU - 100, 12.0], [NU - 9000, 30.0]],
        "celspoor": [[NU - 200, 52.0, 6.5], [NU - 100, 52.01, 6.51]],
        "celsporen": [
            {"id": 3, "punten": [[NU - 100, 52.0, 6.5]]},
            {"id": 7, "punten": [[NU - 4000, 51.0, 6.0]]},
        ],
        "volgend_celkenmerk": 9,
        "min_per_cel": {"3": 12.5, "7": 4.0, "5": 2.0},
        "behoud_cellen": [5],
        "laatste_dichtbij": NU - 600,
        "was_schuilen": True,
        "was_nearby": True,
        "was_approaching": False,
    }
    data.update(extra)
    return _json(data)


class TestSnoeiStorm:
    def test_verse_toestand_komt_terug(self):
        uit = snoei_storm(_bewaard(), NU)
        assert uit["punten"] == [(NU - 100, 52.0, 6.5)]
        assert uit["celspoor"][-1] == (NU - 100, 52.01, 6.51)
        assert [s["id"] for s in uit["celsporen"]] == [3]
        assert uit["laatste_dichtbij"] == NU - 600
        assert uit["was_schuilen"] is True
        assert uit["was_nearby"] is True
        assert uit["was_approaching"] is False

    def test_oude_cellen_en_punten_vallen_weg(self):
        uit = snoei_storm(_bewaard(), NU)
        assert all(t >= NU - MAX_LEEFTIJD_S for t, _, _ in uit["punten"])
        assert 7 not in {s["id"] for s in uit["celsporen"]}

    def test_kenmerk_loopt_door_en_min_per_cel_met_gehele_sleutels(self):
        uit = snoei_storm(_bewaard(), NU)
        assert uit["volgend_celkenmerk"] == 9
        # Cel 3 leeft nog, cel 5 hoort bij een open passagevoorspelling
        assert uit["min_per_cel"] == {3: 12.5, 5: 2.0}

    def test_kenmerk_nooit_lager_dan_een_bewaard_spoor(self):
        uit = snoei_storm(_bewaard(volgend_celkenmerk=2), NU)
        assert uit["volgend_celkenmerk"] == 8

    def test_inslagen_volgen_het_ringvenster(self):
        uit = snoei_storm(_bewaard(), NU, inslag_leeftijd=7200)
        assert uit["inslagen"] == [(NU - 100, 12.0)]

    def test_vlaggen_alleen_na_een_korte_onderbreking(self):
        uit = snoei_storm(_bewaard(opgeslagen_op=NU - 2 * 3600), NU)
        assert uit["was_schuilen"] is None
        assert uit["was_nearby"] is None
        # De tijd zelf blijft; de schuilregel rekent af tegen de naloop
        assert uit["laatste_dichtbij"] == NU - 600

    @pytest.mark.parametrize("bewaard", [None, [], "x", {}, {"punten": "x", "celsporen": [1]}])
    def test_onbruikbare_opslag(self, bewaard):
        uit = snoei_storm(bewaard, NU)
        assert uit["punten"] == [] and uit["celsporen"] == []
        assert uit["volgend_celkenmerk"] == 1
        assert uit["was_schuilen"] is None

    def test_herlaadbeurt_telt_een_inslag_niet_dubbel(self):
        """Dezelfde inslag na een herlaadbeurt geeft dezelfde sleutel."""
        uit = snoei_storm(_bewaard(), NU)
        sleutels = {puntsleutel(*p) for p in uit["punten"]}
        assert puntsleutel(NU - 100.00001, 52.000001, 6.5) in sleutels


class TestSchuilregelOverHerstart:
    """De 30/30-regel na een herstart: geen tweede 'ga naar binnen', wel 'veilig'.

    Nagebootst met dezelfde overgangslogica als _fire_events: een event bij
    False -> True (schuilen) en bij True -> False (veilig); None is
    'nog niet bekend' en levert geen event op.
    """

    @staticmethod
    def _ronde(vorige, schuilen):
        events = []
        if schuilen and vorige is False:
            events.append("schuilen")
        elif not schuilen and vorige:
            events.append("veilig")
        return schuilen, events

    @staticmethod
    def _schuilen(laatste_dichtbij, nu):
        return laatste_dichtbij is not None and (nu - laatste_dichtbij) / 60 < 30

    def test_geen_dubbele_schuilmelding_en_veilig_komt(self):
        uit = snoei_storm(_bewaard(laatste_dichtbij=NU - 600), NU)
        vorige = uit["was_schuilen"]
        vorige, events = self._ronde(vorige, self._schuilen(uit["laatste_dichtbij"], NU))
        assert events == []
        later = NU + 25 * 60
        vorige, events = self._ronde(vorige, self._schuilen(uit["laatste_dichtbij"], later))
        assert events == ["veilig"]

    def test_coordinator_bewaart_de_schuiltijd(self):
        bron = (BRON / "coordinator.py").read_text(encoding="utf-8")
        assert '"laatste_dichtbij": self._laatste_dichtbij' in bron
        assert 'self._laatste_dichtbij = schoon["laatste_dichtbij"]' in bron
        assert 'self._was_schuilen = schoon["was_schuilen"]' in bron


class TestNadering:
    def _trend(self):
        trend = Naderingstrend(900, 3)
        for i, afstand in enumerate((30.0, 28.0, 26.0, 24.0)):
            inslag = datetime.fromtimestamp(NU - 300 + i * 60, tz=timezone.utc)
            trend.bij(NU - 300 + i * 60, afstand, inslag)
        return trend

    def test_snelheid_blijft_na_herstart(self):
        trend = self._trend()
        terug = Naderingstrend(900, 3)
        terug.herstel(_json(trend.naar_opslag()), NU)
        assert terug.snelheid(NU) == trend.snelheid(NU)
        assert list(terug.metingen) == list(trend.metingen)

    def test_zelfde_inslag_na_herstart_is_geen_nieuw_punt(self):
        trend = self._trend()
        terug = Naderingstrend(900, 3)
        terug.herstel(_json(trend.naar_opslag()), NU)
        laatste = datetime.fromtimestamp(NU - 300 + 180, tz=timezone.utc)
        assert terug.bij(NU, 24.0, laatste) is False

    def test_oude_reeks_valt_weg(self):
        trend = self._trend()
        terug = Naderingstrend(900, 3)
        terug.herstel(_json(trend.naar_opslag()), NU + 3600)
        assert not terug.metingen
        assert terug.snelheid(NU + 3600) is None


# ---- 3. Gemelde waarschuwingen ----


class TestGemeld:
    def test_heen_en_terug(self):
        gemeld = {"urn:1": {"tot": NU + 3600, "gemeld_op": NU - 60}}
        assert gemeld_uit_opslag(_json(gemeld_naar_opslag(gemeld)), NU) == gemeld

    def test_verlopen_valt_weg(self):
        gemeld = {
            "oud": {"tot": NU - 1, "gemeld_op": NU - 7200},
            "zonder_einde_oud": {"tot": None, "gemeld_op": NU - GEMELD_ZONDER_EINDE_S - 1},
            "zonder_einde": {"tot": None, "gemeld_op": NU - 60},
        }
        assert set(gemeld_uit_opslag(_json(gemeld), NU)) == {"zonder_einde"}

    def test_rommel_wordt_genegeerd(self):
        assert gemeld_uit_opslag(None, NU) == {}
        assert gemeld_uit_opslag({"a": "b", "c": {"tot": "x"}}, NU) == {}

    def test_coordinator_bewaart_en_laadt_voor_de_eerste_ronde(self):
        alerts = (BRON / "alerts.py").read_text(encoding="utf-8")
        assert "self._gemeld: dict[str, dict] = {}" in alerts
        assert "self.bewaarplan.plan()" in alerts
        init = (BRON / "__init__.py").read_text(encoding="utf-8")
        assert init.index('waarschuwingen.herstel_gemeld(staat.get("gemeld"))') < init.index(
            "await waarschuwingen.async_refresh()"
        )


# ---- 9. Wachttijden en tellers ----


class TestWachttijden:
    def test_heen_en_terug_als_wandkloktijd(self):
        moment = datetime.fromtimestamp(NU - 300, tz=timezone.utc)
        bewaard = _json(tijden_naar_opslag({"onweer": moment, "regen": None}))
        assert bewaard == {"onweer": NU - 300}
        assert tijden_uit_opslag(bewaard, NU) == {"onweer": NU - 300}

    def test_tijd_in_de_toekomst_valt_weg(self):
        assert tijden_uit_opslag({"onweer": NU + 3600, "wind": True}, NU) == {}

    def test_notifier_bewaart_elke_wachttijd(self):
        bron = (BRON / "notifier.py").read_text(encoding="utf-8")
        for regel in (
            "self._laatste = dt_util.utcnow()",
            "self._laatste_regen = dt_util.utcnow()",
            "self._laatste_wind = dt_util.utcnow()",
            "self._laatste_weer[soort] = dt_util.utcnow()",
        ):
            na = bron[bron.index(regel) + len(regel) :][:80]
            assert "self._plan_opslag()" in na, regel


class TestTellers:
    def test_heen_en_terug(self):
        stats = Statistieken()
        stats.bronnen["radar"].gelukt = 12
        stats.bronnen["radar"].mislukt = 2
        stats.bronnen["radar"].op_rij_mislukt = 1
        stats.bronnen["radar"].laatste_succes = datetime(2026, 10, 8, 9, tzinfo=timezone.utc)
        stats.bronnen["radar"].laatste_fout = "HTTP 500"
        stats.regen_via_buienradar = 4
        stats.noteer_event("nearby")
        stats.noteer_melding("nearby")
        stats.meldingen_mislukt = 1

        terug = Statistieken()
        terug.herstel_tellers(_json(stats.tellers_naar_opslag()))
        assert terug.tellers_naar_opslag() == stats.tellers_naar_opslag()
        assert terug.bronnen["radar"].hapert() == stats.bronnen["radar"].hapert()

    def test_rommel_wordt_genegeerd(self):
        stats = Statistieken()
        stats.herstel_tellers(
            {"bronnen": {"radar": {"gelukt": -3, "laatste_succes": "x"}, "onbekend": {}},
             "events": {"nearby": True, "nieuw": 4}, "meldingen_mislukt": "veel"}
        )
        assert stats.bronnen["radar"].gelukt == 0
        assert stats.bronnen["radar"].laatste_succes is None
        assert stats.events["nearby"] == 0 and "nieuw" not in stats.events
        assert stats.meldingen_mislukt == 0

    def test_events_en_meldingen_plannen_het_bewaren(self):
        stats = Statistieken()
        geteld = []
        stats._bij_wijziging = lambda: geteld.append(1)
        stats.noteer_event("nearby")
        stats.noteer_melding("nearby")
        assert len(geteld) == 2

    def test_tellers_staan_naast_de_dagtellers(self):
        init = (BRON / "__init__.py").read_text(encoding="utf-8")
        assert '"tellers": stats.tellers_naar_opslag()' in init
        assert 'stats.herstel_tellers(bewaarde_bron.get("tellers"))' in init


class TestBewaarplan:
    def test_plant_eenmaal_tot_er_geschreven_is(self):
        gepland = []
        plan = Bewaarplan(lambda: gepland.append(1))
        plan.plan()
        plan.plan()
        assert gepland == [1]
        plan.geschreven()
        plan.plan()
        assert gepland == [1, 1]

    def test_zonder_planner_niets(self):
        plan = Bewaarplan()
        plan.plan()
        assert plan.gepland is False


# ---- 2, 4, 5. Opzet, ontladen en afsluiten ----


class TestOpzet:
    @pytest.fixture
    def init(self):
        return (BRON / "__init__.py").read_text(encoding="utf-8")

    def test_toestand_terug_voor_de_eerste_ronde_en_de_notifier(self, init):
        start = init.index("notifier.start()")
        eerste = init.index("async_config_entry_first_refresh()")
        for regel in (
            'storm.herstel(staat.get("storm"))',
            'notifier.herstel(staat.get("notifier"))',
            "onderdeel.herstel_laatste(laatste.get(naam))",
            'bewaard.get("open")',
        ):
            assert init.index(regel) < start < eerste, regel

    def test_meldingenschakelaar_bekend_voor_de_notifier_start(self, init):
        assert init.index("gegevens[DATA_NOTIFY_ENABLED] = stand") < init.index(
            "notifier.start()"
        )
        assert "last_states.get(entity_id)" in init
        assert 'f"{entry.entry_id}_notifications"' in init
        switch = (BRON / "switch.py").read_text(encoding="utf-8")
        assert 'f"{entry.entry_id}_notifications"' in switch

    def test_ontladen_schrijft_alles_meteen_weg(self, init):
        ontladen = init[init.index("async def async_unload_entry") :]
        assert "await _async_bewaar_alles(hass, gegevens)" in ontladen
        assert "plan.plannen = None" in ontladen
        assert "storm.opslag = None" in ontladen
        bewaar = init[init.index("async def _async_bewaar_alles") :]
        bewaar = bewaar[: bewaar.index("\nasync def ")]
        assert "await opslag.async_save(data())" in bewaar
        assert 'posities["opslag"].async_save' in bewaar
        for naam in ("validatie", "staat", "laatste", "bronstatistiek"):
            assert f'("{naam}", ' in init

    def test_afsluiten_schrijft_alles_meteen_weg(self, init):
        assert "async_listen_once(EVENT_HOMEASSISTANT_STOP, _bij_stoppen)" in init
        blok = init[init.index("async def _bij_stoppen") :][:300]
        assert "_async_bewaar_alles(hass, gegevens)" in blok


def test_versie_0470():
    versie = json.loads((BRON / "manifest.json").read_text())["version"]
    assert versie == "0.47.0"
