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

# Configuratie - waarschuwingen
CONF_ALERT_COUNTRY = "alert_country"
CONF_ALERT_REGION = "alert_region"
CONF_ALERT_NOTIFY = "alert_notify"
CONF_ALERT_MIN_LEVEL = "alert_min_level"

ALERT_INTERVAL = timedelta(minutes=15)
METEOALARM_URL = "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-"

# Landen waarvoor MeteoAlarm een feed heeft. Bewust een keuzelijst: uit
# coordinaten alleen valt het land niet af te leiden zonder extra dienst.
ALERT_COUNTRIES = [
    "auto", "uit", "netherlands", "belgium", "germany", "luxembourg", "france",
    "united-kingdom", "denmark", "austria", "switzerland", "italy", "spain",
    "portugal", "poland", "czechia", "norway", "sweden", "ireland",
]
DEFAULT_ALERT_COUNTRY = "auto"

# Omzetten van landcode naar de naam die MeteoAlarm in zijn feed-URL gebruikt
LANDCODES = {
    "NL": "netherlands", "BE": "belgium", "DE": "germany", "LU": "luxembourg",
    "FR": "france", "GB": "united-kingdom", "DK": "denmark", "AT": "austria",
    "CH": "switzerland", "IT": "italy", "ES": "spain", "PT": "portugal",
    "PL": "poland", "CZ": "czechia", "NO": "norway", "SE": "sweden",
    "IE": "ireland", "FI": "finland", "HU": "hungary", "SK": "slovakia",
    "SI": "slovenia", "HR": "croatia", "GR": "greece", "RO": "romania",
    "BG": "bulgaria", "EE": "estonia", "LV": "latvia", "LT": "lithuania",
    "IS": "iceland", "MT": "malta", "CY": "cyprus", "RS": "serbia",
}

# Gratis omgekeerde geocodering zonder sleutel, alleen voor de landcode
GEOCODE_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client"

# MeteoAlarm gebruikt de CAP-schaal; wij vertalen naar de bekende kleuren.
ALERT_LEVELS = {
    "Minor": ("geel", 1),
    "Moderate": ("oranje", 2),
    "Severe": ("rood", 3),
    "Extreme": ("rood", 4),
}
ALERT_LEVEL_CHOICES = ["geel", "oranje", "rood"]
DEFAULT_ALERT_MIN_LEVEL = "geel"

EVENT_ALERT = f"{DOMAIN}_alert"

# Weercodes van Open-Meteo naar de condities die Home Assistant kent
WMO_CONDITIES = {
    0: "sunny", 1: "sunny", 2: "partlycloudy", 3: "cloudy",
    45: "fog", 48: "fog",
    51: "rainy", 53: "rainy", 55: "rainy",
    56: "rainy", 57: "rainy",
    61: "rainy", 63: "rainy", 65: "pouring",
    66: "rainy", 67: "pouring",
    71: "snowy", 73: "snowy", 75: "snowy", 77: "snowy",
    80: "rainy", 81: "rainy", 82: "pouring",
    85: "snowy", 86: "snowy",
    95: "lightning-rainy", 96: "lightning-rainy", 99: "lightning-rainy",
}

# Configuratie - neerslag
CONF_RAIN_LEAD = "rain_lead"
CONF_RAIN_THRESHOLD = "rain_threshold"
CONF_RAIN_NOTIFY = "rain_notify"

DEFAULT_RAIN_LEAD = 10          # minuten vooruit waarschuwen
DEFAULT_RAIN_THRESHOLD = 0.1    # mm/u; hieronder noemen we het droog

RAIN_INTERVAL = timedelta(minutes=5)
BUIENRADAR_URL = "https://gpsgadget.buienradar.nl/data/raintext"

EVENT_RAIN_INCOMING = f"{DOMAIN}_rain_incoming"

# Configuratie - meldingen
CONF_NOTIFY_SERVICES = "notify_services"
CONF_NOTIFY_MAX_DISTANCE = "notify_max_distance"
CONF_NOTIFY_ON_APPROACH = "notify_on_approach"
CONF_NOTIFY_ON_CLEARED = "notify_on_cleared"
CONF_NOTIFY_TITLE = "notify_title"
CONF_NOTIFY_COOLDOWN = "notify_cooldown"
CONF_QUIET_FROM = "quiet_from"
CONF_QUIET_TO = "quiet_to"

DEFAULT_NOTIFY_MAX_DISTANCE = 30
DEFAULT_NOTIFY_TITLE = "Onweer in de buurt"
DEFAULT_NOTIFY_COOLDOWN = 20
DEFAULT_QUIET = "00:00:00"

# Sleutel waaronder de aan/uit-stand van de meldingen wordt bijgehouden
DATA_NOTIFY_ENABLED = "notify_enabled"

SERVICE_TEST_NOTIFICATION = "test_notification"

# Windrichtingen, voluit voor in de meldingstekst
RICHTINGEN = [
    "noorden", "noordnoordoosten", "noordoosten", "oostnoordoosten",
    "oosten", "oostzuidoosten", "zuidoosten", "zuidzuidoosten",
    "zuiden", "zuidzuidwesten", "zuidwesten", "westzuidwesten",
    "westen", "westnoordwesten", "noordwesten", "noordnoordwesten",
]

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
