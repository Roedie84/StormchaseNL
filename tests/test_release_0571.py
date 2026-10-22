"""0.57.1: kleinere bliksemstippen op de radar.

22-10 16:22 (screenshot): "Stormchase radar, kleinere bliksem stippen, deze
zijn veel te groot". Een actieve cel werd een gele vlek over de radar.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"


def test_stippen_kleiner():
    from radar import INSLAG_STRAAL_OUD, INSLAG_STRAAL_VERS

    assert INSLAG_STRAAL_VERS == 3 and INSLAG_STRAAL_OUD == 2
    bron = (ROOT / "image.py").read_text(encoding="utf-8")
    assert "straal = INSLAG_STRAAL_VERS if deel < 0.2 else INSLAG_STRAAL_OUD" in bron
    assert "straal = 6 if deel < 0.2 else 5" not in bron


def test_versie():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "0.57.1"
