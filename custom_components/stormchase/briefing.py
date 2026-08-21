"""Het dagelijkse weerbericht.

Stelt een samenvatting samen uit alles wat de integratie al weet: het weer nu,
de verwachting voor vandaag, de neerslag voor de komende twee uur, de
onweersparameters en eventuele officiele waarschuwingen.

Regels die niets toevoegen worden weggelaten. Bij rustig weer blijft er een
kort bericht over; bij onweer wordt het vanzelf uitgebreider.
"""

from __future__ import annotations

import logging
from datetime import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BRIEFING,
    CONF_BRIEFING_AFTERNOON,
    CONF_BRIEFING_MORNING,
    DEFAULT_BRIEFING_AFTERNOON,
    DEFAULT_BRIEFING_MORNING,
    DOMAIN,
    WMO_TEKST,
)

_LOGGER = logging.getLogger(__name__)


def _tijd(waarde: str | None, standaard: str) -> time | None:
    """Zet een HH:MM:SS string om naar een tijd."""
    tekst = waarde or standaard
    try:
        delen = [int(x) for x in str(tekst).split(":")]
        while len(delen) < 3:
            delen.append(0)
        return time(delen[0], delen[1], delen[2])
    except (ValueError, TypeError):
        return None


def _graden(waarde) -> str:
    """Temperatuur met een komma, zoals we hem hier schrijven."""
    if waarde is None:
        return "onbekend"
    return f"{waarde:.0f} \u00b0C" if float(waarde) % 1 == 0 else (
        f"{waarde:.1f} \u00b0C".replace(".", ",")
    )


class Briefing:
    """Stelt het weerbericht samen en verstuurt het op vaste tijden."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiseer het weerbericht."""
        self.hass = hass
        self.entry = entry
        self._unsubs: list[callable] = []

    def _opt(self, key: str, default=None):
        """Haal een optie op, met de config-entry data als fallback."""
        return self.entry.options.get(key, self.entry.data.get(key, default))

    @property
    def _gegevens(self) -> dict:
        """De onderdelen van de integratie."""
        return self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {})

    def start(self) -> None:
        """Plan de berichten in."""
        if not self._opt(CONF_BRIEFING, True):
            return

        momenten = {
            _tijd(self._opt(CONF_BRIEFING_MORNING), DEFAULT_BRIEFING_MORNING),
            _tijd(self._opt(CONF_BRIEFING_AFTERNOON), DEFAULT_BRIEFING_AFTERNOON),
        }

        for moment in momenten:
            if moment is None:
                continue
            self._unsubs.append(
                async_track_time_change(
                    self.hass,
                    self._verstuur,
                    hour=moment.hour,
                    minute=moment.minute,
                    second=0,
                )
            )
            _LOGGER.debug("Weerbericht ingepland om %s", moment.strftime("%H:%M"))

    def stop(self) -> None:
        """Haal de planning weg."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs = []

    @callback
    async def _verstuur(self, _now=None) -> None:
        """Stuur het bericht op het geplande moment."""
        await self.async_send()

    # ---- Opbouw van de tekst ----

    def _regel_nu(self) -> str | None:
        """Het weer op dit moment."""
        meteo = self._gegevens.get("meteo")
        if meteo is None or not meteo.data:
            return None

        huidig = meteo.data.get("current") or {}
        code = huidig.get("weather_code")
        omschrijving = WMO_TEKST.get(int(code)) if code is not None else None

        delen = []
        if omschrijving:
            delen.append(omschrijving.capitalize())

        temp = huidig.get("temperature_2m")
        if temp is not None:
            deel = _graden(temp)
            gevoel = huidig.get("apparent_temperature")
            if gevoel is not None and abs(gevoel - temp) >= 2:
                deel += f", voelt als {_graden(gevoel)}"
            delen.append(deel)

        wind = huidig.get("wind_speed_10m")
        stoten = huidig.get("wind_gusts_10m")
        if wind is not None:
            deel = f"wind {wind:.0f} km/u"
            if stoten and stoten >= wind * 1.5:
                deel += f" met stoten tot {stoten:.0f}"
            delen.append(deel)

        return "Nu: " + ", ".join(delen) + "." if delen else None

    def _regel_vandaag(self) -> str | None:
        """De verwachting voor de rest van de dag."""
        meteo = self._gegevens.get("meteo")
        if meteo is None or not meteo.data:
            return None

        dagelijks = meteo.data.get("daily") or {}

        def eerste(sleutel):
            waarden = dagelijks.get(sleutel) or []
            return waarden[0] if waarden else None

        maximum = eerste("temperature_2m_max")
        minimum = eerste("temperature_2m_min")
        if maximum is None:
            return None

        deel = f"Vandaag {_graden(maximum)}"
        if minimum is not None:
            deel += f", vannacht {_graden(minimum)}"

        kans = eerste("precipitation_probability_max")
        som = eerste("precipitation_sum")
        if kans:
            deel += f", {kans:.0f} procent kans op neerslag"
            if som:
                deel += f" en tot {som:.1f} mm".replace(".", ",")

        code = eerste("weather_code")
        omschrijving = WMO_TEKST.get(int(code)) if code is not None else None
        if omschrijving:
            deel += f", overwegend {omschrijving}"

        return deel + "."

    def _regel_neerslag(self) -> str | None:
        """Wat er de komende twee uur valt."""
        regen = self._gegevens.get("rain")
        if regen is None or not regen.data:
            return None

        data = regen.data
        if data.get("regent"):
            deel = f"Het regent, {data['intensiteit']:.1f} mm/u".replace(".", ",")
            if data.get("stopt_over"):
                deel += f", nog ongeveer {data['stopt_over']} minuten"
            return deel + "."

        begint = data.get("begint_over")
        if begint is not None:
            deel = f"Regen over ongeveer {begint} minuten"
            piek = data.get("piek")
            if piek:
                deel += f", piek {piek:.1f} mm/u".replace(".", ",")
            return deel + "."

        return "Komende twee uur geen neerslag verwacht."

    def _regel_onweer(self) -> str | None:
        """Onweer in de buurt, of de kans erop."""
        storm = self._gegevens.get("storm")
        meteo = self._gegevens.get("meteo")

        if storm is not None and storm.data and storm.data.distance is not None:
            deel = f"Onweer op {storm.data.distance:.0f} km"
            if storm.data.trend and storm.data.trend != "onbekend":
                deel += f", {storm.data.trend}"
            if storm.data.eta:
                deel += f", hier over {storm.data.eta} minuten"
            return deel + "."

        if meteo is not None and meteo.data:
            potentie = meteo.data.get("cape_peak")
            rotatie = meteo.data.get("rotatiekans") or 0
            hagel = meteo.data.get("hagelkans") or 0

            if rotatie > 20 or hagel > 20:
                return (
                    f"Zwaar weer mogelijk: rotatiekans {rotatie} procent, "
                    f"hagelkans {hagel} procent."
                )
            if potentie and potentie > 500:
                return f"Onweerskans aanwezig, CAPE loopt op tot {potentie:.0f} J/kg."

        return None

    def _regel_waarschuwing(self) -> str | None:
        """Officiele waarschuwingen voor je omgeving."""
        alerts = self._gegevens.get("alerts")
        if alerts is None or not alerts.data:
            return None

        aantal = alerts.data.get("aantal") or 0
        if not aantal:
            return None

        niveau = alerts.data.get("niveau")
        soort = alerts.data.get("soort")
        gebied = alerts.data.get("gebied")

        deel = f"Waarschuwing code {niveau}"
        if soort:
            deel += f" voor {soort}"
        if gebied:
            deel += f" in {gebied}"
        if aantal > 1:
            deel += f", en nog {aantal - 1} andere"
        return deel + "."

    def _regel_locatie(self) -> str | None:
        """Waar dit over gaat, als dat niet je thuisadres is."""
        storm = self._gegevens.get("storm")
        if storm is None or not storm.data:
            return None

        if storm.data.location_source == "thuis":
            return None

        return storm.data.adres or None

    def stel_samen(self) -> str:
        """Zet alle regels achter elkaar."""
        regels = [
            self._regel_waarschuwing(),
            self._regel_nu(),
            self._regel_vandaag(),
            self._regel_neerslag(),
            self._regel_onweer(),
        ]

        tekst = "\n".join(r for r in regels if r)

        plek = self._regel_locatie()
        if plek:
            tekst += f"\n\nLocatie: {plek}"

        return tekst or "Geen weergegevens beschikbaar."

    async def async_send(self) -> None:
        """Stel het bericht samen en verstuur het."""
        notifier = self._gegevens.get("notifier")
        if notifier is None or not notifier.diensten:
            _LOGGER.debug("Geen meldingsdienst voor het weerbericht")
            return

        uur = dt_util.now().hour
        if uur < 12:
            titel = "Weerbericht vanmorgen"
        elif uur < 18:
            titel = "Weerbericht vanmiddag"
        else:
            titel = "Weerbericht vanavond"

        # Het weerbericht gaat langs de wachttijd en de stilstandcontrole:
        # je hebt er zelf om gevraagd op een vast tijdstip.
        await notifier.stuur_direct(self.stel_samen(), "briefing", titel)
