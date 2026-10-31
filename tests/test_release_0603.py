"""0.60.3: eindtijd van een KNMI-waarschuwing zonder extra uur (L-SC-027).

Leerronde 30-10: KNMI-tekst "mist, 06:00 tot 10:00", in de uurverwachting
geel t/m het uur van 09Z (10:00 lokaal), maar `tot` stond op 10Z (11:00).
Hetzelfde op 23-10 en 29-10 (n=4). Het laatste geel-uur is zelf het einde.
"""

from datetime import datetime, timedelta, timezone

try:
    import homeassistant.util.dt  # noqa: F401
except ModuleNotFoundError:
    import sys
    import types

    _dt = types.ModuleType("homeassistant.util.dt")
    _dt.utcnow = lambda: datetime.now(timezone.utc)
    for naam, mod in (
        ("homeassistant", types.ModuleType("homeassistant")),
        ("homeassistant.util", types.ModuleType("homeassistant.util")),
        ("homeassistant.util.dt", _dt),
    ):
        sys.modules.setdefault(naam, mod)
    sys.modules["homeassistant.util"].dt = _dt

from knmi_verwerk import waarschuwingen  # noqa: E402

NU = datetime(2026, 10, 30, 5, 41, tzinfo=timezone.utc)  # 06:41 lokaal
BEGIN = NU.replace(minute=0)


def _payload(niveaus):
    return {
        "alerts": [{"level": "yellow", "description": "Code geel: dichte mist (06:00 tot 10:00)."}],
        "hourly": {
            "forecast": [
                {
                    "dateTime": (BEGIN + timedelta(hours=i)).isoformat().replace("+00:00", "Z"),
                    "alertLevel": niveau,
                }
                for i, niveau in enumerate(niveaus)
            ]
        },
    }


def test_tot_is_laatste_geel_uur_30_10():
    # 05Z geen, 06Z-09Z geel, 10Z geen (zoals 30-10)
    data = waarschuwingen(_payload(["none", "yellow", "yellow", "yellow", "yellow", "none"]), 4, "Gelderland", NU)
    w = data["actief"][0]
    assert w["vanaf"] == (BEGIN + timedelta(hours=1)).isoformat()
    assert w["tot"] == datetime(2026, 10, 30, 9, tzinfo=timezone.utc).isoformat()


def test_een_enkel_uur_geeft_vanaf_gelijk_aan_tot():
    data = waarschuwingen(_payload(["none", "yellow", "none"]), 4, "Gelderland", NU)
    w = data["actief"][0]
    assert w["vanaf"] == w["tot"] == (BEGIN + timedelta(hours=1)).isoformat()


def test_geel_tot_het_einde_van_de_reeks():
    data = waarschuwingen(_payload(["yellow", "yellow"]), 4, "Gelderland", NU)
    w = data["actief"][0]
    assert w["tot"] == (BEGIN + timedelta(hours=1)).isoformat()
