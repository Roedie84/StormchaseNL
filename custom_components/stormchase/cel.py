"""Celtracking: van losse inslagen naar een bui met een richting.

De afstand tot de dichtstbijzijnde inslag springt van bui naar bui en zegt
daardoor weinig over wat er op je afkomt. Deze module clustert de inslagen tot
cellen, volgt het zwaartepunt van de dichtstbijzijnde cel over tijd en rekent
uit waar en wanneer die je passeert.

Alle berekeningen gebeuren in kilometers ten opzichte van jouw positie. Over
de afstanden waar het hier om gaat, hooguit een paar honderd kilometer, is een
vlakke benadering nauwkeurig genoeg en een stuk eenvoudiger dan rekenen op een
bol.
"""

from __future__ import annotations

import math

# Rastermaat voor het clusteren. Een kwart graad is ruwweg 25 kilometer, wat
# aardig overeenkomt met de omvang van een onweerscel.
RASTER = 0.25

# Zwaartepunten die verder dan dit uit elkaar liggen horen niet bij dezelfde
# cel; dan is er kennelijk een andere bui dichterbij gekomen.
CONTINUITEIT_KM = 40.0

# Onder deze snelheid noemen we een cel stilstaand en heeft een passagetijd
# geen betekenis.
MIN_CELSNELHEID = 5.0

# Kleur naar activiteit, zoals op professionele stormkaarten: geel voor een
# gewone bui, oranje als het aantrekt, rood bij een cel die er echt uit
# springt. De grenzen zijn het aantal inslagen binnen het volgvenster.
INTENSITEIT = [
    (25, "rood"),
    (8, "oranje"),
    (0, "geel"),
]


def intensiteit(inslagen: int) -> str:
    """Hoe actief is deze cel?"""
    for grens, naam in INTENSITEIT:
        if inslagen >= grens:
            return naam
    return "geel"


KOMPAS = [
    "N", "NNO", "NO", "ONO", "O", "OZO", "ZO", "ZZO",
    "Z", "ZZW", "ZW", "WZW", "W", "WNW", "NW", "NNW",
]


def naar_km(
    lat: float, lon: float, lat0: float, lon0: float
) -> tuple[float, float]:
    """Zet coordinaten om naar kilometers oost en noord vanaf een nulpunt."""
    x = (lon - lon0) * 111.320 * math.cos(math.radians(lat0))
    y = (lat - lat0) * 110.574
    return (x, y)


def naar_graden(x: float, y: float, lat0: float, lon0: float) -> tuple[float, float]:
    """De omgekeerde weg: van kilometers terug naar coordinaten."""
    lat = lat0 + y / 110.574
    lon = lon0 + x / (111.320 * math.cos(math.radians(lat0)))
    return (lat, lon)


def kompasrichting(graden: float | None) -> str | None:
    """Zet een hoek om naar een windrichting."""
    if graden is None:
        return None
    return KOMPAS[int(round(graden / 22.5)) % 16]


def richting_van_vector(vx: float, vy: float) -> float:
    """De richting waarheen een vector wijst, in graden vanaf noord."""
    return (math.degrees(math.atan2(vx, vy)) + 360) % 360


def zoek_cellen(
    punten: list[tuple[float, float]], lat0: float, lon0: float
) -> list[dict]:
    """Groepeer inslagen tot cellen op basis van een raster.

    Een raster in plaats van echte clustering: dat scheelt een berekening van
    elke inslag tegen elke andere, en bij honderden inslagen per minuut telt
    dat. Buurvakjes worden samengevoegd, zodat een cel die net over een
    rasterlijn valt niet in tweeen wordt geknipt.
    """
    if not punten:
        return []

    vakjes: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for lat, lon in punten:
        sleutel = (int(lat / RASTER), int(lon / RASTER))
        vakjes.setdefault(sleutel, []).append((lat, lon))

    # Buurvakjes aan elkaar plakken
    bezocht: set[tuple[int, int]] = set()
    cellen: list[dict] = []

    for sleutel in vakjes:
        if sleutel in bezocht:
            continue

        groep: list[tuple[float, float]] = []
        wachtrij = [sleutel]

        while wachtrij:
            huidig = wachtrij.pop()
            if huidig in bezocht or huidig not in vakjes:
                continue
            bezocht.add(huidig)
            groep.extend(vakjes[huidig])

            rij, kolom = huidig
            for drij in (-1, 0, 1):
                for dkol in (-1, 0, 1):
                    buur = (rij + drij, kolom + dkol)
                    if buur not in bezocht and buur in vakjes:
                        wachtrij.append(buur)

        gem_lat = sum(p[0] for p in groep) / len(groep)
        gem_lon = sum(p[1] for p in groep) / len(groep)
        x, y = naar_km(gem_lat, gem_lon, lat0, lon0)

        cellen.append(
            {
                "latitude": gem_lat,
                "longitude": gem_lon,
                "inslagen": len(groep),
                "afstand": round(math.hypot(x, y), 1),
            }
        )

    cellen.sort(key=lambda c: c["afstand"])
    return cellen


def beweging_van_reeks(
    reeks: list[tuple[float, float, float]], lat0: float, lon0: float
) -> tuple[float, float] | None:
    """Bepaal de snelheidsvector van een zwaartepunt, in km/u.

    Via regressie over de hele reeks in plaats van eerste tegen laatste: het
    zwaartepunt verspringt telkens een beetje doordat er inslagen bij komen en
    afvallen, en dat middelt zo weg.
    """
    if len(reeks) < 4:
        return None

    tijden = [t for t, _, _ in reeks]
    duur = tijden[-1] - tijden[0]
    if duur < 120:  # minder dan twee minuten zegt te weinig
        return None

    gem_t = sum(tijden) / len(tijden)
    punten = [naar_km(lat, lon, lat0, lon0) for _, lat, lon in reeks]
    gem_x = sum(p[0] for p in punten) / len(punten)
    gem_y = sum(p[1] for p in punten) / len(punten)

    noemer = sum((t - gem_t) ** 2 for t in tijden)
    if noemer == 0:
        return None

    vx = sum((t - gem_t) * (p[0] - gem_x) for t, p in zip(tijden, punten)) / noemer
    vy = sum((t - gem_t) * (p[1] - gem_y) for t, p in zip(tijden, punten)) / noemer

    # Van km per seconde naar km per uur
    return (vx * 3600, vy * 3600)


def passage(
    positie: tuple[float, float], snelheid: tuple[float, float]
) -> tuple[float, float] | None:
    """Bereken wanneer en op welke afstand een cel het dichtst langskomt.

    De cel volgt een rechte lijn. Het dichtste punt is daar waar de verbinding
    tussen jou en de cel loodrecht op die lijn staat. Ligt dat moment in het
    verleden, dan is de cel al voorbij en trekt hij weg.

    Geeft de tijd in minuten en de afstand in kilometers.
    """
    px, py = positie
    vx, vy = snelheid

    snelheid_kwadraat = vx * vx + vy * vy
    if snelheid_kwadraat == 0:
        return None

    # Uren tot het dichtste punt
    uren = -(px * vx + py * vy) / snelheid_kwadraat
    if uren < 0:
        return None  # al voorbij

    dx = px + vx * uren
    dy = py + vy * uren

    return (round(uren * 60), round(math.hypot(dx, dy), 1))


def volg_cel(
    punten: list[tuple[float, float]],
    geschiedenis: list[tuple[float, float, float]],
    lat0: float,
    lon0: float,
    nu: float,
) -> dict | None:
    """Zet alles bij elkaar: welke cel, waarheen, en wanneer hij passeert."""
    cellen = zoek_cellen(punten, lat0, lon0)
    if not cellen:
        return None

    dichtstbij = cellen[0]

    # Hoort dit zwaartepunt bij hetzelfde spoor als de vorige keer? Zo niet,
    # dan is er een andere cel dichterbij gekomen en begint het spoor opnieuw.
    if geschiedenis:
        _, vorige_lat, vorige_lon = geschiedenis[-1]
        x, y = naar_km(dichtstbij["latitude"], dichtstbij["longitude"], vorige_lat, vorige_lon)
        if math.hypot(x, y) > CONTINUITEIT_KM:
            geschiedenis = []

    geschiedenis = geschiedenis + [
        (nu, dichtstbij["latitude"], dichtstbij["longitude"])
    ]

    resultaat = {
        "latitude": dichtstbij["latitude"],
        "longitude": dichtstbij["longitude"],
        # Het spoor van zwaartepunten, om de verplaatsing te kunnen tekenen
        "spoor": [(lat, lon) for _, lat, lon in geschiedenis[-20:]],
        "afstand": dichtstbij["afstand"],
        "inslagen": dichtstbij["inslagen"],
        "cellen": len(cellen),
        "geschiedenis": geschiedenis,
        "richting": None,
        "richting_graden": None,
        "snelheid": None,
        "passage_over": None,
        "passage_afstand": None,
    }

    beweging = beweging_van_reeks(geschiedenis, lat0, lon0)
    if beweging is None:
        return resultaat

    vx, vy = beweging
    snelheid = math.hypot(vx, vy)
    resultaat["snelheid"] = round(snelheid, 1)

    if snelheid < MIN_CELSNELHEID:
        return resultaat

    graden = richting_van_vector(vx, vy)
    resultaat["richting_graden"] = round(graden, 1)
    resultaat["richting"] = kompasrichting(graden)

    positie = naar_km(
        dichtstbij["latitude"], dichtstbij["longitude"], lat0, lon0
    )
    uitkomst = passage(positie, (vx, vy))
    if uitkomst is not None:
        resultaat["passage_over"], resultaat["passage_afstand"] = uitkomst

    return resultaat


def frequentie(tijdstempels: list[float], nu: float, venster: int = 300) -> float:
    """Inslagen per minuut over het opgegeven venster."""
    grens = nu - venster
    aantal = sum(1 for t in tijdstempels if t >= grens)
    return round(aantal / (venster / 60), 1)


def frequentietrend(tijdstempels: list[float], nu: float, venster: int = 300) -> str:
    """Neemt de activiteit toe of af?

    Vergelijkt het laatste venster met het venster daarvoor. Een cel die
    aantrekt verraadt zich in de flitsfrequentie voordat de afstand iets doet.
    """
    recent = sum(1 for t in tijdstempels if t >= nu - venster)
    ervoor = sum(1 for t in tijdstempels if nu - 2 * venster <= t < nu - venster)

    if recent + ervoor < 6:
        return "te weinig gegevens"
    if ervoor == 0:
        return "neemt toe"

    verhouding = recent / ervoor
    if verhouding > 1.5:
        return "neemt snel toe"
    if verhouding > 1.15:
        return "neemt toe"
    if verhouding < 0.5:
        return "neemt snel af"
    if verhouding < 0.85:
        return "neemt af"
    return "stabiel"


def volg_cellen(
    punten: list[tuple[float, float]],
    sporen: list[list[tuple[float, float, float]]],
    lat0: float,
    lon0: float,
    nu: float,
) -> tuple[list[dict], list[list[tuple[float, float, float]]]]:
    """Volg alle cellen tegelijk in plaats van alleen de dichtstbijzijnde.

    Elke cel houdt een eigen spoor bij. Een nieuw zwaartepunt wordt gekoppeld
    aan het spoor waarvan het laatste punt het dichtst ligt; is dat te ver,
    dan begint er een nieuw spoor. Sporen die deze ronde niets kregen
    vervallen, want die cel is uitgeregend of samengevloeid met een andere.
    """
    cellen = zoek_cellen(punten, lat0, lon0)
    if not cellen:
        return ([], [])

    beschikbaar = list(sporen)
    nieuwe_sporen: list[list[tuple[float, float, float]]] = []
    uitkomst: list[dict] = []

    for cel in cellen:
        # Welk bestaand spoor hoort hierbij?
        beste = None
        for index, spoor in enumerate(beschikbaar):
            if not spoor:
                continue
            _, vorige_lat, vorige_lon = spoor[-1]
            x, y = naar_km(cel["latitude"], cel["longitude"], vorige_lat, vorige_lon)
            afstand = math.hypot(x, y)
            if afstand <= CONTINUITEIT_KM and (beste is None or afstand < beste[0]):
                beste = (afstand, index)

        if beste is None:
            spoor = []
        else:
            spoor = beschikbaar.pop(beste[1])

        spoor = (spoor + [(nu, cel["latitude"], cel["longitude"])])[-40:]
        nieuwe_sporen.append(spoor)

        gegevens = {
            **cel,
            "spoor": [(lat, lon) for _, lat, lon in spoor],
            "intensiteit": intensiteit(cel["inslagen"]),
            "richting": None,
            "richting_graden": None,
            "snelheid": None,
            "passage_over": None,
            "passage_afstand": None,
        }

        beweging = beweging_van_reeks(spoor, lat0, lon0)
        if beweging is not None:
            vx, vy = beweging
            snelheid = math.hypot(vx, vy)
            gegevens["snelheid"] = round(snelheid, 1)

            if snelheid >= MIN_CELSNELHEID:
                graden = richting_van_vector(vx, vy)
                gegevens["richting_graden"] = round(graden, 1)
                gegevens["richting"] = kompasrichting(graden)

                positie = naar_km(cel["latitude"], cel["longitude"], lat0, lon0)
                uitslag = passage(positie, (vx, vy))
                if uitslag is not None:
                    gegevens["passage_over"], gegevens["passage_afstand"] = uitslag

        uitkomst.append(gegevens)

    return (uitkomst, nieuwe_sporen)
