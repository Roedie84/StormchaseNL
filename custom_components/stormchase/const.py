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
CONF_ADDRESS_SENSOR = "address_sensor"

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

# Metingen van het dichtstbijzijnde weerstation, gratis en zonder sleutel.
# Dekt Duitsland en de directe omgeving.
BRIGHTSKY_URL = "https://api.brightsky.dev/current_weather"

# Ensemble: hetzelfde model meerdere keren gedraaid met licht verschillende
# beginwaarden. Levert een kans in plaats van een enkele uitkomst. ICON-D2-EPS
# dekt Midden-Europa op twee kilometer; GEFS is de wereldwijde terugval.
# Radarbeeld gecentreerd op je eigen positie, gratis en zonder sleutel.
# Wereldwijde dekking uit meer dan duizend radars.
RAINVIEWER_URL = "https://api.rainviewer.com/public/weather-maps.json"
# RainViewer publiceert ongeveer elke vijf minuten een nieuw beeld, maar niet
# op vaste tijden. Vaker kijken betekent dat je een nieuw beeld eerder ziet;
# het overzicht is klein, dus dat kost weinig.
CONF_RADAR_INTERVAL = "radar_interval"
DEFAULT_RADAR_INTERVAL = 60  # seconden
CONF_RADAR_ZOOM = "radar_zoom"
CONF_RADAR_KLEUR = "radar_kleur"
DEFAULT_RADAR_ZOOM = 7
DEFAULT_RADAR_KLEUR = 2
CONF_WOLKEN = "wolken_op_radar"
CONF_WOLKEN_LAAG = "wolken_laag"
# Wolkenmasker van Meteosat: deelt elk beeldpunt in als helder of bewolkt,
# ongeacht de hoogte van de wolk. Infrarood mist juist de lage bewolking.
DEFAULT_WOLKEN_LAAG = "msg_fes:clm"

# De Duitse weerdienst publiceert zijn radarcompositie als open kaartdienst,
# zonder sleutel. Actueler dan de wereldwijde verzameling van RainViewer,
# maar de dekking houdt op bij de landsgrens en de directe omgeving.
DWD_WMS_URL = "https://maps.dwd.de/geoserver/dwd/ows"
DEFAULT_DWD_LAAG = "dwd:Niederschlagsradar"

CONF_RADARBRON = "radarbron"
CONF_DWD_LAAG = "dwd_laag"
RADARBRONNEN = ["rainviewer", "dwd"]
DEFAULT_RADARBRON = "rainviewer"

# Het ensemble draait op een eigen subdomein; het gedeelde eindpunt gaf 404
ENSEMBLE_URL = "https://ensemble-api.open-meteo.com/v1/ensemble"
ENSEMBLE_LOKAAL = "icon_d2_eps"
ENSEMBLE_WERELD = "gefs025"
METING_INTERVAL = timedelta(minutes=15)

# Update-intervallen
CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 10  # seconden

STORM_INTERVAL = timedelta(seconds=DEFAULT_UPDATE_INTERVAL)
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

# Tijdvenster waarover de afstandsringen tellen. Sluit aan op het venster
# dat de Blitzortung-integratie zelf gebruikt.
CONF_RING_WINDOW = "ring_window"
DEFAULT_RING_WINDOW = 120  # minuten
MAX_INSLAGEN = 5000        # bovengrens voor de bewaarde inslagen

# Celtracking en veiligheid
CELVENSTER = 900          # seconden inslagen die meetellen voor een cel
CELSPOOR = 40             # aantal bewaarde zwaartepunten
SCHUILAFSTAND = 10        # km; hierbinnen geldt de 30/30-regel
SCHUILNALOOP = 30         # minuten na de laatste inslag binnen die afstand
FREQUENTIEVENSTER = 300   # seconden voor de inslagfrequentie

EVENT_SHELTER = f"{DOMAIN}_shelter"

# Configuratie - meldingsvorm
CONF_CRITICAL = "critical_alerts"
CONF_DASHBOARD = "dashboard_path"
DEFAULT_DASHBOARD = "/stormchase"

# Soorten die door de stille modus heen mogen als critical alert is aangezet
CRITICAL_SOORTEN = {"nearby", "shelter", "alert", "outlook"}

# Configuratie - vooruitzicht
CONF_OUTLOOK_NOTIFY = "outlook_notify"
CONF_OUTLOOK_LEVEL = "outlook_level"

OUTLOOK_LEVELS = ["onweer", "zwaar", "noodweer"]
DEFAULT_OUTLOOK_LEVEL = "zwaar"
# Bij welke rang uit indices.py de gekozen drempel hoort
OUTLOOK_RANGEN = {"onweer": 2, "zwaar": 3, "noodweer": 4}

EVENT_OUTLOOK = f"{DOMAIN}_outlook"

# Configuratie - dagelijks weerbericht
CONF_BRIEFING = "briefing"
CONF_BRIEFING_MORNING = "briefing_morning"
CONF_BRIEFING_AFTERNOON = "briefing_afternoon"

DEFAULT_BRIEFING_MORNING = "07:00:00"
DEFAULT_BRIEFING_AFTERNOON = "13:00:00"

SERVICE_SEND_BRIEFING = "send_briefing"

# Weercodes in gewone taal, voor in het weerbericht
WMO_TEKST = {
    0: "onbewolkt", 1: "vrijwel onbewolkt", 2: "half bewolkt", 3: "bewolkt",
    45: "mistig", 48: "mist met rijpvorming",
    51: "lichte motregen", 53: "motregen", 55: "dichte motregen",
    56: "lichte onderkoelde motregen", 57: "onderkoelde motregen",
    61: "lichte regen", 63: "regen", 65: "zware regen",
    66: "lichte onderkoelde regen", 67: "onderkoelde regen",
    71: "lichte sneeuwval", 73: "sneeuwval", 75: "zware sneeuwval",
    77: "korrelsneeuw",
    80: "lichte buien", 81: "buien", 82: "zware buien",
    85: "lichte sneeuwbuien", 86: "zware sneeuwbuien",
    95: "onweer", 96: "onweer met lichte hagel", 99: "onweer met zware hagel",
}

# Configuratie - weersituaties
CONF_WEATHER_TYPES = "weather_types"
CONF_HEAT_THRESHOLD = "heat_threshold"
CONF_FROST_THRESHOLD = "frost_threshold"

WEATHER_TYPES = ["sneeuw", "ijzel", "mist", "hitte", "vorst"]
DEFAULT_WEATHER_TYPES = ["sneeuw", "ijzel", "mist", "hitte", "vorst"]
DEFAULT_HEAT_THRESHOLD = 30.0   # graden
DEFAULT_FROST_THRESHOLD = 0.0   # graden

EVENT_WEATHER = f"{DOMAIN}_weather"

# WMO-weercodes per situatie
CODES_SNEEUW = {71, 73, 75, 77, 85, 86}
CODES_IJZEL = {56, 57, 66, 67}
CODES_MIST = {45, 48}

# Deze situaties gaan over gevaar onderweg en worden ook gemeld als je rijdt.
# De rest wacht tot je ergens bent, want dan pas zegt het iets over waar je
# de komende tijd zit.
ONDERWEG_RELEVANT = {"ijzel", "sneeuw", "mist"}

# Configuratie - wind en stilstand
CONF_WIND_NOTIFY = "wind_notify"
CONF_WIND_THRESHOLD = "wind_threshold"
CONF_ONLY_STATIONARY = "only_stationary"
CONF_STATIONARY_MINUTES = "stationary_minutes"

DEFAULT_WIND_THRESHOLD = 60      # km/u windstoten
CONF_MOVING_SPEED = "moving_speed"

DEFAULT_STATIONARY_MINUTES = 10  # zo lang traag voor je weer 'ter plaatse' bent
DEFAULT_MOVING_SPEED = 30        # km/u; hierboven ben je onderweg
SNELHEID_VENSTER = 180           # seconden waarover de snelheid wordt bepaald
MAX_SNELHEID = 400               # km/u; hierboven is het geen echte beweging
LOCATIE_GESCHIEDENIS = 400       # aantal bewaarde locatiepunten

EVENT_WIND = f"{DOMAIN}_wind"

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

# ICON-D2 is het enige model met bliksempotentie, updraft en wolkentoppen, en
# het levert kwartierwaarden. Alleen in Midden-Europa; daarbuiten komen deze
# velden leeg terug en valt de integratie terug op de gewone waarden.
MODEL_D2 = "dwd_icon_d2"
D2_UURLIJKS = (
    "lightning_potential,updraft,convective_cloud_top,convective_cloud_base"
)
D2_KWARTIER = "cape,lightning_potential,freezing_level_height"

# De Lifted Index publiceert ICON niet, en GFS bij Open-Meteo evenmin: dat
# verzoek slaagde wel maar gaf lege waarden terug. Het Chinese GRAPES-model
# levert hem wel als eigen veld, wereldwijd op vijftien kilometer.
LI_URL = "https://api.open-meteo.com/v1/cma"

# Modellen voor de spreidingsvergelijking. Een enkel getal uit een enkel model
# leest als zekerheid; pas als je ziet dat acht modellen het eens zijn, weet
# je of je er iets mee kunt. Modellen die de locatie niet dekken of het veld
# niet leveren komen leeg terug en tellen niet mee.
ENSEMBLE_MODELLEN = [
    "ecmwf_ifs025",
    "icon_eu",
    "icon_d2",
    "gfs_seamless",
    "ukmo_seamless",
    "gem_seamless",
    "metno_seamless",
    "meteofrance_seamless",
]
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
