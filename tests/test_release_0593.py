"""0.59.3 (L-SC-021): de windstootfactor valt ook NA een lang front niet weg.

Leerronde 24-10 15:40: het front eindigde om ~12:53. Het 24-uursvenster had
126 front-/naloopparen en 2,7 uur rustig; de factor viel weg en het kale model
zat er +6,6 km/u naast (MAE 7,7, n=16) tegen -0,6 (MAE 2,0, n=7) ervoor.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

from const import FRONT_NALOOP_S  # noqa: E402
from windcorrectie import Windcorrectie  # noqa: E402

T0 = 1_760_000_000.0
STAP = 600.0


def _rustig(wc, t, uren, model=60.0, ratio=0.7):
    for _ in range(int(uren * 3600 / STAP)):
        assert wc.bij(t, round(model * ratio, 1), model, t)
        t += STAP
    return t


def _front(wc, t, uren, model=60.0, gemeten=40.0):
    for _ in range(int(uren * 3600 / STAP)):
        assert wc.bij(t, gemeten, model, t, druk_1u=1.6)
        t += STAP
    return t


def _na_front(uren_rustig):
    wc = Windcorrectie()
    t = _rustig(wc, T0, 12.0)
    t = _front(wc, t, 22.0)
    t = _rustig(wc, t, uren_rustig)
    return wc, t - STAP


def test_factor_blijft_na_het_front():
    wc, nu = _na_front(FRONT_NALOOP_S / 3600 + 2.7)
    assert wc.factor(nu)[0] is None  # 24 uur: nog geen zes uur rustig
    uit = wc.corrigeer(48.2, nu)
    assert uit["front"] is False
    assert uit["toegepast"] is True
    assert uit["factor"] == 0.7
    assert uit["waarde"] < 40  # niet het kale model 48,2


def test_na_zes_uur_rustig_weer_de_24_uursfactor():
    wc, nu = _na_front(FRONT_NALOOP_S / 3600 + 7.0)
    assert wc.factor(nu)[0] == 0.7
    assert wc.corrigeer(50.0, nu)["factor_bron"] in ("24 uur", "tijdvak")


def test_meetgat_zonder_front_ongewijzigd():
    wc = Windcorrectie()
    t = _rustig(wc, T0, 8.0)
    t = _rustig(wc, t + 30 * 3600, 2.0)
    uit = wc.corrigeer(50.0, t - STAP)
    assert uit["factor"] is None and uit["waarde"] == 50.0


def test_front_buiten_het_venster_telt_niet():
    """Front ouder dan 24 uur en daarna een meetgat: geen terugval."""
    wc = Windcorrectie()
    t = _rustig(wc, T0, 10.0)
    t = _front(wc, t, 3.0)
    t = _rustig(wc, t + 26 * 3600, 2.0)
    uit = wc.corrigeer(50.0, t - STAP)
    assert uit["factor"] is None and uit["waarde"] == 50.0
