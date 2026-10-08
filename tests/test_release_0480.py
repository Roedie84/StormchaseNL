"""0.48.0: de weerentiteit volgt de radar als het nu regent.

8 oktober: bui van 11:50 tot 12:21 (Buienradar tot 1,0 mm/u, `regen_verwacht`
aan), maar weather.stormchase bleef "sunny". Pas om 12:46, toen het droog was,
werd het "cloudy". De conditie kwam alleen uit de weercode van Open-Meteo.
"""

import ast
import json
from pathlib import Path

import pytest

from conditie import (
    RADAR_MAX_LEEFTIJD_S,
    RADAR_REGEN_MMU,
    RADAR_STORTBUI_MMU,
    huidige_conditie,
    radar_intensiteit,
    wmo_conditie,
)

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"


def _wmo() -> dict:
    """WMO_CONDITIES uit const.py, zonder de module te importeren."""
    boom = ast.parse((BRON / "const.py").read_text(encoding="utf-8"))
    for knoop in ast.walk(boom):
        if (
            isinstance(knoop, ast.Assign)
            and getattr(knoop.targets[0], "id", "") == "WMO_CONDITIES"
        ):
            return ast.literal_eval(knoop.value)
    raise AssertionError("WMO_CONDITIES niet gevonden")


WMO = _wmo()


class TestDrempels:
    def test_waarden(self):
        assert RADAR_REGEN_MMU == 0.1
        assert RADAR_STORTBUI_MMU == 4.0

    def test_standaard_regendrempel_ongewijzigd(self):
        tekst = (BRON / "const.py").read_text(encoding="utf-8")
        assert "DEFAULT_RAIN_THRESHOLD = 0.1" in tekst
        assert "DEFAULT_RAIN_LEAD = 10" in tekst


class TestHuidigeConditie:
    def test_waarneming_8_oktober(self):
        # Open-Meteo zei zon, de radar 1,0 mm/u: regen wint.
        model = wmo_conditie(0, WMO, True)
        assert model == "sunny"
        assert huidige_conditie(model, 1.0) == "rainy"

    @pytest.mark.parametrize("model", ["sunny", "clear-night", "partlycloudy", "cloudy", "fog", None])
    def test_regen_wint_van_droog_model(self, model):
        assert huidige_conditie(model, 0.1) == "rainy"

    def test_net_onder_drempel_blijft_model(self):
        assert huidige_conditie("sunny", 0.09) == "sunny"
        assert huidige_conditie("cloudy", 0.0) == "cloudy"

    def test_geen_radar_blijft_model(self):
        assert huidige_conditie("sunny", None) == "sunny"
        assert huidige_conditie("partlycloudy", "onzin") == "partlycloudy"

    def test_stortbui(self):
        assert huidige_conditie("sunny", 3.99) == "rainy"
        assert huidige_conditie("sunny", 4.0) == "pouring"
        assert huidige_conditie("cloudy", 12.0) == "pouring"

    def test_radar_licht_dempt_model_stortbui(self):
        # De radar is actueler dan de modelcode.
        assert huidige_conditie("pouring", 0.5) == "rainy"

    def test_onweer_dichtbij(self):
        assert huidige_conditie("sunny", 0.2, onweer_dichtbij=True) == "lightning-rainy"
        assert huidige_conditie("cloudy", 6.0, onweer_dichtbij=True) == "lightning-rainy"

    def test_onweerscode_model_blijft_bij_regen(self):
        assert huidige_conditie("lightning-rainy", 5.0) == "lightning-rainy"

    def test_onweer_zonder_regen_verandert_niets(self):
        assert huidige_conditie("cloudy", 0.0, onweer_dichtbij=True) == "cloudy"

    @pytest.mark.parametrize("model", ["snowy", "snowy-rainy", "hail"])
    def test_soort_neerslag_van_model_blijft(self, model):
        assert huidige_conditie(model, 2.0) == model


class TestNacht:
    def test_heldere_nacht_droog(self):
        model = wmo_conditie(0, WMO, False)
        assert model == "clear-night"
        assert huidige_conditie(model, 0.0) == "clear-night"
        assert huidige_conditie(model, None) == "clear-night"

    def test_heldere_nacht_met_regen(self):
        assert huidige_conditie(wmo_conditie(1, WMO, False), 0.6) == "rainy"

    def test_dag_blijft_zon(self):
        assert wmo_conditie(0, WMO, True) == "sunny"
        assert wmo_conditie(2, WMO, False) == "partlycloudy"

    def test_onbekende_code(self):
        assert wmo_conditie(None, WMO) is None
        assert wmo_conditie(1234, WMO) is None
        assert wmo_conditie("x", WMO) is None


class TestRadarIntensiteit:
    def test_vers(self):
        assert radar_intensiteit({"intensiteit": 1.0}, 60) == 1.0

    def test_te_oud(self):
        # Terugval van een uur oud mag de conditie niet sturen.
        assert radar_intensiteit({"intensiteit": 1.0}, RADAR_MAX_LEEFTIJD_S + 1) is None

    def test_onbekende_leeftijd_of_geen_data(self):
        assert radar_intensiteit({"intensiteit": 1.0}, None) is None
        assert radar_intensiteit(None, 10) is None
        assert radar_intensiteit({}, 10) is None


class TestAansluiting:
    """weather.py gebruikt de radar en luistert naar regen en onweer."""

    tekst = (BRON / "weather.py").read_text(encoding="utf-8")

    def test_conditie_gebruikt_radar(self):
        assert "huidige_conditie(" in self.tekst
        assert "radar_intensiteit(" in self.tekst

    def test_luistert_naar_regen_en_onweer(self):
        assert 'gegevens.get("rain")' in self.tekst
        assert 'gegevens.get("storm")' in self.tekst
        assert "async_add_listener" in self.tekst

    def test_onweer_dichtbij_zelfde_regel_als_binary_sensor(self):
        assert "afstand < storm.warn_distance" in self.tekst

    def test_verwachting_blijft_op_model(self):
        # Alleen de huidige conditie volgt de radar, de verwachting niet.
        assert self.tekst.count('condition=_conditie(op("weather_code"))') == 2


def test_versie_0480():
    versie = json.loads((BRON / "manifest.json").read_text())["version"]
    assert tuple(int(d) for d in versie.split(".")) >= (0, 48, 0)
