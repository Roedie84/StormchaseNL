"""Modelwindstoten bijstellen met wat het dichtstbijzijnde station meet (0.51.0).

Open-Meteo zat op 9 oktober uren achter elkaar 15-20 km/u boven wat het
KNMI-station Hupsel (3,4 km) mat: 44-55 km/u verwacht tegen 28-40 km/u
gemeten. Zo'n afwijking is per plek en per weertype vrij vast. Daarom
houden we de verhouding gemeten/model bij en schalen de modelwaarde daarmee.

- Een paar is één stationsmeting met de modelwaarde van rond dat moment
  (hooguit 45 minuten verschil: het model ververst elk half uur, de
  meting loopt ~10 minuten achter).
- De factor is de mediaan van de verhoudingen over de laatste 24 uur. Een
  enkele uitschieter (een windvlaag in een bui) verschuift hem dan nauwelijks.
- Pas bij genoeg paren over minstens een uur telt de factor; tot dan blijft
  de modelwaarde staan.
- De factor blijft tussen 0,5 en 1,3: een kapotte meting kan de verwachting
  zo niet wegpoetsen of verdubbelen.
- Bij weinig wind zegt de verhouding niets (2 tegen 4 km/u is "factor 2");
  paren met een modelwaarde onder 10 km/u tellen niet mee.

Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

from statistics import median

VENSTER_S = 24 * 3600
BEWAAR_S = 48 * 3600
MAX_PAREN = 400
MIN_PAREN = 6
MIN_SPANNE_S = 3600
MIN_MODEL_KMH = 10.0
MAX_TIJDVERSCHIL_S = 45 * 60
FACTOR_MIN = 0.5
FACTOR_MAX = 1.3


class Windcorrectie:
    """Leert de verhouding tussen gemeten en verwachte windstoten."""

    def __init__(self, bewaard: list | None = None) -> None:
        self.paren: list[tuple[float, float, float]] = []
        self.herstel(bewaard)

    # ---- vullen ----

    def bij(
        self,
        tijd: float | None,
        gemeten: float | None,
        model: float | None,
        model_tijd: float | None,
    ) -> bool:
        """Voeg een meting toe. True als er een nieuw paar bij kwam."""
        if tijd is None or gemeten is None or model is None or model_tijd is None:
            return False
        try:
            tijd, gemeten, model, model_tijd = (
                float(tijd), float(gemeten), float(model), float(model_tijd)
            )
        except (TypeError, ValueError):
            return False
        if gemeten < 0 or model < MIN_MODEL_KMH:
            return False
        if abs(tijd - model_tijd) > MAX_TIJDVERSCHIL_S:
            return False
        # Dezelfde stationsmeting komt bij elke ophaalronde terug
        if any(abs(t - tijd) < 1 for t, _, _ in self.paren):
            return False
        self.paren.append((tijd, gemeten, model))
        self.paren.sort(key=lambda p: p[0])
        self._snoei(tijd)
        return True

    def _snoei(self, nu: float) -> None:
        grens = nu - BEWAAR_S
        self.paren = [p for p in self.paren if p[0] >= grens][-MAX_PAREN:]

    # ---- gebruiken ----

    def factor(self, nu: float) -> tuple[float | None, int]:
        """De geleerde factor en het aantal paren waarop hij rust."""
        venster = [p for p in self.paren if nu - VENSTER_S <= p[0] <= nu + 60]
        if len(venster) < MIN_PAREN:
            return None, len(venster)
        if venster[-1][0] - venster[0][0] < MIN_SPANNE_S:
            return None, len(venster)
        ruw = median(g / m for _, g, m in venster)
        return round(min(FACTOR_MAX, max(FACTOR_MIN, ruw)), 2), len(venster)

    def corrigeer(self, model: float | None, nu: float) -> dict:
        """Bijgestelde windstoten plus waar dat op rust."""
        factor, paren = self.factor(nu)
        if model is None:
            waarde = None
        elif factor is None:
            waarde = model
        else:
            waarde = round(model * factor, 1)
        return {
            "waarde": waarde,
            "model": model,
            "factor": factor,
            "paren": paren,
            "toegepast": factor is not None and model is not None,
        }

    # ---- opslag ----

    def naar_opslag(self) -> list:
        return [list(p) for p in self.paren]

    def herstel(self, bewaard) -> None:
        if not isinstance(bewaard, list):
            return
        paren = []
        for p in bewaard:
            try:
                t, g, m = (float(x) for x in p)
            except (TypeError, ValueError):
                continue
            paren.append((t, g, m))
        paren.sort(key=lambda p: p[0])
        self.paren = paren[-MAX_PAREN:]
