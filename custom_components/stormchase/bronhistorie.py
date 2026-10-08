"""Gelukt en mislukt per bron per dag, bewaard over herstarts (L-SC-002).

De tellers in de statistieken beginnen bij elke herstart opnieuw. Op 7
oktober werd de integratie zestien keer herstart, en dan valt uit de
diagnostiek niet af te lezen hoe betrouwbaar een bron over een paar dagen is.
Deze module houdt per kalenderdag (lokale tijd) bij hoe vaak elke bron
slaagde en faalde, en bewaart dat rollend over BEWAAR_DAGEN dagen.

Alleen tellingen: geen foutteksten, geen tijdstippen, geen locatie. Raakt
niets aan meldingen of drempels.

Bewust vrij van Home Assistant-imports, zodat het zonder HA te testen is.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

# Hoeveel dagen we terugkijken. Ouder valt bij de eerstvolgende nieuwe dag af.
BEWAAR_DAGEN = 30

# Versie van het opslagformaat, voor een eventuele latere migratie
OPSLAG_VERSIE = 1


def _als_datum(waarde) -> date | None:
    """Een dagsleutel ('2026-10-07') of datum als date, anders None."""
    if isinstance(waarde, date):
        return waarde
    try:
        return date.fromisoformat(str(waarde))
    except ValueError:
        return None


def _telling(waarde) -> int:
    """Alleen gehele, niet-negatieve tellingen uit de opslag overnemen."""
    if isinstance(waarde, bool) or not isinstance(waarde, int) or waarde < 0:
        return 0
    return waarde


def _percentage(gelukt: int, mislukt: int) -> float | None:
    totaal = gelukt + mislukt
    return round(gelukt / totaal * 100, 1) if totaal else None


class BronHistorie:
    """Tellers per dag per bron, rollend over BEWAAR_DAGEN dagen."""

    def __init__(self, bewaard: dict | None = None) -> None:
        self._dagen: dict[str, dict[str, dict[str, int]]] = {}
        # Of er al een schrijfactie klaarstaat (zie plan_opslag)
        self._gepland = False
        self._laad(bewaard)

    def _laad(self, bewaard: dict | None) -> None:
        """Neem de opgeslagen tellers over en sla alles wat raar is over.

        Een beschadigd of onverwacht bestand mag de integratie niet laten
        vallen; in het ergste geval begint de historie leeg.
        """
        if not isinstance(bewaard, dict):
            return
        dagen = bewaard.get("dagen")
        if not isinstance(dagen, dict):
            return
        for sleutel, bronnen in dagen.items():
            dag = _als_datum(sleutel)
            if dag is None or not isinstance(bronnen, dict):
                continue
            schoon = {}
            for naam, telling in bronnen.items():
                if not isinstance(naam, str) or not isinstance(telling, dict):
                    continue
                schoon[naam] = {
                    "gelukt": _telling(telling.get("gelukt")),
                    "mislukt": _telling(telling.get("mislukt")),
                }
            if schoon:
                self._dagen[dag.isoformat()] = schoon

    def noteer(self, bron: str, gelukt: bool, dag: date) -> None:
        """Tel een geslaagde of mislukte ophaalronde op de gegeven dag."""
        sleutel = dag.isoformat()
        if sleutel not in self._dagen:
            self._dagen[sleutel] = {}
            self.opschonen(dag)
        telling = self._dagen[sleutel].setdefault(bron, {"gelukt": 0, "mislukt": 0})
        telling["gelukt" if gelukt else "mislukt"] += 1

    def opschonen(self, vandaag: date) -> None:
        """Gooi dagen weg die buiten het venster vallen.

        Ook dagen in de toekomst (klok die verzet is) vallen weg, anders
        blijven ze tot in lengte van dagen in het venster hangen.
        """
        grens = vandaag - timedelta(days=BEWAAR_DAGEN - 1)
        for sleutel in list(self._dagen):
            dag = _als_datum(sleutel)
            if dag is None or dag < grens or dag > vandaag:
                del self._dagen[sleutel]

    @property
    def dagen(self) -> list[str]:
        """De bewaarde dagen, oudste eerst."""
        return sorted(self._dagen)

    def plan_opslag(self, plannen) -> None:
        """Plan een schrijfactie, maar niet opnieuw zolang er een klaarstaat.

        De Store van Home Assistant schuift een uitgestelde schrijfactie bij
        elke nieuwe aanvraag weer op. De radar slaagt elke minuut; zonder
        deze rem zou een vertraging van vijf minuten nooit aflopen en kwam
        er pas bij het afsluiten iets op schijf. Nu hooguit eens per
        vertraging, en de eerste ronde na het wegschrijven plant de volgende.
        """
        if self._gepland:
            return
        self._gepland = True
        plannen()

    def naar_opslag(self) -> dict[str, Any]:
        """Wat er in de Store komt (de Store roept dit aan bij het schrijven)."""
        self._gepland = False
        return {
            "versie": OPSLAG_VERSIE,
            "dagen": {
                dag: {naam: dict(t) for naam, t in bronnen.items()}
                for dag, bronnen in sorted(self._dagen.items())
            },
        }

    def als_dict(self) -> dict[str, Any]:
        """Voor in de diagnostiek: per dag en opgeteld over het venster."""
        per_dag = {}
        totaal: dict[str, dict[str, int]] = {}
        for dag in sorted(self._dagen, reverse=True):
            per_dag[dag] = {}
            for naam, t in sorted(self._dagen[dag].items()):
                per_dag[dag][naam] = {
                    "gelukt": t["gelukt"],
                    "mislukt": t["mislukt"],
                    "slaagpercentage": _percentage(t["gelukt"], t["mislukt"]),
                }
                som = totaal.setdefault(naam, {"gelukt": 0, "mislukt": 0, "dagen": 0})
                som["gelukt"] += t["gelukt"]
                som["mislukt"] += t["mislukt"]
                som["dagen"] += 1
        return {
            "bewaar_dagen": BEWAAR_DAGEN,
            "aantal_dagen": len(per_dag),
            "totaal": {
                naam: {
                    **som,
                    "slaagpercentage": _percentage(som["gelukt"], som["mislukt"]),
                }
                for naam, som in sorted(totaal.items())
            },
            "per_dag": per_dag,
        }
