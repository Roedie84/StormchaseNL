"""0.59.1: de dashboardstrategie in een klein, apart bestand.

De frontend van Home Assistant wacht maar een paar seconden tot
ll-strategy-dashboard-stormchase geregistreerd is. Het grote script
(~110 KB, kaarten plus strategie) haalde dat bij een trage verbinding (Nabu
Casa, mobiel) of vlak na een herstart niet altijd: "Timeout waiting for
strategy element". Nu registreert stormchase-dashboard.js (alleen de
strategieklassen) de strategie direct; het grote bestand houdt de kaarten.
"""

import asyncio
import json
import re
import shutil
import subprocess
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
WWW = BRON / "www"
KLEIN = WWW / "stormchase-dashboard.js"
GROOT = WWW / "stormchase-strategy.js"


def _strategieblok(tekst: str) -> str:
    start = tekst.index('const KAART = "stormchase-hud-card";')
    eind = tekst.index("class StormchaseDashboardStrategy")
    eind = tekst.index("\n}\n", eind) + 3
    return tekst[start:eind]


# --- het kleine bestand ---------------------------------------------------


class TestKleinBestand:
    @pytest.fixture
    def script(self):
        assert KLEIN.is_file(), "stormchase-dashboard.js ontbreekt"
        return KLEIN.read_text(encoding="utf-8")

    def test_klein(self, script):
        assert len(script.encode("utf-8")) < 16_000

    def test_alleen_ascii(self, script):
        assert all(ord(c) < 128 for c in script)

    def test_haakjes_in_balans_en_niet_afgekapt(self, script):
        for o, s in (("{", "}"), ("(", ")"), ("[", "]")):
            assert script.count(o) == script.count(s)
        assert script.rstrip().endswith(");")

    def test_registreert_beide_strategieen_met_guard(self, script):
        assert "if (!customElements.get(naam))" in script
        for naam in ("ll-strategy-view-stormchase", "ll-strategy-dashboard-stormchase"):
            assert f'registreer("{naam}"' in script

    def test_hangt_niet_af_van_de_kaarten(self, script):
        assert "StormchaseHudCard" not in script
        assert "extends HTMLElement" not in script
        assert "customCards" not in script
        # Kaarttype alleen als tekst
        assert "type: `custom:${KAART}`" in script

    def test_laadt_niets_extern(self, script):
        for patroon in (r"\bimport\s*\(", r"^\s*import\s", r"\bfetch\(", r"XMLHttpRequest"):
            assert not re.search(patroon, script, re.M), patroon

    def test_strategieblok_identiek_aan_groot_bestand(self, script):
        groot = GROOT.read_text(encoding="utf-8")
        assert _strategieblok(script) == _strategieblok(groot)


# --- uitvoer van generate(): klein, groot en samen gelijk ------------------

_HARNAS = """
const reg = {}; const defs = [];
globalThis.window = globalThis;
globalThis.innerWidth = 0;
globalThis.HTMLElement = class {};
globalThis.HTMLTemplateElement = class {};
globalThis.customElements = { get: (n) => reg[n], define: (n, k) => { if (reg[n]) throw new Error("dubbel " + n); reg[n] = k; defs.push(n); } };
globalThis.document = { querySelector: () => null };
globalThis.performance = { getEntriesByType: () => [] };
globalThis.location = { href: "http://ha.local/" };
console.info = () => {};
for (const f of process.argv.slice(2)) await import(f);
const hass = {
  config: { latitude: 52.1, longitude: 6.6 },
  states: {
    "sensor.stormchase_afstand": { entity_id: "sensor.stormchase_afstand", state: "12", attributes: {} },
    "sensor.stormchase_actieve_locatie": { entity_id: "sensor.stormchase_actieve_locatie", state: "thuis", attributes: { latitude: 52.234, longitude: 6.789 } },
    "binary_sensor.stormchase_onweer": { entity_id: "binary_sensor.stormchase_onweer", state: "off", attributes: {} },
    "weather.stormchase": { entity_id: "weather.stormchase", state: "rainy", attributes: {} },
    "light.keuken": { entity_id: "light.keuken", state: "on", attributes: {} },
  },
};
const leeg = { config: { latitude: 51.9, longitude: 5.1 }, states: {} };
const configs = [{}, { title: "Onweer", distance_entity: "sensor.x" },
  { maps: { blitzortung: true, satelliet: true, windy: false }, map_ratio: "50%" },
  { maps: false, alle_waarden: false }, { latitude: 50, longitude: 4 }];
const uit = {};
for (const [i, c] of configs.entries()) {
  uit["dash" + i] = await reg["ll-strategy-dashboard-stormchase"].generate(c, hass);
  uit["leeg" + i] = await reg["ll-strategy-dashboard-stormchase"].generate(c, leeg);
  uit["view" + i] = await reg["ll-strategy-view-stormchase"].generate(c, hass);
}
console.log(JSON.stringify({ uit, defs }));
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js niet beschikbaar")
def test_generate_identiek_klein_groot_en_samen(tmp_path):
    harnas = tmp_path / "harnas.mjs"
    harnas.write_text(_HARNAS, encoding="utf-8")

    def draai(*bestanden):
        uit = subprocess.run(
            ["node", str(harnas), *(b.as_uri() for b in bestanden)],
            capture_output=True, text=True, timeout=60, check=True,
        )
        return json.loads(uit.stdout.strip().splitlines()[-1])

    klein = draai(KLEIN)
    groot = draai(GROOT)
    samen = draai(KLEIN, GROOT)
    omgekeerd = draai(GROOT, KLEIN)

    assert klein["uit"] == groot["uit"] == samen["uit"] == omgekeerd["uit"]
    # Het kleine bestand registreert de strategie zonder kaart
    assert klein["defs"] == ["ll-strategy-view-stormchase", "ll-strategy-dashboard-stormchase"]
    # Samen: elk element precies een keer (de harnas gooit bij dubbel)
    assert sorted(samen["defs"]) == sorted(omgekeerd["defs"]) == sorted(
        ["stormchase-hud-card", "ll-strategy-view-stormchase", "ll-strategy-dashboard-stormchase"]
    )
    dash = klein["uit"]["dash0"]
    assert [v["path"] for v in dash["views"]] == ["stormchase", "kaarten", "waarden"]
    assert dash["views"][0]["cards"] == [{"type": "custom:stormchase-hud-card"}]
    # Kaarten volgen de actieve locatie, Alle waarden de entiteiten
    assert "lat=52.23" in json.dumps(dash["views"][1])
    assert dash["views"][2]["sections"][0]["cards"][0]["entities"] == [
        "binary_sensor.stormchase_onweer",
        "sensor.stormchase_actieve_locatie",
        "sensor.stormchase_afstand",
        "weather.stormchase",
    ]


# --- registratie van de bronnen (frontend.py) -----------------------------


class NepBronnen:
    def __init__(self, items=None):
        self.items = [dict(i) for i in (items or [])]
        self.volgnr = 100
        self.log = []

    async def async_get_info(self):
        return {"resources": len(self.items)}

    def async_items(self):
        return list(self.items)

    async def async_create_item(self, data):
        self.volgnr += 1
        self.items.append({"id": str(self.volgnr), "type": data["res_type"], "url": data["url"]})
        self.log.append(("create", data["url"]))

    async def async_update_item(self, item_id, data):
        for item in self.items:
            if item["id"] == item_id:
                item.update(type=data["res_type"], url=data["url"])
        self.log.append(("update", item_id, data["url"]))

    async def async_delete_item(self, item_id):
        self.items = [i for i in self.items if i["id"] != item_id]
        self.log.append(("delete", item_id))


class NepHttp:
    def __init__(self, bestaand=()):
        self.paden = []
        self.bestaand = set(bestaand)

    async def async_register_static_paths(self, configs):
        for c in configs:
            if c.url_path in self.bestaand:
                raise RuntimeError("route bestaat al")
            self.paden.append(c)
            self.bestaand.add(c.url_path)


@pytest.fixture
def fe(monkeypatch):
    """frontend.py laden met minimale stand-ins voor Home Assistant."""
    extra = []

    frontend_mod = types.ModuleType("homeassistant.components.frontend")
    frontend_mod.add_extra_js_url = lambda hass, url, es5=False: extra.append(url)
    frontend_mod.remove_extra_js_url = lambda hass, url, es5=False: extra.remove(url)

    http_mod = types.ModuleType("homeassistant.components.http")

    class StaticPathConfig:
        def __init__(self, url_path, path, cache_headers=True):
            self.url_path, self.path, self.cache_headers = url_path, path, cache_headers

    http_mod.StaticPathConfig = StaticPathConfig

    core_mod = types.ModuleType("homeassistant.core")
    core_mod.HomeAssistant = object

    dt_mod = types.ModuleType("homeassistant.util.dt")
    dt_mod.utcnow = lambda: datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)
    util_mod = types.ModuleType("homeassistant.util")
    util_mod.dt = dt_mod

    for naam, mod in {
        "homeassistant": types.ModuleType("homeassistant"),
        "homeassistant.components": types.ModuleType("homeassistant.components"),
        "homeassistant.components.frontend": frontend_mod,
        "homeassistant.components.http": http_mod,
        "homeassistant.core": core_mod,
        "homeassistant.util": util_mod,
        "homeassistant.util.dt": dt_mod,
    }.items():
        monkeypatch.setitem(sys.modules, naam, mod)

    bron = (BRON / "frontend.py").read_text(encoding="utf-8")
    bron = bron.replace("from .const import", "from const import")
    mod = types.ModuleType("stormchase_frontend_test")
    mod.__file__ = str(BRON / "frontend.py")
    exec(compile(bron, mod.__file__, "exec"), mod.__dict__)
    mod.EXTRA = extra
    return mod


def _hass(bronnen=None, http=None, data=None):
    hass = types.SimpleNamespace()
    hass.http = http or NepHttp()
    hass.data = dict(data or {})
    if bronnen is not None:
        hass.data["lovelace"] = types.SimpleNamespace(resources=bronnen)
    return hass


T = int(datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc).timestamp())
KLEIN_URL = f"/stormchase/stormchase-dashboard.js?v=0.59.1&t={T}"
GROOT_URL = f"/stormchase/stormchase-strategy.js?v=0.59.1&t={T}"


def test_beide_paden_met_cache_headers(fe):
    hass = _hass(NepBronnen())
    asyncio.run(fe.async_register_frontend(hass, "0.59.1"))
    assert [(c.url_path, Path(c.path).name, c.cache_headers) for c in hass.http.paden] == [
        ("/stormchase/stormchase-dashboard.js", "stormchase-dashboard.js", True),
        ("/stormchase/stormchase-strategy.js", "stormchase-strategy.js", True),
    ]
    for c in hass.http.paden:
        assert Path(c.path).is_file()


def test_nieuwe_installatie_maakt_twee_bronnen(fe):
    bronnen = NepBronnen()
    hass = _hass(bronnen)
    asyncio.run(fe.async_register_frontend(hass, "0.59.1"))
    assert [(i["type"], i["url"]) for i in bronnen.items] == [
        ("module", KLEIN_URL),
        ("module", GROOT_URL),
    ]
    # Ook via add_extra_js_url, de kleine eerst
    assert fe.EXTRA == [KLEIN_URL, GROOT_URL]


def test_update_werkt_bij_en_ruimt_dubbel_en_verweesd_op(fe):
    bronnen = NepBronnen(
        [
            {"id": "1", "type": "module", "url": "/stormchase/stormchase-strategy.js?v=0.59.0&t=1"},
            {"id": "2", "type": "module", "url": "/stormchase/stormchase-strategy.js?v=0.58.4&t=0"},
            {"id": "3", "type": "module", "url": "/stormchase/oud-bestand.js?v=0.40.0"},
            {"id": "4", "type": "module", "url": "/hacsfiles/button-card/button-card.js"},
            {"id": "5", "type": "module", "url": "/local/stormchase-eigen.js"},
        ]
    )
    hass = _hass(bronnen)
    asyncio.run(fe.async_register_frontend(hass, "0.59.1"))
    urls = sorted(i["url"] for i in bronnen.items)
    assert urls == sorted(
        [GROOT_URL, KLEIN_URL, "/hacsfiles/button-card/button-card.js", "/local/stormchase-eigen.js"]
    )
    # De bestaande bron is bijgewerkt (zelfde id), niet vervangen
    assert next(i for i in bronnen.items if i["url"] == GROOT_URL)["id"] == "1"
    assert ("delete", "2") in bronnen.log and ("delete", "3") in bronnen.log


def test_tweede_start_zelfde_url_doet_niets(fe):
    bronnen = NepBronnen()
    hass = _hass(bronnen)
    asyncio.run(fe.async_register_frontend(hass, "0.59.1"))
    bronnen.log.clear()
    asyncio.run(fe.async_register_frontend(hass, "0.59.1"))
    assert bronnen.log == []
    assert len(bronnen.items) == 2
    # Geen opstapeling in de extra-js-lijst bij een herlaad
    assert fe.EXTRA == [KLEIN_URL, GROOT_URL]


def test_herlaad_na_update_zonder_herstart(fe):
    """Oude versie zette True en registreerde alleen het grote pad."""
    http = NepHttp(bestaand={"/stormchase/stormchase-strategy.js"})
    hass = _hass(NepBronnen(), http=http, data={"stormchase_frontend_registered": True})
    asyncio.run(fe.async_register_frontend(hass, "0.59.1"))
    assert [c.url_path for c in http.paden] == ["/stormchase/stormchase-dashboard.js"]
    assert hass.data["stormchase_frontend_registered"] == {
        "/stormchase/stormchase-strategy.js",
        "/stormchase/stormchase-dashboard.js",
    }


def test_yaml_modus_valt_terug_op_extra_js(fe):
    hass = _hass(None)
    asyncio.run(fe.async_register_frontend(hass, "0.59.1"))
    assert fe.EXTRA == [KLEIN_URL, GROOT_URL]
    assert len(hass.http.paden) == 2


def test_const():
    import const

    assert const.DASHBOARD_URL == "/stormchase/stormchase-dashboard.js"
    assert const.FRONTEND_FILES[0] == (const.DASHBOARD_FILE, const.DASHBOARD_URL)
    assert const.FRONTEND_FILES[1] == (const.STRATEGY_FILE, const.STRATEGY_URL)


def test_versie():
    manifest = json.loads((BRON / "manifest.json").read_text(encoding="utf-8"))
    assert tuple(int(x) for x in manifest["version"].split(".")) >= (0, 59, 1)
