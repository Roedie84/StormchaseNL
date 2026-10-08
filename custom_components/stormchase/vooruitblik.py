"""Radarvooruitblik: een geanimeerde reeks van een uur terug tot twee uur vooruit.

De beelden komen van de WMS van het KNMI: het actuele composietbeeld voor
het verleden en de radarverwachting (radar_forecast_2.0) voor de komende
twee uur, steeds per tien minuten. Elk frame wordt bewaard; bij een nieuwe
radarronde worden alleen de frames opgehaald die er nog niet zijn.

Hier alleen de planning, de cache en het samenstellen van de GIF; het ophalen
gebeurt in image.py. Bewust zonder Home Assistant erin, zodat het los te
testen is.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from io import BytesIO

# Bovengrens voor de cache: ruim twee volledige reeksen
MAX_FRAMES = 48


def frame_tijden(
    referentie: datetime, terug: int = 60, vooruit: int = 120, stap: int = 10
) -> list[tuple[datetime, bool]]:
    """De tijdstippen van de reeks, met of het een verwachting is.

    Het verleden ligt op een vast raster van `stap` minuten (13:00, 13:10,
    ...), zodat die frames bij de volgende radarronde uit de cache komen. Valt
    de referentietijd daartussen, dan komt hij er als laatste gemeten beeld
    bij. Daarna de verwachting met die referentietijd, per `stap` minuten.
    """
    raster = referentie.replace(
        minute=referentie.minute - referentie.minute % stap, second=0, microsecond=0
    )
    uit: list[tuple[datetime, bool]] = []
    moment = raster - timedelta(minutes=terug)
    while moment <= raster:
        uit.append((moment, False))
        moment += timedelta(minutes=stap)
    if raster != referentie:
        uit.append((referentie, False))
    moment = referentie + timedelta(minutes=stap)
    eind = referentie + timedelta(minutes=vooruit)
    while moment <= eind:
        uit.append((moment, True))
        moment += timedelta(minutes=stap)
    return uit


def framesleutel(
    bbox: str, maat: int, stijl: str, tijd: datetime, referentie: datetime | None
) -> tuple:
    """Sleutel van een frame in de cache.

    Een gemeten beeld hangt niet af van de referentietijd, een verwachting
    wel: de verwachting voor 14:30 van 13:00 is een ander beeld dan die van
    13:05.
    """
    return (bbox, maat, stijl, tijd.isoformat(), referentie.isoformat() if referentie else None)


class FrameCache:
    """Opgehaalde frames, met een bovengrens; de oudste gaan er het eerst uit."""

    def __init__(self, maximum: int = MAX_FRAMES) -> None:
        self._frames: dict[tuple, bytes] = {}
        self._maximum = maximum

    def __contains__(self, sleutel: tuple) -> bool:
        return sleutel in self._frames

    def __len__(self) -> int:
        return len(self._frames)

    def get(self, sleutel: tuple) -> bytes | None:
        return self._frames.get(sleutel)

    def zet(self, sleutel: tuple, inhoud: bytes) -> None:
        self._frames.pop(sleutel, None)
        self._frames[sleutel] = inhoud
        while len(self._frames) > self._maximum:
            self._frames.pop(next(iter(self._frames)))

    def leeg(self) -> None:
        self._frames.clear()


def framelabel(tijd: datetime, referentie: datetime, verschuiving: int) -> str:
    """Tekst op een frame: lokale tijd, en hoeveel minuten voor of na nu."""
    lokaal = tijd + timedelta(seconds=verschuiving)
    minuten = int(round((tijd - referentie).total_seconds() / 60))
    if minuten > 0:
        return f"KNMI-verwachting {lokaal:%H:%M} (+{minuten} min)"
    if minuten < 0:
        return f"KNMI-radar {lokaal:%H:%M} ({minuten} min)"
    return f"KNMI-radar {lokaal:%H:%M} (nu)"


def stel_gif_samen(
    achtergrond,
    frames: list[tuple[str, bytes | None]],
    uitsnede: tuple[int, int, int],
    positie: tuple[float, float],
    duur_ms: int = 400,
) -> bytes | None:
    """Leg elk radarframe over de achtergrond en maak er een GIF van.

    `achtergrond` is een PIL-beeld (RGBA) van het hele raster, `frames` een
    lijst van (label, PNG of None), `uitsnede` (links, boven, maat) en
    `positie` het eigen punt in rastercoordinaten. Een ontbrekend frame
    wordt overgeslagen. Draait in een executor: beeldbewerking blokkeert.
    """
    from PIL import Image, ImageDraw, ImageFont

    links, boven, maat = uitsnede
    try:
        lettertype = ImageFont.load_default(size=14)
    except TypeError:  # oudere Pillow
        lettertype = ImageFont.load_default()

    beelden = []
    for label, inhoud in frames:
        if inhoud is None:
            continue
        try:
            radar = Image.open(BytesIO(inhoud)).convert("RGBA")
        except Exception:  # noqa: BLE001 - beschadigd frame overslaan
            continue
        if radar.size != achtergrond.size:
            radar = radar.resize(achtergrond.size)
        doek = achtergrond.copy()
        doek.paste(radar, (0, 0), radar)

        tekenaar = ImageDraw.Draw(doek, "RGBA")
        px, py = positie
        tekenaar.ellipse((px - 7, py - 7, px + 7, py + 7), outline=(255, 255, 255, 200), width=2)
        tekenaar.ellipse((px - 2, py - 2, px + 2, py + 2), fill=(255, 60, 60, 255))

        stuk = doek.crop((links, boven, links + maat, boven + maat))
        tekenaar = ImageDraw.Draw(stuk, "RGBA")
        vak = tekenaar.textbbox((0, 0), label, font=lettertype)
        hoogte = vak[3] - vak[1]
        tekenaar.rectangle(
            (6, maat - 6 - hoogte - 8, 6 + (vak[2] - vak[0]) + 12, maat - 6),
            fill=(0, 0, 0, 160),
        )
        tekenaar.text((12, maat - 6 - hoogte - 4), label, font=lettertype, fill=(240, 240, 240, 255))
        beelden.append(stuk.convert("RGB"))

    if not beelden:
        return None

    uit = BytesIO()
    beelden[0].save(
        uit,
        format="GIF",
        save_all=True,
        append_images=beelden[1:],
        duration=duur_ms,
        loop=0,
        optimize=False,
        disposal=2,
    )
    return uit.getvalue()
