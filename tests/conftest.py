"""Gedeelde opzet voor de tests.

De modules cel, indices, taal en validatie zijn bewust vrij van Home
Assistant-imports, zodat ze zonder die hele installatie te testen zijn. Dat
maakt de suite snel genoeg om bij elke wijziging te draaien.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "stormchase"))
