"""0.52.2: KNMI-push geeft geen draadfout meer als de event loop al dicht is."""

from __future__ import annotations

import asyncio
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

from knmi_push import KnmiPush  # noqa: E402


class _Bericht:
    payload = b"{}"


def _push(loop):
    return KnmiPush("geheim", loop, None, lambda d, b: None, lambda cid: None)


def _in_draad(functie):
    fouten = []

    def draad():
        try:
            functie()
        except BaseException as fout:  # noqa: BLE001
            fouten.append(fout)

    t = threading.Thread(target=draad)
    t.start()
    t.join()
    return fouten


def test_callbacks_na_gesloten_loop_zonder_fout():
    loop = asyncio.new_event_loop()
    loop.close()
    push = _push(loop)
    fouten = _in_draad(lambda: (
        push._bij_verbreken(None, None, 0),
        push._bij_bericht(None, None, _Bericht()),
        push._bij_verbinden(None, None, None, 5),
    ))
    assert fouten == []


def test_runtimeerror_tijdens_sluiten_gevangen():
    class Sluitend:
        def is_closed(self):
            return False

        def call_soon_threadsafe(self, *_a):
            raise RuntimeError("Event loop is closed")

    push = _push(Sluitend())
    assert _in_draad(lambda: push._bij_verbreken(None, None, 0)) == []


def test_open_loop_krijgt_de_callback_nog():
    loop = asyncio.new_event_loop()
    try:
        push = _push(loop)
        push.status = "verbinden"
        assert _in_draad(lambda: push._bij_verbreken(None, None, 0)) == []
        loop.run_until_complete(asyncio.sleep(0.01))
        assert push.status == "verbinding verbroken"
    finally:
        loop.close()
