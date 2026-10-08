"""Haalt het overzicht van radarbeelden op bij RainViewer.

0.49.0: met een WMS-sleutel en in Nederland ook het tijdstip van het nieuwste
radarbeeld van het KNMI. Dat komt bij voorkeur uit een melding van de
Notification Service; zonder melding wordt het hooguit elke vijf minuten bij
de WMS opgevraagd. Het beeld zelf wordt pas opgehaald als iemand kijkt.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_RADAR_INTERVAL,
    DEFAULT_RADAR_INTERVAL,
    KNMI_RADAR_INTERVAL,
    RAINVIEWER_URL,
)
from .knmi_api import poging
from .radar import laatste_frame, laatste_satelliet
from .verouderd import VerouderdMixin

_LOGGER = logging.getLogger(__name__)


class RadarCoordinator(VerouderdMixin, DataUpdateCoordinator[dict]):
    """Houdt bij welk radarbeeld het meest recent is.

    Het overzicht is klein en ververst elke vijf minuten; het beeld zelf
    wordt pas opgehaald wanneer iemand ernaar kijkt.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiseer de coordinator."""
        seconden = entry.options.get(
            CONF_RADAR_INTERVAL,
            entry.data.get(CONF_RADAR_INTERVAL, DEFAULT_RADAR_INTERVAL),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.title} radar",
            update_interval=timedelta(seconds=int(seconden)),
        )
        self.entry = entry
        self._session = async_get_clientsession(hass)
        self.stats = None
        # 0.49.0: KNMI-radar
        self.knmi = None  # KnmiBronnen, wordt na het aanmaken gezet
        self.storm = None  # voor de actieve positie
        self._knmi_tijd: datetime | None = None
        self._knmi_gevraagd: datetime | None = None
        self._knmi_gemeld: datetime | None = None

    def _positie(self) -> tuple[float, float]:
        data = getattr(self.storm, "data", None)
        breedte = getattr(data, "latitude", None)
        lengte = getattr(data, "longitude", None)
        if breedte is None or lengte is None:
            return (self.hass.config.latitude, self.hass.config.longitude)
        return (breedte, lengte)

    def knmi_actief(self) -> bool:
        """Of de KNMI-radar hier gebruikt kan worden (sleutel en in Nederland)."""
        knmi = self.knmi
        if knmi is None or knmi.wms is None:
            return False
        return knmi.land.in_nederland(*self._positie())

    def knmi_melding(self, referentie: datetime | None) -> None:
        """Nieuwe radarverwachting gemeld; die tijd geldt vanaf de volgende ronde."""
        if referentie is not None:
            self._knmi_gemeld = referentie

    async def _knmi(self) -> dict | None:
        """Tijdstip van het nieuwste KNMI-radarbeeld, of None."""
        if not self.knmi_actief():
            return None
        nu = dt_util.utcnow()

        gemeld = self._knmi_gemeld
        if gemeld is not None and (self._knmi_tijd is None or gemeld > self._knmi_tijd):
            self._knmi_tijd = gemeld
            self._knmi_gevraagd = nu
        elif self._knmi_gevraagd is None or nu - self._knmi_gevraagd >= KNMI_RADAR_INTERVAL:
            self._knmi_gevraagd = nu
            tijd, _ = await poging(
                self.knmi.afremming["wms"],
                self.stats.bronnen["knmi_wms"] if self.stats is not None else None,
                "radar",
                self.knmi.wms.laatste_radartijd,
            )
            if tijd is not None and (self._knmi_tijd is None or tijd > self._knmi_tijd):
                self._knmi_tijd = tijd

        if self._knmi_tijd is None:
            return None
        # Een beeld van meer dan een half uur oud: dan liever de terugval
        if nu - self._knmi_tijd > timedelta(minutes=30):
            return None
        return {
            "tijd": int(self._knmi_tijd.timestamp()),
            "referentie": self._knmi_tijd.isoformat(),
        }

    async def _async_update_data(self) -> dict:
        """Vraag het overzicht op en pak het nieuwste beeld."""
        knmi = await self._knmi()

        try:
            async with async_timeout.timeout(20):
                antwoord = await self._session.get(RAINVIEWER_URL)
                antwoord.raise_for_status()
                payload = await antwoord.json()
            if self.stats is not None:
                self.stats.bronnen["radar"].succes()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Radaroverzicht niet beschikbaar: %s", err)
            if self.stats is not None:
                self.stats.bronnen["radar"].fout(err)
            if knmi is not None:
                # De KNMI-radar werkt nog; de vorige RainViewer-gegevens blijven
                vorige = self.data or {}
                return {**vorige, "knmi": knmi}
            return self.val_terug(err)

        frame = laatste_frame(payload)
        if frame is None:
            if knmi is not None:
                return {**(self.data or {}), "knmi": knmi}
            return self.val_terug(ValueError("geen radarbeelden in het overzicht"))

        return self.onthoud(
            {"radar": frame, "satelliet": laatste_satelliet(payload), "knmi": knmi}
        )
