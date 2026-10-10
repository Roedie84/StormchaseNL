"""0.51.1 - het dashboard verspringt niet meer tijdens scrollen op mobiel."""
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "custom_components" / "stormchase" / "www" / "stormchase-strategy.js"


def _script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_panelen_vergelijken_met_de_vorige_opbouw():
    """Vergelijken met innerHTML is altijd 'anders' (de browser schrijft het
    anders terug), dus dan werd elk paneel bij elke update vervangen."""
    script = _script()
    assert "el.innerHTML !== html" not in script
    assert "if (this._html[paneel] === html) continue;" in script
    assert "kopEl.innerHTML !== kop" not in script


def test_tekenen_wacht_tot_het_scrollen_klaar_is():
    script = _script()
    assert "const scrolltNog = () =>" in script
    assert "if (scrolltNog()) {" in script
    for gebeurtenis in ("scroll", "touchstart", "touchmove", "touchend", "touchcancel", "wheel"):
        assert f'window.addEventListener("{gebeurtenis}"' in script
    assert "passive: true" in script


def test_alleen_ascii():
    assert all(ord(c) < 128 for c in _script())
