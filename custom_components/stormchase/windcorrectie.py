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
- Pas bij genoeg paren over minstens zes uur telt de factor; tot dan blijft
  de modelwaarde staan (0.52.0, was een uur).
- De factor blijft tussen 0,5 en 1,3: een kapotte meting kan de verwachting
  zo niet wegpoetsen of verdubbelen.
- Bij weinig wind zegt de verhouding niets (2 tegen 4 km/u is "factor 2");
  paren met een modelwaarde onder 10 km/u tellen niet mee.
- 0.52.0 (L-SC-007): paren tijdens een front leren de factor niet. In de
  nacht van 9 op 10 oktober leerde hij 0,50 van één koufront en zat daarna
  uren te laag; bij rustig weer bleek 0,55 te kloppen. Wat een front is staat
  in const.py (onweer bij het station, drukverandering over een uur, sprong
  in de gemeten stoot), plus een uur naloop.

Opslag: per paar [tijd, gemeten, model, front]. Paren uit 0.51.x hebben geen
frontvlag; bij het terugzetten kijken we dan alsnog naar de stootsprong.

Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

from statistics import median

try:
    from .const import (
        FRONT_DRUK_1U_HPA,
        FRONT_NALOOP_S,
        FRONT_STOOT_SPRONG_KMH,
        FRONT_STOOT_VENSTER_S,
        WINDCORRECTIE_MIN_SPANNE_S,
    )
except ImportError:  # in de tests zonder pakketstructuur
    from const import (
        FRONT_DRUK_1U_HPA,
        FRONT_NALOOP_S,
        FRONT_STOOT_SPRONG_KMH,
        FRONT_STOOT_VENSTER_S,
        WINDCORRECTIE_MIN_SPANNE_S,
    )

VENSTER_S = 24 * 3600
BEWAAR_S = 48 * 3600
MAX_PAREN = 400
MIN_PAREN = 6
MIN_SPANNE_S = WINDCORRECTIE_MIN_SPANNE_S
MIN_MODEL_KMH = 10.0
MAX_TIJDVERSCHIL_S = 45 * 60
FACTOR_MIN = 0.5
FACTOR_MAX = 1.3


class Windcorrectie:
    """Leert de verhouding tussen gemeten en verwachte windstoten."""

    def __init__(self, bewaard: list | None = None) -> None:
        # (tijd, gemeten, model, front)
        self.paren: list[tuple[float, float, float, bool]] = []
        self.herstel(bewaard)

    # ---- vullen ----

    def bij(
        self,
        tijd: float | None,
        gemeten: float | None,
        model: float | None,
        model_tijd: float | None,
        onweer: bool | None = None,
        druk_1u: float | None = None,
    ) -> bool:
        """Voeg een meting toe. True als er een nieuw paar bij kwam.

        `onweer` en `druk_1u` (drukverandering over een uur, hPa) komen van
        de stationsmeting en wijzen op een front (0.52.0).
        """
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
        if any(abs(p[0] - tijd) < 1 for p in self.paren):
            return False
        front = (
            bool(onweer)
            or _drukfront(druk_1u)
            or _stootsprong(self.paren, tijd, gemeten)
        )
        self.paren.append((tijd, gemeten, model, front))
        self.paren.sort(key=lambda p: p[0])
        self._snoei(tijd)
        return True

    def _snoei(self, nu: float) -> None:
        grens = nu - BEWAAR_S
        self.paren = [p for p in self.paren if p[0] >= grens][-MAX_PAREN:]

    # ---- gebruiken ----

    def _venster(self, nu: float) -> list:
        return [p for p in self.paren if nu - VENSTER_S <= p[0] <= nu + 60]

    @staticmethod
    def _rustig(venster: list) -> list:
        """Paren buiten een front en buiten de naloop erna."""
        fronten = [p[0] for p in venster if p[3]]
        return [
            p for p in venster
            if not p[3] and not any(0 < p[0] - f <= FRONT_NALOOP_S for f in fronten)
        ]

    def factor(self, nu: float) -> tuple[float | None, int]:
        """De geleerde factor en het aantal (rustige) paren waarop hij rust."""
        rustig = self._rustig(self._venster(nu))
        if len(rustig) < MIN_PAREN:
            return None, len(rustig)
        if rustig[-1][0] - rustig[0][0] < MIN_SPANNE_S:
            return None, len(rustig)
        ruw = median(p[1] / p[2] for p in rustig)
        return round(min(FACTOR_MAX, max(FACTOR_MIN, ruw)), 2), len(rustig)

    def corrigeer(self, model: float | None, nu: float) -> dict:
        """Bijgestelde windstoten plus waar dat op rust."""
        factor, paren = self.factor(nu)
        venster = self._venster(nu)
        rustig = self._rustig(venster)
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
            # 0.52.0: wat er buiten de leerset viel en hoeveel uur er is
            "paren_front": len(venster) - len(rustig),
            "front": bool(venster) and venster[-1] not in rustig,
            "uren": round((rustig[-1][0] - rustig[0][0]) / 3600, 1) if rustig else 0.0,
        }

    # ---- opslag ----

    def naar_opslag(self) -> list:
        return [[t, g, m, bool(f)] for t, g, m, f in self.paren]

    def herstel(self, bewaard) -> None:
        """Bewaarde paren terugzetten; rommel valt weg.

        Paren uit 0.51.x hebben drie velden en geen frontvlag. Die krijgen
        alsnog de stootsprongtoets tegen de paren ervoor (druk en onweer van
        toen zijn niet bewaard).
        """
        if not isinstance(bewaard, list):
            return
        paren: list = []
        for p in bewaard:
            if not isinstance(p, (list, tuple)) or len(p) not in (3, 4):
                continue
            try:
                t, g, m = (float(x) for x in p[:3])
            except (TypeError, ValueError):
                continue
            paren.append((t, g, m, p[3] if len(p) == 4 else None))
        paren.sort(key=lambda p: p[0])
        klaar: list = []
        for t, g, m, f in paren:
            if f is None:
                f = _stootsprong(klaar, t, g)
            klaar.append((t, g, m, bool(f)))
        self.paren = klaar[-MAX_PAREN:]


def _drukfront(druk_1u) -> bool:
    """Drukverandering over een uur groter dan bij gewoon weer."""
    try:
        return druk_1u is not None and abs(float(druk_1u)) >= FRONT_DRUK_1U_HPA
    except (TypeError, ValueError):
        return False


def _stootsprong(paren: list, tijd: float, gemeten: float) -> bool:
    """Wijkt de gemeten stoot sterk af van de mediaan van het uur ervoor?"""
    eerder = [
        p[1] for p in paren if 0 < tijd - p[0] <= FRONT_STOOT_VENSTER_S
    ]
    if not eerder:
        return False
    return abs(gemeten - median(eerder)) >= FRONT_STOOT_SPRONG_KMH
