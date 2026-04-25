import os

METSERVICE_API_KEY  = os.environ.get("METSERVICE_API_KEY", "")
METSERVICE_BASE_URL = "https://forecast-v2.metoceanapi.com"

# "openmeteo" (no key, ECMWF IFS) or "metservice" (MetOcean API key required)
WEATHER_PROVIDER = "openmeteo"

# North Shore Auckland
WEATHER_LOCATION = {"lat": -36.80, "lon": 174.75, "name": "North Shore"}

# faces: compass bearing the break faces (direction waves arrive from).
# Offshore wind = faces + 180° (mod 360).
# First DISPLAY_SURF_COUNT spots are shown on screen.
SURF_SPOTS = [
    {"name": "Te Arai",    "lat": -36.347, "lon": 174.726, "faces": 80},   # east coast, faces E
    {"name": "Maori Bay",  "lat": -36.874, "lon": 174.430, "faces": 310},  # west coast, faces NW
    {"name": "Piha",       "lat": -36.949, "lon": 174.463, "faces": 255},  # west coast, faces WSW
    {"name": "Whangamata", "lat": -37.198, "lon": 175.876, "faces": 50},   # Coromandel, faces NE
    {"name": "Takapuna",   "lat": -36.772, "lon": 174.774, "faces": 50},   # harbour, faces NE
    {"name": "Tawheranui", "lat": -36.378, "lon": 174.848, "faces": 70},   # north coast, faces ENE
]

DISPLAY_SURF_COUNT = 4  # how many spots to show on the e-ink screen

WEATHER_VARIABLES = [
    "air.temperature.at-2m",
    "wind.speed.at-10m",
    "wind.direction.at-10m",
    "wind.speed.gust.at-10m",
    "precipitation.rate",
    "cloud.cover",
    "air.humidity.at-2m",
    "air.pressure.at-sea-level",
]

WAVE_VARIABLES = [
    "wave.height",
    "wave.period.peak",
    "wave.direction.peak",
    "wave.height.primary-swell",
    "wave.period.primary-swell.peak",
    "wave.direction.primary-swell.mean",
    "wave.height.wind-sea",
    "wave.period.wind-sea.peak",
    "wave.direction.wind-sea.mean",  # proxy for local wind direction
]

FORECAST_INTERVAL = "3h"
FORECAST_STEPS    = 40   # 40 × 3h = 5 days

WEATHER_TTL = 30 * 60
SURF_TTL    = 2 * 60 * 60
SWIM_TTL    = 30 * 60

SAFESWIM_SLUGS = ["milford", "milford-south"]
