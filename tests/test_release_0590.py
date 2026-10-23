"""0.59.0 (L-SC-017): windstootverwachting bijsturen met de fout van het laatste uur.

Leerronde: de bijgestelde verwachting loopt ~een half uur achter op de
meting (te hoog bij afnemende, te laag bij toenemende wind). De helft van de
laatste fout gaat bij de komende stoten, begrensd op +-15 km/u en aflopend
naar 0 over drie uur. Replay 10 dagen (238 uur): uurfout 2,52 -> 2,24 km/u.
"""

from __future__ import annotations

import json
from pathlib import Path

import const
from windcorrectie import Windcorrectie, bijsturing

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
T0 = 1_760_000_000.0  # willekeurig, ver genoeg van alles
STAP = 600.0


def _geleerd(uren: float = 7.0, model: float = 40.0, ratio: float = 0.6) -> tuple[Windcorrectie, float]:
    """Rustige paren met een vaste verhouding: factor 0,6."""
    wc = Windcorrectie()
    t = T0
    for _ in range(int(uren * 3600 / STAP)):
        assert wc.bij(t, model * ratio, model, t)
        t += STAP
    return wc, t


def _basis(wc, nu, model=40.0):
    """De bijgestelde waarde zonder bijsturing."""
    factor = wc.corrigeer(model, nu)["factor"]
    return round(model * factor, 1)


class TestBijsturing:
    def test_afnemende_wind_omlaag(self):
        wc, t = _geleerd()
        # verwacht 40 x 0,6 = 24, gemeten 18: fout -6, bijsturing -3
        wc.bij(t, 18.0, 40.0, t)
        uit = wc.corrigeer(40.0, t)
        assert uit["factor"] == 0.6
        assert uit["bijsturing_fout"] == -6.0
        assert uit["bijsturing"] == -3.0
        assert uit["waarde"] == 21.0

    def test_toenemende_wind_omhoog(self):
        wc, t = _geleerd()
        wc.bij(t, 32.0, 40.0, t)  # fout +8
        uit = wc.corrigeer(40.0, t)
        assert uit["bijsturing"] == 4.0
        assert uit["waarde"] == 28.0

    def test_begrensd(self):
        wc, t = _geleerd()
        wc.bij(t, 80.0, 40.0, t)  # fout +56 -> +28, begrensd op +15
        uit = wc.corrigeer(40.0, t)
        assert uit["bijsturing"] == const.WINDBIJSTURING_MAX_KMH == 15.0
        assert uit["waarde"] == 24.0 + 15.0
        neer = bijsturing((t, 0.0, 100.0), t, 0.6)  # fout -60 -> -15
        assert neer["kmh"] == -15.0

    def test_neemt_af_naar_nul(self):
        wc, t = _geleerd()
        wc.bij(t, 32.0, 40.0, t)  # start +4
        uren = [(t + 3600 * i, 40.0) for i in range(1, 5)]
        uit = dict(wc.bijgestuurde_uren(uren, t, 0.6))
        assert uit[t + 3600] > uit[t + 7200] > uit[t + 10800]
        assert uit[t + 3600] == round(24 + 4 * 2 / 3, 1)
        assert uit[t + 10800] == 24.0 and uit[t + 14400] == 24.0
        # de bijsturing op 'nu' loopt ook af met de leeftijd van de meting
        assert 0 < wc.bijsturing(t + 1800, 0.6)["kmh"] < 4.0

    def test_ontbrekende_meting_geen_bijsturing(self):
        wc, t = _geleerd()
        wc.bij(t, 32.0, 40.0, t)
        # geen nieuwe meting: na een uur geen bijsturing meer
        later = t + const.WINDBIJSTURING_MAX_LEEFTIJD_S + 60
        assert wc.bij(later, None, 40.0, later) is False
        uit = wc.corrigeer(40.0, later)
        assert uit["bijsturing"] == 0.0 and uit["bijsturing_fout"] is None
        assert uit["waarde"] == _basis(wc, later)
        # nooit een meting gehad
        assert bijsturing(None, t)["kmh"] == 0.0
        assert Windcorrectie().corrigeer(40.0, t)["waarde"] == 40.0

    def test_zonder_factor_kaal_model(self):
        wc = Windcorrectie()
        wc.bij(T0, 10.0, 40.0, T0)
        uit = wc.corrigeer(40.0, T0)
        assert uit["factor"] is None and uit["waarde"] == 40.0
        assert uit["bijsturing"] == 0.0

    def test_laatste_meting_overleeft_herstart(self):
        wc, t = _geleerd()
        wc.bij(t, 32.0, 40.0, t)
        terug = Windcorrectie(wc.naar_opslag())
        assert terug.corrigeer(40.0, t) == wc.corrigeer(40.0, t)


def test_manifest_versie():
    manifest = json.loads((BRON / "manifest.json").read_text())
    assert tuple(int(x) for x in manifest["version"].split(".")) >= (0, 59, 0)
