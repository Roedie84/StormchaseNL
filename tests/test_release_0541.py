"""0.54.1: onweerskans ensemble bleef sinds 11-10 op unknown (0 leden).

De bron `ensemble_leden` gaf 'geslaagd' zodra het antwoord een tijdreeks had,
ook als er voor de komende twaalf uur geen bruikbare CAPE-waarden in stonden.
Nu telt een model alleen als genoeg leden waarden hebben (anders het volgende
model, gefs025), en wordt het venster in de eigen tijdreeks van het ensemble
gezocht.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

from spreiding import MIN_LEDEN, ensemble, leden_pieken  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BRON = ROOT / "custom_components" / "stormchase"
TIJDEN = [f"2026-10-12T{u:02d}:00" for u in range(24)] + [f"2026-10-13T{u:02d}:00" for u in range(24)]


def _blok(leden=20, waarde=50.0, leeg=False):
    blok = {"time": TIJDEN}
    for i in range(leden):
        blok[f"cape_member{i:02d}"] = [None if leeg else waarde + i] * len(TIJDEN)
    return blok


def test_pieken_per_lid_in_het_venster():
    blok = _blok(leden=6)
    blok["cape_member03"][15] = 900.0  # binnen 13:00-24:59
    pieken = leden_pieken(blok, "2026-10-12T13:00")
    assert len(pieken) == 6 and max(pieken) == 900.0


def test_lege_waarden_geven_geen_leden():
    assert leden_pieken(_blok(leeg=True), "2026-10-12T13:00") == []


def test_eigen_tijdreeks_van_het_ensemble():
    # ensemble begint later dan de gewone voorspelling: het venster moet op
    # het eigen uur vallen, niet op de index van de gewone reeks
    blok = {"time": TIJDEN[12:], "cape": [None] * 1 + [10.0] * (len(TIJDEN) - 13)}
    pieken = leden_pieken(blok, "2026-10-12T13:00")
    assert pieken == [10.0]


def test_venster_voorbij_de_reeks():
    assert leden_pieken(_blok(), "2026-10-14T05:00") == []
    assert leden_pieken({}, "2026-10-12T13:00") == []


def test_stabiel_weer_geeft_nul_procent():
    uit = ensemble(leden_pieken(_blok(leden=30, waarde=0.0), "2026-10-12T13:00"))
    assert uit["leden"] == 30 and uit["kans_onweer"] == 0


class TestKoppeling:
    def test_model_alleen_bruikbaar_met_genoeg_leden(self):
        bron = (BRON / "coordinator.py").read_text(encoding="utf-8")
        assert 'len(leden_pieken(payload.get("hourly"), stamp_nu)) >= ENSEMBLE_MIN_LEDEN' in bron
        assert "\"geen ensemble met bruikbare leden\"" in bron
        assert 'pieken = leden_pieken((leden_payload or {}).get("hourly"), stamp)' in bron
        assert MIN_LEDEN == 5

    def test_versie(self):
        import json

        manifest = json.loads((BRON / "manifest.json").read_text())
        assert tuple(int(x) for x in manifest["version"].split(".")) >= (0, 54, 1)
        assert "## [0.54.1]" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
