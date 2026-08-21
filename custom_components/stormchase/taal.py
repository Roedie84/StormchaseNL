"""Vertaling van de Engelse termen die MeteoAlarm gebruikt.

De feed levert het soort waarschuwing als vrije tekst in het Engels, en die
tekst verschilt per land: het ene instituut schrijft "heavy rain", het andere
"rain-flood" of "severe thunderstorms". Een vaste lijst dekt dat niet, dus we
zoeken op trefwoorden.

De volgorde is van specifiek naar algemeen: "freezing rain" moet eerder
gevonden worden dan "rain", anders wordt ijzel gewoon regen.
"""

from __future__ import annotations

# Volgorde is bepalend, dus dit is bewust een lijst en geen dict
TREFWOORDEN: list[tuple[str, str]] = [
    # Neerslag, van bijzonder naar gewoon
    ("freezing rain", "ijzel"),
    ("freezing drizzle", "onderkoelde motregen"),
    ("rain-flood", "regen en wateroverlast"),
    ("rain flood", "regen en wateroverlast"),
    ("heavy rain", "zware regen"),
    ("extreme rain", "extreme regenval"),
    ("rainfall", "regenval"),
    ("drizzle", "motregen"),
    ("rain", "regen"),
    # Onweer
    ("severe thunderstorm", "zwaar onweer"),
    ("thunderstorm", "onweer"),
    ("lightning", "bliksem"),
    # Wind
    ("gale-force wind", "stormachtige wind"),
    ("gale", "storm"),
    ("severe wind", "zware wind"),
    ("strong wind", "harde wind"),
    ("wind gust", "windstoten"),
    ("squall", "windstoot"),
    ("hurricane", "orkaan"),
    ("tornado", "windhoos"),
    ("storm", "storm"),
    ("wind", "wind"),
    # Winterweer
    ("snow-ice", "sneeuw en ijzel"),
    ("snow ice", "sneeuw en ijzel"),
    ("heavy snow", "zware sneeuwval"),
    ("snowfall", "sneeuwval"),
    ("snow", "sneeuw"),
    ("black ice", "ijzel"),
    ("ice", "ijzel"),
    ("frost", "vorst"),
    ("avalanche", "lawines"),
    # Temperatuur
    ("extreme high temperature", "extreme hitte"),
    ("high temperature", "hoge temperaturen"),
    ("extreme low temperature", "extreme kou"),
    ("low temperature", "lage temperaturen"),
    ("heatwave", "hittegolf"),
    ("heat", "hitte"),
    ("cold wave", "koudegolf"),
    ("cold", "kou"),
    # Overig
    ("coastal event", "kustweer"),
    ("coastal flood", "overstroming aan de kust"),
    ("forest fire", "bosbrand"),
    ("wildfire", "natuurbrand"),
    ("flooding", "overstroming"),
    ("flood", "overstroming"),
    ("fog", "mist"),
    ("hail", "hagel"),
    ("dust", "stof"),
    ("sandstorm", "zandstorm"),
    ("air quality", "luchtkwaliteit"),
    ("unknown", "onbekend"),
]


def vertaal_soort(soort: str | None) -> str | None:
    """Vertaal het soort waarschuwing naar het Nederlands.

    Wordt er geen trefwoord herkend, dan blijft de oorspronkelijke tekst
    staan. Liever een Engelse term die klopt dan een Nederlandse die de lading
    niet dekt.
    """
    if not soort:
        return soort

    laag = soort.lower().strip()

    for engels, nederlands in TREFWOORDEN:
        if engels in laag:
            return nederlands

    return soort
