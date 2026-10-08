"""Verbindingen met de KNMI-bronnen.

Drie diensten:

- de API achter de KNMI-app (`api.app.knmi.cloud`): waarschuwingen,
  weersverwachting en de neerslagverwachting per vijf minuten. Zonder
  sleutel.
- EDR van het KNMI Data Platform: de tienminutenwaarnemingen van alle
  automatische weerstations. Met sleutel.
- WMS van het KNMI Data Platform: de radarkaart (actueel en verwachting tot
  twee uur vooruit). Met sleutel.

Gebouwd naar het voorbeeld van ha-nl-weather (PaulVanSchayck, Apache-2.0)
voor de vorm van de verzoeken en antwoorden; de code is eigen werk.

De sleutels gaan alleen in de Authorization-header mee en komen nooit in een
foutmelding of logregel terecht.

Bewust zonder Home Assistant erin, zodat het los te testen is.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta, timezone

import aiohttp

_LOGGER = logging.getLogger(__name__)

APP_URL = "https://api.app.knmi.cloud"
EDR_URL = (
    "https://api.dataplatform.knmi.nl/edr/v1/collections/"
    "10-minute-in-situ-meteorological-observations"
)
WMS_URL = "https://api.dataplatform.knmi.nl/wms/adaguc-server"

# Gebied waarin EDR naar stations zoekt (minlon,minlat,maxlon,maxlat). Ruim
# om Nederland heen; de Caribische stations vallen er bewust buiten.
EDR_BBOX = "2.5,50.4,7.6,54.0"

# De WMS staat volgens het KNMI 20 verzoeken per seconde toe. Wij blijven
# daar ruim onder, en doen er nooit twee tegelijk.
WMS_PER_SECONDE = 5

TIMEOUT_APP = 15
TIMEOUT_EDR = 25
TIMEOUT_WMS = 20

# Dataset en lagen van de radar
RADAR_ACTUEEL_DATASET = "nl_rdr_data_rtcor_5m"
RADAR_ACTUEEL_LAAG = "precipitation_real_time"
RADAR_VERWACHTING_DATASET = "radar_forecast_2.0"
RADAR_VERWACHTING_LAAG = "precipitation_nowcast"


class KnmiFout(Exception):
    """Een KNMI-bron gaf geen bruikbaar antwoord.

    `status` en `headers` volgen de vorm van een aiohttp-fout, zodat de
    bestaande herkansingslogica (429, Retry-After) er gewoon mee werkt.
    """

    def __init__(self, melding: str, status: int | None = None, headers=None):
        super().__init__(melding)
        self.status = status
        self.headers = headers or {}


class SleutelGeweigerd(KnmiFout):
    """401/403: sleutel ongeldig, verlopen of quotum op."""


class TeVeelVerzoeken(KnmiFout):
    """429: de bron remt ons af."""


class NietGevonden(KnmiFout):
    """404: geen gegevens voor deze vraag."""


class OngeldigVerzoek(KnmiFout):
    """400: de bron begrijpt de vraag niet."""


class ServerFout(KnmiFout):
    """5xx: storing aan de kant van het KNMI."""


def tijd_z(moment: datetime) -> str:
    """ISO-tijd in UTC met 'Z' en op hele seconden, zoals de KNMI-API's willen.

    De 'Z'-schrijfwijze (in plaats van +00:00) laat de WMS zijn cache
    gebruiken.
    """
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return (
        moment.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def vijf_minuten_slot(nu: datetime) -> datetime:
    """Het begin van het lopende vijfminutenvak (UTC)."""
    nu = nu.astimezone(timezone.utc)
    return nu.replace(minute=nu.minute - nu.minute % 5, second=0, microsecond=0)


def _fout_voor_status(status: int, headers) -> KnmiFout:
    """Zet een HTTP-status om naar de passende fout, zonder de body of sleutel."""
    if status in (401, 403):
        return SleutelGeweigerd(f"HTTP {status}: sleutel geweigerd of quotum op", status, headers)
    if status == 429:
        return TeVeelVerzoeken("HTTP 429: te veel verzoeken", status, headers)
    if status == 404:
        return NietGevonden("HTTP 404: geen gegevens", status, headers)
    if status == 400:
        return OngeldigVerzoek("HTTP 400: ongeldig verzoek", status, headers)
    if status >= 500:
        return ServerFout(f"HTTP {status}: storing bij het KNMI", status, headers)
    return KnmiFout(f"HTTP {status}", status, headers)


async def _haal(
    session,
    url: str,
    params: dict | None,
    timeout: float,
    sleutel: str | None = None,
    als: str = "json",
):
    """Eén GET met timeout; fouten als KnmiFout, nooit met de sleutel erin."""
    headers = {"Authorization": sleutel} if sleutel else None
    try:
        async with session.get(
            url,
            params=params,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as antwoord:
            if antwoord.status >= 400:
                raise _fout_voor_status(antwoord.status, dict(antwoord.headers))
            if als == "bytes":
                return await antwoord.read()
            tekst = await antwoord.text()
    except KnmiFout:
        raise
    except asyncio.TimeoutError as err:
        raise KnmiFout(f"geen antwoord binnen {timeout} s") from err
    except aiohttp.ClientError as err:
        # Alleen het soort fout: de URL kan in de tekst staan, de sleutel niet
        raise KnmiFout(f"verbindingsfout ({type(err).__name__})") from err

    if als == "tekst":
        return tekst
    try:
        return json.loads(tekst)
    except ValueError as err:
        raise KnmiFout("onleesbaar antwoord") from err


class KnmiApp:
    """De API achter de KNMI-app. Geen sleutel nodig."""

    def __init__(self, session) -> None:
        self._session = session

    async def weer(self, cel: str, regio: int) -> dict:
        """Verwachting, waarschuwingen en waarschuwingsniveau per uur."""
        return await _haal(
            self._session,
            f"{APP_URL}/weather",
            {"location": cel, "region": str(regio)},
            TIMEOUT_APP,
        )

    async def weer_detail(self, cel: str, regio: int, datum: str) -> dict:
        """Details van een dag: neerslagkans, wind, uv-index."""
        return await _haal(
            self._session,
            f"{APP_URL}/weather/detail",
            {"location": cel, "region": str(regio), "date": datum},
            TIMEOUT_APP,
        )

    async def neerslaggrafiek(self, radarcel: str, slot: datetime) -> dict:
        """Neerslag per vijf minuten voor de komende twee uur."""
        return await _haal(
            self._session,
            f"{APP_URL}/precipitation/graph",
            {"location": radarcel, "time": tijd_z(slot)},
            TIMEOUT_APP,
        )


class KnmiEdr:
    """Waarnemingen van de automatische weerstations (EDR)."""

    def __init__(self, session, sleutel: str) -> None:
        self._session = session
        self._sleutel = sleutel

    async def kubus(self, tot: datetime, parameters, terug_minuten: int = 30) -> list:
        """Alle stations in het gebied met de laatste waarden (coverages)."""
        van = tot - timedelta(minutes=terug_minuten)
        antwoord = await _haal(
            self._session,
            f"{EDR_URL}/cube",
            {
                "datetime": f"{tijd_z(van)}/{tijd_z(tot)}",
                "parameter-name": ",".join(parameters),
                "bbox": EDR_BBOX,
            },
            TIMEOUT_EDR,
            self._sleutel,
        )
        return list((antwoord or {}).get("coverages") or [])

    async def stations(self, moment: datetime) -> dict[str, str]:
        """Stationsnummer naar naam."""
        antwoord = await _haal(
            self._session,
            f"{EDR_URL}/locations",
            {"datetime": tijd_z(moment), "bbox": EDR_BBOX},
            TIMEOUT_EDR,
            self._sleutel,
        )
        namen: dict[str, str] = {}
        for kenmerk in (antwoord or {}).get("features") or []:
            sleutel = kenmerk.get("id")
            naam = (kenmerk.get("properties") or {}).get("name")
            if sleutel and naam:
                namen[str(sleutel)] = str(naam)
        return namen


def laatste_tijd_uit_capabilities(tekst: str) -> datetime | None:
    """Het nieuwste tijdstip uit een WMS GetCapabilities-antwoord.

    De tijddimensie staat er als 'begin/eind/stap' of als lijst; het eind
    (of het laatste element) is het nieuwste beeld.
    """
    try:
        from defusedxml import ElementTree as veilig_et

        wortel = veilig_et.fromstring(tekst)
    except ImportError:  # pragma: no cover - defusedxml zit in Home Assistant
        from xml.etree import ElementTree as et

        wortel = et.fromstring(tekst)
    except Exception:  # noqa: BLE001 - onleesbare XML
        return None

    laatste: datetime | None = None
    for element in wortel.iter():
        naam = element.tag.rsplit("}", 1)[-1]
        if naam not in ("Dimension", "Extent"):
            continue
        if (element.get("name") or "").lower() != "time" or not element.text:
            continue
        waarde = element.text.strip()
        delen = waarde.split("/")
        kandidaat = delen[1] if len(delen) == 3 else waarde.split(",")[-1]
        try:
            moment = datetime.fromisoformat(kandidaat.strip().replace("Z", "+00:00"))
        except ValueError:
            continue
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        if laatste is None or moment > laatste:
            laatste = moment
    return laatste


class KnmiWms:
    """Radarkaart als beeld, rechtstreeks in webmercator (EPSG:3857)."""

    def __init__(self, session, sleutel: str, per_seconde: float = WMS_PER_SECONDE) -> None:
        self._session = session
        self._sleutel = sleutel
        self._interval = 1.0 / per_seconde
        self._slot = asyncio.Lock()
        self._vorige = 0.0

    async def _wacht_beurt(self) -> None:
        """Nooit vaker dan WMS_PER_SECONDE verzoeken per seconde."""
        wacht = self._interval - (time.monotonic() - self._vorige)
        if wacht > 0:
            await asyncio.sleep(wacht)
        self._vorige = time.monotonic()

    async def _get(self, params: dict, als: str):
        async with self._slot:
            await self._wacht_beurt()
            return await _haal(
                self._session, WMS_URL, params, TIMEOUT_WMS, self._sleutel, als
            )

    async def laatste_radartijd(self) -> datetime | None:
        """Tijdstip van het nieuwste actuele radarbeeld."""
        tekst = await self._get(
            {
                "SERVICE": "WMS",
                "REQUEST": "GetCapabilities",
                "DATASET": RADAR_ACTUEEL_DATASET,
            },
            "tekst",
        )
        return laatste_tijd_uit_capabilities(tekst)

    @staticmethod
    def kaartparameters(
        bbox: str,
        breedte: int,
        hoogte: int,
        stijl: str,
        tijd: datetime,
        referentie: datetime | None = None,
    ) -> dict:
        """De parameters van één GetMap-verzoek.

        Met een referentietijd is het de verwachting (radar_forecast_2.0),
        anders het actuele composietbeeld.
        """
        params = {
            "SERVICE": "WMS",
            "REQUEST": "GetMap",
            "VERSION": "1.3.0",
            "FORMAT": "image/png",
            "TRANSPARENT": "TRUE",
            "CRS": "EPSG:3857",
            "BBOX": bbox,
            "WIDTH": str(breedte),
            "HEIGHT": str(hoogte),
            "STYLES": stijl,
            "TIME": tijd_z(tijd),
        }
        if referentie is None:
            params["DATASET"] = RADAR_ACTUEEL_DATASET
            params["LAYERS"] = RADAR_ACTUEEL_LAAG
        else:
            params["DATASET"] = RADAR_VERWACHTING_DATASET
            params["LAYERS"] = RADAR_VERWACHTING_LAAG
            params["DIM_REFERENCE_TIME"] = tijd_z(referentie)
        return params

    async def kaart(self, params: dict) -> bytes:
        """Haal één beeld op; een tekstantwoord in plaats van PNG is een fout."""
        inhoud = await self._get(params, "bytes")
        if not inhoud or not inhoud.startswith(b"\x89PNG"):
            raise OngeldigVerzoek("geen PNG in het antwoord van de WMS")
        return inhoud


# ---------------------------------------------------------------------
# Afremmen na fouten
# ---------------------------------------------------------------------

# Wachttijd na een storing (5xx, time-out): verdubbelt per fout op rij
STORING_BASIS = 120
STORING_MAX = 1800
# Na een 429: minstens tien minuten, verdubbelend, en nooit korter dan de
# bron zelf vraagt
LIMIET_BASIS = 600
LIMIET_MAX = 7200
# Na een geweigerde sleutel (of quotum op): een uur
SLEUTEL_WACHT = 3600


class Afremming:
    """Houdt per bron bij wanneer een nieuwe poging weer mag.

    Zolang een bron afgeremd is, slaat de integratie hem over en gebruikt de
    terugvalbron. Zo komt er bij een storing of een quotum dat op is geen
    stroom aan verzoeken en geen stroom aan foutmeldingen.
    """

    def __init__(self) -> None:
        self.op_rij = 0
        self.tot: float = 0.0
        self.reden: str | None = None

    def mag(self, nu: float | None = None) -> bool:
        """Of er nu een verzoek mag."""
        return (nu if nu is not None else time.time()) >= self.tot

    def succes(self) -> None:
        self.op_rij = 0
        self.tot = 0.0
        self.reden = None

    def fout(self, fout: Exception, nu: float | None = None) -> float:
        """Noteer een fout en geef de wachttijd in seconden terug."""
        nu = nu if nu is not None else time.time()
        self.op_rij += 1
        stap = 2 ** (self.op_rij - 1)
        status = getattr(fout, "status", None)
        if status == 429:
            wacht = min(LIMIET_BASIS * stap, LIMIET_MAX)
            gevraagd = _retry_after(fout)
            if gevraagd:
                wacht = max(wacht, min(gevraagd, LIMIET_MAX))
            self.reden = "afgeremd (429)"
        elif status in (401, 403):
            wacht = SLEUTEL_WACHT
            self.reden = "sleutel geweigerd of quotum op"
        else:
            wacht = min(STORING_BASIS * stap, STORING_MAX)
            self.reden = "storing"
        self.tot = nu + wacht
        return wacht

    def als_dict(self, nu: float | None = None) -> dict:
        nu = nu if nu is not None else time.time()
        return {
            "fouten_op_rij": self.op_rij,
            "wacht_nog_s": max(int(self.tot - nu), 0),
            "reden": self.reden,
        }


def _retry_after(fout) -> int | None:
    headers = getattr(fout, "headers", None) or {}
    try:
        waarde = headers.get("Retry-After")
    except AttributeError:
        return None
    try:
        seconden = int(str(waarde).strip())
    except (TypeError, ValueError):
        return None
    return seconden if seconden > 0 else None


# ---------------------------------------------------------------------
# Alles bij elkaar, gedeeld door de coordinators
# ---------------------------------------------------------------------

try:
    from .knmi_grid import Landbepaling
except ImportError:  # in de tests zonder pakketstructuur
    from knmi_grid import Landbepaling


class KnmiBronnen:
    """De KNMI-verbindingen van één config entry.

    Een verbinding zonder sleutel bestaat niet (None); de coordinators vallen
    dan meteen terug op hun gewone bron, zonder fout of logregel.
    """

    NAMEN = ("waarschuwingen", "verwachting", "nowcast", "edr", "wms")

    def __init__(
        self,
        session,
        wms_sleutel: str | None = None,
        edr_sleutel: str | None = None,
        notificatie_sleutel: str | None = None,
    ) -> None:
        self.app = KnmiApp(session)
        self.edr = KnmiEdr(session, edr_sleutel) if edr_sleutel else None
        self.wms = KnmiWms(session, wms_sleutel) if wms_sleutel else None
        self.notificatie_sleutel = notificatie_sleutel or None
        self.push = None  # KnmiPush, als er een notificatiesleutel is
        self.land = Landbepaling()
        self.afremming = {naam: Afremming() for naam in self.NAMEN}

    def ontbrekende_functies(self) -> list[str]:
        """Welke functies uit staan omdat de sleutel ontbreekt."""
        uit = []
        if self.wms is None:
            uit.append("radarkaart (WMS-sleutel)")
        if self.edr is None:
            uit.append("waarnemingen (EDR-sleutel)")
        if self.notificatie_sleutel is None:
            uit.append("pushmeldingen (Notification Service-sleutel)")
        return uit

    def als_dict(self) -> dict:
        """Voor de bronstatus en diagnostiek; nooit de sleutels zelf."""
        return {
            "sleutels": {
                "wms": self.wms is not None,
                "edr": self.edr is not None,
                "notificatie": self.notificatie_sleutel is not None,
            },
            "push": self.push.als_dict() if self.push is not None else None,
            "afremming": {
                naam: rem.als_dict()
                for naam, rem in self.afremming.items()
                if rem.op_rij
            },
        }


async def poging(afremming: Afremming, bronstatus, naam: str, maak):
    """Eén poging bij een KNMI-bron, met afremming en bronstatistiek.

    Geeft (resultaat, None) bij succes en (None, reden) bij een fout of zolang
    de bron afgeremd is. De aanroeper valt dan terug op zijn gewone bron.
    Een geweigerde sleutel of 429 wordt eenmalig gelogd per reeks fouten,
    een storing alleen op debugniveau.
    """
    if not afremming.mag():
        return None, afremming.reden or "afgeremd"
    try:
        resultaat = await maak()
    except (KnmiFout, ValueError, KeyError, TypeError) as err:
        if bronstatus is not None:
            bronstatus.fout(err)
        eerste = afremming.op_rij == 0
        wacht = afremming.fout(err)
        if eerste and getattr(err, "status", None) in (401, 403, 429):
            _LOGGER.warning(
                "KNMI %s: %s; %d minuten de gewone bron", naam, err, wacht // 60
            )
        else:
            _LOGGER.debug("KNMI %s niet bruikbaar (%s); terugval", naam, err)
        return None, str(err)
    afremming.succes()
    if bronstatus is not None:
        bronstatus.succes()
    return resultaat, None
