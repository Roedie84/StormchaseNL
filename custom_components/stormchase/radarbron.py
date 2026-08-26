"""Haalt het overzicht van radarbeelden op bij RainViewer."""

from __future__ import annotations

import logging

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import RADAR_INTERVAL, RAINVIEWER_URL
from .radar import laatste_frame
from .verouderd import VerouderdMixin

_LOGGER = logging.getLogger(__name__)


class RadarCoordinator(VerouderdMixin, DataUpdateCoordinator[dict]):
    """Houdt bij welk radarbeeld het meest recent is.

    Het overzicht is klein en ververst elke vijf minuten; het beeld zelf
    wordt pas opgehaald wanneer iemand ernaar kijkt.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiseer de coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.title} radar",
            update_interval=RADAR_INTERVAL,
        )
        self.entry = entry
        self._session = async_get_clientsession(hass)
        self.stats = None

    async def _async_update_data(self) -> dict:
        """Vraag het overzicht op en pak het nieuwste beeld."""
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
            return self.val_terug(err)

        frame = laatste_frame(payload)
        if frame is None:
            return self.val_terug(ValueError("geen radarbeelden in het overzicht"))

        return self.onthoud(frame)
