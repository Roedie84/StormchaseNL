"""Meldingen versturen op basis van de Stormchase-events."""

from __future__ import annotations

import logging
from datetime import datetime, time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import (
    CONF_NOTIFY_COOLDOWN,
    CONF_ALERT_NOTIFY,
    CONF_ONLY_STATIONARY,
    CONF_RAIN_NOTIFY,
    CONF_WIND_NOTIFY,
    CONF_NOTIFY_MAX_DISTANCE,
    CONF_NOTIFY_ON_APPROACH,
    CONF_NOTIFY_ON_CLEARED,
    CONF_NOTIFY_SERVICES,
    CONF_NOTIFY_TITLE,
    CONF_QUIET_FROM,
    CONF_QUIET_TO,
    DATA_NOTIFY_ENABLED,
    DEFAULT_NOTIFY_COOLDOWN,
    DEFAULT_NOTIFY_MAX_DISTANCE,
    DEFAULT_NOTIFY_TITLE,
    DEFAULT_QUIET,
    DOMAIN,
    EVENT_APPROACHING,
    EVENT_CLEARED,
    EVENT_NEARBY,
    EVENT_ALERT,
    EVENT_RAIN_INCOMING,
    EVENT_WIND,
    RICHTINGEN,
)

_LOGGER = logging.getLogger(__name__)


def _parse_tijd(waarde: str | None) -> time | None:
    """Zet een HH:MM:SS string om naar een tijd."""
    if not waarde:
        return None
    try:
        deel = [int(x) for x in str(waarde).split(":")]
        while len(deel) < 3:
            deel.append(0)
        return time(deel[0], deel[1], deel[2])
    except (ValueError, TypeError):
        return None


class StormNotifier:
    """Luistert naar de events en stuurt er meldingen over.

    Zit in de integratie in plaats van in een losse automatisering, zodat je
    na het instellen niets meer hoeft te doen. De aan/uit-schakelaar en de
    instellingen zitten bij de integratie zelf.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiseer de notifier."""
        self.hass = hass
        self.entry = entry
        # Onweer en regen hebben elk hun eigen wachttijd, anders zou een
        # regenmelding een onweerswaarschuwing kunnen tegenhouden.
        self._laatste: datetime | None = None
        self._laatste_regen: datetime | None = None
        self.stats = None  # wordt na het aanmaken gezet
        self.storm = None  # coordinator, voor de stilstandcontrole
        self._laatste_wind: datetime | None = None
        self._unsubs: list[callable] = []

    def _opt(self, key: str, default=None):
        """Haal een optie op, met de config-entry data als fallback."""
        return self.entry.options.get(key, self.entry.data.get(key, default))

    @property
    def diensten(self) -> list[str]:
        """De ingestelde notify-diensten."""
        waarde = self._opt(CONF_NOTIFY_SERVICES) or []
        if isinstance(waarde, str):
            return [waarde]
        return list(waarde)

    @property
    def ingeschakeld(self) -> bool:
        """Staat de schakelaar aan?"""
        gegevens = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {})
        return gegevens.get(DATA_NOTIFY_ENABLED, True)

    def start(self) -> None:
        """Begin met luisteren naar de events."""
        self._unsubs = [
            self.hass.bus.async_listen(EVENT_NEARBY, self._handle_nearby),
            self.hass.bus.async_listen(EVENT_APPROACHING, self._handle_approaching),
            self.hass.bus.async_listen(EVENT_CLEARED, self._handle_cleared),
            self.hass.bus.async_listen(EVENT_RAIN_INCOMING, self._handle_rain),
            self.hass.bus.async_listen(EVENT_ALERT, self._handle_alert),
            self.hass.bus.async_listen(EVENT_WIND, self._handle_wind),
        ]

    def stop(self) -> None:
        """Stop met luisteren."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs = []

    def _ter_plaatse(self) -> bool:
        """Sta je lang genoeg op deze plek om een melding zinvol te maken?

        Tijdens het rijden verandert het weer ter plaatse elke paar minuten,
        en dan is een bericht over regen hier alweer achterhaald voor je het
        leest. Onweer en officiele waarschuwingen gaan hier bewust langs: die
        wil je ook onderweg weten.
        """
        if not self._opt(CONF_ONLY_STATIONARY, True):
            return True

        if self.storm is None or self.storm.data is None:
            return True

        onderweg = self.storm.data.onderweg
        # Nog te weinig gegevens om iets te zeggen: dan maar wel melden.
        if onderweg is None:
            return True

        if onderweg:
            _LOGGER.debug("Melding onderdrukt: onderweg")
        return not onderweg

    def _in_stiltevenster(self) -> bool:
        """Valt dit moment binnen het ingestelde stiltevenster?"""
        van = _parse_tijd(self._opt(CONF_QUIET_FROM, DEFAULT_QUIET))
        tot = _parse_tijd(self._opt(CONF_QUIET_TO, DEFAULT_QUIET))

        # Gelijke tijden betekent: geen stiltevenster.
        if van is None or tot is None or van == tot:
            return False

        nu = dt_util.now().time()
        if van < tot:
            return van <= nu < tot
        # Venster loopt over middernacht heen
        return nu >= van or nu < tot

    def _te_snel(self) -> bool:
        """Is de wachttijd sinds de vorige melding nog niet verstreken?"""
        wacht = int(self._opt(CONF_NOTIFY_COOLDOWN, DEFAULT_NOTIFY_COOLDOWN))
        if wacht <= 0 or self._laatste is None:
            return False
        verstreken = (dt_util.utcnow() - self._laatste).total_seconds()
        return verstreken < wacht * 60

    def _mag_melden(self, afstand: float | None) -> bool:
        """Alle voorwaarden op een rij."""
        if not self.ingeschakeld or not self.diensten:
            return False

        maximum = float(
            self._opt(CONF_NOTIFY_MAX_DISTANCE, DEFAULT_NOTIFY_MAX_DISTANCE)
        )
        if afstand is None or afstand > maximum:
            return False

        if self._in_stiltevenster():
            _LOGGER.debug("Melding onderdrukt: stiltevenster actief")
            return False

        if self._te_snel():
            _LOGGER.debug("Melding onderdrukt: wachttijd nog niet verstreken")
            return False

        return True

    @staticmethod
    def _richting(azimut: float | None) -> str | None:
        """Zet een azimut om naar een windrichting voluit."""
        if azimut is None:
            return None
        return RICHTINGEN[int(round(azimut / 22.5)) % 16]

    def _bericht(self, data: dict, soort: str) -> str:
        """Stel de meldingstekst samen."""
        afstand = data.get("afstand")
        afstand_tekst = f"{afstand:.1f} km".replace(".", ",") if afstand else "onbekend"

        if soort == "cleared":
            return f"Het onweer is weggetrokken, laatste inslag op {afstand_tekst}."

        # Richting hoort zonder komma aan de afstand vast, de trend juist
        # met een komma ervoor. Anders leest het als een opsomming.
        tekst = f"Blikseminslag op {afstand_tekst}"

        richting = self._richting(data.get("azimut"))
        if richting:
            tekst += f" in het {richting}"

        trend = data.get("trend")
        if trend and trend != "onbekend":
            tekst += f", {trend}"

        eta = data.get("aankomst_minuten")
        if eta:
            tekst += f", hier over ongeveer {int(eta)} minuten"

        return tekst + "."

    async def _stuur(
        self, bericht: str, soort: str = "nearby", titel: str | None = None
    ) -> None:
        """Verstuur naar alle ingestelde diensten."""
        if titel is None:
            titel = self._opt(CONF_NOTIFY_TITLE, DEFAULT_NOTIFY_TITLE)

        for dienst in self.diensten:
            # De gebruiker kiest 'mobile_app_telefoon', wij bellen
            # notify.mobile_app_telefoon aan.
            domein, _, naam = dienst.partition(".")
            if not naam:
                domein, naam = "notify", dienst

            try:
                await self.hass.services.async_call(
                    domein,
                    naam,
                    {
                        "title": f"\u26a1 {titel}",
                        "message": bericht,
                        "data": {
                            "tag": f"{DOMAIN}_{soort}",
                            "channel": "Onweer",
                            "importance": "high",
                            "notification_icon": "mdi:flash-alert",
                        },
                    },
                    blocking=False,
                )
            except Exception as err:  # noqa: BLE001 - dienst kan verdwenen zijn
                _LOGGER.warning("Melding via %s mislukt: %s", dienst, err)
                if self.stats is not None:
                    self.stats.meldingen_mislukt += 1
                continue

            if self.stats is not None:
                self.stats.noteer_melding(soort)

        if soort not in ("rain", "wind"):
            self._laatste = dt_util.utcnow()

    @callback
    async def _handle_nearby(self, event: Event) -> None:
        """Onweer is binnen de waarschuwingsafstand gekomen."""
        if self._mag_melden(event.data.get("afstand")):
            await self._stuur(self._bericht(event.data, "nearby"), "nearby")

    @callback
    async def _handle_approaching(self, event: Event) -> None:
        """Onweer komt structureel dichterbij."""
        if not self._opt(CONF_NOTIFY_ON_APPROACH, True):
            return
        if self._mag_melden(event.data.get("afstand")):
            await self._stuur(self._bericht(event.data, "approaching"), "approaching")

    @callback
    async def _handle_cleared(self, event: Event) -> None:
        """Onweer is weggetrokken."""
        if not self._opt(CONF_NOTIFY_ON_CLEARED, False):
            return
        # Voor het sein-veilig bericht negeren we de maximale afstand; het
        # onweer is per definitie verder weg dan de drempel.
        if not self.ingeschakeld or not self.diensten or self._in_stiltevenster():
            return
        await self._stuur(self._bericht(event.data, "cleared"), "cleared")

    @callback
    async def _handle_rain(self, event: Event) -> None:
        """Er komt regen aan."""
        if not self._opt(CONF_RAIN_NOTIFY, True):
            return
        if not self.ingeschakeld or not self.diensten:
            return
        if self._in_stiltevenster() or not self._ter_plaatse():
            return

        wacht = int(self._opt(CONF_NOTIFY_COOLDOWN, DEFAULT_NOTIFY_COOLDOWN))
        if wacht > 0 and self._laatste_regen is not None:
            verstreken = (dt_util.utcnow() - self._laatste_regen).total_seconds()
            if verstreken < wacht * 60:
                return

        minuten = event.data.get("over_minuten")
        piek = event.data.get("intensiteit") or 0

        if piek >= 5:
            zwaarte = "flinke bui"
        elif piek >= 1:
            zwaarte = "regen"
        else:
            zwaarte = "lichte regen"

        bericht = f"Over ongeveer {minuten} minuten {zwaarte}"
        if piek:
            bericht += f", tot {piek:.1f} mm/u".replace(".", ",")
        bericht += "."

        await self._stuur(bericht, "rain", titel="Regen op komst")
        self._laatste_regen = dt_util.utcnow()

    @callback
    async def _handle_alert(self, event: Event) -> None:
        """Officiele weerwaarschuwing van kracht.

        Geen wachttijd en geen stiltevenster: dit komt van een nationale
        weerdienst en gaat over gevaar. Elke waarschuwing wordt maar een keer
        gemeld, dus herhaling is geen risico.
        """
        if not self._opt(CONF_ALERT_NOTIFY, True):
            return
        if not self.ingeschakeld or not self.diensten:
            return

        niveau = event.data.get("niveau", "")
        soort = event.data.get("soort") or "weerwaarschuwing"
        gebied = event.data.get("gebied")
        tot = event.data.get("tot")

        bericht = f"{soort}"
        if gebied:
            bericht += f" voor {gebied}"
        if tot:
            moment = dt_util.parse_datetime(tot)
            if moment is not None:
                lokaal = dt_util.as_local(moment)
                bericht += f", tot {lokaal.strftime('%H:%M')}"
        bericht += "."

        await self._stuur(bericht, "alert", titel=f"Code {niveau}")

    @callback
    async def _handle_wind(self, event: Event) -> None:
        """Harde windstoten op de huidige locatie."""
        if not self._opt(CONF_WIND_NOTIFY, True):
            return
        if not self.ingeschakeld or not self.diensten:
            return
        if self._in_stiltevenster() or not self._ter_plaatse():
            return

        wacht = int(self._opt(CONF_NOTIFY_COOLDOWN, DEFAULT_NOTIFY_COOLDOWN))
        if wacht > 0 and self._laatste_wind is not None:
            verstreken = (dt_util.utcnow() - self._laatste_wind).total_seconds()
            if verstreken < wacht * 60:
                return

        stoten = event.data.get("windstoten") or 0

        if stoten >= 100:
            zwaarte = "zware windstoten"
        elif stoten >= 75:
            zwaarte = "krachtige windstoten"
        else:
            zwaarte = "harde windstoten"

        bericht = f"{zwaarte.capitalize()} tot {stoten:.0f} km/u op je locatie."

        await self._stuur(bericht, "wind", titel="Harde wind")
        self._laatste_wind = dt_util.utcnow()

    async def async_test(self) -> None:
        """Stuur een proefmelding, ongeacht drempels en wachttijden."""
        if not self.diensten:
            _LOGGER.warning("Geen meldingsdienst ingesteld")
            return
        await self._stuur(
            "Dit is een proefmelding van Stormchase. Ziet dit er goed uit, "
            "dan komen echte waarschuwingen ook aan.",
            "test",
        )
