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


def test_geen_verdwaalde_importregels():
    """Een constantnaam op importniveau midden in een functie hoort niet.

    Bij het bewerken van importlijsten belandden constanten drie keer in een
    aanroep verderop in het bestand. Dat compileert prima: een aanroep krijgt
    dan gewoon meer argumenten dan bedoeld, of de eerste parameter wordt
    vervangen. Een van die gevallen liet de weersituatie-melding onder een
    verkeerde naam afgaan, wat maandenlang onopgemerkt had kunnen blijven.

    Het kenmerk is een regel met precies vier spaties inspringing die alleen
    uit een hoofdlettersnaam en een komma bestaat, buiten een importblok.
    """
    import re

    patroon = re.compile(r"^    [A-Z][A-Z0-9_]*,\s*$")
    fouten = []

    for pad in BESTANDEN:
        in_import = False
        for nummer, regel in enumerate(pad.read_text(encoding="utf-8").splitlines(), 1):
            if re.match(r"^(from|import)\b", regel):
                in_import = "(" in regel and ")" not in regel
                continue
            if in_import:
                if ")" in regel:
                    in_import = False
                continue
            if patroon.match(regel):
                fouten.append(f"{pad.name}:{nummer} -> {regel.strip()}")

    assert not fouten, "\n".join(fouten)


def test_events_worden_met_een_naam_afgevuurd():
    """async_fire krijgt een eventnaam en hoogstens gegevens mee.

    Meer argumenten wijst op een verdwaalde regel; de eventnaam is dan
    verschoven en het event komt onder een verkeerde naam binnen.
    """
    fouten = []
    for pad, boom in bomen():
        for knoop in ast.walk(boom):
            if (
                isinstance(knoop, ast.Call)
                and getattr(knoop.func, "attr", "") == "async_fire"
                and len(knoop.args) > 2
            ):
                fouten.append(f"{pad.name}:{knoop.lineno} heeft {len(knoop.args)} argumenten")

    assert not fouten, "\n".join(fouten)


def test_verzoeken_hebben_een_url():
    """session.get krijgt een URL en verder alleen benoemde argumenten."""
    fouten = []
    for pad, boom in bomen():
        for knoop in ast.walk(boom):
            if (
                isinstance(knoop, ast.Call)
                and getattr(knoop.func, "attr", "") in ("get", "post")
                and "session" in ast.dump(knoop.func)
                and len(knoop.args) > 1
            ):
                fouten.append(f"{pad.name}:{knoop.lineno} heeft {len(knoop.args)} argumenten")

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
    vrij = {"cel.py", "indices.py", "taal.py", "validatie.py", "tijd.py", "spreiding.py", "radar.py", "wolken.py"}
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


def test_luisteraars_staan_aan_voor_de_eerste_ronde():
    """De notifier moet luisteren voordat er gegevens worden opgehaald.

    Stond dat andersom, dan vuurden de gebeurtenissen uit de eerste ronde in
    het niets. Bij een herstart midden in een onweer betekende dat de eerste
    melding van elke soort verloren ging: in een echte meting twee
    waarschuwingen afgevuurd en nul verstuurd.
    """
    bron = (BRON / "__init__.py").read_text(encoding="utf-8")

    start = bron.index("notifier.start()")
    eerste_ronde = bron.index("async_config_entry_first_refresh()")

    assert start < eerste_ronde, (
        "notifier.start() moet voor de eerste ophaalronde staan"
    )
