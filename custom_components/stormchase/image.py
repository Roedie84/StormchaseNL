"""Radarbeeld dat je eigen positie volgt.

Een gewone entiteit in plaats van een ingesloten webpagina: geen
cookiemelding, geen advertenties, en het beeld schuift mee met de locatie die
de integratie gebruikt.
"""

from __future__ import annotations

import asyncio
import logging
import math
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
    CONF_DWD_LAAG,
    CONF_RADARBRON,
    CONF_WOLKEN,
    CONF_WOLKEN_LAAG,
    DEFAULT_DWD_LAAG,
    DEFAULT_RADARBRON,
    DEFAULT_WOLKEN_LAAG,
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
    beeldlabel,
    radartegel_url,
    rastergrenzen,
    tegelraster,
)
from .const import DWD_WMS_URL
from .wolken import (
    UITSNIJDING,
    VERVAGING,
    alfa_van_helderheid,
    mercatorrij,
    wms_url,
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
    # Het beeld wordt als PNG samengesteld. Zonder dit kondigt Home Assistant
    # het als JPEG aan, wat browsers weigeren te tonen.
    _attr_content_type = "image/png"

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
        # Meteen een tijdstempel, anders weet Home Assistant niet dat er een
        # beeld is en blijft het vak leeg tot de eerste verversingsronde.
        self._attr_image_last_updated = dt_util.utcnow()

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
            doorzicht = int(255 - deel * 120)
            groen = int(255 - deel * 130)
            straal = 6 if deel < 0.2 else 5

            px, py = positie

            # Een donkere rand eromheen, anders verdwijnt een oranje stip in
            # het geel en rood van de radar eronder.
            tekenaar.ellipse(
                (px - straal - 2, py - straal - 2, px + straal + 2, py + straal + 2),
                fill=(20, 10, 40, min(doorzicht, 180)),
            )
            tekenaar.ellipse(
                (px - straal, py - straal, px + straal, py + straal),
                fill=(255, groen, 60, doorzicht),
            )
            # Witte kern: die blijft op elke ondergrond zichtbaar
            tekenaar.ellipse(
                (px - 2, py - 2, px + 2, py + 2),
                fill=(255, 255, 255, doorzicht),
            )

    # Kleur per activiteit, zoals op professionele stormkaarten
    KLEUREN = {
        "geel": (255, 214, 60),
        "oranje": (255, 149, 40),
        "rood": (255, 71, 51),
    }

    @classmethod
    def _plak_wolken(cls, doek, inhoud: bytes, raster: dict) -> None:
        """Leg de bewolking over de kaart, in grijstinten.

        De afgeleide producten komen met hun eigen palet, dat over een kaart
        heen onleesbaar wordt. Daarom wordt het beeld zelf omgezet naar grijs
        en licht vervaagd: donker is helder, licht is bewolkt, met vloeiende
        overgangen zoals op elke weerkaart.
        """
        from PIL import Image, ImageFilter, ImageOps

        recht = cls._herprojecteer(inhoud, raster)
        if recht is None:
            return

        grijs = recht.convert("L")

        # Uitrekken over het volledige bereik. Zonder dit zou een vaste
        # drempel 's nachts vrijwel alle bewolking wegsnijden, omdat de
        # gemeten waarden dan veel dichter bij elkaar liggen.
        grijs = ImageOps.autocontrast(grijs, cutoff=UITSNIJDING)
        grijs = grijs.filter(ImageFilter.GaussianBlur(VERVAGING))
        doorzicht = grijs.point(alfa_van_helderheid)

        wolk = Image.merge("RGBA", (grijs, grijs, grijs, doorzicht))
        doek.paste(wolk, (0, 0), wolk)

    @staticmethod
    def _herprojecteer(inhoud: bytes, raster: dict):
        """Zet een beeld van een kaartdienst om naar webmercator.
        Zulke diensten leveren een plat beeld op breedtegraad, terwijl het
        radarbeeld in webmercator staat. Zonder omrekening zou alles
        tientallen kilometers verkeerd komen te liggen; hier wordt het beeld
        rij voor rij opnieuw opgebouwd.
        """
        from PIL import Image

        try:
            bron = Image.open(BytesIO(inhoud)).convert("RGBA")
        except Exception as err:  # noqa: BLE001 - laag mag ontbreken
            _LOGGER.debug("Beeld van de kaartdienst onbruikbaar: %s", err)
            return None

        afmeting = raster["afmeting"]
        if bron.size != (afmeting, afmeting):
            bron = bron.resize((afmeting, afmeting))

        zuid, _, noord, _ = rastergrenzen(raster)
        recht = Image.new("RGBA", (afmeting, afmeting), (0, 0, 0, 0))

        for rij in range(afmeting):
            bronrij = int(round(mercatorrij(rij, afmeting, zuid, noord)))
            bronrij = min(max(bronrij, 0), afmeting - 1)
            recht.paste(bron.crop((0, bronrij, afmeting, bronrij + 1)), (0, rij))

        return recht

    @classmethod
    def _plak_gebiedsbeeld(cls, doek, inhoud: bytes, raster: dict) -> None:
        """Leg een beeld van een kaartdienst ongewijzigd over het doek."""
        recht = cls._herprojecteer(inhoud, raster)
        if recht is not None:
            doek.paste(recht, (0, 0), recht)

    @classmethod
    def _teken_cellen(cls, doek, raster: dict, cellen: list) -> None:
        """Teken elke cel met zijn koers en verwachte posities.

        De ring geeft aan waar de bui zit en hoe actief hij is; de streepjes
        op de lijn zijn de posities per kwartier vooruit. Zo zie je in een
        oogopslag welke cel je kant op komt en wanneer.
        """
        for cel in cellen or []:
            cls._teken_cel(doek, raster, cel)

    @classmethod
    def _teken_cel(cls, doek, raster: dict, cel: dict | None) -> None:
        """Teken een enkele cel."""
        if not cel or cel.get("latitude") is None:
            return

        from PIL import ImageDraw

        from .radar import naar_pixels_per_uur

        tekenaar = ImageDraw.Draw(doek, "RGBA")
        kleur = cls.KLEUREN.get(cel.get("intensiteit", "geel"), cls.KLEUREN["geel"])

        midden = pixelpositie(cel["latitude"], cel["longitude"], raster)
        if midden is None:
            return

        # Het afgelegde spoor, gedempt zodat het niet met de koers concurreert
        punten = []
        for lat, lon in cel.get("spoor") or []:
            positie = pixelpositie(lat, lon, raster)
            if positie is not None:
                punten.append(positie)

        if len(punten) >= 2:
            tekenaar.line(punten, fill=(*kleur, 90), width=2)

        # De ring om de cel, groter naarmate er meer inslagen in zitten
        straal = 8 + min(cel.get("inslagen", 0), 40) / 4
        tekenaar.ellipse(
            (
                midden[0] - straal,
                midden[1] - straal,
                midden[0] + straal,
                midden[1] + straal,
            ),
            outline=(*kleur, 235),
            width=2,
        )

        richting = cel.get("richting_graden")
        snelheid = cel.get("snelheid")
        if richting is None or not snelheid:
            return

        # De koers vooruit, met een streepje per kwartier
        per_uur = naar_pixels_per_uur(snelheid, raster)
        hoek = math.radians(richting)

        eind = (
            midden[0] + math.sin(hoek) * per_uur,
            midden[1] - math.cos(hoek) * per_uur,
        )
        tekenaar.line([midden, eind], fill=(*kleur, 200), width=2)

        for kwartier in (1, 2, 3, 4):
            afstand = per_uur * kwartier / 4
            punt = (
                midden[0] + math.sin(hoek) * afstand,
                midden[1] - math.cos(hoek) * afstand,
            )
            dwars = hoek + math.pi / 2
            tekenaar.line(
                [
                    (punt[0] - math.sin(dwars) * 5, punt[1] + math.cos(dwars) * 5),
                    (punt[0] + math.sin(dwars) * 5, punt[1] - math.cos(dwars) * 5),
                ],
                fill=(*kleur, 200),
                width=2,
            )

    @staticmethod
    def _teken_label(doek, tekst: str) -> None:
        """Zet linksonder wanneer het beeld gemaakt is.

        Zonder dat weet je niet of je naar iets van net kijkt of naar een
        beeld dat al een kwartier oud is omdat de bron hapert.
        """
        from PIL import ImageDraw, ImageFont

        tekenaar = ImageDraw.Draw(doek, "RGBA")

        try:
            lettertype = ImageFont.load_default(size=14)
        except TypeError:
            # Oudere Pillow kent de maat nog niet
            lettertype = ImageFont.load_default()

        breedte, hoogte = doek.size
        vak = tekenaar.textbbox((0, 0), tekst, font=lettertype)
        rand = 6

        tekenaar.rectangle(
            (
                rand,
                hoogte - rand - (vak[3] - vak[1]) - 8,
                rand + (vak[2] - vak[0]) + 12,
                hoogte - rand,
            ),
            fill=(0, 0, 0, 150),
        )
        tekenaar.text(
            (rand + 6, hoogte - rand - (vak[3] - vak[1]) - 4),
            tekst,
            font=lettertype,
            fill=(235, 235, 235, 255),
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
        self,
        kaarten: list,
        wolken: bytes | None,
        radars: list,
        dwd_beeld: bytes | None,
        raster: dict,
        inslagen: list,
        cel: list | None,
        label: str,
    ) -> bytes:
        """Leg de radar over de kaart en snijd rond het middelpunt uit.

        Draait in een aparte draad, want beeldbewerking blokkeert anders de
        rest van Home Assistant.
        """
        from PIL import Image, ImageEnhance

        afmeting = raster["afmeting"]
        doek = Image.new("RGBA", (afmeting, afmeting), (18, 18, 22, 255))

        def plak(laag, sterkte: float = 1.0):
            """Leg een set tegels op het doek; een missende tegel is geen ramp.

            Met een sterkte onder een wordt de laag doorzichtiger gemaakt, wat
            nodig is voor de wolken: die bedekken anders de hele kaart.
            """
            for tegel, inhoud in zip(raster["tegels"], laag):
                if inhoud is None:
                    continue
                try:
                    beeld = Image.open(BytesIO(inhoud)).convert("RGBA")
                except Exception:  # noqa: BLE001 - beschadigde tegel overslaan
                    continue

                if sterkte < 1.0:
                    doorzicht = beeld.getchannel("A").point(
                        lambda waarde: int(waarde * sterkte)
                    )
                    beeld.putalpha(doorzicht)

                doek.paste(beeld, (tegel["plak_x"], tegel["plak_y"]), beeld)

        # Eerst de kaart, die daarna gedempt wordt. De radar gaat er pas
        # overheen, anders zou die mee verduisteren en onzichtbaar worden.
        plak(kaarten)
        doek = ImageEnhance.Brightness(doek.convert("RGB")).enhance(
            KAART_HELDERHEID
        )
        doek = ImageEnhance.Color(doek).enhance(KAART_KLEUR).convert("RGBA")

        # Wolken tussen kaart en radar: ze laten zien waar bewolking zit,
        # ook waar nog geen neerslag valt.
        if wolken is not None:
            self._plak_wolken(doek, wolken, raster)
        if dwd_beeld is not None:
            self._plak_gebiedsbeeld(doek, dwd_beeld, raster)
        else:
            plak(radars)

        # Cel, inslagen en de eigen positie gaan als laatste over alles heen
        self._teken_cellen(doek, raster, cel)
        self._teken_inslagen(doek, raster, inslagen)
        self._teken_positie(doek, raster)

        # Uitsnijden rond de gevraagde positie, binnen de randen blijven
        helft = UITSNEDE // 2
        links = int(min(max(raster["midden_x"] - helft, 0), afmeting - UITSNEDE))
        boven = int(min(max(raster["midden_y"] - helft, 0), afmeting - UITSNEDE))

        uitsnede = doek.crop((links, boven, links + UITSNEDE, boven + UITSNEDE))
        self._teken_label(uitsnede, label)

        buffer = BytesIO()
        uitsnede.convert("RGB").save(buffer, format="PNG")
        return buffer.getvalue()

    async def async_image(self) -> bytes | None:
        """Bouw het radarbeeld met een kaart eronder.

        RainViewer levert alleen de neerslaglaag. Zonder ondergrond zweven er
        vlekken in het niets en is niet te zien waar de bui hangt.
        """
        gegevens = self.coordinator.data or {}
        frame = gegevens.get("radar")
        if frame is None:
            return None

        latitude, longitude = self._positie
        zoom = int(self._opt(CONF_RADAR_ZOOM, DEFAULT_RADAR_ZOOM))
        kleur = int(self._opt(CONF_RADAR_KLEUR, DEFAULT_RADAR_KLEUR))
        raster = tegelraster(latitude, longitude, zoom)

        kaarten = await asyncio.gather(
            *(self._haal_tegel(basiskaart_url(t, zoom)) for t in raster["tegels"])
        )
        wolken = None
        if self._opt(CONF_WOLKEN, True):
            wolken = await self._haal_tegel(
                wms_url(
                    rastergrenzen(raster),
                    raster["afmeting"],
                    raster["afmeting"],
                    self._opt(CONF_WOLKEN_LAAG, DEFAULT_WOLKEN_LAAG),
                )
            )
        # Twee wegen naar hetzelfde beeld: tegels van RainViewer, of een
        # gebiedsverzoek bij de Duitse weerdienst. Die laatste is actueler
        # maar houdt op bij de grens en omgeving.
        via_dwd = self._opt(CONF_RADARBRON, DEFAULT_RADARBRON) == "dwd"

        radars: list = []
        dwd_beeld = None

        if via_dwd:
            dwd_beeld = await self._haal_tegel(
                wms_url(
                    rastergrenzen(raster),
                    raster["afmeting"],
                    raster["afmeting"],
                    self._opt(CONF_DWD_LAAG, DEFAULT_DWD_LAAG),
                    DWD_WMS_URL,
                )
            )

        if dwd_beeld is None:
            radars = list(
                await asyncio.gather(
                    *(
                        self._haal_tegel(radartegel_url(frame, t, zoom, kleur))
                        for t in raster["tegels"]
                    )
                )
            )

        if not any(kaarten) and not any(radars) and dwd_beeld is None:
            return None

        inslagen = (
            self._storm.recente_inslagen(INSLAG_VENSTER) if self._storm else []
        )
        cellen = getattr(self._storm.data, "cellen", None) if self._storm else None

        return await self.hass.async_add_executor_job(
            self._stel_samen,
            list(kaarten),
            wolken,
            list(radars),
            dwd_beeld,
            raster,
            inslagen,
            cellen,
            beeldlabel(
                frame.get("tijd"),
                dt_util.utcnow().timestamp(),
                int(dt_util.now().utcoffset().total_seconds()),
            ),
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
        frame = (self.coordinator.data or {}).get("radar") or {}
        gegevens = self._storm.data if self._storm else None
        tijd = frame.get("tijd")
        return {
            "beeld_tijd": tijd,
            "beeld_leeftijd_minuten": (
                max(int((dt_util.utcnow().timestamp() - tijd) // 60), 0)
                if tijd
                else None
            ),
            "zoom": self._opt(CONF_RADAR_ZOOM, DEFAULT_RADAR_ZOOM),
            "locatie_bron": getattr(gegevens, "location_source", None),
        }
