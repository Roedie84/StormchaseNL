"""Radarbeeld dat je eigen positie volgt.

Een gewone entiteit in plaats van een ingesloten webpagina: geen
cookiemelding, geen advertenties, en het beeld schuift mee met de locatie die
de integratie gebruikt.
"""

from __future__ import annotations

import asyncio
import logging
from io import BytesIO

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

# Uitsnede rond het middelpunt; 512 bij een raster van 768 laat genoeg
# omgeving zien zonder dat de randen van het raster in beeld komen.
UITSNEDE = 512

from .const import (
    CONF_RADAR_KLEUR,
    CONF_RADAR_ZOOM,
    DEFAULT_RADAR_KLEUR,
    DEFAULT_RADAR_ZOOM,
    DOMAIN,
)
from .radar import (
    INSLAG_VENSTER,
    KAART_HELDERHEID,
    KAART_KLEUR,
    TEGEL_AGENT,
    basiskaart_url,
    pixelpositie,
    radartegel_url,
    tegelraster,
)
from .radarbron import RadarCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Zet het radarbeeld op."""
    gegevens = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [RadarImage(hass, gegevens["radar"], gegevens["storm"], entry)]
    )


class RadarImage(CoordinatorEntity[RadarCoordinator], ImageEntity):
    """Het meest recente radarbeeld rond je positie."""

    _attr_has_entity_name = True
    _attr_translation_key = "radar"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: RadarCoordinator,
        storm,
        entry: ConfigEntry,
    ) -> None:
        """Initialiseer het beeld."""
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)

        self._storm = storm
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_radar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Stormchase",
            manufacturer="Stormchase",
            model="Onweersmonitor",
        )
        self._vorige_url = None

    def _opt(self, sleutel: str, standaard):
        """Instelling ophalen."""
        return self._entry.options.get(
            sleutel, self._entry.data.get(sleutel, standaard)
        )

    @property
    def _positie(self) -> tuple[float, float]:
        """De locatie waarop het beeld gecentreerd wordt."""
        gegevens = self._storm.data if self._storm else None
        latitude = getattr(gegevens, "latitude", None)
        longitude = getattr(gegevens, "longitude", None)

        if latitude is None or longitude is None:
            return (self.hass.config.latitude, self.hass.config.longitude)
        return (latitude, longitude)

    async def _haal_tegel(self, url: str | None) -> bytes | None:
        """Haal een enkele tegel op; een missende tegel is geen probleem."""
        if url is None:
            return None
        try:
            antwoord = await self._client.get(
                url, timeout=15, headers={"User-Agent": TEGEL_AGENT}
            )
            antwoord.raise_for_status()
            return antwoord.content
        except Exception as err:  # noqa: BLE001 - een tegel mag ontbreken
            _LOGGER.debug("Tegel niet opgehaald: %s (%s)", url, err)
            return None

    @staticmethod
    def _teken_inslagen(doek, raster: dict, inslagen: list) -> None:
        """Zet de blikseminslagen op het beeld.

        De radar laat zien waar de neerslag hangt, de inslagen waar de bui
        echt actief is. Verse inslagen zijn fel wit, oudere doven uit, zodat
        je in een oogopslag ziet welke kant de activiteit op schuift.
        """
        from PIL import ImageDraw

        tekenaar = ImageDraw.Draw(doek, "RGBA")

        for ouderdom, latitude, longitude in inslagen:
            positie = pixelpositie(latitude, longitude, raster)
            if positie is None:
                continue

            # Van fel wit naar diep oranje naarmate de inslag ouder wordt
            deel = min(ouderdom / INSLAG_VENSTER, 1.0)
            doorzicht = int(255 - deel * 190)
            groen = int(255 - deel * 130)
            straal = 4 if deel < 0.2 else 3

            px, py = positie
            tekenaar.ellipse(
                (px - straal, py - straal, px + straal, py + straal),
                fill=(255, groen, 60, doorzicht),
            )

    @staticmethod
    def _teken_positie(doek, raster: dict) -> None:
        """Markeer waar je zelf bent, anders zegt de rest weinig."""
        from PIL import ImageDraw

        tekenaar = ImageDraw.Draw(doek, "RGBA")
        px, py = raster["midden_x"], raster["midden_y"]

        tekenaar.ellipse((px - 7, py - 7, px + 7, py + 7), outline=(255, 255, 255, 180), width=2)
        tekenaar.ellipse((px - 2, py - 2, px + 2, py + 2), fill=(255, 255, 255, 230))

    def _stel_samen(
        self, kaarten: list, radars: list, raster: dict, inslagen: list
    ) -> bytes:
        """Leg de radar over de kaart en snijd rond het middelpunt uit.

        Draait in een aparte draad, want beeldbewerking blokkeert anders de
        rest van Home Assistant.
        """
        from PIL import Image, ImageEnhance

        afmeting = raster["afmeting"]
        doek = Image.new("RGBA", (afmeting, afmeting), (18, 18, 22, 255))

        def plak(laag):
            """Leg een set tegels op het doek; een missende tegel is geen ramp."""
            for tegel, inhoud in zip(raster["tegels"], laag):
                if inhoud is None:
                    continue
                try:
                    beeld = Image.open(BytesIO(inhoud)).convert("RGBA")
                except Exception:  # noqa: BLE001 - beschadigde tegel overslaan
                    continue
                doek.paste(beeld, (tegel["plak_x"], tegel["plak_y"]), beeld)

        # Eerst de kaart, die daarna gedempt wordt. De radar gaat er pas
        # overheen, anders zou die mee verduisteren en onzichtbaar worden.
        plak(kaarten)
        doek = ImageEnhance.Brightness(doek.convert("RGB")).enhance(
            KAART_HELDERHEID
        )
        doek = ImageEnhance.Color(doek).enhance(KAART_KLEUR).convert("RGBA")

        plak(radars)

        # Inslagen en de eigen positie gaan als laatste over alles heen
        self._teken_inslagen(doek, raster, inslagen)
        self._teken_positie(doek, raster)

        # Uitsnijden rond de gevraagde positie, binnen de randen blijven
        helft = UITSNEDE // 2
        links = int(min(max(raster["midden_x"] - helft, 0), afmeting - UITSNEDE))
        boven = int(min(max(raster["midden_y"] - helft, 0), afmeting - UITSNEDE))

        uitsnede = doek.crop((links, boven, links + UITSNEDE, boven + UITSNEDE))

        buffer = BytesIO()
        uitsnede.convert("RGB").save(buffer, format="PNG")
        return buffer.getvalue()

    async def async_image(self) -> bytes | None:
        """Bouw het radarbeeld met een kaart eronder.

        RainViewer levert alleen de neerslaglaag. Zonder ondergrond zweven er
        vlekken in het niets en is niet te zien waar de bui hangt.
        """
        frame = self.coordinator.data
        if frame is None:
            return None

        latitude, longitude = self._positie
        zoom = int(self._opt(CONF_RADAR_ZOOM, DEFAULT_RADAR_ZOOM))
        kleur = int(self._opt(CONF_RADAR_KLEUR, DEFAULT_RADAR_KLEUR))
        raster = tegelraster(latitude, longitude, zoom)

        kaarten = await asyncio.gather(
            *(self._haal_tegel(basiskaart_url(t, zoom)) for t in raster["tegels"])
        )
        radars = await asyncio.gather(
            *(
                self._haal_tegel(radartegel_url(frame, t, zoom, kleur))
                for t in raster["tegels"]
            )
        )

        if not any(kaarten) and not any(radars):
            return None

        inslagen = (
            self._storm.recente_inslagen(INSLAG_VENSTER) if self._storm else []
        )

        return await self.hass.async_add_executor_job(
            self._stel_samen, list(kaarten), list(radars), raster, inslagen
        )

    def _handle_coordinator_update(self) -> None:
        """Ververs het beeld wanneer er een nieuw frame is.

        Home Assistant haalt het plaatje pas op als de tijdstempel wijzigt,
        dus die moet mee wanneer de URL verandert.
        """
        # Een nieuw frame of een verschoven positie betekent een nieuw beeld
        frame = self.coordinator.data or {}
        aantal = len(self._storm.recente_inslagen(INSLAG_VENSTER)) if self._storm else 0
        kenmerk = (frame.get("path"), aantal, *(round(w, 3) for w in self._positie))
        if kenmerk != self._vorige_url:
            self._vorige_url = kenmerk
            self._attr_image_last_updated = dt_util.utcnow()

        super()._handle_coordinator_update()

    @property
    def extra_state_attributes(self) -> dict:
        """Wanneer het beeld gemaakt is en waar het op centreert."""
        frame = self.coordinator.data or {}
        gegevens = self._storm.data if self._storm else None
        return {
            "beeld_tijd": frame.get("tijd"),
            "zoom": self._opt(CONF_RADAR_ZOOM, DEFAULT_RADAR_ZOOM),
            "locatie_bron": getattr(gegevens, "location_source", None),
        }
