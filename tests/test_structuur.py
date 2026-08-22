"""Structuurcontroles op de code zelf.

Deze tests bestaan omdat er ooit constantnamen op de verkeerde regel
terechtkwamen bij het bewerken van de importlijsten. Dat compileerde prima en
sloeg pas toe toen een gebruiker het formulier opende. Zulke fouten zijn
statisch te vinden.
"""

import ast
from pathlib import Path

import pytest

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
BESTANDEN = sorted(BRON.glob("*.py"))


def bomen():
    """Alle modules als ontleedboom."""
    for pad in BESTANDEN:
        yield pad, ast.parse(pad.read_text(encoding="utf-8"))


def test_er_zijn_modules():
    assert BESTANDEN, "geen broncode gevonden"


@pytest.mark.parametrize("pad", BESTANDEN, ids=lambda p: p.name)
def test_module_is_geldig(pad):
    ast.parse(pad.read_text(encoding="utf-8"))


def test_formuliervelden_hebben_een_argument():
    """vol.Required en vol.Optional verwachten precies een sleutel.

    Meer argumenten leveren pas bij het openen van het formulier een fout op,
    met als enige melding "Unknown error occurred".
    """
    fouten = []
    for pad, boom in bomen():
        for knoop in ast.walk(boom):
            if (
                isinstance(knoop, ast.Call)
                and isinstance(knoop.func, ast.Attribute)
                and knoop.func.attr in ("Required", "Optional")
                and len(knoop.args) != 1
            ):
                fouten.append(f"{pad.name}:{knoop.lineno} heeft {len(knoop.args)} argumenten")

    assert not fouten, "\n".join(fouten)


def test_geen_kale_namen_als_dictsleutel():
    """Een losse constantnaam als sleutel wijst op een verdwaalde importregel."""
    fouten = []
    for pad, boom in bomen():
        for knoop in ast.walk(boom):
            if isinstance(knoop, ast.Dict):
                for sleutel in knoop.keys:
                    if isinstance(sleutel, ast.Name):
                        fouten.append(f"{pad.name}:{sleutel.lineno} -> {sleutel.id}")

    assert not fouten, "\n".join(fouten)


def test_geen_losse_namen_als_statement():
    """Een regel die alleen uit een naam bestaat doet niets en hoort er niet."""
    fouten = []
    for pad, boom in bomen():
        for knoop in ast.walk(boom):
            if isinstance(knoop, ast.Expr) and isinstance(knoop.value, ast.Name):
                fouten.append(f"{pad.name}:{knoop.lineno} -> {knoop.value.id}")

    assert not fouten, "\n".join(fouten)


def test_kernmodules_zijn_vrij_van_home_assistant():
    """Deze modules moeten zonder Home Assistant te testen zijn."""
    vrij = {"cel.py", "indices.py", "taal.py", "validatie.py"}
    fouten = []

    for pad, boom in bomen():
        if pad.name not in vrij:
            continue
        for knoop in ast.walk(boom):
            namen = []
            if isinstance(knoop, ast.Import):
                namen = [a.name for a in knoop.names]
            elif isinstance(knoop, ast.ImportFrom) and knoop.module:
                namen = [knoop.module]
            if any(n.startswith("homeassistant") for n in namen):
                fouten.append(f"{pad.name}:{knoop.lineno}")

    assert not fouten, "\n".join(fouten)


def test_vertalingen_dekken_alle_stappen():
    """Elke stap in de config flow heeft een titel in beide talen."""
    import json

    stappen = set()
    boom = ast.parse((BRON / "config_flow.py").read_text(encoding="utf-8"))
    for knoop in ast.walk(boom):
        if isinstance(knoop, ast.Call) and getattr(knoop.func, "attr", "") == "async_show_form":
            for sleutel in knoop.keywords:
                if sleutel.arg == "step_id" and isinstance(sleutel.value, ast.Constant):
                    stappen.add(sleutel.value.value)

    for bestand in ("translations/nl.json", "translations/en.json"):
        vertaling = json.loads((BRON / bestand).read_text(encoding="utf-8"))
        aanwezig = set(vertaling["config"]["step"]) | set(vertaling["options"]["step"])
        ontbreekt = stappen - aanwezig
        assert not ontbreekt, f"{bestand} mist {ontbreekt}"


class TestStrategieBestand:
    """Het dashboardscript wordt door de browser als module geladen.

    Gaat er onderweg iets mis met de codering of raakt het bestand afgekapt,
    dan registreert de module niets en krijgt de gebruiker alleen
    "Timeout waiting for strategy element". Dat is dan lastig te herleiden,
    dus we controleren het hier.
    """

    @pytest.fixture
    def script(self):
        pad = BRON / "www" / "stormchase-strategy.js"
        assert pad.is_file(), "strategiebestand ontbreekt"
        return pad.read_text(encoding="utf-8")

    def test_alleen_ascii(self, script):
        """Niet-ASCII overleeft een editor met de verkeerde codering niet.

        Een middelpunt werd ooit Â·, wat het bestand onbruikbaar maakte.
        Alles staat daarom als escape in de broncode.
        """
        raar = {c for c in script if ord(c) > 127}
        assert not raar, f"niet-ASCII gevonden: {sorted(raar)}"

    def test_niet_afgekapt(self, script):
        """Het bestand moet eindigen op de afsluitende regel."""
        assert script.rstrip().endswith(");"), "bestand lijkt afgekapt"

    def test_haakjes_in_balans(self, script):
        """Grove controle op een afgekapt bestand."""
        for open_teken, sluit_teken in (("{", "}"), ("(", ")"), ("[", "]")):
            assert script.count(open_teken) == script.count(sluit_teken), (
                f"ongelijk aantal {open_teken}{sluit_teken}"
            )

    def test_registreert_beide_strategieen(self, script):
        for naam in ("ll-strategy-view-stormchase", "ll-strategy-dashboard-stormchase"):
            assert naam in script
