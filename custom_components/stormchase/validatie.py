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

# Een voorspelling die zo lang na het verwachte moment nog niet is uitgekomen,
# geldt als niet uitgekomen.
GEDULD_MINUTEN = {
    "regen": 45,
    "aankomst": 60,
    "passage": 30,
}


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

        self._rond_af(
            "passage",
            nu,
            {
                "uitgekomen": werkelijke_afstand is not None,
                "verwachte_afstand_km": verwacht,
                "werkelijke_afstand_km": werkelijke_afstand,
                "afwijking_km": verschil,
            },
        )

    # ---- Samenvatten ----

    def samenvatting(self) -> dict:
        """Per soort hoe goed de voorspellingen uitkwamen."""
        uit: dict[str, dict] = {}

        for soort in {r["soort"] for r in self.uitkomsten}:
            regels = [r for r in self.uitkomsten if r["soort"] == soort]
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

            uit[soort] = samenvatting

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
