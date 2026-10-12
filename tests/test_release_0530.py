"""0.53.0 (L-SC-008 optie c): windmelding kijkt ook naar de stationsmeting.

De bijstelling haalt de modelwindstoot bij rustig weer terecht omlaag
(factor ~0,55-0,7). Bij een harde (convectieve) stoot zat de bijgestelde
waarde juist te laag: 10-10 11:40 model 37,1, bijgesteld 23,4, gemeten 39,3;
bij gemeten >= 33 km/u gemiddeld -6,5 km/u. Voor de windmelding telt daarom
de hoogste van de bijgestelde verwachting en een verse stationsmeting.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))

import const  # noqa: E402
from windcorrectie import Windcorrectie, voor_melding  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BRON = ROOT / "custom_components" / "stormchase"
NU = 1_791_800_000.0


class TestVoorMelding:
    def test_station_boven_bijgesteld_telt(self):
        uit = voor_melding(45.0, 62.0, NU - 600, NU)
        assert uit["waarde"] == 62.0 and uit["bron"] == "station"
        assert uit["verwachting"] == 45.0 and uit["gemeten"] == 62.0

    def test_bijgesteld_boven_station_telt(self):
        uit = voor_melding(64.0, 40.0, NU - 600, NU)
        assert uit["waarde"] == 64.0 and uit["bron"] == "verwachting"

    def test_gelijk_blijft_verwachting(self):
        assert voor_melding(50.0, 50.0, NU - 600, NU)["bron"] == "verwachting"

    def test_oude_meting_telt_niet(self):
        oud = NU - const.WIND_MELDING_STATION_MAX_S - 1
        uit = voor_melding(45.0, 80.0, oud, NU)
        assert uit["waarde"] == 45.0 and uit["bron"] == "verwachting"
        assert uit["gemeten"] is None

    def test_meting_op_de_grens_telt_nog(self):
        grens = NU - const.WIND_MELDING_STATION_MAX_S
        assert voor_melding(45.0, 80.0, grens, NU)["bron"] == "station"

    def test_meting_ver_in_de_toekomst_telt_niet(self):
        assert voor_melding(45.0, 80.0, NU + 3600, NU)["bron"] == "verwachting"

    def test_zonder_verwachting_alleen_station(self):
        uit = voor_melding(None, 30.0, NU - 60, NU)
        assert uit["waarde"] == 30.0 and uit["bron"] == "station"

    def test_niets_bekend(self):
        uit = voor_melding(None, None, None, NU)
        assert uit["waarde"] is None and uit["bron"] is None

    def test_rommel_geeft_geen_fout(self):
        uit = voor_melding("x", "y", "z", NU)
        assert uit["waarde"] is None
        assert voor_melding(40.0, -5.0, NU, NU)["bron"] == "verwachting"

    def test_constante_veertig_minuten(self):
        assert const.WIND_MELDING_STATION_MAX_S == 40 * 60


class TestBijstellingDuwtStootNietOnderDrempel:
    """Rustige dag leert ~0,55; daarna een harde bui met 65 km/u gemeten."""

    def test_harde_stoot_na_rustige_dag(self):
        wc = Windcorrectie()
        t = NU - 8 * 3600
        while t <= NU - 600:
            wc.bij(t, 22.0, 40.0, t - 120)  # verhouding 0,55
            t += 600
        bijgesteld = wc.corrigeer(80.0, NU)
        assert bijgesteld["toegepast"] and bijgesteld["waarde"] < 60
        drempel = const.DEFAULT_WIND_THRESHOLD
        melding = voor_melding(bijgesteld["waarde"], 65.0, NU - 600, NU)
        assert melding["waarde"] >= drempel and melding["bron"] == "station"
        # de bijgestelde sensorwaarde zelf verandert niet
        assert wc.corrigeer(80.0, NU)["waarde"] == bijgesteld["waarde"]


class TestKoppeling:
    def test_coordinator_gebruikt_windmelding(self):
        code = (BRON / "coordinator.py").read_text(encoding="utf-8")
        assert "from .windcorrectie import voor_melding" in code
        assert 'self._controleer_wind(windmelding["waarde"], windmelding["bron"])' in code
        assert 'self._controleer_wind(wind["waarde"])' not in code
        assert '"windmelding": windmelding' in code
        assert re.search(r'EVENT_WIND,\s*\{"windstoten": windstoten, "drempel": drempel, "bron": bron\}', code)

    def test_stationsmeting_gaat_naar_de_melding(self):
        init = (BRON / "__init__.py").read_text(encoding="utf-8")
        assert "meteo.meld_gemeten_wind(" in init
        # voor de bijstelling, zodat ook een meting zonder paar meetelt
        assert init.index("meteo.meld_gemeten_wind(") < init.index("if windcorrectie.bij(")

    def test_sensor_attributen(self):
        sensor = (BRON / "sensor.py").read_text(encoding="utf-8")
        assert '"windstoten_melding"' in sensor and '"melding_bron"' in sensor

    def test_bericht_noemt_station(self):
        notifier = (BRON / "notifier.py").read_text(encoding="utf-8")
        assert 'event.data.get("bron") == "station"' in notifier
        assert "gemeten" in notifier

    def test_versie_en_changelog(self):
        # 0.54.0 en later: de versie loopt door, de changelog-regel blijft
        manifest = json.loads((BRON / "manifest.json").read_text(encoding="utf-8"))
        assert tuple(int(x) for x in manifest["version"].split(".")) >= (0, 53, 0)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "## [0.53.0]" in changelog
