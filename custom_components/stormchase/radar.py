"""Radarbeelden van RainViewer.

Er is een eindpunt dat op coordinaten centreert in plaats van op kaarttegels.
Daarmee is een radarbeeld te maken dat je eigen positie volgt, als gewone
entiteit in Home Assistant: geen ingesloten webpagina, geen cookiemelding,
geen advertenties.

Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

import math

# Het hoogste zoomniveau dat RainViewer aanbiedt
MAX_ZOOM = 7
MIN_ZOOM = 1

# Alleen deze twee formaten worden geleverd
FORMATEN = (256, 512)

# Kleurschema's lopen van 0 tot en met 8
MAX_KLEUR = 8


def laatste_frame(payload: dict | None) -> dict | None:
    """Pak het meest recente radarbeeld uit het overzicht.

    De reeks loopt van oud naar nieuw, dus het laatste element is het meest
    actuele. Ontbreekt de reeks, dan komt er niets terug en blijft het beeld
    op zijn vorige waarde staan.
    """
    if not payload:
        return None

    frames = ((payload.get("radar") or {}).get("past")) or []
    if not frames:
        return None

    laatste = frames[-1]
    if not laatste.get("path"):
        return None

    return {
        "host": payload.get("host") or "https://tilecache.rainviewer.com",
        "path": laatste["path"],
        "tijd": laatste.get("time"),
    }


def laatste_satelliet(payload: dict | None) -> dict | None:
    """Pak het nieuwste infraroodbeeld uit het overzicht.

    Satelliet laat bewolking zien, ook waar nog geen neerslag valt. Daarmee
    zie je opbouwende cumulus voordat de radar iets oppikt.
    """
    if not payload:
        return None

    frames = ((payload.get("satellite") or {}).get("infrared")) or []
    if not frames or not frames[-1].get("path"):
        return None

    return {
        "host": payload.get("host") or "https://tilecache.rainviewer.com",
        "path": frames[-1]["path"],
        "tijd": frames[-1].get("time"),
    }


def satelliettegel_url(frame: dict | None, tegel: dict, zoom: int) -> str | None:
    """URL van een wolkentegel. Infrarood kent geen kleurschema of opties."""
    if frame is None:
        return None

    return (
        f"{frame['host']}{frame['path']}/{TEGELMAAT}/{zoom}"
        f"/{tegel['x']}/{tegel['y']}/0/0_0.png"
    )


def bouw_url(
    frame: dict | None,
    latitude: float,
    longitude: float,
    zoom: int = 7,
    formaat: int = 512,
    kleur: int = 2,
    vloeiend: bool = True,
    sneeuw: bool = True,
) -> str | None:
    """Stel de URL van een radarbeeld samen, gecentreerd op een positie.

    De coordinaten moeten een punt bevatten, ook als ze rond zijn; daarom
    worden ze altijd met decimalen geschreven.
    """
    if frame is None:
        return None

    zoom = max(MIN_ZOOM, min(int(zoom), MAX_ZOOM))
    formaat = formaat if formaat in FORMATEN else 512
    kleur = max(0, min(int(kleur), MAX_KLEUR))

    opties = f"{1 if vloeiend else 0}_{1 if sneeuw else 0}"

    return (
        f"{frame['host']}{frame['path']}/{formaat}/{zoom}"
        f"/{latitude:.4f}/{longitude:.4f}/{kleur}/{opties}.png"
    )


# ---------------------------------------------------------------------
# Kaarttegels
#
# RainViewer levert alleen de neerslaglaag: een doorzichtige overlay zonder
# ondergrond. Zonder kaart eronder zweven er blobs in het niets en zie je
# niet waar de bui hangt. Daarom worden de tegels van een donkere kaart en
# de radar over elkaar heen gelegd.
# ---------------------------------------------------------------------

TEGELMAAT = 256

# OpenStreetMap heeft geen sleutel nodig. De donkere varianten van andere
# aanbieders zijn de laatste jaren allemaal achter een sleutel verdwenen, dus
# we nemen de gewone kaart en maken hem zelf donker.
BASISKAART = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

# Hun gebruiksvoorwaarden vragen om een herkenbare naam bij het ophalen
TEGEL_AGENT = "StormchaseNL Home Assistant integratie"

# Hoeveel de kaart gedempt wordt voordat de radar erover gaat. Donker genoeg
# om de neerslag te laten opvallen, licht genoeg om plaatsnamen te lezen.
KAART_HELDERHEID = 0.45
KAART_KLEUR = 0.55

# Hoe ver terug de inslagen op het beeld getekend worden. Kwartier is genoeg
# om de verplaatsing van een cel te zien zonder dat het een vlek wordt.
INSLAG_VENSTER = 900

# Infrarood toont alle bewolking, ook hoge sluierbewolking. Op volle sterkte
# legt dat een waas over de hele kaart en zijn plaatsnamen niet meer te lezen.
WOLKEN_STERKTE = 0.45


def tegelpositie(latitude: float, longitude: float, zoom: int) -> tuple[float, float]:
    """Reken coordinaten om naar een tegelpositie met decimalen.

    De standaard webmercator-omrekening. De decimalen geven aan waar binnen
    de tegel het punt ligt, wat nodig is om het beeld precies op de locatie
    te centreren.
    """
    n = 2.0 ** zoom
    x = (longitude + 180.0) / 360.0 * n

    rad = math.radians(latitude)
    y = (1.0 - math.asinh(math.tan(rad)) / math.pi) / 2.0 * n

    return (x, y)


def tegelraster(
    latitude: float, longitude: float, zoom: int, breedte: int = 3
) -> dict:
    """Bepaal welke tegels er nodig zijn en waar het middelpunt ligt.

    Een raster van drie bij drie geeft genoeg omgeving om een bui te kunnen
    plaatsen, ook als hij net buiten het midden valt.
    """
    x, y = tegelpositie(latitude, longitude, zoom)
    midden = breedte // 2

    begin_x = int(x) - midden
    begin_y = int(y) - midden
    grens = 2 ** zoom

    tegels = []
    for rij in range(breedte):
        for kolom in range(breedte):
            tegels.append(
                {
                    "x": (begin_x + kolom) % grens,
                    "y": min(max(begin_y + rij, 0), grens - 1),
                    "plak_x": kolom * TEGELMAAT,
                    "plak_y": rij * TEGELMAAT,
                }
            )

    return {
        "tegels": tegels,
        "begin_x": begin_x,
        "begin_y": begin_y,
        "zoom": zoom,
        # Waar het gevraagde punt ligt binnen het samengestelde beeld
        "midden_x": (x - begin_x) * TEGELMAAT,
        "midden_y": (y - begin_y) * TEGELMAAT,
        "afmeting": breedte * TEGELMAAT,
    }


def basiskaart_url(tegel: dict, zoom: int) -> str:
    """URL van een kaarttegel."""
    return BASISKAART.format(z=zoom, x=tegel["x"], y=tegel["y"])


def radartegel_url(
    frame: dict | None,
    tegel: dict,
    zoom: int,
    kleur: int = 2,
    vloeiend: bool = True,
    sneeuw: bool = True,
) -> str | None:
    """URL van een radartegel op dezelfde positie."""
    if frame is None:
        return None

    opties = f"{1 if vloeiend else 0}_{1 if sneeuw else 0}"
    return (
        f"{frame['host']}{frame['path']}/{TEGELMAAT}/{zoom}"
        f"/{tegel['x']}/{tegel['y']}/{kleur}/{opties}.png"
    )


def pixelpositie(
    latitude: float, longitude: float, raster: dict
) -> tuple[float, float] | None:
    """Reken coordinaten om naar een plek binnen het samengestelde beeld.

    Nodig om blikseminslagen op de juiste plek te tekenen. Valt het punt
    buiten het raster, dan komt er niets terug en wordt het overgeslagen.
    """
    x, y = tegelpositie(latitude, longitude, raster["zoom"])

    px = (x - raster["begin_x"]) * TEGELMAAT
    py = (y - raster["begin_y"]) * TEGELMAAT

    afmeting = raster["afmeting"]
    if not (0 <= px <= afmeting and 0 <= py <= afmeting):
        return None

    return (px, py)


def naar_pixels_per_uur(snelheid_kmh: float, raster: dict) -> float:
    """Hoeveel pixels een cel in een uur aflegt op dit zoomniveau.

    Nodig om de pijl van de celbeweging op schaal te tekenen: even lang als
    de afstand die de bui werkelijk aflegt.
    """
    # Breedte van een tegel in kilometers op deze breedtegraad
    n = 2.0 ** raster["zoom"]
    km_per_tegel = 40075.0 / n

    return snelheid_kmh / km_per_tegel * TEGELMAAT


def beeldlabel(tijd: int | None, nu: float, verschuiving: int = 0) -> str:
    """Tekst met het tijdstip van het beeld en hoe oud het is.

    Het tijdstip van de opname zegt meer dan het moment waarop wij het
    ophaalden: dat laatste kan vers zijn terwijl het beeld al tien minuten
    oud is.

    De verschuiving is het aantal seconden tussen lokale tijd en UTC.
    """
    if not tijd:
        return "Tijd onbekend"

    uren = int((tijd + verschuiving) // 3600 % 24)
    minuten = int((tijd + verschuiving) // 60 % 60)
    ouderdom = max(int((nu - tijd) // 60), 0)

    if ouderdom == 0:
        return f"Radar {uren:02d}:{minuten:02d} \u00b7 zojuist"
    if ouderdom == 1:
        return f"Radar {uren:02d}:{minuten:02d} \u00b7 1 minuut oud"
    return f"Radar {uren:02d}:{minuten:02d} \u00b7 {ouderdom} minuten oud"


def coordinaat_van_tegel(x: float, y: float, zoom: int) -> tuple[float, float]:
    """De omgekeerde weg: van tegelpositie terug naar coordinaten."""
    n = 2.0 ** zoom
    longitude = x / n * 360.0 - 180.0
    latitude = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return (latitude, longitude)


def rastergrenzen(raster: dict) -> tuple[float, float, float, float]:
    """De hoeken van het samengestelde beeld, als zuid, west, noord, oost.

    Nodig om een kaartdienst om precies dit gebied te vragen.
    """
    zoom = raster["zoom"]
    breedte = raster["afmeting"] // TEGELMAAT

    noord, west = coordinaat_van_tegel(raster["begin_x"], raster["begin_y"], zoom)
    zuid, oost = coordinaat_van_tegel(
        raster["begin_x"] + breedte, raster["begin_y"] + breedte, zoom
    )

    return (zuid, west, noord, oost)
