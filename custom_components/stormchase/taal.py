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
    ("heavy thunderstorm", "zwaar onweer"),
    ("strong thunderstorm", "zwaar onweer"),
    ("isolated thunderstorm", "lokaal onweer"),
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


def hoofdletter(tekst: str | None) -> str | None:
    """Zet alleen de eerste letter om naar een hoofdletter.

    Niet capitalize(): die verlaagt de rest van de tekst, waardoor "IJzel"
    verandert in "Ijzel" en "CAPE 2400" in "Cape 2400".
    """
    if not tekst:
        return tekst

    # De ij is in het Nederlands een letter: aan het begin van een zin gaan
    # beide tekens omhoog, dus IJzel en niet Ijzel.
    if tekst[:2].lower() == "ij":
        return "IJ" + tekst[2:]

    return tekst[0].upper() + tekst[1:]


def vertaal_soort(soort: str | None) -> str | None:
    """Vertaal het soort waarschuwing naar het Nederlands.

    Een waarschuwing noemt vaak meer dan een verschijnsel tegelijk, zoals
    "heavy thunderstorms with heavy rain". Een enkel trefwoord pakken zou
    daar de helft van weglaten, dus we zoeken alle onderdelen en zetten ze
    weer aan elkaar.

    Wordt er niets herkend, dan blijft de oorspronkelijke tekst staan. Liever
    een Engelse term die klopt dan een Nederlandse die de lading niet dekt.
    """
    if not soort:
        return soort

    laag = soort.lower().strip()

    gevonden: list[tuple[int, str]] = []
    bezet: list[tuple[int, int]] = []

    # Specifieke termen eerst, zodat "heavy rain" wint van "rain" en het
    # stuk tekst daarna niet nog eens meetelt.
    for engels, nederlands in TREFWOORDEN:
        start = laag.find(engels)
        if start == -1:
            continue

        eind = start + len(engels)
        if any(start < b and eind > a for a, b in bezet):
            continue

        bezet.append((start, eind))
        gevonden.append((start, nederlands))

    if not gevonden:
        return soort

    gevonden.sort()
    delen = [tekst for _, tekst in gevonden]

    if len(delen) == 1:
        return delen[0]

    # Het eerste onderdeel is het hoofdverschijnsel, de rest hangt eraan
    return f"{delen[0]} met {' en '.join(delen[1:])}"
