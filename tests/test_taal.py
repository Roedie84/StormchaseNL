"""Vertaling van de Engelse termen uit MeteoAlarm."""

import pytest

from taal import hoofdletter, vertaal_soort


@pytest.mark.parametrize(
    "engels,nederlands",
    [
        ("heavy rain", "zware regen"),
        ("rain", "regen"),
        ("freezing rain", "ijzel"),
        ("severe thunderstorm", "zwaar onweer"),
        ("thunderstorm", "onweer"),
        ("snow-ice", "sneeuw en ijzel"),
        ("gale-force wind", "stormachtige wind"),
        ("extreme high temperature", "extreme hitte"),
        ("forest fire", "bosbrand"),
        ("fog", "mist"),
        ("Wind", "wind"),
        ("SNOW", "sneeuw"),
    ],
)
def test_enkelvoudige_termen(engels, nederlands):
    assert vertaal_soort(engels) == nederlands


def test_specifiek_gaat_voor_algemeen():
    """IJzel mag geen gewone regen worden."""
    assert vertaal_soort("freezing rain") == "ijzel"
    assert vertaal_soort("heavy rain") == "zware regen"


def test_samengestelde_termen():
    """Meerdere verschijnselen tegelijk blijven allemaal staan."""
    assert vertaal_soort("heavy thunderstorms with heavy rain") == (
        "zwaar onweer met zware regen"
    )
    assert vertaal_soort("severe thunderstorms with hail and strong wind") == (
        "zwaar onweer met hagel en harde wind"
    )


def test_overlap_telt_niet_dubbel():
    """'heavy rain' mag daarna niet nog eens als 'rain' meetellen."""
    assert vertaal_soort("heavy rain").count("regen") == 1


def test_onbekende_term_blijft_staan():
    assert vertaal_soort("something unusual") == "something unusual"
    assert vertaal_soort(None) is None
    assert vertaal_soort("") == ""


@pytest.mark.parametrize(
    "invoer,verwacht",
    [
        ("ijzel", "IJzel"),
        ("ijzel op de weg", "IJzel op de weg"),
        ("zware regen", "Zware regen"),
        ("CAPE loopt op", "CAPE loopt op"),
        ("", ""),
        (None, None),
    ],
)
def test_hoofdletter(invoer, verwacht):
    """De ij is een letter, en bestaande hoofdletters blijven staan."""
    assert hoofdletter(invoer) == verwacht
