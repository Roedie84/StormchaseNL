"""0.48.1: app-icoon via de brand-map in de integratie (HA 2026.3+)."""

import json
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BRON = ROOT / "custom_components" / "stormchase"
BRAND = BRON / "brand"


def _png_maat(pad: Path) -> tuple[int, int]:
    data = pad.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{pad.name} is geen PNG"
    return struct.unpack(">II", data[16:24])


@pytest.mark.parametrize(
    "naam,maat",
    [("icon.png", (256, 256)), ("icon@2x.png", (512, 512))],
)
def test_icoon_aanwezig_en_juiste_maat(naam, maat):
    assert _png_maat(BRAND / naam) == maat


@pytest.mark.parametrize("naam", ["logo.png", "logo@2x.png"])
def test_logo_aanwezig(naam):
    _png_maat(BRAND / naam)


@pytest.mark.parametrize(
    "naam", ["icon.png", "icon@2x.png", "logo.png", "logo@2x.png"]
)
def test_brand_gelijk_aan_root_brands(naam):
    # De root-map brands/ blijft de bron; de kopie mag niet afwijken.
    assert (BRAND / naam).read_bytes() == (ROOT / "brands" / naam).read_bytes()


def test_versie_0481():
    versie = json.loads((BRON / "manifest.json").read_text())["version"]
    assert tuple(int(d) for d in versie.split(".")) >= (0, 48, 1)
