"""0.61.0: windbijsturing na een modelsprong (L-SC-028) en motregen van het
nabije station als "regent nu" (L-SC-029).

L-SC-028, 01-11 11:45:39 (n=1): bij de locatiewissel ging het model 17,6 ->
4,7 km/u. De fout van de oude plek (12,7 verwacht tegen 6,3 gemeten: -6,4)
ging voor de helft absoluut bij 4,7 x 0,72 = 3,4: 0,3 km/u, gemeten daarna 7,8.

L-SC-029, 01-11 (n=2 perioden, ~130 min): Hupsel (3,4 km) mat motregen
(0,01-0,51 mm/u, weercode 51/57), de nowcast gaf 0,0 en het regenbeeld zei
"Droog, komende 2 uur geen regen".
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

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

import const  # noqa: E402
from buienreeks import (  # noqa: E402
    begin_weergave,
    lees_reeks,
    met_station_regen,
    regenbeeld,
    station_regen,
)
from knmi_verwerk import metingen  # noqa: E402
from windcorrectie import Windcorrectie, bijsturing, modelsprong  # noqa: E402

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
T0 = 1_760_000_000.0
STAP = 600.0


# ---------------------------------------------------------------------
# L-SC-028: windbijsturing
# ---------------------------------------------------------------------


def _geleerd(ratio: float = 0.72, model: float = 20.0) -> tuple[Windcorrectie, float]:
    """Zeven uur rustige paren met een vaste verhouding."""
    wc = Windcorrectie()
    t = T0
    for _ in range(int(7 * 3600 / STAP)):
        assert wc.bij(t, model * ratio, model, t)
        t += STAP
    return wc, t


class TestModelsprong:
    def test_reeks_01_11_locatiewissel(self):
        wc, t = _geleerd()
        wc.bij(t, 6.3, 17.6, t)  # laatste meting op de oude plek
        voor = wc.corrigeer(17.6, t + 60)
        assert voor["factor"] == 0.72
        assert voor["bijsturing"] < -3.0  # op dezelfde plek telt de fout gewoon
        # Locatiewissel: model 4,7. Voorheen 3,4 - 3,1 = 0,3 km/u
        na = wc.corrigeer(4.7, t + 540)
        assert na["bijsturing"] == 0.0
        assert na["bijsturing_vervallen"] == "modelsprong"
        assert na["bijsturing_fout"] == -6.4  # de oude fout blijft zichtbaar
        assert na["waarde"] == 3.4  # model x factor, geen 0,3

    def test_volgende_meting_stuurt_weer_bij(self):
        wc, t = _geleerd()
        wc.bij(t, 6.3, 17.6, t)
        assert wc.corrigeer(4.7, t + 540)["bijsturing_vervallen"] == "modelsprong"
        # Nieuwe meting gekoppeld aan het nieuwe model: 7,8 tegen 3,4 verwacht
        wc.bij(t + 600, 7.8, 4.7, t + 600)
        uit = wc.corrigeer(4.7, t + 600)
        assert uit["bijsturing_vervallen"] is None
        assert uit["bijsturing"] == 2.2  # (7,8 - 3,384) / 2
        assert uit["waarde"] == 5.6

    def test_kleine_modelwijziging_houdt_bijsturing(self):
        wc, t = _geleerd()
        wc.bij(t, 6.3, 17.6, t)
        uit = wc.corrigeer(15.0, t + 60)  # -15 %: geen sprong
        assert uit["bijsturing_vervallen"] is None
        assert uit["bijsturing"] < -3.0

    def test_sprong_omhoog_ook(self):
        wc, t = _geleerd()
        wc.bij(t, 30.0, 30.0, t)  # verwacht 21,6, fout +8,4
        uit = wc.corrigeer(50.0, t + 60)  # +67 %
        assert uit["bijsturing"] == 0.0
        assert uit["waarde"] == 36.0

    def test_komende_uren_zonder_bijsturing_na_sprong(self):
        wc, t = _geleerd()
        wc.bij(t, 6.3, 17.6, t)
        uren = [(t + 3600, 4.7), (t + 7200, 5.0)]
        assert wc.bijgestuurde_uren(uren, t + 540, 0.72, 4.7) == [
            (t + 3600, 3.4), (t + 7200, 3.6)
        ]
        # Zonder model (oude aanroep) zoals voorheen bijgestuurd
        oud = dict(wc.bijgestuurde_uren(uren, t + 540, 0.72))
        assert oud[t + 3600] < 3.4

    def test_grenzen_modelsprong(self):
        assert modelsprong(17.6, 4.7)
        assert modelsprong(10.0, 14.5)  # +45 %, 4,5 km/u
        assert not modelsprong(10.0, 14.0)  # precies 40 %
        assert not modelsprong(4.0, 6.0)  # +50 %, maar 2 km/u: weinig wind
        assert modelsprong(0.0, 5.0)
        assert not modelsprong(None, 5.0) and not modelsprong(5.0, None)

    def test_losse_functie_zonder_model_ongewijzigd(self):
        # Zonder modelwaarde van nu: gedrag van 0.59.0
        uit = bijsturing((T0, 6.3, 17.6), T0, 0.72)
        assert uit["kmh"] == -3.2 and "vervallen" not in uit
        assert bijsturing((T0, 6.3, 17.6), T0, 0.72, 4.7)["vervallen"] == "modelsprong"

    def test_constanten(self):
        assert const.WINDBIJSTURING_SPRONG_DEEL == 0.40
        assert const.WINDBIJSTURING_SPRONG_MIN_KMH == 3.0

    def test_aansluiting(self):
        bron = (BRON / "coordinator.py").read_text(encoding="utf-8")
        assert "# 0.61.0 (L-SC-028): na een modelsprong geen bijsturing\n                model," in bron
        assert '"bijsturing_vervallen"' in (BRON / "sensor.py").read_text(encoding="utf-8")


# ---------------------------------------------------------------------
# L-SC-029: motregen van het station
# ---------------------------------------------------------------------

NU = datetime(2026, 11, 1, 21, 55, tzinfo=timezone.utc)
NU_S = NU.timestamp()


def _knmi(**extra) -> dict:
    """Meting zoals Hupsel op 01-11 22:50 lokaal: motregen, radar droog."""
    data = {
        "bron": "knmi_edr",
        "waargenomen_op": (NU - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        "neerslag_intensiteit": 0.01,
        "neerslag_station": "Hupsel",
        "neerslag_station_afstand_km": 3.4,
        "weercode": 51,
        "weer_station": "Hupsel",
        "weer_station_afstand_km": 3.4,
        "station": "Hupsel",
        "station_afstand_km": 3.4,
    }
    data.update(extra)
    return data


DROOG = [(m, 0.0) for m in range(-10, 125, 5)]


def _radar(reeks=DROOG) -> dict:
    data = lees_reeks(reeks, 0.1)
    data["begint_over_kaal"] = data["begint_over"]
    data["drempel"] = 0.1
    data["verwachting"] = [{"minuten": m, "mm_per_uur": mm} for m, mm in reeks]
    return data


class TestStationRegen:
    def test_motregencode_01_11(self):
        st = station_regen(_knmi(), 0.1, NU_S)
        assert st is not None
        assert st["station"] == "Hupsel" and st["afstand_km"] == 3.4
        assert st["weercode"] == 51 and st["motregen"] is True

    def test_intensiteit_zonder_code(self):
        st = station_regen(_knmi(weercode=0, neerslag_intensiteit=0.51), 0.1, NU_S)
        assert st is not None and st["intensiteit"] == 0.51

    def test_te_weinig_en_geen_code_is_droog(self):
        assert station_regen(_knmi(weercode=0, neerslag_intensiteit=0.05), 0.1, NU_S) is None
        assert station_regen(_knmi(weercode=None, neerslag_intensiteit=0.0), 0.1, NU_S) is None

    def test_station_te_ver(self):
        ver = _knmi(weer_station_afstand_km=12.0, neerslag_station_afstand_km=12.0)
        assert station_regen(ver, 0.1, NU_S) is None
        # Code van een ver station telt niet, intensiteit van een dichtbij wel
        gemengd = _knmi(weer_station_afstand_km=12.0, neerslag_intensiteit=0.3)
        assert station_regen(gemengd, 0.1, NU_S)["station"] == "Hupsel"

    def test_oude_meting_telt_niet(self):
        oud = _knmi(waargenomen_op=(NU - timedelta(minutes=45)).isoformat())
        assert station_regen(oud, 0.1, NU_S) is None
        assert station_regen(_knmi(waargenomen_op=None), 0.1, NU_S) is None

    def test_sneeuw_en_onweercodes_tellen_niet(self):
        for code in (71, 95, 45):
            assert station_regen(_knmi(weercode=code, neerslag_intensiteit=0.0), 0.1, NU_S) is None
        regen = station_regen(_knmi(weercode=61, neerslag_intensiteit=0.0), 0.1, NU_S)
        assert regen is not None and regen["motregen"] is False

    def test_bright_sky(self):
        bs = {
            "bron": "brightsky",
            "waargenomen_op": (NU - timedelta(minutes=10)).isoformat(),
            "neerslag": 0.05,  # mm per 10 minuten = 0,3 mm/u
            "station": "Ahaus",
            "station_afstand_km": 8.0,
        }
        st = station_regen(bs, 0.1, NU_S)
        assert st is not None and st["intensiteit"] == 0.3 and st["station"] == "Ahaus"

    def test_geen_meting(self):
        assert station_regen(None, 0.1, NU_S) is None
        assert station_regen({}, 0.1, NU_S) is None


class TestRegenbeeldMetStation:
    def test_droog_wordt_motregen(self):
        radar = _radar()
        assert regenbeeld(radar) == "Droog, komende 2 uur geen regen."
        data = met_station_regen(radar, station_regen(_knmi(), 0.1, NU_S))
        assert data["regent"] is True and data["regen_bron"] == "station"
        assert data["stopt_over"] is None
        assert regenbeeld(data) == "Lichte motregen (station Hupsel), radar droog."

    def test_intensiteit_in_de_zin(self):
        data = met_station_regen(
            _radar(), station_regen(_knmi(neerslag_intensiteit=0.51), 0.1, NU_S)
        )
        assert regenbeeld(data) == "Lichte motregen (station Hupsel, 0,5 mm/u), radar droog."

    def test_radarbui_blijft_staan(self):
        reeks = [(m, 1.2 if 25 <= m <= 50 else 0.0) for m in range(-10, 125, 5)]
        radar = _radar(reeks)
        data = met_station_regen(radar, station_regen(_knmi(), 0.1, NU_S))
        # begint_over (meldingen, validatie) ongewijzigd; de bui is de volgende
        assert data["begint_over"] == 25 and data["volgende_bui_over"] == 25
        assert begin_weergave(data) == 25
        assert regenbeeld(data) == (
            "Lichte motregen (station Hupsel), radar droog; "
            "over 25 min een bui (licht, tot 1,2 mm/u)."
        )

    def test_radarregen_ongewijzigd(self):
        reeks = [(m, 2.0 if m <= 30 else 0.0) for m in range(-10, 125, 5)]
        radar = _radar(reeks)
        data = met_station_regen(radar, station_regen(_knmi(), 0.1, NU_S))
        assert data["regen_bron"] == "radar" and data["station_regen"] is None
        assert {k: v for k, v in data.items() if k not in ("regen_bron", "station_regen")} == radar
        assert regenbeeld(data) == regenbeeld(radar)

    def test_zonder_station_alleen_extra_velden(self):
        radar = _radar()
        data = met_station_regen(radar, None)
        assert data["regent"] is False and data["regen_bron"] is None
        assert data["station_regen"] is None


class TestAansluitingStation:
    def test_knmi_meting_geeft_neerslagstation(self):
        tijden = ["2026-11-01T21:40:00Z", "2026-11-01T21:50:00Z"]

        def cov(station, br, le, **waarden):
            return {
                "type": "Coverage",
                "eumetnet:locationId": station,
                "domain": {"axes": {"x": {"values": [le]}, "y": {"values": [br]},
                                    "t": {"values": tijden}}},
                "ranges": {p: {"type": "NdArray", "values": v} for p, v in waarden.items()},
            }

        data = metingen(
            [cov("06283", 52.068, 6.657, ta=[9.0, 9.0], rg=[0.0, 0.01], ww=[51, 51])],
            52.1, 6.65, {"06283": "Hupsel"},
        )
        assert data["neerslag_station"] == "Hupsel"
        assert data["neerslag_station_afstand_km"] is not None
        assert station_regen(data, 0.1, datetime(2026, 11, 1, 21, 55, tzinfo=timezone.utc).timestamp())

    def test_rain_coordinator_gebruikt_station(self):
        rain = (BRON / "rain.py").read_text(encoding="utf-8")
        assert 'station_regen(getattr(self.meting, "data", None), drempel, nu)' in rain
        assert "data = met_station_regen(data, station)" in rain
        assert '"regen_bron": "station"' in rain  # validatie: regen (station)
        assert "regen.meting = meting" in (BRON / "__init__.py").read_text(encoding="utf-8")

    def test_constanten(self):
        assert const.STATION_REGEN_MAX_KM == 10.0
        assert 51 in const.STATION_REGEN_CODES and 57 in const.STATION_REGEN_CODES
        assert 67 in const.STATION_REGEN_CODES and 68 not in const.STATION_REGEN_CODES


def test_versie_0610():
    versie = json.loads((BRON / "manifest.json").read_text())["version"]
    assert tuple(int(d) for d in versie.split(".")) >= (0, 61, 0)
