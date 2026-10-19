"""0.54.2: meerdere ensemblemodellen proberen.

Na 0.54.1 bleek live dat icon_d2_eps geen bruikbare CAPE-leden meer geeft en
dat gefs025 geen geldige modelnaam is: de bron stond (terecht) op fout en de
kans bleef unknown. Nu worden geldige modellen op volgorde geprobeerd.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

import const  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BRON = ROOT / "custom_components" / "stormchase"


def test_kandidaten_op_volgorde():
    k = const.ENSEMBLE_KANDIDATEN
    assert k[0] == "icon_d2_eps"
    assert {"icon_eu_eps", "icon_seamless_eps", "ecmwf_ifs025", "gfs025"} <= set(k)
    assert len(k) == len(set(k))


def test_coordinator_loopt_de_kandidaten_af():
    bron = (BRON / "coordinator.py").read_text(encoding="utf-8")
    assert "for model in ENSEMBLE_KANDIDATEN:" in bron
    # een falende kandidaat is geen bronfout; pas als geen enkele lukt
    i = bron.index("for model in ENSEMBLE_KANDIDATEN:")
    stuk = bron[i:i + 2500]
    assert 'fouten_ensemble.append(f"{model}: {err}")' in stuk
    assert stuk.count('stats.bronnen["ensemble_leden"].fout(') == 1


def test_versie():
    manifest = json.loads((BRON / "manifest.json").read_text())
    # 0.56.0: niet vastpinnen op deze versie, wel niet ouder
    assert tuple(int(x) for x in manifest["version"].split(".")) >= (0, 54, 2)
    assert "## [0.54.2]" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
