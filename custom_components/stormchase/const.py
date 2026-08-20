"""Constanten voor de Stormchase integratie."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "stormchase"

# Configuratie — bronsensoren
CONF_DISTANCE_SENSOR = "distance_sensor"
CONF_AZIMUTH_SENSOR = "azimuth_sensor"
CONF_COUNTER_SENSOR = "counter_sensor"
CONF_GEO_PATTERN = "geo_pattern"

# Configuratie — afstanden
CONF_WARN_DISTANCE = "warn_distance"
CONF_RING_NEAR = "ring_near"
CONF_RING_MID = "ring_mid"
CONF_RING_FAR = "ring_far"

# Configuratie — locatie
CONF_LOCATION_MODE = "location_mode"
CONF_ZONE_ENTITY = "zone_entity"
CONF_TRACKER_ENTITY = "tracker_entity"
CONF_MANUAL_LOCATION = "manual_location"

MODE_HOME = "home"
MODE_ZONE = "zone"
MODE_TRACKER = "tracker"
MODE_MANUAL = "manual"
LOCATION_MODES = [MODE_HOME, MODE_ZONE, MODE_TRACKER, MODE_MANUAL]

# Standaardwaarden
DEFAULT_GEO_PATTERN = "lightning_strike"
DEFAULT_WARN_DISTANCE = 15
DEFAULT_RING_NEAR = 10
DEFAULT_RING_MID = 25
DEFAULT_RING_FAR = 50

# Update-intervallen
STORM_INTERVAL = timedelta(seconds=30)
METEO_INTERVAL = timedelta(minutes=30)

# Venster waarover de naderingssnelheid wordt berekend
TREND_WINDOW = timedelta(minutes=15)
# Minimaal aantal metingen voordat een snelheid betekenis heeft
MIN_SAMPLES = 4
# Onder deze snelheid (km/u) noemen we het stabiel in plaats van nadering
SPEED_DEADZONE = 1.0
# Verplaats je verder dan dit, dan worden de weerparameters direct opnieuw
# opgehaald in plaats van te wachten op het volgende interval
MOVE_THRESHOLD_KM = 15

# Frontend / dashboardstrategie
STRATEGY_FILE = "stormchase-strategy.js"
STRATEGY_URL = f"/{DOMAIN}/{STRATEGY_FILE}"

# Open-Meteo
METEO_URL = "https://api.open-meteo.com/v1/forecast"
METEO_HOURLY = "cape,lifted_index,convective_inhibition"

# Events voor automatiseringen
EVENT_NEARBY = f"{DOMAIN}_nearby"
EVENT_APPROACHING = f"{DOMAIN}_approaching"
EVENT_CLEARED = f"{DOMAIN}_cleared"
# Onweer geldt als weggetrokken zodra de afstand hierboven uitkomt
CLEARED_FACTOR = 1.5

# Trendteksten (Nederlands, sluit aan op de rest van het dashboard)
TREND_FAST_APPROACH = "nadert snel"
TREND_APPROACH = "nadert"
TREND_STABLE = "stabiel"
TREND_RECEDE = "trekt weg"
TREND_FAST_RECEDE = "trekt snel weg"
TREND_UNKNOWN = "onbekend"
