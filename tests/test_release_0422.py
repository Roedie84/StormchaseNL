"""0.42.2: strategie-sjablonen vallen niet om op None bij het opstarten.

Na de herstart van 7 oktober 18:26 gaf HA acht keer "NoneType object is not
iterable": de attributen van de onweersverwachting bestaan, maar zijn None
tot de eerste Open-Meteo-ronde. ``default('x')`` vangt alleen ontbrekende
waarden, ``default('x', true)`` ook None en lege tekst.
"""
import re
from pathlib import Path

JS = Path(__file__).parent.parent / "custom_components" / "stormchase" / "www" / "stormchase-strategy.js"


def test_geen_default_zonder_true_voor_indexeren():
    bron = JS.read_text()
    fout = re.findall(r"default\('[^']*'\) %\}\{\{ [a-z]\[0\]", bron)
    assert not fout, fout


def test_alle_zes_parameters_beschermd():
    assert JS.read_text().count("default('onbekend', true)") >= 6
