"""0.50.1: KNMI-radar in kleur, ook in de donkere stijl."""
import json
from pathlib import Path

BASIS = Path(__file__).resolve().parent.parent / "custom_components" / "stormchase"


def test_donker_is_in_kleur():
    bron = (BASIS / "const.py").read_text()
    assert '"donker": "rainrate-blue-to-purple/nearest"' in bron
    assert '"radar/nearest"' not in bron


def test_versie():
    manifest = json.loads((BASIS / "manifest.json").read_text())
    versie = tuple(int(x) for x in manifest["version"].split("."))
    assert versie >= (0, 50, 1)
