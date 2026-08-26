"""Bewolking van EUMETSAT.

De infraroodlaag van RainViewer meet wolktoptemperatuur. Hoge bewolking is
ijskoud en steekt scherp af, maar lage en middelhoge bewolking heeft een
wolktop die nauwelijks kouder is dan de grond eronder en verdwijnt daardoor
vrijwel volledig. Precies de bewolking die je op een chase-dag wil zien.

De afgeleide producten van EUMETSAT komen met hun eigen palet: het
wolkenmasker kleurt heldere gebieden groen en blauw, de wolktophoogte gebruikt
een regenboogschaal met harde blokken. Beide zijn gemaakt om los bekeken te
worden, niet om over een kaart te leggen.

Daarom wordt hier het onbewerkte infraroodkanaal gebruikt en zelf omgezet naar
grijstinten, zoals elke weerkaart bewolking toont: donker is helder, licht is
bewolkt, met vloeiende overgangen ertussen.

De kaartdienst levert in EPSG:4326, terwijl het radarbeeld in webmercator
staat. Zonder herprojectie schuift alles verticaal weg; die berekening staat
hieronder en is los te testen.
"""

from __future__ import annotations

import math

WMS_URL = "https://view.eumetsat.int/geoserver/wms"

# Het infraroodkanaal op 10,8 micrometer: het standaardbeeld voor bewolking,
# elk kwartier ververst en met dekking over heel Europa.
STANDAARD_LAAG = "msg_fes:ir108"

# Hoe zwaar de laag meetelt. Genoeg om de bewolking te zien liggen, niet
# zoveel dat de kaart eronder verdwijnt.
STERKTE = 0.55

# Onder deze helderheid rekenen we het tot onbewolkt. Zonder ondergrens legt
# de laag ook over onbewolkte gebieden een grijze waas.
DREMPEL = 70

# Het bronbeeld is grof, ongeveer drie kilometer per beeldpunt. Een lichte
# vervaging maakt de blokken tot vloeiende overgangen, zoals je op een
# weerkaart verwacht.
VERVAGING = 2.5


def wms_url(
    grenzen: tuple[float, float, float, float],
    breedte: int,
    hoogte: int,
    laag: str = STANDAARD_LAAG,
    basis: str = WMS_URL,
) -> str:
    """Stel een verzoek samen voor precies dit gebied.

    In versie 1.3.0 van de standaard staat de volgorde van de hoeken voor
    EPSG:4326 op breedtegraad eerst. Dat is een klassieke valkuil: met de
    verkeerde volgorde komt er een leeg beeld terug zonder foutmelding.
    """
    zuid, west, noord, oost = grenzen

    velden = {
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": laag,
        "styles": "",
        "format": "image/png",
        "transparent": "true",
        "crs": "EPSG:4326",
        "bbox": f"{zuid},{west},{noord},{oost}",
        "width": str(breedte),
        "height": str(hoogte),
    }

    return basis + "?" + "&".join(f"{k}={v}" for k, v in velden.items())


def mercatorrij(
    rij: int, hoogte: int, zuid: float, noord: float
) -> float:
    """Van welke rij uit het platte beeld komt deze rij in het mercatorbeeld?

    Webmercator rekt de afstand tussen breedtegraden op naarmate je verder
    van de evenaar komt. Een plat beeld op schaal daaroverheen leggen zou de
    bewolking tientallen kilometers verkeerd neerzetten.
    """
    def naar_mercator(graden: float) -> float:
        return math.log(math.tan(math.pi / 4 + math.radians(graden) / 2))

    boven = naar_mercator(noord)
    onder = naar_mercator(zuid)

    # Waar ligt deze rij op de mercatorschaal?
    hier = boven - (boven - onder) * (rij / max(hoogte - 1, 1))

    # En welke breedtegraad hoort daarbij?
    breedtegraad = math.degrees(2 * math.atan(math.exp(hier)) - math.pi / 2)

    # Terug naar een rij in het platte bronbeeld
    deel = (noord - breedtegraad) / max(noord - zuid, 1e-9)
    return deel * (hoogte - 1)


def alfa_van_helderheid(
    waarde: int, drempel: int = DREMPEL, sterkte: float = STERKTE
) -> int:
    """Zet de helderheid van een beeldpunt om naar doorzichtigheid.

    Donker is heldere lucht en wordt volledig doorzichtig; hoe lichter, hoe
    dichter de bewolking. Zo verdwijnt de waas boven onbewolkte gebieden en
    blijft de kaart eronder leesbaar.
    """
    if waarde <= drempel:
        return 0

    deel = (waarde - drempel) / (255 - drempel)
    return int(min(deel, 1.0) * 255 * sterkte)
