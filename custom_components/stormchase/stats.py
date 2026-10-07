"""Statistieken bijhouden over hoe de integratie zich gedraagt.

Bedoeld om samen met de diagnostiek te delen. Het gaat om tellingen en
tijdstippen, niet om de inhoud van je gegevens: hoe vaak een bron faalde,
welke bron er gebruikt is, hoeveel meldingen er uit zijn gegaan.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from homeassistant.util import dt as dt_util

try:
    from .herpoging import is_beperkt, retry_after
except ImportError:  # in de tests zonder pakketstructuur
    from herpoging import is_beperkt, retry_after

# Hoeveel meetpunten we bewaren voor de afstandsreeks
GESCHIEDENIS = 180

# Een bron hapert pas na zoveel mislukte rondes op rij (0.42.0). Een enkele
# gemiste ronde - de radar slaat af en toe één minuut over - is geen storing.
HAPERT_NA_POGINGEN = 2

# ... of als het laatste succes langer geleden is dan dit, ook bij één
# mislukte ronde: een bron die zelden ophaalt, mist er dan echt een.
HAPERT_NA_MINUTEN = 15


@dataclass
class BronStatus:
    """Hoe vaak een externe bron slaagde of faalde."""

    gelukt: int = 0
    mislukt: int = 0
    laatste_succes: datetime | None = None
    laatste_fout: str | None = None
    laatste_fout_op: datetime | None = None
    op_rij_mislukt: int = 0
    # 0.43.0: herkansing na een storing
    beperkt: bool = False
    retry_after: timedelta | None = None
    volgende_poging: datetime | None = None
    herkansing: bool = False

    def succes(self) -> None:
        """Noteer een geslaagde ophaalronde."""
        self.gelukt += 1
        self.op_rij_mislukt = 0
        self.laatste_succes = dt_util.utcnow()
        self.beperkt = False
        self.retry_after = None

    def fout(self, melding) -> None:
        """Noteer een mislukte ophaalronde.

        Is de melding een HTTP 429, dan onthouden we dat de bron ons afremt,
        zodat er geen vervroegde herkansing komt (0.43.0).
        """
        self.beperkt = is_beperkt(melding)
        self.retry_after = retry_after(melding) if self.beperkt else None
        self.mislukt += 1
        self.op_rij_mislukt += 1
        self.laatste_fout = str(melding)[:200]
        self.laatste_fout_op = dt_util.utcnow()

    def hapert(self, nu: datetime | None = None) -> bool:
        """Of deze bron nu echt hapert (0.42.0).

        Niet bij één gemiste ronde: pas na HAPERT_NA_POGINGEN op rij, of als
        het laatste succes langer dan HAPERT_NA_MINUTEN geleden is.
        """
        if self.op_rij_mislukt == 0:
            return False
        if self.op_rij_mislukt >= HAPERT_NA_POGINGEN:
            return True
        if self.laatste_succes is None:
            return True
        nu = nu or dt_util.utcnow()
        return (nu - self.laatste_succes).total_seconds() > HAPERT_NA_MINUTEN * 60

    def als_dict(self) -> dict[str, Any]:
        """Voor in de diagnostiek."""
        totaal = self.gelukt + self.mislukt
        return {
            "gelukt": self.gelukt,
            "mislukt": self.mislukt,
            "slaagpercentage": round(self.gelukt / totaal * 100) if totaal else None,
            "laatste_succes": _tijd(self.laatste_succes),
            "laatste_fout": self.laatste_fout,
            "laatste_fout_op": _tijd(self.laatste_fout_op),
            "op_rij_mislukt": self.op_rij_mislukt,
            "volgende_poging": _tijd(self.volgende_poging),
            "herkansing": self.herkansing,
            "afgeremd": self.beperkt,
        }


def _tijd(moment: datetime | None) -> str | None:
    """Tijdstip als leesbare tekst."""
    return moment.isoformat() if moment else None


@dataclass
class Statistieken:
    """Alles wat we over de werking van de integratie bijhouden."""

    gestart_op: datetime = field(default_factory=dt_util.utcnow)

    # Externe bronnen
    bronnen: dict[str, BronStatus] = field(
        default_factory=lambda: {
            "open_meteo": BronStatus(),
            "buienradar": BronStatus(),
            "meteoalarm": BronStatus(),
            "geocodering": BronStatus(),
            "icon_d2": BronStatus(),
            "lifted_index": BronStatus(),
            "ensemble": BronStatus(),
            "meting": BronStatus(),
            "ensemble_leden": BronStatus(),
            "radar": BronStatus(),
        }
    )

    # Welke neerslagbron er daadwerkelijk gebruikt is
    regen_via_buienradar: int = 0
    regen_via_open_meteo: int = 0

    # Events die de integratie heeft afgevuurd
    events: dict[str, int] = field(
        default_factory=lambda: {
            "nearby": 0,
            "approaching": 0,
            "cleared": 0,
            "rain_incoming": 0,
            "wind": 0,
            "weather": 0,
            "outlook": 0,
            "shelter": 0,
            "alert": 0,
        }
    )

    # Verstuurde meldingen
    meldingen_verstuurd: dict[str, int] = field(default_factory=dict)
    meldingen_mislukt: int = 0

    # Waarschuwingen: hoeveel er landelijk waren en hoeveel er overbleven
    alert_laatste_in_land: int | None = None
    alert_laatste_na_filter: int | None = None
    alert_filternamen: list[str] = field(default_factory=list)

    # Reeks van afstanden met de berekende snelheid erbij, om achteraf te
    # kunnen beoordelen of de nadering klopte
    afstandsreeks: deque = field(
        default_factory=lambda: deque(maxlen=GESCHIEDENIS)
    )

    def noteer_event(self, soort: str) -> None:
        """Tel een afgevuurd event."""
        if soort in self.events:
            self.events[soort] += 1

    def noteer_melding(self, soort: str) -> None:
        """Tel een verstuurde melding."""
        self.meldingen_verstuurd[soort] = self.meldingen_verstuurd.get(soort, 0) + 1

    def noteer_meting(self, afstand: float | None, snelheid: float | None) -> None:
        """Bewaar een meetpunt, maar alleen als er iets te meten viel."""
        if afstand is None:
            return
        self.afstandsreeks.append(
            {
                "op": _tijd(dt_util.utcnow()),
                "afstand": afstand,
                "snelheid": snelheid,
            }
        )

    def als_dict(self) -> dict[str, Any]:
        """Alles op een rij voor in de diagnostiek."""
        draaitijd = dt_util.utcnow() - self.gestart_op
        return {
            "gestart_op": _tijd(self.gestart_op),
            "draaitijd_uren": round(draaitijd.total_seconds() / 3600, 1),
            "bronnen": {naam: bron.als_dict() for naam, bron in self.bronnen.items()},
            "regenbron_gebruikt": {
                "buienradar": self.regen_via_buienradar,
                "open_meteo": self.regen_via_open_meteo,
            },
            "events_afgevuurd": dict(self.events),
            "meldingen_verstuurd": dict(self.meldingen_verstuurd),
            "meldingen_mislukt": self.meldingen_mislukt,
            "waarschuwingen": {
                "laatste_aantal_in_land": self.alert_laatste_in_land,
                "laatste_aantal_na_filter": self.alert_laatste_na_filter,
                "filternamen": self.alert_filternamen,
            },
            "afstandsreeks": list(self.afstandsreeks),
        }
