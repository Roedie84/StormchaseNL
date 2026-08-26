"""Waarden opzoeken in reeksen met verschillende tijdstappen."""

from datetime import datetime, timedelta, timezone

import pytest

from tijd import MARGE_KWARTIER, aantal_gevuld, dichtstbijzijnde, op_stempel

NU = datetime(2026, 8, 22, 14, 20, tzinfo=timezone.utc)


def reeks(start_uur, stap_uren, aantal, waarden=None):
    """Bouw tijdstempels met een vaste stap."""
    basis = NU.replace(hour=start_uur, minute=0)
    tijden = [
        (basis + timedelta(hours=stap_uren * i)).strftime("%Y-%m-%dT%H:%M")
        for i in range(aantal)
    ]
    return tijden, waarden if waarden is not None else list(range(aantal))


class TestExact:
    def test_treffer(self):
        tijden, waarden = reeks(12, 1, 6)
        assert op_stempel(tijden, waarden, "2026-08-22T14:00") == 2

    def test_geen_treffer(self):
        tijden, waarden = reeks(12, 3, 4)
        assert op_stempel(tijden, waarden, "2026-08-22T14:00") is None


class TestDichtstbijzijnde:
    def test_uurstappen(self):
        tijden, waarden = reeks(12, 1, 6)
        assert dichtstbijzijnde(tijden, waarden, NU) == 2

    def test_driewaardige_stappen(self):
        """Een model met stappen van drie uur mag niet leeg opleveren.

        Dit was het geval bij de Lifted Index: de bron slaagde maar zoeken op
        een exact uur vond nooit iets.
        """
        tijden, waarden = reeks(6, 3, 8)
        assert dichtstbijzijnde(tijden, waarden, NU) == 3  # 15:00 ligt het dichtst

    def test_buiten_de_marge(self):
        tijden, waarden = reeks(0, 1, 3)  # tot 02:00, ver van 14:20
        assert dichtstbijzijnde(tijden, waarden, NU) is None

    def test_lege_waarden_overslaan(self):
        """Een lege waarde mag een bruikbare iets verderop niet verdringen."""
        tijden, _ = reeks(12, 1, 6)
        waarden = [0, 1, None, 3, 4, 5]
        assert dichtstbijzijnde(tijden, waarden, NU) == 3

    def test_alles_leeg(self):
        tijden, _ = reeks(12, 1, 6)
        assert dichtstbijzijnde(tijden, [None] * 6, NU) is None

    def test_kwartiermarge_is_strenger(self):
        """Voor kwartierwaarden telt alleen wat echt dichtbij ligt."""
        tijden, waarden = reeks(12, 1, 6)
        assert dichtstbijzijnde(tijden, waarden, NU, MARGE_KWARTIER) is None

    def test_zonder_tijdzone_in_de_reeks(self):
        """Modellen leveren vaak lokale tijd zonder zone erbij."""
        tijden = ["2026-08-22T14:00", "2026-08-22T15:00"]
        assert dichtstbijzijnde(tijden, [7, 8], NU) == 7

    def test_onleesbare_tijdstempel(self):
        assert dichtstbijzijnde(["geen tijd"], [1], NU) is None

    def test_lege_reeks(self):
        assert dichtstbijzijnde([], [], NU) is None


class TestAantalGevuld:
    @pytest.mark.parametrize(
        "waarden,verwacht",
        [([1, 2, None, 4], 3), ([None, None], 0), ([], 0), (None, 0)],
    )
    def test_tellen(self, waarden, verwacht):
        assert aantal_gevuld(waarden) == verwacht
