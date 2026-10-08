"""Statistieken bijhouden over hoe de integratie zich gedraagt.

Bedoeld om samen met de diagnostiek te delen. Het gaat om tellingen en
tijdstippen, niet om de inhoud van je gegevens: hoe vaak een bron faalde,
welke bron er gebruikt is, hoeveel meldingen er uit zijn gegaan.
"""

from __future__ import annotations

import logging
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.util import dt as dt_util

try:
    from .bronhistorie import BronHistorie
    from .herpoging import is_beperkt, retry_after
except ImportError:  # in de tests zonder pakketstructuur
    from bronhistorie import BronHistorie
    from herpoging import is_beperkt, retry_after

_LOGGER = logging.getLogger(__name__)

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
    # L-SC-002: wordt na elke ronde aangeroepen met True (gelukt) of False,
    # zodat de tellers per dag over herstarts bewaard kunnen worden
    bij_uitkomst: Callable[[bool], None] | None = field(
        default=None, repr=False, compare=False
    )

    def _meld(self, gelukt: bool) -> None:
        """Geef de uitkomst door aan de dagtellers; nooit ten koste van de bron."""
        if self.bij_uitkomst is None:
            return
        try:
            self.bij_uitkomst(gelukt)
        except Exception:  # noqa: BLE001 - statistiek mag het ophalen niet breken
            _LOGGER.debug("Bronstatistiek per dag niet bijgewerkt", exc_info=True)

    def succes(self) -> None:
        """Noteer een geslaagde ophaalronde."""
        self.gelukt += 1
        self.op_rij_mislukt = 0
        self.laatste_succes = dt_util.utcnow()
        self.beperkt = False
        self.retry_after = None
        self._meld(True)

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
        self._meld(False)

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


def _telling(waarde) -> int:
    """Alleen gehele, niet-negatieve tellingen uit de opslag overnemen."""
    if isinstance(waarde, bool) or not isinstance(waarde, int) or waarde < 0:
        return 0
    return waarde


def _moment(waarde) -> datetime | None:
    """Een ISO-tijdstip uit de opslag, alleen met tijdzone."""
    if not isinstance(waarde, str):
        return None
    try:
        moment = datetime.fromisoformat(waarde)
    except ValueError:
        return None
    return moment if moment.tzinfo is not None else None


def _vandaag() -> date:
    """De kalenderdag in de tijdzone van Home Assistant."""
    nu = getattr(dt_util, "now", None)
    return (nu() if nu is not None else dt_util.utcnow()).date()


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

    # L-SC-002: gelukt/mislukt per bron per dag, bewaard over herstarts
    historie: BronHistorie | None = None
    _bij_wijziging: Callable[[], None] | None = field(
        default=None, repr=False, compare=False
    )

    def koppel_historie(
        self,
        historie: BronHistorie,
        bij_wijziging: Callable[[], None] | None = None,
        vandaag: Callable[[], date] = _vandaag,
    ) -> None:
        """Laat elke ophaalronde ook in de dagtellers meetellen.

        `bij_wijziging` plant het wegschrijven naar de opslag; dat gebeurt
        vertraagd, niet bij elke ronde.
        """
        self.historie = historie
        self._bij_wijziging = bij_wijziging

        def maak(naam: str) -> Callable[[bool], None]:
            def noteer(gelukt: bool) -> None:
                historie.noteer(naam, gelukt, vandaag())
                if self._bij_wijziging is not None:
                    self._bij_wijziging()

            return noteer

        for naam, bron in self.bronnen.items():
            bron.bij_uitkomst = maak(naam)

    def noteer_event(self, soort: str) -> None:
        """Tel een afgevuurd event."""
        if soort in self.events:
            self.events[soort] += 1
            self._wijziging()

    def noteer_melding(self, soort: str) -> None:
        """Tel een verstuurde melding."""
        self.meldingen_verstuurd[soort] = self.meldingen_verstuurd.get(soort, 0) + 1
        self._wijziging()

    def _wijziging(self) -> None:
        """Plan het wegschrijven; nooit ten koste van wat er geteld werd."""
        if self._bij_wijziging is None:
            return
        try:
            self._bij_wijziging()
        except Exception:  # noqa: BLE001 - statistiek mag niets breken
            _LOGGER.debug("Tellers niet ingepland voor opslag", exc_info=True)

    # ---- 0.47.0: tellers over een herstart ----

    def tellers_naar_opslag(self) -> dict[str, Any]:
        """De tellers die een herstart moeten overleven.

        Alleen tellingen en tijdstippen, net als de dagtellers. De
        herkansingsplanning (volgende_poging) hoort bij een lopende sessie
        en blijft erbuiten.
        """
        return {
            "bronnen": {
                naam: {
                    "gelukt": bron.gelukt,
                    "mislukt": bron.mislukt,
                    "op_rij_mislukt": bron.op_rij_mislukt,
                    "laatste_succes": _tijd(bron.laatste_succes),
                    "laatste_fout": bron.laatste_fout,
                    "laatste_fout_op": _tijd(bron.laatste_fout_op),
                }
                for naam, bron in self.bronnen.items()
            },
            "regen_via_buienradar": self.regen_via_buienradar,
            "regen_via_open_meteo": self.regen_via_open_meteo,
            "events": dict(self.events),
            "meldingen_verstuurd": dict(self.meldingen_verstuurd),
            "meldingen_mislukt": self.meldingen_mislukt,
        }

    def herstel_tellers(self, bewaard) -> None:
        """Neem bewaarde tellers over; alles wat raar is wordt overgeslagen."""
        if not isinstance(bewaard, dict):
            return
        for naam, waarden in (bewaard.get("bronnen") or {}).items():
            bron = self.bronnen.get(naam)
            if bron is None or not isinstance(waarden, dict):
                continue
            bron.gelukt = _telling(waarden.get("gelukt"))
            bron.mislukt = _telling(waarden.get("mislukt"))
            bron.op_rij_mislukt = _telling(waarden.get("op_rij_mislukt"))
            bron.laatste_succes = _moment(waarden.get("laatste_succes"))
            fout = waarden.get("laatste_fout")
            bron.laatste_fout = fout[:200] if isinstance(fout, str) else None
            bron.laatste_fout_op = _moment(waarden.get("laatste_fout_op"))
        self.regen_via_buienradar = _telling(bewaard.get("regen_via_buienradar"))
        self.regen_via_open_meteo = _telling(bewaard.get("regen_via_open_meteo"))
        for soort, aantal in (bewaard.get("events") or {}).items():
            if soort in self.events:
                self.events[soort] = _telling(aantal)
        self.meldingen_verstuurd = {
            str(soort): _telling(aantal)
            for soort, aantal in (bewaard.get("meldingen_verstuurd") or {}).items()
        }
        self.meldingen_mislukt = _telling(bewaard.get("meldingen_mislukt"))

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
            # L-SC-002: per dag, over herstarts heen (rollend venster)
            "bronnen_per_dag": self.historie.als_dict() if self.historie else None,
        }
