"""Afgeleide onweersindices uit modeldata.

Belangrijk om te weten wat dit wel en niet is. Rotatie en hagel worden hier
niet gedetecteerd; dat kan alleen met dopplerradar en dual-polarisatie, en die
ruwe data is niet vrij beschikbaar. Wat hier berekend wordt is of de
*omgeving* rotatie en hagel toelaat. Een hoge score betekent dat buien die
zich vormen zich zo kunnen gedragen, niet dat er nu iets draait.

Alle drempels zijn de gangbare vuistregels uit de stormjagerspraktijk en
staan in de commentaren, zodat je kunt nagaan waar een getal vandaan komt.
"""

from __future__ import annotations

import math

# Windschering over 0-6 km waarboven supercellen mogelijk worden.
# 20 m/s is de klassieke grens, omgerekend 72 km/u.
SHEAR_SUPERCEL = 72.0
# Boven deze waarde is de schering zelden nog de beperkende factor.
SHEAR_HAGEL = 60.0
# CAPE waarbij de opwaartse stroming sterk genoeg is voor forse buien.
CAPE_VOL = 2000.0
CAPE_HAGEL = 2500.0
# Vriesniveau waarbinnen hagel de grond haalt zonder te smelten. Ligt het
# lager, dan is de bui vaak te zwak; ligt het hoger, dan smelt de hagel weg.
VRIESNIVEAU_ONDER = 2000
VRIESNIVEAU_BOVEN = 3500
# WMO-codes voor onweer met hagel
CODES_HAGEL = {96, 99}

# Lightning Potential Index, J/kg. Boven de eerste grens is onweer mogelijk,
# boven de laatste gaat het hard.
LPI_LICHT = 1.0
LPI_FORS = 5.0
LPI_ZWAAR = 20.0

# Maximale opwaartse snelheid in m/s. Vanaf ongeveer twintig kan een bui
# hagelstenen lang genoeg omhoog houden om ze fors te laten worden.
UPDRAFT_MATIG = 5.0
UPDRAFT_FORS = 10.0
UPDRAFT_ZWAAR = 20.0


def peiling(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Bereken de richting van punt 1 naar punt 2, in graden vanaf noord.

    Nodig om zelf de azimut van een blikseminslag te bepalen wanneer we de
    afstand herberekenen vanaf een andere positie dan waar de bron mee
    rekent.
    """
    f1, f2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)

    x = math.sin(dl) * math.cos(f2)
    y = math.cos(f1) * math.sin(f2) - math.sin(f1) * math.cos(f2) * math.cos(dl)

    return round((math.degrees(math.atan2(x, y)) + 360) % 360, 1)


def _componenten(snelheid: float, richting: float) -> tuple[float, float]:
    """Zet windsnelheid en -richting om naar oost- en noordcomponent.

    Meteorologische richting geeft aan waar de wind vandaan komt, dus de
    vector wijst de andere kant op. Voor het verschil tussen twee niveaus
    maakt dat niet uit, zolang je het consequent doet.
    """
    hoek = math.radians(richting)
    return (-snelheid * math.sin(hoek), -snelheid * math.cos(hoek))


def windschering(
    snelheid_onder: float | None,
    richting_onder: float | None,
    snelheid_boven: float | None,
    richting_boven: float | None,
) -> float | None:
    """Bereken de vectorschering tussen twee niveaus, in km/u.

    Het gaat om het verschil in vector, niet in snelheid: wind die van
    richting draait levert schering op, ook als hij even hard blijft waaien.
    Dat draaien is juist wat een bui aan het roteren brengt.
    """
    if None in (snelheid_onder, richting_onder, snelheid_boven, richting_boven):
        return None

    u1, v1 = _componenten(snelheid_onder, richting_onder)
    u2, v2 = _componenten(snelheid_boven, richting_boven)

    return round(math.hypot(u2 - u1, v2 - v1), 1)


def total_totals(
    t850: float | None, td850: float | None, t500: float | None
) -> float | None:
    """De Total Totals index, een klassieke maat voor onweerskans.

    Onder 44 gebeurt er weinig, vanaf 50 zijn zware buien mogelijk en boven
    56 wordt het serieus.
    """
    if None in (t850, td850, t500):
        return None
    return round((t850 + td850) - 2 * t500, 1)


def _schaal(waarde: float | None, maximum: float) -> float:
    """Schaal een waarde naar 0 tot 1, afgekapt op het maximum."""
    if waarde is None or waarde <= 0:
        return 0.0
    return min(waarde / maximum, 1.0)


def rotatiekans(cape: float | None, schering_6km: float | None) -> tuple[int, dict]:
    """Kans dat buien gaan roteren, op basis van de omgeving.

    Het product van beide factoren, niet de som: zonder energie gebeurt er
    niets, en zonder schering roteert een bui niet. Beide zijn nodig.
    """
    energie = _schaal(cape, CAPE_VOL)
    draaiing = _schaal(schering_6km, SHEAR_SUPERCEL)
    score = round(energie * draaiing * 100)

    return score, {
        "cape_factor": round(energie, 2),
        "schering_factor": round(draaiing, 2),
        "schering_0_6km": schering_6km,
        "toelichting": (
            "Product van CAPE en windschering over 0-6 km. Dit is een "
            "omgevingsinschatting, geen detectie van draaiing in een bui."
        ),
    }


def _vriesniveaufactor(hoogte: float | None) -> float:
    """Hoe gunstig is het vriesniveau voor hagel die de grond haalt?"""
    if hoogte is None:
        return 0.5  # onbekend; niet uitsluiten, maar ook niet belonen

    if VRIESNIVEAU_ONDER <= hoogte <= VRIESNIVEAU_BOVEN:
        return 1.0

    # Buiten het gunstige venster loopt de factor af, tot nul op 1000 meter
    # eronder of 1500 meter erboven.
    if hoogte < VRIESNIVEAU_ONDER:
        return max(0.0, 1 - (VRIESNIVEAU_ONDER - hoogte) / 1000)
    return max(0.0, 1 - (hoogte - VRIESNIVEAU_BOVEN) / 1500)


def hagelkans(
    cape: float | None,
    schering_6km: float | None,
    vriesniveau: float | None,
    weercode: int | None = None,
) -> tuple[int, dict]:
    """Kans op hagel van betekenis, op basis van de omgeving.

    Hagel heeft drie dingen nodig: een sterke opwaartse stroming om de
    korrels omhoog te houden, schering zodat ze meerdere rondes maken, en een
    vriesniveau dat laag genoeg ligt om ze niet te laten smelten.
    """
    energie = _schaal(cape, CAPE_HAGEL)
    draaiing = _schaal(schering_6km, SHEAR_HAGEL)
    smelt = _vriesniveaufactor(vriesniveau)

    score = energie * draaiing * smelt * 100

    # Zegt het model zelf onweer met hagel, dan tilt dat de score op.
    modelhagel = weercode in CODES_HAGEL if weercode is not None else False
    if modelhagel:
        score = max(score, 60)

    return round(min(score, 100)), {
        "cape_factor": round(energie, 2),
        "schering_factor": round(draaiing, 2),
        "vriesniveau_factor": round(smelt, 2),
        "vriesniveau_m": vriesniveau,
        "model_meldt_hagel": modelhagel,
        "toelichting": (
            "Product van CAPE, windschering en vriesniveau. Dit is een "
            "omgevingsinschatting; hagel zelf is alleen met dual-polarisatie "
            "radar vast te stellen."
        ),
    }


# ---------------------------------------------------------------------
# Duiding: van getal naar taal
#
# De drempels zijn de gangbare vuistregels. Ze zijn bewust ruim genomen,
# want een enkel getal zegt nooit alles: het gaat om de combinatie.
# ---------------------------------------------------------------------


def duiding_cape(cape: float | None) -> str:
    """Hoeveel energie zit er in de atmosfeer?"""
    if cape is None:
        return "onbekend"
    if cape < 150:
        return "nauwelijks energie"
    if cape < 500:
        return "weinig energie"
    if cape < 1500:
        return "matige energie"
    if cape < 2500:
        return "veel energie"
    return "zeer veel energie"


def duiding_stabiliteit(
    lifted_index: float | None, total_totals: float | None
) -> str:
    """Hoe onstabiel is de lucht?

    Bij voorkeur op de Lifted Index; ontbreekt die, dan op Total Totals.
    Beide zeggen hetzelfde, alleen op een andere schaal.
    """
    if lifted_index is not None:
        if lifted_index >= 0:
            return "stabiel"
        if lifted_index > -3:
            return "licht onstabiel"
        if lifted_index > -6:
            return "onstabiel"
        return "sterk onstabiel"

    if total_totals is not None:
        if total_totals < 44:
            return "stabiel"
        if total_totals < 50:
            return "licht onstabiel"
        if total_totals < 56:
            return "onstabiel"
        return "sterk onstabiel"

    return "onbekend"


def duiding_schering(schering: float | None) -> str:
    """Genoeg windschering voor georganiseerde buien?"""
    if schering is None:
        return "onbekend"
    if schering < 25:
        return "zwak"
    if schering < 50:
        return "matig"
    if schering < SHEAR_SUPERCEL:
        return "sterk"
    return "supercelwaardig"


def duiding_vriesniveau(hoogte: float | None) -> str:
    """Kan hagel de grond halen zonder te smelten?"""
    if hoogte is None:
        return "onbekend"
    if hoogte < VRIESNIVEAU_ONDER:
        return "laag"
    if hoogte <= VRIESNIVEAU_BOVEN:
        return "gunstig voor hagel"
    return "te hoog voor hagel"


# Oplopende ernst, zodat er te vergelijken valt of het vooruitzicht opschaalt
RANG_GEEN = 0
RANG_KLEIN = 1
RANG_ONWEER = 2
RANG_ZWAAR = 3
RANG_NOODWEER = 4


def onweersverwachting(
    cape_piek: float | None,
    lifted_index: float | None,
    total_totals: float | None,
    schering: float | None,
    rotatie: int | None = None,
    hagel: int | None = None,
    lpi: float | None = None,
    updraft: float | None = None,
) -> tuple[str, str, int]:
    """Vat de hele situatie samen in een oordeel plus toelichting.

    Het gaat om de combinatie: energie zonder onstabiliteit levert niets op,
    en energie zonder schering levert hooguit een losse bui op die zichzelf
    binnen een uur opruimt.
    """
    energie = cape_piek or 0
    stabiliteit = duiding_stabiliteit(lifted_index, total_totals)
    stabiel = stabiliteit in ("stabiel", "onbekend")
    rotatie = rotatie or 0
    hagel = hagel or 0
    schering_waarde = schering or 0

    # Het model kan zelf al bliksem en een sterke opwaartse stroming melden.
    # Dat weegt zwaarder dan mijn afgeleide drempels: het is de uitkomst van
    # het weermodel zelf en niet iets wat ik uit losse velden bij elkaar reken.
    if lpi is not None and lpi >= LPI_ZWAAR:
        return (
            "Kans op noodweer",
            f"Model meldt zeer actief onweer, {duiding_updraft(updraft)} "
            f"opwaartse stroming",
            RANG_NOODWEER,
        )

    if (updraft is not None and updraft >= UPDRAFT_ZWAAR) or (
        lpi is not None and lpi >= LPI_FORS and schering_waarde >= 50
    ):
        return (
            "Kans op zwaar onweer",
            f"{duiding_lpi(lpi)}, opwaartse stroming {duiding_updraft(updraft)}, "
            f"schering {duiding_schering(schering)}",
            RANG_ZWAAR,
        )

    if lpi is not None and lpi >= LPI_LICHT:
        return (
            "Kans op onweer",
            f"{duiding_lpi(lpi)}, {stabiliteit}",
            RANG_ONWEER,
        )

    # Zonder energie of bij stabiele lucht gebeurt er niets, hoe hard het ook
    # waait op hoogte.
    if energie < 150 or stabiel:
        return (
            "Geen onweer verwacht",
            f"{duiding_cape(cape_piek)}, lucht is {stabiliteit}",
            RANG_GEEN,
        )

    if rotatie > 60 or hagel > 70 or (energie > 2500 and schering_waarde > SHEAR_SUPERCEL):
        return (
            "Kans op noodweer",
            f"{duiding_cape(cape_piek)}, {stabiliteit}, schering "
            f"{duiding_schering(schering)}. Supercellen mogelijk.",
            RANG_NOODWEER,
        )

    if energie >= 1500 and schering_waarde >= 50 or rotatie > 40 or hagel > 40:
        return (
            "Kans op zwaar onweer",
            f"{duiding_cape(cape_piek)}, {stabiliteit}, schering "
            f"{duiding_schering(schering)}. Georganiseerde buien mogelijk.",
            RANG_ZWAAR,
        )

    if energie >= 500:
        return (
            "Kans op onweer",
            f"{duiding_cape(cape_piek)}, lucht is {stabiliteit}",
            RANG_ONWEER,
        )

    return (
        "Kleine kans op onweer",
        f"{duiding_cape(cape_piek)}, lucht is {stabiliteit}",
        RANG_KLEIN,
    )


def duiding_lpi(lpi: float | None) -> str:
    """Hoeveel bliksem zit erin volgens het model?"""
    if lpi is None:
        return "onbekend"
    if lpi < LPI_LICHT:
        return "geen bliksem verwacht"
    if lpi < LPI_FORS:
        return "enkele ontladingen"
    if lpi < LPI_ZWAAR:
        return "actief onweer"
    return "zeer actief onweer"


def duiding_updraft(updraft: float | None) -> str:
    """Hoe krachtig is de opwaartse stroming?"""
    if updraft is None:
        return "onbekend"
    if updraft < UPDRAFT_MATIG:
        return "zwak"
    if updraft < UPDRAFT_FORS:
        return "matig"
    if updraft < UPDRAFT_ZWAAR:
        return "krachtig"
    return "zeer krachtig"


def duiding_wolkentop(hoogte: float | None) -> str:
    """Hoe hoog reikt de bui?"""
    if hoogte is None:
        return "onbekend"
    if hoogte < 4000:
        return "lage bewolking"
    if hoogte < 8000:
        return "opbouwende bui"
    if hoogte < 11000:
        return "forse bui"
    return "zeer hoge toppen"


def draairichting(richtingen: list[float | None]) -> str:
    """Draait de wind met de hoogte mee met de klok of ertegenin?

    Een hodograaf die met de klok meedraait hoort bij een omgeving waarin
    supercellen zich kunnen organiseren; tegen de klok in werkt tegen. Dit is
    de kern van wat een hodograaf laat zien, zonder dat je hem hoeft te
    kunnen lezen.

    De richtingen komen van laag naar hoog binnen.
    """
    bekend = [r for r in richtingen if r is not None]
    if len(bekend) < 3:
        return "onbekend"

    totaal = 0.0
    for onder, boven in zip(bekend, bekend[1:]):
        verschil = (boven - onder + 540) % 360 - 180  # -180 tot +180
        totaal += verschil

    if totaal > 30:
        return "rechtsdraaiend"
    if totaal < -30:
        return "linksdraaiend"
    return "nauwelijks draaiing"
