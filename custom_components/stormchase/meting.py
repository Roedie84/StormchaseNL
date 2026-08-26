"""Metingen van het dichtstbijzijnde weerstation.

Alles wat de integratie verder toont is voorspeld: CAPE, schering, wind,
temperatuur. Deze bron levert wat er daadwerkelijk gemeten is, door de
Duitse weerdienst, op het dichtstbijzijnde station. Dat maakt zichtbaar of
het model er die dag naast zit.

Gratis en zonder sleutel. Dekt Duitsland en de directe omgeving; daarbuiten
komt er niets terug en blijft de sensor leeg.
"""

from __future__ import annotations

import logging

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import BRIGHTSKY_URL, METING_INTERVAL
from .coordinator import LocationMixin
from .verouderd import VerouderdMixin

_LOGGER = logging.getLogger(__name__)


class MetingCoordinator(VerouderdMixin, LocationMixin, DataUpdateCoordinator[dict]):
    """Haalt de meting van het dichtstbijzijnde station op."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiseer de coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.title} meting",
            update_interval=METING_INTERVAL,
        )
        self.entry = entry
        self._session = async_get_clientsession(hass)
        self.stats = None

    async def _async_update_data(self) -> dict:
        """Vraag de laatste waarneming op."""
        latitude, longitude, _ = self.resolve_location()

        try:
            async with async_timeout.timeout(20):
                antwoord = await self._session.get(
                    BRIGHTSKY_URL,
                    params={"lat": round(latitude, 4), "lon": round(longitude, 4)},
                )
                antwoord.raise_for_status()
                payload = await antwoord.json()
            if self.stats is not None:
                self.stats.bronnen["meting"].succes()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Geen meting beschikbaar: %s", err)
            if self.stats is not None:
                self.stats.bronnen["meting"].fout(err)
            return self.val_terug(err)

        weer = payload.get("weather") or {}
        bronnen = payload.get("sources") or []
        station = bronnen[0] if bronnen else {}

        return self.onthoud(
            {
                "temperatuur": weer.get("temperature"),
                "wind": weer.get("wind_speed_10"),
                "windstoten": weer.get("wind_gust_speed_10"),
                "neerslag": weer.get("precipitation_10"),
                "luchtdruk": weer.get("pressure_msl"),
                "luchtvochtigheid": weer.get("relative_humidity"),
                "zicht": weer.get("visibility"),
                "bewolking": weer.get("cloud_cover"),
                "waargenomen_op": weer.get("timestamp"),
                "station": station.get("station_name"),
                "station_afstand_km": (
                    round(station["distance"] / 1000, 1)
                    if station.get("distance") is not None
                    else None
                ),
            }
        )
