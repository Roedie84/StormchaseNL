"""0.63.0: het regenbeeld voor thuis, los van de actieve locatie.

Ruud 16-11: "Kunnen we het opsplitsen? Tablet geeft voor thuis locatie?
Meldingen op iPhone voor actuele locatie?" De tracker stond op het werk
(12,9 km van huis) en het tablet thuis toonde de regen van het werk.
"""

from __future__ import annotations

import json
from pathlib import Path

from buienreeks import THUIS_IS_HIER_KM, afstand_km, thuis_is_hier, van_hoofd, voor_thuis_opgehaald

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
THUIS = (52.10, 6.64)
WERK = (52.08, 6.45)


def test_afstand_thuis_werk_is_ongeveer_dertien_km():
    assert 12.5 < afstand_km(THUIS, WERK) < 13.5
    assert afstand_km(THUIS, THUIS) == 0.0


def test_op_het_werk_is_niet_thuis_en_thuis_wel():
    assert thuis_is_hier(WERK, THUIS) is False
    assert thuis_is_hier(THUIS, THUIS) is True
    assert thuis_is_hier((52.105, 6.645), THUIS) is True          # ~650 m
    assert THUIS_IS_HIER_KM == 1.0


def test_onbekende_positie_telt_als_niet_thuis():
    assert thuis_is_hier(None, THUIS) is False
    assert thuis_is_hier((None, 6.6), THUIS) is False
    assert afstand_km(("x", 1), THUIS) is None


def test_de_naam_staat_in_alle_vertalingen_en_heeft_een_icoon():
    for bestand, naam in (("strings.json", "Rain outlook home"), ("translations/en.json", "Rain outlook home"),
                          ("translations/nl.json", "Regenbeeld thuis")):
        tekst = json.loads((BRON / bestand).read_text(encoding="utf-8"))
        assert tekst["entity"]["sensor"]["rain_summary_home"]["name"] == naam
    iconen = json.loads((BRON / "icons.json").read_text(encoding="utf-8"))
    assert iconen["entity"]["sensor"]["rain_summary_home"]["default"]


def test_de_sensor_en_de_coordinator_zijn_aangesloten():
    start = (BRON / "__init__.py").read_text(encoding="utf-8")
    assert "ThuisRainCoordinator(hass, entry, regen)" in start
    assert '"rain_home": regen_thuis' in start
    assert "regen.async_add_listener(regen_thuis.volg_hoofd)" in start
    # thuis telt niet mee in de statistiek en krijgt geen validatie of station
    assert "regen_thuis.stats" not in start and "regen_thuis.validatie" not in start
    sensor = (BRON / "sensor.py").read_text(encoding="utf-8")
    assert 'RainHomeSensor(regen_thuis, entry, RAIN_HOME_SUMMARY)' in sensor
    assert 'key="rain_summary_home"' in sensor


# ---- overnemen of zelf ophalen ----


def test_actieve_locatie_thuis_dan_neemt_hij_de_hoofdverwachting_over():
    assert van_hoofd(THUIS, THUIS, {"regent": True, "bron": "knmi"}) == {
        "regent": True, "bron": "knmi", "thuis_bron": "actieve locatie"}


def test_actieve_locatie_weg_dan_haalt_hij_zelf_op_voor_thuis():
    assert van_hoofd(WERK, THUIS, {"regent": True, "bron": "knmi"}) is None
    assert voor_thuis_opgehaald({"regent": False, "bron": "knmi"}) == {
        "regent": False, "bron": "knmi", "thuis_bron": "thuis"}


def test_zonder_hoofdverwachting_of_positie_haalt_hij_zelf_op():
    assert van_hoofd(THUIS, THUIS, None) is None
    assert van_hoofd(THUIS, THUIS, {}) is None
    assert van_hoofd(None, THUIS, {"regent": True}) is None


def test_de_hoofdverwachting_wordt_niet_aangepast():
    hoofd = {"regent": True}
    van_hoofd(THUIS, THUIS, hoofd)
    assert hoofd == {"regent": True}
    assert voor_thuis_opgehaald(None) is None


def _klasse() -> str:
    bron = (BRON / "rain.py").read_text(encoding="utf-8")
    return bron[bron.index("class ThuisRainCoordinator(RainCoordinator):"):]


def test_thuis_staat_vast_op_de_thuislocatie_en_meldt_niets():
    klasse = _klasse()
    assert 'return (self.hass.config.latitude, self.hass.config.longitude, "thuis")' in klasse
    assert "async_fire" not in klasse                       # geen gebeurtenis, dus geen melding
    assert "return self.hoofd._regencorrectie(bron)" in klasse
    assert "voor_thuis_opgehaald(await super()._haal_op())" in klasse
