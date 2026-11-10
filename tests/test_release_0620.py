"""0.62.0: landelijke waarschuwingen en MeteoAlarm via de JSON-API.

Ruud 10-11 06:53: "Het KNMI geeft momenteel code geel, ik zie dat niet terug
op dashboard tablet". Code geel (dichte mist) voor "Nederland met
uitzondering van Zeeland, Waddeneilanden, IJsselmeergebied en
Waddenzeegebied en delen van: Limburg"; de KNMI-app gaf voor Gelderland
niets, de Atom-feed van MeteoAlarm was leeg en het gebiedsfilter vond geen
provincienaam.
"""

from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path

import meteoalarm_json as M

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
NU = datetime(2026, 11, 10, 6, 0, tzinfo=timezone.utc)

NL = ("Nederland met uitzondering van Zeeland, Waddeneilanden, IJsselmeergebied "
      "en Waddenzeegebied en delen van: Limburg")
EN = ("The Netherlands except Zeeland, Wadden Islands, IJsselmeer area and Wadden "
      "Sea area and parts of: Limburg")


def _melding(niveau="2; yellow; Moderate", urgency="Expected", expires="2026-11-10T11:00:00+00:00",
             msg="Update", response=None):
    en = {
        "language": "en-GB", "area": [{"areaDesc": EN}], "certainty": "Likely",
        "event": "Moderate Fog", "expires": expires, "headline": "Locally fog, visibility less than 200 m",
        "onset": "2026-11-09T22:30:00+00:00",
        "parameter": [{"value": niveau, "valueName": "awareness_level"},
                      {"value": "4; Fog", "valueName": "awareness_type"}],
        "severity": "Moderate", "urgency": urgency,
    }
    if response:
        en["responseType"] = response
    nl = dict(en, language="nl-NL", area=[{"areaDesc": NL}], event="Matige mist",
              headline="Plaatselijk mist met zicht minder dan 200 m")
    return {"alert": {"identifier": "2.49.0.0.528.0.NL.x_4", "msgType": msg, "info": [en, nl]},
            "uuid": "abc"}


def test_landelijk_geldt_voor_gelderland_niet_voor_zeeland():
    for tekst in (NL, EN):
        assert M.landelijk(tekst)
        assert M.landelijk_geldt(tekst, ["Gelderland"])
        assert M.landelijk_geldt(tekst, ["berkelland", "gelderland"])
        assert not M.landelijk_geldt(tekst, ["Zeeland"])
        assert not M.landelijk_geldt(tekst, ["Waddeneilanden"])
        assert not M.landelijk_geldt(tekst, ["IJsselmeergebied"])
        # "delen van Limburg": de rest van Limburg heeft het wel
        assert M.landelijk_geldt(tekst, ["Limburg"])
    assert M.landelijk_geldt("Nederland", ["Gelderland"])
    assert not M.landelijk("Delen van: Groningen, Drenthe en Overijssel")


def test_json_waarschuwing_10_11():
    lijst = M.waarschuwingen({"warnings": [_melding()]}, NU)
    assert len(lijst) == 1
    w = lijst[0]
    assert (w["niveau"], w["rang"], w["soort"]) == ("geel", 1, "mist")
    assert w["gebied"] == NL and w["landelijk"]
    assert w["titel"].startswith("Plaatselijk mist")
    assert w["id"] == "meteoalarm|geel|mist|2026-11-09T22:30:00+00:00"


def test_groen_verlopen_en_ingetrokken_vallen_weg():
    assert M.waarschuwingen({"warnings": [_melding(niveau="1; green; Minor")]}, NU) == []
    assert M.waarschuwingen({"warnings": [_melding(urgency="Past")]}, NU) == []
    assert M.waarschuwingen({"warnings": [_melding(expires="2026-11-10T05:00:00+00:00")]}, NU) == []
    assert M.waarschuwingen({"warnings": [_melding(msg="Cancel")]}, NU) == []
    assert M.waarschuwingen({"warnings": [_melding(response=["AllClear"])]}, NU) == []
    assert M.waarschuwingen("onzin", NU) == []


def test_niveau_per_uur_aangevuld():
    per_uur = [{"tijd": f"2026-11-10T{u:02d}:00:00+00:00", "niveau": "geen"} for u in range(5, 13)]
    w = M.waarschuwingen({"warnings": [_melding()]}, NU)
    uit = M.vul_per_uur(per_uur, w)
    kleuren = [u["niveau"] for u in uit]
    assert kleuren[:6] == ["geel"] * 6      # 05:00-10:00
    assert kleuren[6:] == ["geen", "geen"]  # 11:00 (= einde) en 12:00


def test_cap_ernst_een_kleur_lager():
    from const import ALERT_LEVELS
    assert "Minor" not in ALERT_LEVELS
    assert ALERT_LEVELS["Moderate"] == ("geel", 1)
    assert ALERT_LEVELS["Severe"] == ("oranje", 2)


def test_alerts_gebruikt_json_en_vult_knmi_aan():
    code = (BRON / "alerts.py").read_text(encoding="utf-8")
    boom = ast.parse(code)
    namen = {k.name for k in ast.walk(boom) if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert {"_meteoalarm_json", "_vul_aan_met_meteoalarm", "_meteoalarm_resultaat"} <= namen
    assert "await self._vul_aan_met_meteoalarm(knmi, land)" in code
    assert "ma_json.landelijk_geldt(gebied, namen)" in code
