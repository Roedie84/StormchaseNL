"""0.42.2, bijgewerkt in 0.50.0: geen 'unknown'-rommel op het dashboard.

Na de herstart van 7 oktober 18:26 gaf HA acht keer "NoneType object is not
iterable": de attributen van de onweersverwachting bestaan, maar zijn None
tot de eerste Open-Meteo-ronde. Sinds 0.50.0 tekent het dashboard zelf (geen
Jinja-sjablonen meer); dezelfde bescherming zit nu in de kaart: lege,
onbekende en onbeschikbare waarden worden een streepje of verborgen, en
tekst wordt alleen geindexeerd als hij bestaat.
"""
from pathlib import Path

JS = Path(__file__).parent.parent / "custom_components" / "stormchase" / "www" / "stormchase-strategy.js"


def test_geen_jinja_meer():
    bron = JS.read_text()
    assert "{% " not in bron
    assert "{{ " not in bron


def test_onbruikbare_toestanden_afgevangen():
    bron = JS.read_text()
    assert 'const ONBRUIKBAAR = ["unknown", "unavailable", "none", ""];' in bron
    # Een waarde zonder getal wordt een streepje, onbeschikbaar wordt gedimd
    assert "const waardeHtml = " in bron
    assert 'onbeschikbaar(s) ? "niet beschikbaar"' in bron


def test_hoofdletter_veilig_bij_lege_tekst():
    bron = JS.read_text()
    blok = bron[bron.index("const hoofd = ") :][:250]
    assert 'if (!t) return "";' in blok
