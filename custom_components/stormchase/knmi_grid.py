"""Rekenwerk voor de KNMI-bronnen: rastercellen, projecties en regio's.

De KNMI-app werkt niet met coordinaten maar met celnummers in twee vaste
rasters. Raster A is de weersverwachting (graden), raster B het radarraster
voor de neerslagverwachting per vijf minuten. Dat laatste ligt in een
polaire stereografische projectie op een ellipsoide; de omrekening staat
hieronder in gewoon Python, zodat er geen zware bibliotheek als pyproj nodig
is. De rasterdefinities zijn die van de KNMI-app (open source, KNMI-OSS).

Verder: omrekening naar webmercator (EPSG:3857) voor de radarkaart, afstand
tussen twee punten, een grove grens van Nederland als terugval, en de
waarschuwingsregio's (1..15) van het KNMI.

Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------------
# Raster A: weersverwachting, in graden. Noordwesthoek is cel 0, eerst naar
# het zuiden (35 rijen), dan per kolom naar het oosten (30 kolommen).
# ---------------------------------------------------------------------

VERWACHTING_ZUID = 50.7
VERWACHTING_WEST = 3.2
VERWACHTING_NOORD = 53.6
VERWACHTING_OOST = 7.4
VERWACHTING_RIJEN = 35
VERWACHTING_KOLOMMEN = 30

# ---------------------------------------------------------------------
# Raster B: radar, in kilometers in de polaire stereografische projectie
# van het KNMI (pool als oorsprong, ware schaal op 60 graden noord). Een
# cel is een vierkante kilometer.
# ---------------------------------------------------------------------

RADAR_A = 6378.14  # km, halve lange as van de ellipsoide
RADAR_B = 6356.75  # km, halve korte as
RADAR_WARE_SCHAAL = 60.0  # graden noord
RADAR_ZUID = -4240.0  # y, km
RADAR_NOORD = -3889.0
RADAR_WEST = 247.0  # x, km
RADAR_OOST = 510.0
RADAR_RIJEN = 351
RADAR_KOLOMMEN = 263

# Webmercator (EPSG:3857)
AARDSTRAAL_M = 6378137.0
MERCATOR_MAX_BREEDTE = 85.05112878

# Voor afstanden tussen twee punten
AARDSTRAAL_KM = 6371.0


def _cel(rij: float, kolom: float, rijen: int) -> int:
    """Celnummer: kolom voor kolom, binnen een kolom van noord naar zuid."""
    return int(rij) + int(kolom) * rijen


def verwachtingscel(breedte: float, lengte: float) -> str | None:
    """Celkenmerk in het verwachtingsraster (bijv. 'A858'), of None erbuiten."""
    if not (VERWACHTING_ZUID < breedte <= VERWACHTING_NOORD):
        return None
    if not (VERWACHTING_WEST <= lengte < VERWACHTING_OOST):
        return None
    rij = (VERWACHTING_NOORD - breedte) * (
        VERWACHTING_RIJEN / (VERWACHTING_NOORD - VERWACHTING_ZUID)
    )
    kolom = (lengte - VERWACHTING_WEST) * (
        VERWACHTING_KOLOMMEN / (VERWACHTING_OOST - VERWACHTING_WEST)
    )
    return f"A{_cel(rij, kolom, VERWACHTING_RIJEN)}"


def stereografisch(breedte: float, lengte: float) -> tuple[float, float]:
    """Polaire stereografische projectie (noordpool, ellipsoide), in km.

    De standaardformule voor een projectie met een standaardparallel: de
    schaal is waar op RADAR_WARE_SCHAAL, de meridiaan van Greenwich wijst
    vanaf de pool naar beneden (negatieve y).
    """
    e2 = 1.0 - (RADAR_B * RADAR_B) / (RADAR_A * RADAR_A)
    e = math.sqrt(e2)

    def t(phi: float) -> float:
        sin_phi = math.sin(phi)
        return math.tan(math.pi / 4 - phi / 2) / (
            ((1 - e * sin_phi) / (1 + e * sin_phi)) ** (e / 2)
        )

    def m(phi: float) -> float:
        sin_phi = math.sin(phi)
        return math.cos(phi) / math.sqrt(1 - e2 * sin_phi * sin_phi)

    phi_c = math.radians(RADAR_WARE_SCHAAL)
    phi = math.radians(breedte)
    lam = math.radians(lengte)

    rho = RADAR_A * m(phi_c) * t(phi) / t(phi_c)
    return rho * math.sin(lam), -rho * math.cos(lam)


def radarcel(breedte: float, lengte: float) -> str | None:
    """Celkenmerk in het radarraster (bijv. 'B79855'), of None erbuiten."""
    x, y = stereografisch(breedte, lengte)
    if not (RADAR_ZUID < y <= RADAR_NOORD and RADAR_WEST <= x < RADAR_OOST):
        return None
    rij = (RADAR_NOORD - y) * (RADAR_RIJEN / (RADAR_NOORD - RADAR_ZUID))
    kolom = (x - RADAR_WEST) * (RADAR_KOLOMMEN / (RADAR_OOST - RADAR_WEST))
    return f"B{_cel(rij, kolom, RADAR_RIJEN)}"


def naar_webmercator(breedte: float, lengte: float) -> tuple[float, float]:
    """Graden naar EPSG:3857 in meters (x, y)."""
    breedte = max(min(breedte, MERCATOR_MAX_BREEDTE), -MERCATOR_MAX_BREEDTE)
    x = AARDSTRAAL_M * math.radians(lengte)
    y = AARDSTRAAL_M * math.log(math.tan(math.pi / 4 + math.radians(breedte) / 2))
    return x, y


def bbox_webmercator(grenzen: tuple[float, float, float, float]) -> str:
    """(zuid, west, noord, oost) in graden naar 'minx,miny,maxx,maxy' in EPSG:3857.

    In EPSG:3857 is de volgorde altijd x eerst, ook in WMS 1.3.0; alleen
    EPSG:4326 draait de assen om.
    """
    zuid, west, noord, oost = grenzen
    minx, miny = naar_webmercator(zuid, west)
    maxx, maxy = naar_webmercator(noord, oost)
    return f"{minx:.1f},{miny:.1f},{maxx:.1f},{maxy:.1f}"


def afstand_km(breedte1: float, lengte1: float, breedte2: float, lengte2: float) -> float:
    """Afstand over de bol (haversine), in km."""
    dphi = math.radians(breedte2 - breedte1)
    dlam = math.radians(lengte2 - lengte1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(math.radians(breedte1))
        * math.cos(math.radians(breedte2))
        * math.sin(dlam / 2) ** 2
    )
    return 2 * AARDSTRAAL_KM * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------
# Grove grens van Nederland (lengte, breedte), inclusief de Waddeneilanden
# en een strook kustwater. Alleen een terugval voor als de omgekeerde
# geocodering geen land kon leveren: dicht bij de grens kan hij een paar
# kilometer naast zitten.
# ---------------------------------------------------------------------

NL_GRENS: tuple[tuple[float, float], ...] = (
    (3.36, 51.37), (3.38, 51.27), (3.80, 51.21), (3.98, 51.24),
    (4.24, 51.36), (4.40, 51.36), (4.47, 51.47), (4.93, 51.44),
    (5.10, 51.42), (5.30, 51.27), (5.48, 51.25), (5.75, 51.18),
    (5.82, 51.12), (5.73, 50.97), (5.64, 50.85), (5.69, 50.75),
    (6.02, 50.75), (6.08, 50.87), (6.02, 50.98), (5.90, 51.05),
    (6.17, 51.17), (6.07, 51.24), (6.22, 51.36), (6.22, 51.51),
    (6.10, 51.65), (6.02, 51.70), (6.03, 51.78), (6.10, 51.85),
    (6.25, 51.87), (6.40, 51.83), (6.50, 51.86), (6.72, 51.90),
    (6.83, 51.98), (6.76, 52.10), (6.86, 52.12), (6.99, 52.22),
    (7.07, 52.26), (7.07, 52.38), (6.98, 52.45), (6.70, 52.52),
    (6.75, 52.64), (7.05, 52.64), (7.07, 52.85), (7.20, 53.00),
    (7.21, 53.24), (7.20, 53.32), (7.00, 53.45), (6.60, 53.62),
    (5.80, 53.55), (5.00, 53.45), (4.60, 53.25), (4.45, 52.95),
    (4.35, 52.50), (4.05, 52.10), (3.75, 51.85), (3.35, 51.60),
    (3.25, 51.40),
)


def in_nederland_grof(breedte: float, lengte: float) -> bool:
    """Ligt dit punt binnen de grove grens? (ray casting)"""
    binnen = False
    punten = NL_GRENS
    j = len(punten) - 1
    for i, (xi, yi) in enumerate(punten):
        xj, yj = punten[j]
        if (yi > breedte) != (yj > breedte):
            snij = (xj - xi) * (breedte - yi) / (yj - yi) + xi
            if lengte < snij:
                binnen = not binnen
        j = i
    return binnen


# ---------------------------------------------------------------------
# Waarschuwingsregio's van het KNMI (zoals in de KNMI-app)
# ---------------------------------------------------------------------

KNMI_REGIOS: dict[int, str] = {
    1: "Drenthe",
    2: "Flevoland",
    3: "Friesland",
    4: "Gelderland",
    5: "Groningen",
    6: "IJsselmeergebied",
    7: "Limburg",
    8: "Noord-Brabant",
    9: "Noord-Holland",
    10: "Overijssel",
    11: "Utrecht",
    12: "Waddeneilanden",
    13: "Waddenzee",
    14: "Zeeland",
    15: "Zuid-Holland",
}

# ISO 3166-2-code van de provincie (zoals de geocodering hem levert)
PROVINCIECODES: dict[str, int] = {
    "NL-DR": 1, "NL-FL": 2, "NL-FR": 3, "NL-GE": 4, "NL-GR": 5,
    "NL-LI": 7, "NL-NB": 8, "NL-NH": 9, "NL-OV": 10, "NL-UT": 11,
    "NL-ZE": 14, "NL-ZH": 15,
}

# Provincienamen in het Engels, Nederlands en Fries, in kleine letters
PROVINCIENAMEN: dict[str, int] = {
    "drenthe": 1, "flevoland": 2, "friesland": 3, "fryslân": 3, "fryslan": 3,
    "frisia": 3, "gelderland": 4, "groningen": 5, "limburg": 7,
    "north brabant": 8, "noord-brabant": 8, "noord brabant": 8,
    "north holland": 9, "noord-holland": 9, "noord holland": 9,
    "overijssel": 10, "utrecht": 11, "zeeland": 14,
    "south holland": 15, "zuid-holland": 15, "zuid holland": 15,
}

# Gemeenten op de Waddeneilanden: die vallen onder regio 12, niet onder
# Noord-Holland of Friesland.
WADDENGEMEENTEN = {"texel", "vlieland", "terschelling", "ameland", "schiermonnikoog"}

# Namen van open water, voor als je op het water bent
WATERNAMEN: tuple[tuple[str, int], ...] = (
    ("ijsselmeer", 6),
    ("markermeer", 6),
    ("waddenzee", 13),
    ("wadden sea", 13),
)

# Middelpunten, voor als de geocodering geen provincie kent
REGIO_MIDDEN: dict[int, tuple[float, float]] = {
    1: (52.86, 6.62), 2: (52.53, 5.60), 3: (53.11, 5.85), 4: (52.06, 5.95),
    5: (53.22, 6.74), 6: (52.80, 5.35), 7: (51.21, 5.94), 8: (51.56, 5.18),
    9: (52.58, 4.87), 10: (52.44, 6.45), 11: (52.08, 5.20), 12: (53.40, 5.40),
    13: (53.25, 5.70), 14: (51.47, 3.83), 15: (51.99, 4.47),
}


def dichtstbijzijnde_regio(breedte: float, lengte: float) -> int:
    """De regio waarvan het middelpunt het dichtst bij ligt."""
    return min(
        REGIO_MIDDEN,
        key=lambda r: afstand_km(breedte, lengte, *REGIO_MIDDEN[r]),
    )


def _namen(geocode: dict) -> list[str]:
    """Alle plaats- en gebiedsnamen uit een geocodeerantwoord, klein geschreven."""
    namen: list[str] = []
    for sleutel in ("locality", "city", "principalSubdivision"):
        waarde = geocode.get(sleutel)
        if waarde:
            namen.append(str(waarde).strip().lower())
    info = geocode.get("localityInfo") or {}
    for soort in ("administrative", "informative"):
        for niveau in info.get(soort) or []:
            naam = (niveau or {}).get("name")
            if naam:
                namen.append(str(naam).strip().lower())
    return namen


def regio_uit_geocode(
    geocode: dict | None, breedte: float, lengte: float
) -> tuple[int, str]:
    """Bepaal de KNMI-regio en hoe die gevonden is.

    Volgorde: Waddeneiland (gemeentenaam), provinciecode, provincienaam,
    open water, en anders de regio met het dichtstbijzijnde middelpunt.
    """
    geocode = geocode or {}
    namen = _namen(geocode)

    if any(naam in WADDENGEMEENTEN for naam in namen):
        return 12, "gemeente"

    code = str(geocode.get("principalSubdivisionCode") or "").upper()
    if code in PROVINCIECODES:
        return PROVINCIECODES[code], "provincie"

    for naam in namen:
        if naam in PROVINCIENAMEN:
            return PROVINCIENAMEN[naam], "provincie"

    for naam in namen:
        for water, regio in WATERNAMEN:
            if water in naam:
                return regio, "water"

    return dichtstbijzijnde_regio(breedte, lengte), "dichtstbijzijnd"


# Binnen deze afstand (graden) van het punt van de laatste geocodering geldt
# het land dat daar gevonden werd; verder weg de grove grens.
LAND_GELDIG_GRADEN = 0.15


class Landbepaling:
    """Of een positie in Nederland ligt, gedeeld tussen de onderdelen.

    De waarschuwingscoordinator zoekt het land al op via omgekeerde
    geocodering; die uitkomst geldt hier ook voor de andere KNMI-bronnen.
    Zonder bruikbare geocodering in de buurt beslist de grove grens.
    """

    def __init__(self) -> None:
        self.landcode: str | None = None
        self.voor: tuple[float, float] | None = None

    def noteer(self, breedte: float, lengte: float, landcode: str | None) -> None:
        if not landcode:
            return
        self.landcode = landcode.upper()
        self.voor = (breedte, lengte)

    def in_nederland(self, breedte: float, lengte: float) -> bool:
        if self.voor is not None and self.landcode:
            verschil = max(abs(self.voor[0] - breedte), abs(self.voor[1] - lengte))
            if verschil <= LAND_GELDIG_GRADEN:
                return self.landcode == "NL"
        return in_nederland_grof(breedte, lengte)
