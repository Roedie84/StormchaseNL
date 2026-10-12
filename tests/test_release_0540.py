"""0.54.0 (L-SC-010): windstootfactor per tijd van de dag.

Met één factor over 24 uur zat de bijgestelde windstoot 's nachts ~+5 km/u
te hoog en overdag ~-3 km/u te laag (H-SC-7, drie nachten op rij). Nu telt de
mediaan van de rustige paren uit hetzelfde tijdvak van de dag (+-2 uur) over
72 uur, met de 24-uursfactor als terugval bij minder dan vier paren.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

import const  # noqa: E402
from windcorrectie import BEWAAR_S, Windcorrectie  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BRON = ROOT / "custom_components" / "stormchase"
AMS = timezone(timedelta(hours=2))  # zomertijd, genoeg voor de test
START = datetime(2026, 10, 9, 12, 0, tzinfo=AMS).timestamp()


def _nacht(t: float, tz=AMS) -> bool:
    uur = datetime.fromtimestamp(t, tz).hour
    return uur >= 22 or uur < 8


def _vul(wc: Windcorrectie, uren: int, dag=0.8, nacht=0.5, model=30.0) -> float:
    """Elke 10 minuten een paar; 's nachts een lagere verhouding."""
    t = START
    for _ in range(uren * 6):
        r = nacht if _nacht(t) else dag
        assert wc.bij(t, round(model * r, 1), model, t)
        t += 600
    return t - 600


class TestTijdvak:
    def test_nacht_krijgt_nachtfactor(self):
        wc = Windcorrectie(tijdzone=AMS)
        _vul(wc, 72)  # 09-10 12:00 tot 12-10 11:50
        nu = datetime(2026, 10, 12, 3, 0, tzinfo=AMS).timestamp()
        uit = wc.corrigeer(40.0, nu)
        assert uit["factor_bron"] == "tijdvak"
        assert uit["factor"] == 0.5
        assert uit["waarde"] == 20.0
        assert uit["factor_24u"] is not None and uit["factor_24u"] > 0.5

    def test_dag_krijgt_dagfactor(self):
        wc = Windcorrectie(tijdzone=AMS)
        laatste = _vul(wc, 72)
        uit = wc.corrigeer(40.0, laatste)  # 11:50 's ochtends
        assert uit["factor_bron"] == "tijdvak" and uit["factor"] == 0.8
        assert uit["paren_tijdvak"] >= const.WINDCORRECTIE_TIJDVAK_MIN_PAREN

    def test_uur_van_de_dag_in_de_tijdzone_van_ha(self):
        # Dezelfde paren; in UTC valt 'nacht' twee uur anders dan in Amsterdam.
        wc = Windcorrectie(tijdzone=AMS)
        laatste = _vul(wc, 72)
        nu = datetime(2026, 10, 12, 5, 0, tzinfo=AMS).timestamp()
        assert wc.factor_tijdvak(nu)[0] == 0.5
        assert wc._seconde_van_de_dag(nu) == 5 * 3600
        utc = Windcorrectie(tijdzone=timezone.utc)
        assert utc._seconde_van_de_dag(nu) == 3 * 3600
        assert laatste > nu

    def test_te_weinig_in_het_tijdvak_dan_24_uursfactor(self):
        wc = Windcorrectie(tijdzone=AMS)
        t = datetime(2026, 10, 12, 8, 0, tzinfo=AMS).timestamp()
        # acht uur aan paren 08-16 u: het tijdvak rond 02 u is leeg
        for i in range(48):
            wc.bij(t + i * 600, 21.0, 30.0, t + i * 600)
        nu = t + 47 * 600
        factor_24u, _ = wc.factor(nu)
        assert factor_24u == 0.7
        # Om 02 u 's nachts erna: tijdvak heeft niets, terugval op 24 uur
        nacht = datetime(2026, 10, 13, 2, 0, tzinfo=AMS).timestamp()
        uit = wc.corrigeer(40.0, nacht)
        assert uit["paren_tijdvak"] < const.WINDCORRECTIE_TIJDVAK_MIN_PAREN
        assert uit["factor_bron"] in ("24 uur", None)

    def test_zonder_24_uursfactor_geen_tijdvakfactor(self):
        # Te kort geleerd (< 6 uur): modelwaarde blijft staan, ook al zijn er
        # vier paren in het tijdvak.
        wc = Windcorrectie(tijdzone=AMS)
        t = START
        for i in range(6):
            wc.bij(t + i * 600, 15.0, 30.0, t + i * 600)
        uit = wc.corrigeer(40.0, t + 3600)
        assert uit["factor"] is None and uit["waarde"] == 40.0
        assert uit["toegepast"] is False and uit["factor_bron"] is None

    def test_grenzen_blijven(self):
        wc = Windcorrectie(tijdzone=AMS)
        laatste = _vul(wc, 72, dag=0.2, nacht=0.2)
        assert wc.corrigeer(40.0, laatste)["factor"] == 0.5
        hoog = Windcorrectie(tijdzone=AMS)
        laatste = _vul(hoog, 72, dag=2.0, nacht=2.0, model=20.0)
        assert hoog.corrigeer(40.0, laatste)["factor"] == 1.3

    def test_frontparen_tellen_niet_in_het_tijdvak(self):
        wc = Windcorrectie(tijdzone=AMS)
        laatste = _vul(wc, 72)
        # Een front op het laatste uur met een hele andere verhouding
        for i in range(1, 7):
            t = laatste + i * 600
            wc.bij(t, 30.0, 30.0, t, onweer=True)
        uit = wc.corrigeer(40.0, laatste + 3600)
        assert uit["factor"] == 0.8

    def test_72_uur_wordt_bewaard(self):
        assert BEWAAR_S >= const.WINDCORRECTIE_TIJDVAK_VENSTER_S
        wc = Windcorrectie(tijdzone=AMS)
        laatste = _vul(wc, 80)
        assert wc.paren[0][0] <= laatste - const.WINDCORRECTIE_TIJDVAK_VENSTER_S
        terug = Windcorrectie(wc.naar_opslag(), tijdzone=AMS)
        assert terug.corrigeer(40.0, laatste) == wc.corrigeer(40.0, laatste)

    def test_tijdvak_over_middernacht(self):
        wc = Windcorrectie(tijdzone=AMS)
        _vul(wc, 72)
        nu = datetime(2026, 10, 12, 0, 30, tzinfo=AMS).timestamp()
        # 22:30-02:30 is helemaal nacht
        assert wc.factor_tijdvak(nu)[0] == 0.5


class TestKoppeling:
    def test_ha_tijdzone_wordt_meegegeven(self):
        init = (BRON / "__init__.py").read_text()
        assert "tijdzone=_dt.get_default_time_zone()" in init

    def test_attributen_op_de_sensor(self):
        sensor = (BRON / "sensor.py").read_text()
        for sleutel in ('"factor_bron"', '"correctiefactor_24u"', '"paren_tijdvak"'):
            assert sleutel in sensor

    def test_versie(self):
        import json

        manifest = json.loads((BRON / "manifest.json").read_text())
        assert tuple(int(x) for x in manifest["version"].split(".")) >= (0, 54, 0)
        assert "## [0.54.0]" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
