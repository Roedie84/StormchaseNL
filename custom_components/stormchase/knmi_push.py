"""Meldingen van de KNMI Notification Service (MQTT over websockets).

Het KNMI Data Platform meldt via MQTT zodra er een nieuw bestand in een
dataset staat: elke tien minuten de stationswaarnemingen, elke vijf minuten
een nieuwe radarverwachting. Met zo'n melding hoeft Stormchase niet te raden
wanneer er iets nieuws is: kort na de melding wordt de bron opgehaald.

Bewust met paho-mqtt (dat Home Assistant al meelevert) en los van de
MQTT-integratie van Home Assistant: dit is een eigen verbinding met een
eigen broker. paho draait zijn netwerklus in een eigen draad; berichten
gaan via call_soon_threadsafe terug naar de event loop. Bij een verbroken
verbinding probeert paho het zelf opnieuw, met een wachttijd die oploopt
van 5 seconden tot 10 minuten.

Zonder sleutel, of als de verbinding wegvalt, blijft alles gewoon pollen; de
meldingen maken het alleen sneller.

Bewust zonder Home Assistant-imports, zodat het los te testen is.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Callable

_LOGGER = logging.getLogger(__name__)

BROKER = "mqtt.dataplatform.knmi.nl"
POORT = 443
WS_PAD = "/mqtt"
KEEPALIVE = 60

DATASET_WAARNEMINGEN = "10-minute-in-situ-meteorological-observations"
DATASET_RADARVERWACHTING = "radar_forecast"

ONDERWERPEN = (
    f"dataplatform/file/v1/{DATASET_WAARNEMINGEN}/1.0/#",
    f"dataplatform/file/v1/{DATASET_RADARVERWACHTING}/2.0/#",
)

# Wachttijd tussen pogingen na een verbroken verbinding (exponentieel)
HERVERBIND_MIN = 5
HERVERBIND_MAX = 600

# MQTT 5-redenen bij een geweigerde aanmelding
REDENEN_GEWEIGERD = {134, 135}  # bad user name or password, not authorized


def _reden(waarde) -> int | None:
    """Redencode als getal, uit een paho ReasonCode of een gewoon getal."""
    if waarde is None:
        return None
    for veld in ("value",):
        if hasattr(waarde, veld):
            try:
                return int(getattr(waarde, veld))
            except (TypeError, ValueError):
                return None
    try:
        return int(waarde)
    except (TypeError, ValueError):
        return None


def lees_melding(payload: bytes | str) -> tuple[str, str | None] | None:
    """(dataset, bestandsnaam) uit een melding, of None als hij onleesbaar is."""
    try:
        gebeurtenis = json.loads(payload)
    except (TypeError, ValueError):
        return None
    data = (gebeurtenis or {}).get("data") if isinstance(gebeurtenis, dict) else None
    if not isinstance(data, dict) or not data.get("datasetName"):
        return None
    return str(data["datasetName"]), data.get("filename")


def _maak_paho_client(client_id: str):
    """Een paho-client voor MQTT 5 over websockets (paho 1.6 en 2.x)."""
    import paho.mqtt.client as mqtt

    try:
        return mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
            protocol=mqtt.MQTTv5,
            transport="websockets",
        )
    except AttributeError:  # paho 1.x kent geen callback_api_version
        return mqtt.Client(
            client_id=client_id, protocol=mqtt.MQTTv5, transport="websockets"
        )


class KnmiPush:
    """Eén MQTT-verbinding met het KNMI, met een callback per dataset."""

    def __init__(
        self,
        sleutel: str,
        loop,
        ssl_context,
        bij_melding: Callable[[str, str | None], None],
        client_fabriek: Callable[[str], object] = _maak_paho_client,
    ) -> None:
        self._sleutel = sleutel
        self._loop = loop
        self._ssl = ssl_context
        self._bij_melding = bij_melding
        self._fabriek = client_fabriek
        self._client = None
        self.status = "niet gestart"
        self.verbonden_sinds: float | None = None
        self.verbroken_sinds: float | None = None
        self.laatste_melding: float | None = None
        self.meldingen = 0
        self.verbindingen = 0

    # ---- vanuit de event loop ----

    def start(self) -> None:
        """Verbinding opzetten; blokkeert niet (paho verbindt in zijn draad)."""
        client = self._fabriek(f"stormchase-{uuid.uuid4()}")
        client.username_pw_set("token", self._sleutel)
        if self._ssl is not None:
            client.tls_set_context(self._ssl)
        try:
            client.ws_set_options(path=WS_PAD)
        except AttributeError:  # pragma: no cover - oude paho
            pass
        client.reconnect_delay_set(min_delay=HERVERBIND_MIN, max_delay=HERVERBIND_MAX)
        client.on_connect = self._bij_verbinden
        client.on_disconnect = self._bij_verbreken
        client.on_message = self._bij_bericht
        self._client = client
        self.status = "verbinden"
        client.connect_async(BROKER, POORT, KEEPALIVE)
        client.loop_start()

    def stop(self) -> None:
        """Verbinding sluiten en de draad stoppen. Blokkeert kort: in een executor."""
        client, self._client = self._client, None
        if client is None:
            return
        try:
            client.disconnect()
        except Exception:  # noqa: BLE001 - afsluiten mag niet stuklopen
            pass
        try:
            client.loop_stop()
        except Exception:  # noqa: BLE001
            pass
        if self.status != "sleutel geweigerd":
            self.status = "gestopt"

    def als_dict(self) -> dict:
        """Voor de bronstatus en diagnostiek (zonder sleutel)."""
        nu = time.time()
        return {
            "status": self.status,
            "verbonden_sinds_s": int(nu - self.verbonden_sinds) if self.verbonden_sinds else None,
            "verbroken_sinds_s": int(nu - self.verbroken_sinds) if self.verbroken_sinds else None,
            "laatste_melding_s": int(nu - self.laatste_melding) if self.laatste_melding else None,
            "meldingen": self.meldingen,
            "verbindingen": self.verbindingen,
        }

    # ---- callbacks: in de draad van paho ----

    def _bij_verbinden(self, client, _userdata, _flags, reden, *_rest) -> None:
        code = _reden(reden)
        if code not in (None, 0):
            self._loop.call_soon_threadsafe(self._geweigerd_of_mislukt, code)
            return
        for onderwerp in ONDERWERPEN:
            client.subscribe(onderwerp)
        self._loop.call_soon_threadsafe(self._verbonden)

    def _bij_verbreken(self, _client, _userdata, *rest) -> None:
        self._loop.call_soon_threadsafe(self._verbroken)

    def _bij_bericht(self, _client, _userdata, bericht) -> None:
        self._loop.call_soon_threadsafe(self._bericht, bericht.payload)

    # ---- terug in de event loop ----

    def _verbonden(self) -> None:
        self.status = "verbonden"
        self.verbindingen += 1
        self.verbonden_sinds = time.time()
        self.verbroken_sinds = None
        _LOGGER.debug("KNMI Notification Service verbonden")

    def _verbroken(self) -> None:
        if self.status in ("gestopt", "sleutel geweigerd"):
            return
        self.status = "verbinding verbroken"
        self.verbonden_sinds = None
        if self.verbroken_sinds is None:
            self.verbroken_sinds = time.time()
        _LOGGER.debug("KNMI Notification Service verbroken; paho probeert opnieuw")

    def _geweigerd_of_mislukt(self, code: int) -> None:
        if code in REDENEN_GEWEIGERD:
            # Opnieuw proberen heeft geen zin; eenmalig melden en stoppen.
            # Het pollen gaat gewoon door.
            self.status = "sleutel geweigerd"
            self.verbonden_sinds = None
            _LOGGER.warning(
                "KNMI Notification Service weigert de sleutel (reden %s); "
                "meldingen uit, de bronnen worden gewoon gepold",
                code,
            )
            self._loop.run_in_executor(None, self.stop)
            return
        self._verbroken()

    def _bericht(self, payload) -> None:
        gelezen = lees_melding(payload)
        if gelezen is None:
            return
        self.meldingen += 1
        self.laatste_melding = time.time()
        dataset, bestand = gelezen
        try:
            self._bij_melding(dataset, bestand)
        except Exception:  # noqa: BLE001 - een melding mag de verbinding niet breken
            _LOGGER.debug("Melding %s niet verwerkt", dataset, exc_info=True)
