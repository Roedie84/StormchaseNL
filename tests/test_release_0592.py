"""0.59.2: windstootfactor valt niet weg tijdens een lang front, en de
radar-vooruitblik noemt de tijd van het getoonde beeld (L-SC-018).

Leerronde 24-10: na een front van ~18 uur had het 24-uursvenster om 03:24
minder dan zes uur rustige paren. De factor (0,70) viel weg en de sensor
sprong van 43 naar het kale model 64 km/u, bij 35 km/u gemeten.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

from vooruitblik import gebouwde_stand  # noqa: E402
from windcorrectie import Windcorrectie  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BRON = ROOT / "custom_components" / "stormchase"
T0 = 1_760_000_000.0
STAP = 600.0


def _rustig(wc: Windcorrectie, t: float, uren: float, model=60.0, ratio=0.7) -> float:
    for _ in range(int(uren * 3600 / STAP)):
        assert wc.bij(t, round(model * ratio, 1), model, t)
        t += STAP
    return t


def _front(wc: Windcorrectie, t: float, uren: float, model=60.0, gemeten=40.0) -> float:
    for _ in range(int(uren * 3600 / STAP)):
        assert wc.bij(t, gemeten, model, t, druk_1u=1.6)
        t += STAP
    return t


class TestLangFront:
    def test_factor_blijft_na_18_uur_front(self):
        wc = Windcorrectie()
        t = _rustig(wc, T0, 12.0)
        t = _front(wc, t, 20.0)
        nu = t - STAP
        assert wc.factor(nu)[0] is None  # 24 uur: te weinig rustig
        uit = wc.corrigeer(64.4, nu)
        assert uit["toegepast"] is True
        assert uit["factor"] == 0.7
        assert uit["factor_bron"] in ("72 uur (front)", "tijdvak")
        assert uit["waarde"] < 50  # niet het kale model
        assert uit["front"] is True

    def test_zonder_front_blijft_de_oude_regel(self):
        """Te weinig rustig in 24 uur, maar het laatste paar is rustig: geen
        terugval op 72 uur (alleen een gat in de metingen)."""
        wc = Windcorrectie()
        t = _rustig(wc, T0, 8.0)
        t = _rustig(wc, t + 30 * 3600, 2.0)
        nu = t - STAP
        uit = wc.corrigeer(50.0, nu)
        assert uit["factor"] is None and uit["waarde"] == 50.0

    def test_bij_de_start_geen_factor_tijdens_een_front(self):
        """Nooit zes uur rustig gehad: kaal model, zoals voorheen."""
        wc = Windcorrectie()
        t = _rustig(wc, T0, 3.0)
        t = _front(wc, t, 4.0)
        uit = wc.corrigeer(64.0, t - STAP)
        assert uit["factor"] is None and uit["waarde"] == 64.0
        assert uit["factor_bron"] is None

    def test_front_leert_nog_steeds_niet(self):
        wc = Windcorrectie()
        t = _rustig(wc, T0, 10.0, ratio=0.7)
        t = _front(wc, t, 20.0, gemeten=20.0)  # verhouding 0,33 in het front
        assert wc.factor_tijdens_front(t - STAP)[0] == 0.7

    def test_uitleg_op_de_sensor(self):
        bron = (BRON / "sensor.py").read_text(encoding="utf-8")
        assert '"72 uur (front)"' in bron
        assert "72 uur (front)" in (BRON / "windcorrectie.py").read_text(encoding="utf-8")


def _ts(uur: int, minuut: int) -> int:
    return int(datetime(2026, 10, 23, uur, minuut, tzinfo=timezone.utc).timestamp())


class TestVooruitblikStand:
    def test_verouderd_zonder_kijker(self):
        """23-10: gebouwd 13:45Z, coördinator al op 17:35Z."""
        status, ref = gebouwde_stand("actueel", _ts(13, 45), _ts(17, 35), False)
        assert status == "verouderd (geen kijker)"
        assert ref == "2026-10-23T13:45:00+00:00"

    def test_wordt_bijgewerkt(self):
        status, _ = gebouwde_stand("actueel", _ts(13, 45), _ts(17, 35), True)
        assert status == "wordt bijgewerkt"

    def test_actueel_als_het_dezelfde_ronde_is(self):
        status, ref = gebouwde_stand("actueel", _ts(17, 35), _ts(17, 35), False)
        assert status == "actueel" and ref.startswith("2026-10-23T17:35")

    def test_foutstatus_blijft_staan(self):
        assert gebouwde_stand("bouwen mislukt", _ts(13, 45), _ts(17, 35), False)[0] == "bouwen mislukt"
        assert gebouwde_stand("wacht op radarbeeld", None, _ts(17, 35), False) == (
            "wacht op radarbeeld", None
        )

    def test_attributen_in_image(self):
        bron = (BRON / "image.py").read_text(encoding="utf-8")
        assert "gebouwde_stand(" in bron
        assert '"referentie_beschikbaar"' in bron


def test_versie_en_changelog():
    manifest = json.loads((BRON / "manifest.json").read_text())
    assert tuple(int(x) for x in manifest["version"].split(".")) >= (0, 59, 2)
    assert "## [0.59.2]" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
