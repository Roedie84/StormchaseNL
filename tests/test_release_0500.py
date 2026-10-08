"""0.50.0: het dashboard als storm-chase-commandocentrum.

De strategie levert een panel-view met een eigen kaart
(<stormchase-hud-card>) in hetzelfde script: Shadow DOM, eigen opmaak,
geen HACS-kaarten en geen externe bestanden. Deze tests controleren de
broncode en, als Node.js beschikbaar is, de uitvoer van de strategie.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
JS = BRON / "www" / "stormchase-strategy.js"


@pytest.fixture(scope="module")
def script():
    return JS.read_text(encoding="utf-8")


def test_registreert_het_eigen_element(script):
    assert 'const KAART = "stormchase-hud-card";' in script
    assert "registreer(KAART, StormchaseHudCard);" in script
    assert "class StormchaseHudCard extends HTMLElement" in script
    assert 'this.attachShadow({ mode: "open" })' in script
    # De strategieen blijven bestaan
    for naam in ("ll-strategy-view-stormchase", "ll-strategy-dashboard-stormchase"):
        assert f'registreer("{naam}"' in script


def test_laadt_geen_externe_bestanden(script):
    """Geen CDN, geen import, geen externe stylesheet, lettertype of fetch."""
    verboden = [
        r"\bimport\s*\(",
        r"^\s*import\s",
        r"@import",
        r"<script",
        r"<link",
        r"url\(\s*['\"]?https?:",
        r"\bfetch\(",
        r"XMLHttpRequest",
        r"src=[\"']https?:",
        r"href=[\"']https?:",
    ]
    for patroon in verboden:
        assert not re.search(patroon, script, re.M), patroon

    # De enige externe adressen zijn de iframes in de tab Kaarten; die laadt
    # de ingebouwde iframe-kaart van Home Assistant, niet dit script.
    adressen = set(re.findall(r"https?://[^/\"'`\s]+", script))
    toegestaan = {
        "https://iradar.app",
        "https://gadgets.buienradar.nl",
        "https://embed.windy.com",
        "https://map.blitzortung.org",
        "https://www.meteox.com",
    }
    assert adressen <= toegestaan, adressen - toegestaan
    # In de kaart zelf (tot aan de strategie) staat geen enkel adres
    kaartdeel = script[: script.index("/* De strategie ")]
    assert not re.search(r"https?://", kaartdeel)


def test_geen_hacs_kaarten_meer(script):
    for kaart in ("mushroom", "apexcharts", "compass-card", "card_mod: { style: TILE"):
        assert kaart not in script


def test_kent_alle_entiteiten_van_de_integratie(script):
    """Elke translation_key van de integratie zit in de opzoektabel."""
    vertaling = json.loads((BRON / "translations" / "nl.json").read_text(encoding="utf-8"))
    for domein, items in vertaling["entity"].items():
        for sleutel in items:
            assert f'["{domein}", "{sleutel}",' in script, f"{domein}.{sleutel}"


def test_nieuwe_entiteiten_uit_0490(script):
    for net in (
        "stormchase_radar_vooruitblik",
        "stormchase_windstoten_gemeten",
        "stormchase_luchtdruk_gemeten",
        "stormchase_luchtdrukverandering_per_uur",
        "stormchase_luchtdrukverandering_per_3_uur",
        "stormchase_onweer_gemeten_bij_station",
        "stormchase_hagel_gemeten_bij_station",
    ):
        assert f'"{net}"' in script
    assert '"niveau_per_uur"' in script
    assert "knmi.push" in script


def test_live_en_zuinig(script):
    # Alleen panelen opnieuw tekenen waarvan een state veranderde
    assert "set hass(hass)" in script
    assert "const AFHANKELIJK = {" in script
    assert "if (s !== this._vorige[id])" in script
    # Uurverwachting via de websocket, met afmelden
    assert '"weather/subscribe_forecast"' in script
    assert "disconnectedCallback()" in script
    assert "_stopAbonnement()" in script
    # Opslag in de browser altijd binnen try
    for regel in re.findall(r".*localStorage.*", script):
        idx = script.index(regel)
        assert "try {" in script[max(0, idx - 200) : idx], regel


def test_toegankelijk_en_responsive(script):
    assert "prefers-reduced-motion" in script
    assert "container-type: inline-size" in script
    assert "@container (min-width: 1180px)" in script
    assert "@container (max-width: 520px)" in script
    assert "font-variant-numeric: tabular-nums" in script
    assert "backdrop-filter" in script


def test_frontend_cachebust_met_versie():
    """De URL van het script krijgt de versie mee, zodat browsers verversen."""
    bron = (BRON / "frontend.py").read_text(encoding="utf-8")
    assert 'versioned_url = f"{STRATEGY_URL}?v={version}&t={stempel}"' in bron
    assert "add_extra_js_url(hass, versioned_url)" in bron
    init = (BRON / "__init__.py").read_text(encoding="utf-8")
    assert "async_register_frontend(" in init


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js niet beschikbaar")
def test_strategie_levert_panel_view(tmp_path):
    """Voer de strategie uit in Node met een minimale browseromgeving."""
    proef = tmp_path / "proef.mjs"
    proef.write_text(
        """
const reg = {};
globalThis.window = globalThis;
globalThis.HTMLElement = class {};
globalThis.HTMLTemplateElement = class {};
globalThis.customElements = { get: (n) => reg[n], define: (n, k) => { reg[n] = k; } };
globalThis.document = { querySelector: () => null };
console.info = () => {};
await import(process.argv[2]);
const hass = {
  config: { latitude: 52.1, longitude: 6.6 },
  states: {
    "sensor.stormchase_afstand": { entity_id: "sensor.stormchase_afstand", state: "12", attributes: {} },
    "sensor.stormchase_actieve_locatie": { entity_id: "sensor.stormchase_actieve_locatie", state: "thuis", attributes: { latitude: 52.2, longitude: 6.7 } },
  },
};
const dash = await reg["ll-strategy-dashboard-stormchase"].generate({ title: "Onweer", distance_entity: "sensor.x" }, hass);
const view = await reg["ll-strategy-view-stormchase"].generate({}, hass);
console.log(JSON.stringify({ dash, view, kaart: typeof reg["stormchase-hud-card"], kaarten: (window.customCards || []).map((k) => k.type) }));
""",
        encoding="utf-8",
    )
    uit = subprocess.run(
        ["node", str(proef), JS.as_uri()], capture_output=True, text=True, timeout=60, check=True
    )
    data = json.loads(uit.stdout.strip().splitlines()[-1])
    hoofd = data["dash"]["views"][0]
    assert hoofd["type"] == "panel"
    assert hoofd["title"] == "Onweer"
    assert hoofd["cards"] == [
        {"type": "custom:stormchase-hud-card", "title": "Onweer", "distance_entity": "sensor.x"}
    ]
    paden = [v["path"] for v in data["dash"]["views"]]
    assert paden == ["stormchase", "kaarten", "waarden"]
    # Kaarten centreren op de actieve locatie
    assert "lat=52.20" in json.dumps(data["dash"]["views"][1])
    assert data["view"]["type"] == "panel"
    assert data["kaart"] == "function"
    assert "stormchase-hud-card" in data["kaarten"]


def test_versie_0500():
    versie = json.loads((BRON / "manifest.json").read_text())["version"]
    assert tuple(int(d) for d in versie.split(".")) >= (0, 50, 0)
