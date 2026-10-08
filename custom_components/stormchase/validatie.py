"""Voorspellingen bijhouden en achteraf nakijken.

De integratie doet uitspraken die te controleren zijn: over hoeveel minuten
het gaat regenen, wanneer het onweer aankomt, en op welke afstand een cel
passeert. Deze module legt die uitspraken vast en vergelijkt ze later met wat
er daadwerkelijk gebeurde.

Dat levert twee dingen op. Je ziet zelf of de getallen kloppen, en de
uitkomsten komen mee in de diagnostiek zodat de drempels op echte metingen
bijgesteld kunnen worden in plaats van op aannames.

Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

# Hoeveel afgeronde voorspellingen we bewaren
MAX_UITKOMSTEN = 60

# Voorspellingen worden per horizon gegroepeerd. Een nowcast tien minuten
# vooruit is iets heel anders dan een uur vooruit, en dat door elkaar middelen
# verbergt precies wat je wil weten.
HORIZONNEN = [(15, "tot 15 min"), (45, "15 tot 45 min"), (10**9, "meer dan 45 min")]


def horizon(minuten: float) -> str:
    """In welke groep valt deze voorspelling?"""
    for grens, naam in HORIZONNEN:
        if minuten <= grens:
            return naam
    return HORIZONNEN[-1][1]


# Een voorspelling die zo lang na het verwachte moment nog niet is uitgekomen,
# geldt als niet uitgekomen.
# Voor de aankomst was dit een uur, ongeacht hoe kort vooruit de voorspelling
# ging. Daardoor kon een voorspelling van "binnen tien minuten" nog als
# uitgekomen tellen toen het onweer zevenenveertig minuten later arriveerde.
# Dat is geen treffer maar een misser die te laat werd afgerekend.
GEDULD_MINUTEN = {
    "regen": 45,
    "aankomst": 20,
    "passage": 30,
}


# Een passage is pas raak als de cel ook echt op ongeveer de voorspelde
# afstand langskwam. Tot 0.46.0 telde elke gemeten afstand als uitgekomen,
# waardoor passage 21/21 haalde terwijl maar 5 van de 12 bewaarde uitkomsten
# binnen 10 km zaten (uitschieters tot 56 km).
PASSAGE_RAAK_KM = 10.0
PASSAGE_RUIM_KM = 20.0


def _mediaan(waarden: list[float]) -> float:
    rij = sorted(waarden)
    midden = len(rij) // 2
    if len(rij) % 2:
        return rij[midden]
    return (rij[midden - 1] + rij[midden]) / 2


class Validatie:
    """Houdt open voorspellingen bij en rekent ze af."""

    def __init__(self, uitkomsten: list | None = None) -> None:
        """Begin met eventueel bewaarde uitkomsten."""
        self.open: dict[str, dict] = {}
        self.uitkomsten: list[dict] = list(uitkomsten or [])

    # ---- Vastleggen ----

    def voorspel(self, soort: str, nu: float, over_minuten: float, extra: dict) -> None:
        """Leg een voorspelling vast, als er nog geen open staat.

        Eentje tegelijk per soort: anders zou elke ronde van tien seconden een
        nieuwe voorspelling opleveren en zegt het gemiddelde niets meer.
        """
        if soort in self.open:
            return

        self.open[soort] = {
            "gemaakt_op": nu,
            "verwacht_op": nu + over_minuten * 60,
            "verwacht_over": round(over_minuten),
            **extra,
        }

    def _rond_af(self, soort: str, nu: float, uitkomst: dict) -> None:
        """Sluit een voorspelling af en bewaar het resultaat."""
        voorspelling = self.open.pop(soort, None)
        if voorspelling is None:
            return

        regel = {
            "soort": soort,
            "voorspeld_over_min": voorspelling["verwacht_over"],
            "horizon": horizon(voorspelling["verwacht_over"]),
            "gemaakt_op": voorspelling["gemaakt_op"],
            **uitkomst,
        }
        self.uitkomsten.append(regel)
        del self.uitkomsten[:-MAX_UITKOMSTEN]

    # ---- Nakijken ----

    def uitgekomen(self, soort: str, nu: float, extra: dict | None = None) -> None:
        """Het voorspelde gebeurde: reken uit hoeveel het scheelde."""
        voorspelling = self.open.get(soort)
        if voorspelling is None:
            return

        afwijking = (nu - voorspelling["verwacht_op"]) / 60
        self._rond_af(
            soort,
            nu,
            {
                "uitgekomen": True,
                "afwijking_min": round(afwijking, 1),
                "werkelijk_over_min": round((nu - voorspelling["gemaakt_op"]) / 60),
                **(extra or {}),
            },
        )

    def verlopen(self, nu: float) -> None:
        """Ruim voorspellingen op die ruim over tijd zijn."""
        for soort, voorspelling in list(self.open.items()):
            geduld = GEDULD_MINUTEN.get(soort, 45) * 60
            if nu > voorspelling["verwacht_op"] + geduld:
                self._rond_af(soort, nu, {"uitgekomen": False})

    def passage_afgerond(
        self, nu: float, werkelijke_afstand: float | None
    ) -> None:
        """Een celpassage beoordelen op afstand in plaats van op tijd."""
        voorspelling = self.open.get("passage")
        if voorspelling is None or nu < voorspelling["verwacht_op"]:
            return

        verwacht = voorspelling.get("verwachte_afstand")
        verschil = None
        if verwacht is not None and werkelijke_afstand is not None:
            verschil = round(werkelijke_afstand - verwacht, 1)

        # `uitgekomen` blijft "er is een afstand gemeten", zodat oude en
        # nieuwe tellingen vergelijkbaar zijn. Of de voorspelling raak was,
        # staat in `raak` / `binnen_10_km` / `binnen_20_km`.
        binnen_10 = verschil is not None and abs(verschil) <= PASSAGE_RAAK_KM
        binnen_20 = verschil is not None and abs(verschil) <= PASSAGE_RUIM_KM
        self._rond_af(
            "passage",
            nu,
            {
                "uitgekomen": werkelijke_afstand is not None,
                "raak": binnen_10,
                "binnen_10_km": binnen_10,
                "binnen_20_km": binnen_20,
                "verwachte_afstand_km": verwacht,
                "werkelijke_afstand_km": werkelijke_afstand,
                "afwijking_km": verschil,
            },
        )

    # ---- Samenvatten ----

    def samenvatting(self, per_horizon: bool = True) -> dict:
        """Hoe goed de voorspellingen uitkwamen, per soort en per horizon.

        Zonder die opsplitsing trekt een enkele uitschieter ver vooruit het
        gemiddelde scheef en lijkt de hele voorspelling slecht, terwijl hij
        dichtbij prima werkt.
        """
        uit: dict[str, dict] = {}

        sleutels = {
            (r["soort"], r.get("horizon") if per_horizon else None)
            for r in self.uitkomsten
        }

        for soort, groep in sleutels:
            regels = [
                r
                for r in self.uitkomsten
                if r["soort"] == soort
                and (not per_horizon or r.get("horizon") == groep)
            ]
            raak = [r for r in regels if r.get("uitgekomen")]

            samenvatting = {
                "aantal": len(regels),
                "uitgekomen": len(raak),
            }

            afwijkingen = [
                abs(r["afwijking_min"]) for r in raak if "afwijking_min" in r
            ]
            if afwijkingen:
                samenvatting["gemiddelde_afwijking_min"] = round(
                    sum(afwijkingen) / len(afwijkingen), 1
                )
                samenvatting["grootste_afwijking_min"] = round(max(afwijkingen), 1)

            km = [abs(r["afwijking_km"]) for r in raak if r.get("afwijking_km") is not None]
            if km:
                samenvatting["gemiddelde_afwijking_km"] = round(sum(km) / len(km), 1)

            if soort == "passage":
                samenvatting.update(self._passage_trefkans(regels))

            naam = f"{soort} ({groep})" if per_horizon and groep else soort
            uit[naam] = samenvatting

        return dict(sorted(uit.items()))

    @staticmethod
    def _passage_trefkans(regels: list[dict]) -> dict:
        """Trefkans op afstand: raak binnen 10 km, ruim raak binnen 20 km.

        Berekend uit `afwijking_km`, zodat ook uitkomsten van voor 0.46.0
        meetellen. Een passage zonder gemeten afstand telt als mis.
        """
        aantal = len(regels)
        km = [
            abs(r["afwijking_km"])
            for r in regels
            if r.get("afwijking_km") is not None
        ]
        binnen_10 = sum(1 for a in km if a <= PASSAGE_RAAK_KM)
        binnen_20 = sum(1 for a in km if a <= PASSAGE_RUIM_KM)
        uit = {
            "uitgekomen_betekent": "afstand gemeten",
            "raak": binnen_10,
            "binnen_10_km": binnen_10,
            "binnen_20_km": binnen_20,
            "trefkans_10_km_pct": round(100 * binnen_10 / aantal) if aantal else None,
            "trefkans_20_km_pct": round(100 * binnen_20 / aantal) if aantal else None,
        }
        if km:
            uit["mediane_afwijking_km"] = round(_mediaan(km), 1)
            uit["grootste_afwijking_km"] = round(max(km), 1)
        return uit

    def als_dict(self) -> dict:
        """Alles voor in de diagnostiek en om te bewaren."""
        return {
            "open": {
                soort: {
                    "verwacht_over_min": v["verwacht_over"],
                    **{k: w for k, w in v.items() if k not in
                       ("gemaakt_op", "verwacht_op", "verwacht_over")},
                }
                for soort, v in self.open.items()
            },
            "samenvatting": self.samenvatting(),
            "uitkomsten": self.uitkomsten[-20:],
        }
