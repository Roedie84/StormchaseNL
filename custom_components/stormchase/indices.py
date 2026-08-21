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
