"""Meldingen versturen op basis van de Stormchase-events."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .taal import hoofdletter

from .const import (
    CONF_NOTIFY_COOLDOWN,
    CONF_ALERT_NOTIFY,
    CONF_CRITICAL,
    CONF_DASHBOARD,
    CRITICAL_SOORTEN,
    WACHT_OP_DIENST,
    DEFAULT_DASHBOARD,
    CONF_ONLY_STATIONARY,
    CONF_OUTLOOK_NOTIFY,
    CONF_RAIN_NOTIFY,
    CONF_WEATHER_TYPES,
    DEFAULT_WEATHER_TYPES,
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
    EVENT_SHELTER,
    EVENT_OUTLOOK,
    EVENT_WEATHER,
    EVENT_WIND,
    ONDERWEG_RELEVANT,
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
        # Elke weersituatie houdt zijn eigen wachttijd bij, zodat sneeuw geen
        # vorstmelding kan tegenhouden.
        self._laatste_weer: dict[str, datetime] = {}
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
            self.hass.bus.async_listen(EVENT_WEATHER, self._handle_weather),
            self.hass.bus.async_listen(EVENT_OUTLOOK, self._handle_outlook),
            self.hass.bus.async_listen(EVENT_SHELTER, self._handle_shelter),
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

        tekst += "."

        # Wat de cel als geheel doet zegt meer dan de losse inslag
        cel = data.get("cel") or {}
        if cel.get("richting") and cel.get("snelheid"):
            deel = f" Cel trekt naar het {cel['richting']} met {cel['snelheid']:.0f} km/u"
            if cel.get("passage_over") is not None:
                deel += (
                    f" en passeert over {cel['passage_over']} minuten op "
                    f"{cel['passage_afstand']:.0f} km"
                )
            tekst += deel + "."

        frequentie = data.get("frequentie")
        if frequentie and frequentie >= 1:
            tekst += f" {frequentie:.0f} inslagen per minuut.".replace(".0 ", " ")

        return tekst

    async def _wacht_op_dienst(self, domein: str, naam: str) -> bool:
        """Wacht tot een meldingsdienst bestaat.

        De diensten van de companion-app worden door Home Assistant pas
        aangemaakt nadat die integratie geladen is, en dat kan later zijn dan
        wij. Meteen opgeven zou betekenen dat je de eerste melding na een
        herstart misloopt, precies wanneer je die het hardst nodig hebt.
        """
        if self.hass.services.has_service(domein, naam):
            return True

        for _ in range(int(WACHT_OP_DIENST / 2)):
            await asyncio.sleep(2)
            if self.hass.services.has_service(domein, naam):
                _LOGGER.debug("Dienst %s.%s is er nu", domein, naam)
                return True

        return False

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

            if not await self._wacht_op_dienst(domein, naam):
                _LOGGER.warning(
                    "Meldingsdienst %s.%s bestaat niet; melding niet verstuurd",
                    domein,
                    naam,
                )
                if self.stats is not None:
                    self.stats.meldingen_mislukt += 1
                continue

            try:
                await self.hass.services.async_call(
                    domein,
                    naam,
                    {
                        "title": f"\u26a1 {titel}",
                        "message": bericht,
                        "data": self._extras(soort),
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

        # Alleen onweersmeldingen delen de hoofdteller; regen, wind en de
        # weersituaties hebben hun eigen wachttijd.
        if soort in ("nearby", "approaching", "cleared"):
            self._laatste = dt_util.utcnow()

    def _extras(self, soort: str) -> dict:
        """De extra velden bij een melding.

        Een knop naar het dashboard scheelt zoeken op het moment dat het ertoe
        doet. Bij gevaar mag de melding door de stille modus heen, mits je dat
        hebt aangezet: dat werkt alleen als je de app daar toestemming voor
        hebt gegeven.
        """
        pad = self._opt(CONF_DASHBOARD, DEFAULT_DASHBOARD)

        extras: dict = {
            "tag": f"{DOMAIN}_{soort}",
            "channel": "Onweer",
            "importance": "high",
            "notification_icon": "mdi:flash-alert",
            "actions": [
                {"action": "URI", "title": "Bekijk kaart", "uri": pad},
            ],
        }

        dringend = self._opt(CONF_CRITICAL, False) and soort in CRITICAL_SOORTEN
        if dringend:
            # iOS wil een critical-vlag met volume, Android een eigen kanaal
            extras["push"] = {
                "interruption-level": "critical",
                "sound": {"name": "default", "critical": 1, "volume": 1.0},
            }
            extras["channel"] = "Onweer dringend"
            extras["importance"] = "max"
            extras["ttl"] = 0
            extras["priority"] = "high"

        return extras

    @callback
    async def _handle_shelter(self, event: Event) -> None:
        """De 30/30-regel gaat in of loopt af."""
        if not self.ingeschakeld or not self.diensten:
            return

        if event.data.get("schuilen"):
            afstand = event.data.get("afstand")
            bericht = "Onweer binnen tien kilometer. Ga naar binnen."
            if afstand:
                bericht = (
                    f"Onweer op {afstand:.1f} km. Ga naar binnen en blijf "
                    "binnen tot dertig minuten na de laatste inslag."
                ).replace(".", ",", 1)
            await self._stuur(bericht, "shelter", titel="Schuilen")
        else:
            await self._stuur(
                "Dertig minuten geen onweer meer in de buurt. Het is weer "
                "veilig buiten.",
                "safe",
                titel="Veilig",
            )

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

        bericht = hoofdletter(soort)
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

    @staticmethod
    def _weerbericht(soort: str, data: dict) -> tuple[str, str]:
        """Stel titel en tekst samen voor een weersituatie."""
        temp = data.get("temperatuur")
        gevoel = data.get("gevoelstemperatuur")
        sneeuw = data.get("sneeuwval")
        stoten = data.get("windstoten")

        def graden(waarde) -> str:
            if waarde is None:
                return "onbekend"
            return f"{waarde:.1f} \u00b0C".replace(".", ",")

        if soort == "sneeuw":
            tekst = f"Sneeuwval op je locatie bij {graden(temp)}"
            if sneeuw:
                tekst += f", ongeveer {sneeuw:.1f} cm per uur".replace(".", ",")
            if stoten and stoten >= 40:
                tekst += f", met windstoten tot {stoten:.0f} km/u"
            return "Sneeuw", tekst + "."

        if soort == "ijzel":
            return (
                "IJzel",
                f"Onderkoelde neerslag bij {graden(temp)}. Wegen en paden "
                "kunnen spiegelglad worden.",
            )

        if soort == "mist":
            vocht = data.get("luchtvochtigheid")
            tekst = "Dichte mist op je locatie"
            if vocht:
                tekst += f", luchtvochtigheid {vocht:.0f} procent"
            return "Mist", tekst + "."

        if soort == "hitte":
            tekst = f"Het is {graden(temp)} op je locatie"
            if gevoel is not None and abs(gevoel - (temp or 0)) >= 1:
                tekst += f", gevoelstemperatuur {graden(gevoel)}"
            return "Hitte", tekst + "."

        if soort == "vorst":
            tekst = f"Het vriest: {graden(temp)}"
            if gevoel is not None and gevoel < (temp or 0) - 1:
                tekst += f", gevoelstemperatuur {graden(gevoel)}"
            return "Vorst", tekst + "."

        return "Weer", f"Weersituatie: {soort}."

    @callback
    async def _handle_weather(self, event: Event) -> None:
        """Bijzondere weersituatie op de huidige locatie."""
        soort = event.data.get("soort", "")

        # Dezelfde standaard als de coordinator gebruikt. Stond hier eerst
        # een lege lijst, waardoor elke weersituatie werd gedetecteerd en
        # daarna weggegooid zolang je de instelling niet had opgeslagen.
        gekozen = self._opt(CONF_WEATHER_TYPES, DEFAULT_WEATHER_TYPES) or []
        if soort not in gekozen:
            return
        if not self.ingeschakeld or not self.diensten:
            return
        if self._in_stiltevenster():
            return

        # IJzel, sneeuw en mist gaan over gevaar onderweg; die komen ook door
        # tijdens het rijden. De rest zegt pas iets als je ergens bent.
        if soort not in ONDERWEG_RELEVANT and not self._ter_plaatse():
            return

        wacht = int(self._opt(CONF_NOTIFY_COOLDOWN, DEFAULT_NOTIFY_COOLDOWN))
        vorige = self._laatste_weer.get(soort)
        if wacht > 0 and vorige is not None:
            if (dt_util.utcnow() - vorige).total_seconds() < wacht * 60:
                return

        titel, bericht = self._weerbericht(soort, event.data)
        await self._stuur(bericht, f"weather_{soort}", titel=titel)
        self._laatste_weer[soort] = dt_util.utcnow()

    @callback
    async def _handle_outlook(self, event: Event) -> None:
        """Het vooruitzicht is opgeschaald naar zwaar weer.

        Gaat over de komende uren en over de hele omgeving, dus dit komt ook
        door tijdens het rijden: juist dan wil je weten dat de dag omslaat.
        """
        if not self._opt(CONF_OUTLOOK_NOTIFY, True):
            return
        if not self.ingeschakeld or not self.diensten:
            return
        if self._in_stiltevenster():
            return

        oordeel = event.data.get("oordeel", "")
        toelichting = event.data.get("toelichting", "")

        bericht = f"{oordeel} in de komende uren."
        if toelichting:
            bericht += f"\n{hoofdletter(toelichting)}"

        await self._stuur(bericht, "outlook", titel="Vooruitzicht")

    async def stuur_direct(self, bericht: str, soort: str, titel: str) -> None:
        """Verstuur zonder wachttijd of stilstandcontrole.

        Voor berichten die je zelf hebt ingepland, zoals het dagelijkse
        weerbericht: dat moet komen op het moment dat je hebt afgesproken,
        ook als er net iets anders gemeld is.
        """
        if not self.ingeschakeld or not self.diensten:
            return
        await self._stuur(bericht, soort, titel=titel)

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
