"""0.44.0: het radarbeeld ververst bij elk nieuw frame.

Live op 8 oktober: `image.stormchase_radar` stond 4,7 uur op dezelfde
tijdstempel (23:05:28) terwijl het radarframe elke 10 minuten nieuw was. Het
kenmerk las `data["path"]`; het frame staat onder `data["radar"]`.
"""

import ast
from pathlib import Path

from radar import beeldkenmerk

BRON = Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"
POS = (52.1, 6.6)


def _data(radar_pad="/v2/radar/1000", tijd=1000, sat_pad="/v2/sat/1000"):
    return {
        "radar": {"host": "https://tilecache.rainviewer.com", "path": radar_pad, "tijd": tijd},
        "satelliet": {"host": "https://tilecache.rainviewer.com", "path": sat_pad, "tijd": tijd},
    }


def test_een_nieuw_radarframe_is_een_nieuw_kenmerk():
    oud = beeldkenmerk(_data(), 0, POS)
    nieuw = beeldkenmerk(_data(radar_pad="/v2/radar/1600", tijd=1600), 0, POS)
    assert oud != nieuw


def test_een_nieuw_wolkenbeeld_is_een_nieuw_kenmerk():
    assert beeldkenmerk(_data(), 0, POS) != beeldkenmerk(_data(sat_pad="/v2/sat/1600"), 0, POS)


def test_hetzelfde_frame_hetzelfde_kenmerk():
    assert beeldkenmerk(_data(), 3, POS) == beeldkenmerk(_data(), 3, POS)


def test_inslagen_en_positie_tellen_nog_steeds():
    basis = beeldkenmerk(_data(), 0, POS)
    assert beeldkenmerk(_data(), 1, POS) != basis
    assert beeldkenmerk(_data(), 0, (52.2, 6.6)) != basis


def test_zonder_gegevens_geen_fout():
    assert beeldkenmerk(None, 0, POS)[:3] == (None, None, None)
    assert beeldkenmerk({"radar": None}, 0, POS)[:3] == (None, None, None)


def test_het_beeld_gebruikt_het_kenmerk():
    """Het oude kenmerk (`frame.get("path")` op het hoogste niveau) is weg."""
    bron = (BRON / "image.py").read_text()
    boom = ast.parse(bron)
    methode = next(
        n for n in ast.walk(boom)
        if isinstance(n, ast.FunctionDef) and n.name == "_handle_coordinator_update"
    )
    tekst = ast.get_source_segment(bron, methode)
    assert "beeldkenmerk(self.coordinator.data" in tekst
    assert 'frame.get("path")' not in tekst
