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

- 0.54.0 (L-SC-010): de verhouding hangt af van de tijd van de dag. Met
  één factor over 24 uur zat de bijstelling 's nachts ~+5 km/u te hoog en
  overdag ~-3 km/u te laag (drie nachten op rij). Nu telt de mediaan van de
  rustige paren uit hetzelfde tijdvak (uur van de dag +-2 uur) over de laatste
  72 uur. Zijn dat er minder dan vier, dan blijft de 24-uursfactor gelden.
  Replay 10-10/12-10 (n=274): MAE 4,30 -> 3,77 km/u. Grenzen en frontregels
  blijven gelijk.

- 0.59.0 (L-SC-017): uurbijsturing. Uit de leerronde bleek dat de bijgestelde
  verwachting ~een half uur achterloopt op de meting. De laatste
  stationsmeting min de verwachting van dat moment (modelwaarde x factor) is
  de fout (alleen zodra er een factor is; anders blijft het kale model); de helft daarvan gaat bij de komende stoten, begrensd op +-15 km/u
  en lineair aflopend naar 0 over drie uur. Geen (verse) meting: geen
  bijsturing. De factor zelf leert ongewijzigd met de kale modelwaarde.
  Replay 10 dagen (238 uur): uurfout 2,52 -> 2,24 km/u (-11 %).
- 0.59.2: tijdens een front valt de factor niet weg. Lag het laatste paar in
  een front of de naloop en had het 24-uursvenster geen zes uur rustige paren
  meer, dan gold het kale model (24-10 03:24: 64 km/u bij 35 gemeten). Nu
  telt dan de factor uit de rustige paren van 72 uur (zelfde eisen). Bij de
  start (geen 72 uur) blijft het kale model staan zoals voorheen.
- 0.59.3 (L-SC-021): hetzelfde na het front. Zolang het 24-uursvenster nog
  front- of naloopparen bevat en daardoor geen zes uur rustig heeft, telt de
  factor uit de rustige paren van 72 uur. 24-10 12:53-15:34: kaal model
  +6,6 km/u (MAE 7,7, n=16). Een meetgat zonder front: ongewijzigd.

- 0.60.0 (L-SC-022): tijdens een front (laatste paar in front of naloop)
  telt de mediane verhouding gemeten/model van dat front zelf, vanaf het
  eerste front- of naloopparen na rustig weer, in plaats van de algemene
  geleerde factor. De verwachting liep 4 dagen op rij achter bij op- en
  aflopende wind (tot +-6 km/u). Pas vanaf WINDCORRECTIE_FRONT_MIN_PAREN
  frontparen, alleen als er al een geleerde factor is, grenzen 0,5-1,3. De
  bijsturing van 0.59.0 rekent dan met de frontfactor. De geleerde factor
  zelf (`factor`, `factor_bron`) en het leren blijven ongewijzigd; de
  toegepaste staat in `factor_toegepast`.

Opslag: per paar [tijd, gemeten, model, front]. Paren uit 0.51.x hebben geen
frontvlag; bij het terugzetten kijken we dan alsnog naar de stootsprong.

Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

from datetime import datetime, timezone, tzinfo
from statistics import median

try:
    from .const import (
        FRONT_DRUK_1U_HPA,
        WINDBIJSTURING_AANDEEL,
        WINDBIJSTURING_AFLOOP_S,
        WINDBIJSTURING_MAX_KMH,
        WINDBIJSTURING_MAX_LEEFTIJD_S,
        FRONT_NALOOP_S,
        FRONT_STOOT_SPRONG_KMH,
        FRONT_STOOT_VENSTER_S,
        WIND_MELDING_STATION_MAX_S,
        WINDCORRECTIE_FRONT_MIN_PAREN,
        WINDCORRECTIE_MIN_SPANNE_S,
        WINDCORRECTIE_TIJDVAK_MIN_PAREN,
        WINDCORRECTIE_TIJDVAK_S,
        WINDCORRECTIE_TIJDVAK_VENSTER_S,
    )
except ImportError:  # in de tests zonder pakketstructuur
    from const import (
        FRONT_DRUK_1U_HPA,
        WINDBIJSTURING_AANDEEL,
        WINDBIJSTURING_AFLOOP_S,
        WINDBIJSTURING_MAX_KMH,
        WINDBIJSTURING_MAX_LEEFTIJD_S,
        FRONT_NALOOP_S,
        FRONT_STOOT_SPRONG_KMH,
        FRONT_STOOT_VENSTER_S,
        WIND_MELDING_STATION_MAX_S,
        WINDCORRECTIE_FRONT_MIN_PAREN,
        WINDCORRECTIE_MIN_SPANNE_S,
        WINDCORRECTIE_TIJDVAK_MIN_PAREN,
        WINDCORRECTIE_TIJDVAK_S,
        WINDCORRECTIE_TIJDVAK_VENSTER_S,
    )

VENSTER_S = 24 * 3600
# 0.54.0: 72 uur nodig voor het tijdvak (+ marge); ~6 paren per uur
BEWAAR_S = 80 * 3600
MAX_PAREN = 600
MIN_PAREN = 6
MIN_SPANNE_S = WINDCORRECTIE_MIN_SPANNE_S
MIN_MODEL_KMH = 10.0
MAX_TIJDVERSCHIL_S = 45 * 60
FACTOR_MIN = 0.5
FACTOR_MAX = 1.3


class Windcorrectie:
    """Leert de verhouding tussen gemeten en verwachte windstoten."""

    def __init__(self, bewaard: list | None = None, tijdzone: tzinfo | None = None) -> None:
        # (tijd, gemeten, model, front)
        self.paren: list[tuple[float, float, float, bool]] = []
        # 0.54.0: voor het uur van de dag (Home Assistant geeft zijn tijdzone)
        self.tijdzone: tzinfo = tijdzone or timezone.utc
        # 0.59.0 (L-SC-017): laatste stationsmeting met de modelwaarde van
        # dat moment (tijd, gemeten, model), voor de uurbijsturing
        self.laatste: tuple[float, float, float] | None = None
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
        if gemeten < 0 or model < 0:
            return False
        if abs(tijd - model_tijd) > MAX_TIJDVERSCHIL_S:
            return False
        # 0.59.0: ook bij weinig wind telt de fout voor de uurbijsturing
        if self.laatste is None or tijd > self.laatste[0]:
            self.laatste = (tijd, gemeten, model)
        if model < MIN_MODEL_KMH:
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

    def factor_tijdens_front(self, nu: float) -> tuple[float | None, int]:
        """0.59.2: de factor uit de rustige paren van de laatste 72 uur,
        zolang het 24-uursvenster front- of naloopparen bevat (0.59.3: ook
        na het front, tot er weer zes uur rustig in het venster ligt).

        Leerronde 24-10: na een front van ~18 uur zakten de rustige paren in
        het 24-uursvenster onder de zes uur (03:24); de factor (0,70) viel weg
        en de sensor sprong van 43 naar het kale model 64 km/u bij 35 gemeten.
        Een front leert de factor niet (0.52.0) - dan mag hij hem ook niet
        laten verdwijnen. Zelfde eisen (MIN_PAREN, zes uur spanne, grenzen).
        """
        venster = self._venster(nu)
        rustig = self._rustig(venster)
        # 0.59.3 (L-SC-021): ook NA het front, zolang het 24-uursvenster nog
        # front- of naloopparen bevat. Leerronde 24-10 15:40: het front eindigde
        # om ~12:53, het venster had 126 frontparen en 2,7 uur rustig; de factor
        # viel weg en het kale model zat er +6,6 km/u naast (n=16). Een gat in de
        # metingen zonder front (geen frontparen) blijft zoals voorheen.
        if not venster or len(rustig) == len(venster):
            return None, 0
        lang = self._rustig(
            [p for p in self.paren
             if nu - WINDCORRECTIE_TIJDVAK_VENSTER_S <= p[0] <= nu + 60]
        )
        if len(lang) < MIN_PAREN or lang[-1][0] - lang[0][0] < MIN_SPANNE_S:
            return None, len(lang)
        ruw = median(p[1] / p[2] for p in lang)
        return round(min(FACTOR_MAX, max(FACTOR_MIN, ruw)), 2), len(lang)

    def factor_front(self, nu: float) -> tuple[float | None, int]:
        """0.60.0 (L-SC-022): de verhouding gemeten/model van het lopende front.

        Het front loopt vanaf het eerste front- of naloopparen na het laatste
        rustige paar (een meetgat langer dan de naloop breekt het af). None als
        het laatste paar rustig is of er minder dan
        WINDCORRECTIE_FRONT_MIN_PAREN frontparen zijn.
        """
        paren = [p for p in self.paren if p[0] <= nu + 60]
        if not paren:
            return None, 0
        rustig = set(self._rustig(paren))
        reeks: list = []
        for p in reversed(paren):
            if p in rustig:
                break
            if reeks and reeks[-1][0] - p[0] > FRONT_NALOOP_S:
                break
            reeks.append(p)
        if len(reeks) < WINDCORRECTIE_FRONT_MIN_PAREN:
            return None, len(reeks)
        ruw = median(p[1] / p[2] for p in reeks)
        return round(min(FACTOR_MAX, max(FACTOR_MIN, ruw)), 2), len(reeks)

    def _seconde_van_de_dag(self, t: float) -> int:
        d = datetime.fromtimestamp(t, self.tijdzone)
        return d.hour * 3600 + d.minute * 60 + d.second

    def factor_tijdvak(self, nu: float) -> tuple[float | None, int]:
        """0.54.0 (L-SC-010): mediaan van de rustige paren uit hetzelfde
        tijdvak van de dag (+-2 uur) over 72 uur, en hoeveel dat er zijn.
        None zolang er minder dan WINDCORRECTIE_TIJDVAK_MIN_PAREN zijn."""
        venster = [p for p in self.paren
                   if nu - WINDCORRECTIE_TIJDVAK_VENSTER_S <= p[0] <= nu + 60]
        rustig = self._rustig(venster)
        nu_s = self._seconde_van_de_dag(nu)
        dag = 24 * 3600
        vak = []
        for p in rustig:
            verschil = abs(self._seconde_van_de_dag(p[0]) - nu_s)
            if min(verschil, dag - verschil) <= WINDCORRECTIE_TIJDVAK_S:
                vak.append(p)
        if len(vak) < WINDCORRECTIE_TIJDVAK_MIN_PAREN:
            return None, len(vak)
        ruw = median(p[1] / p[2] for p in vak)
        return round(min(FACTOR_MAX, max(FACTOR_MIN, ruw)), 2), len(vak)

    def corrigeer(self, model: float | None, nu: float) -> dict:
        """Bijgestelde windstoten plus waar dat op rust."""
        factor_24u, paren = self.factor(nu)
        # 0.54.0: tijdvakfactor alleen als het leren al loopt (24-uursfactor
        # bestaat); anders blijft de modelwaarde staan zoals voorheen.
        factor_vak, paren_vak = self.factor_tijdvak(nu)
        # 0.59.2: tijdens een lang front niet terug naar het kale model.
        basis, basis_bron = factor_24u, "24 uur"
        if basis is None:
            basis, _ = self.factor_tijdens_front(nu)
            basis_bron = "72 uur (front)"
        if basis is not None and factor_vak is not None:
            factor, bron = factor_vak, "tijdvak"
        else:
            factor, bron = basis, (basis_bron if basis is not None else None)
        venster = self._venster(nu)
        rustig = self._rustig(venster)
        # 0.60.0 (L-SC-022): tijdens een front de verhouding van dat front,
        # zodra er genoeg frontparen zijn; anders de geleerde factor.
        factor_front, paren_front_nu = (None, 0)
        if factor is not None and venster and venster[-1] not in rustig:
            factor_front, paren_front_nu = self.factor_front(nu)
        toegepast = factor_front if factor_front is not None else factor
        if model is None:
            waarde = None
        elif toegepast is None:
            waarde = model
        else:
            waarde = round(model * toegepast, 1)
        # 0.59.0 (L-SC-017): de helft van de laatste fout erbij, aflopend
        # Alleen op de bijgestelde waarde: zonder factor blijft het kale model
        sturing = (self.bijsturing(nu, toegepast) if toegepast is not None
                   else {"kmh": 0.0, "start": 0.0, "fout": None})
        if waarde is not None and sturing["kmh"]:
            waarde = round(max(0.0, waarde + sturing["kmh"]), 1)
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
            # 0.54.0 (L-SC-010)
            "factor_bron": bron,
            "factor_24u": factor_24u,
            "paren_tijdvak": paren_vak,
            # 0.59.0 (L-SC-017)
            "bijsturing": sturing["kmh"],
            "bijsturing_fout": sturing["fout"],
            # 0.60.0 (L-SC-022)
            "factor_front": factor_front,
            "paren_lopend_front": paren_front_nu,
            "factor_toegepast": toegepast,
        }

    def bijsturing(self, nu: float, factor: float | None = None) -> dict:
        """0.59.0 (L-SC-017): bijsturing met de fout van het laatste uur.

        fout = laatste stationsmeting - verwachting van dat moment (model x
        factor, of de kale modelwaarde zolang er geen factor is). De
        bijsturing is WINDBIJSTURING_AANDEEL x fout, begrensd, en loopt
        lineair af naar 0 over WINDBIJSTURING_AFLOOP_S na de meting. Geen
        meting, of een ouder dan WINDBIJSTURING_MAX_LEEFTIJD_S: geen bijsturing.
        """
        return bijsturing(self.laatste, nu, factor)

    def bijgestuurde_uren(self, uren: list, nu: float, factor: float | None = None) -> list:
        """Komende uurstoten [(epoch, model)] bijgesteld en bijgestuurd."""
        if factor is None:
            return [(t, round(float(m), 1)) for t, m in uren if m is not None]
        f = factor
        start = self.bijsturing(nu, factor)["start"]
        laatste_t = self.laatste[0] if self.laatste else nu
        uit = []
        for t, model in uren:
            if model is None:
                continue
            waarde = float(model) * f + start * _afloop(t - laatste_t)
            uit.append((t, round(max(0.0, waarde), 1)))
        return uit

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
        # 0.59.0: de laatste meting voor de uurbijsturing (verloopt na een uur)
        if self.paren:
            self.laatste = tuple(self.paren[-1][:3])


def voor_melding(
    bijgesteld: float | None,
    gemeten: float | None,
    gemeten_tijd: float | None,
    nu: float,
    max_leeftijd_s: float = WIND_MELDING_STATION_MAX_S,
) -> dict:
    """Welke windstoot telt voor de windmelding (0.53.0, L-SC-008 optie c)?

    De hoogste van de bijgestelde verwachting en de laatste stationsmeting,
    als die meting vers genoeg is. Zo kan de bijstelling (die bij rustig weer
    terecht omlaag gaat) een echt gemeten harde stoot nooit onder de drempel
    duwen. Geeft de waarde en waar die vandaan komt: "verwachting",
    "station" of None als er niets is.
    """
    station = None
    if gemeten is not None and gemeten_tijd is not None:
        try:
            gemeten, gemeten_tijd = float(gemeten), float(gemeten_tijd)
        except (TypeError, ValueError):
            gemeten = None
        else:
            leeftijd = nu - gemeten_tijd
            if gemeten >= 0 and -300 <= leeftijd <= max_leeftijd_s:
                station = gemeten
    try:
        verwacht = None if bijgesteld is None else float(bijgesteld)
    except (TypeError, ValueError):
        verwacht = None
    if station is not None and (verwacht is None or station > verwacht):
        return {"waarde": station, "bron": "station",
                "verwachting": verwacht, "gemeten": station}
    return {"waarde": verwacht, "bron": "verwachting" if verwacht is not None else None,
            "verwachting": verwacht, "gemeten": station}


def _afloop(sinds_s: float) -> float:
    """Lineair van 1 (bij de meting) naar 0 na WINDBIJSTURING_AFLOOP_S."""
    if sinds_s <= 0:
        return 1.0
    return max(0.0, 1.0 - sinds_s / WINDBIJSTURING_AFLOOP_S)


def bijsturing(laatste, nu: float, factor: float | None = None) -> dict:
    """0.59.0 (L-SC-017): {"kmh": nu, "start": bij de meting, "fout"}."""
    leeg = {"kmh": 0.0, "start": 0.0, "fout": None}
    if not laatste:
        return leeg
    try:
        tijd, gemeten, model = (float(x) for x in laatste)
    except (TypeError, ValueError):
        return leeg
    leeftijd = nu - tijd
    if leeftijd > WINDBIJSTURING_MAX_LEEFTIJD_S or leeftijd < -300:
        return leeg
    verwacht = model * (1.0 if factor is None else factor)
    fout = gemeten - verwacht
    start = max(-WINDBIJSTURING_MAX_KMH,
                min(WINDBIJSTURING_MAX_KMH, WINDBIJSTURING_AANDEEL * fout))
    return {"kmh": round(start * _afloop(leeftijd), 1),
            "start": round(start, 2), "fout": round(fout, 1)}


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
