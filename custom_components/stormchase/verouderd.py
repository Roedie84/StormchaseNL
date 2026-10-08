"""Oude gegevens blijven tonen als een bron eruit ligt.

Standaard maakt Home Assistant alle entiteiten van een coordinator
onbeschikbaar zodra een ophaalronde faalt. Voor weergegevens is dat de
verkeerde keuze: een waarde van een uur oud met een melding erbij zegt meer
dan een leeg vakje, zeker als je midden in een onweer op je scherm kijkt.

Deze mixin vangt een storing op en geeft de laatst bekende gegevens terug,
tot ze te oud worden om nog iets te betekenen.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

# Hoe lang oude gegevens nog getoond worden als een bron eruit ligt. Liever
# een waarde van een uur oud met een melding erbij dan een leeg dashboard.
MAX_VEROUDERD = timedelta(hours=3)

_LOGGER = logging.getLogger(__name__)


class VerouderdMixin:
    """Houdt de laatst geslaagde gegevens vast bij een storing."""

    _laatst_gelukt = None
    _laatste_gegevens = None
    # 0.47.0: plant het bewaren van de laatst geslaagde gegevens. Zonder dat
    # bleven de sensoren na een herstart onbeschikbaar als de eerste
    # ophaalronde mislukte, ook al was er een uur eerder nog een goede waarde.
    bij_onthoud = None

    def onthoud(self, gegevens):
        """Leg vast dat deze ronde geslaagd is."""
        self._laatst_gelukt = dt_util.utcnow()
        self._laatste_gegevens = gegevens
        if self.bij_onthoud is not None:
            try:
                self.bij_onthoud()
            except Exception:  # noqa: BLE001 - bewaren mag het ophalen niet breken
                _LOGGER.debug("Laatste gegevens niet ingepland voor opslag", exc_info=True)
        return gegevens

    def laatste_naar_opslag(self) -> dict | None:
        """De laatst geslaagde gegevens met hun tijdstip, voor de Store."""
        if self._laatste_gegevens is None or self._laatst_gelukt is None:
            return None
        return {
            "op": self._laatst_gelukt.isoformat(),
            "gegevens": self._laatste_gegevens,
        }

    def herstel_laatste(self, bewaard) -> None:
        """Zet bewaarde gegevens terug als terugval voor de eerste ronde.

        Alleen als terugval: val_terug() houdt zich aan MAX_VEROUDERD, dus te
        oude gegevens worden ook na een herstart niet getoond. Een geslaagde
        ronde overschrijft ze meteen.
        """
        if self._laatste_gegevens is not None or not isinstance(bewaard, dict):
            return
        gegevens = bewaard.get("gegevens")
        try:
            op = datetime.fromisoformat(str(bewaard.get("op")))
        except ValueError:
            return
        if not isinstance(gegevens, dict) or op.tzinfo is None:
            return
        if op > dt_util.utcnow():
            return
        self._laatst_gelukt = op
        self._laatste_gegevens = gegevens

    def val_terug(self, fout: Exception):
        """Geef de vorige gegevens terug, of geef alsnog op.

        Boven de maximale ouderdom heeft terugvallen geen zin meer: dan is een
        onbeschikbare sensor eerlijker dan een waarde die niet meer klopt.
        """
        if self._laatste_gegevens is None or self._laatst_gelukt is None:
            raise UpdateFailed(str(fout)) from fout

        ouderdom = dt_util.utcnow() - self._laatst_gelukt
        if ouderdom > MAX_VEROUDERD:
            raise UpdateFailed(
                f"{fout}; laatste gegevens zijn {ouderdom} oud"
            ) from fout

        minuten = int(ouderdom.total_seconds() / 60)
        _LOGGER.debug(
            "%s: storing, gegevens van %s minuten geleden blijven staan (%s)",
            self.name,
            minuten,
            fout,
        )

        if isinstance(self._laatste_gegevens, dict):
            return {**self._laatste_gegevens, "verouderd_minuten": minuten}
        return self._laatste_gegevens
