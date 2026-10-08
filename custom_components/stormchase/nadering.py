"""Naderingssnelheid uit nieuwe inslagafstanden.

Vrij van Home Assistant-imports, zodat het zonder die installatie te testen is.

Tot 0.45.0 kreeg de regressie elke ronde van tien seconden een punt, ook als
er geen nieuwe inslag was. Eén nieuwe afstand tussen tientallen herhalingen
gaf eerst een steile helling en daarna, naarmate de oude punten uit het
venster van 15 minuten vielen, een steeds vlakkere. Op 7 oktober sprong de
aankomsttijd zo van 45 naar 1214 minuten zonder één nieuwe inslag, en duurden
3 van de 4 nadert-perioden precies 15 minuten: het venster zelf.

Nu telt een punt alleen als er een nieuwe inslag is (of de afstand echt
veranderd is, bijvoorbeeld omdat je rijdt). De snelheid wordt alleen bij zo'n
nieuw punt berekend en daarna vastgehouden. Ze vervalt zodra er te weinig
metingen in het venster over zijn; ze verandert nooit doordat een oud punt uit
het venster valt.
"""

from __future__ import annotations

from collections import deque

# Zonder nieuwe inslag telt een afstandsverschil pas vanaf hier als nieuwe
# meting. Kleiner is ruis van de GPS of afronding; groter is verplaatsing.
VERPLAATSING_KM = 0.5


def regressiesnelheid(punten: list[tuple[float, float]]) -> float | None:
    """Snelheid in km/u uit (tijd in s, afstand in km); positief = nadert."""
    n = len(punten)
    if n < 2:
        return None
    gem_t = sum(t for t, _ in punten) / n
    gem_d = sum(d for _, d in punten) / n
    teller = sum((t - gem_t) * (d - gem_d) for t, d in punten)
    noemer = sum((t - gem_t) ** 2 for t, _ in punten)
    if noemer == 0:
        return None
    # Plus nul, anders levert een vlakke reeks -0.0 op ("-0,0 km/u").
    return round(-teller / noemer * 3600, 1) + 0.0


class Naderingstrend:
    """Houdt de nieuwe afstandsmetingen bij en de daaruit berekende snelheid."""

    def __init__(self, venster_s: float, min_metingen: int, maxlen: int = 240):
        self.venster_s = venster_s
        self.min_metingen = min_metingen
        self.metingen: deque[tuple[float, float]] = deque(maxlen=maxlen)
        self._sleutel = None
        self._snelheid: float | None = None
        # Tijdstip waarna de vastgehouden snelheid te weinig steun heeft
        self._geldig_tot: float | None = None

    def bij(self, nu: float, afstand: float | None, inslag=None) -> bool:
        """Verwerk een ronde. True als dit een nieuwe meting was.

        `inslag` is de tijd van de nieuwste inslag (of iets anders dat alleen
        bij een nieuwe inslag verandert). Zonder die tijd telt elke
        afstandsverandering als nieuw.
        """
        if afstand is None:
            return False

        if self.metingen:
            vorige = self.metingen[-1][1]
            if inslag is None:
                nieuw = afstand != vorige
            else:
                nieuw = (
                    inslag != self._sleutel
                    or abs(afstand - vorige) >= VERPLAATSING_KM
                )
        else:
            nieuw = True

        self._sleutel = inslag
        if not nieuw:
            return False

        self.metingen.append((nu, afstand))
        recent = [(t, d) for t, d in self.metingen if t >= nu - self.venster_s]
        if len(recent) < self.min_metingen:
            self._snelheid = None
            self._geldig_tot = None
            return True

        self._snelheid = regressiesnelheid(recent)
        # Geldig zolang de min_metingen nieuwste punten in het venster liggen
        self._geldig_tot = recent[-self.min_metingen][0] + self.venster_s
        return True

    def snelheid(self, nu: float) -> float | None:
        """De laatst berekende snelheid, of None als die te weinig steun heeft."""
        if self._snelheid is None or self._geldig_tot is None:
            return None
        if nu > self._geldig_tot:
            return None
        return self._snelheid

    def wis(self) -> None:
        self.metingen.clear()
        self._sleutel = None
        self._snelheid = None
        self._geldig_tot = None
