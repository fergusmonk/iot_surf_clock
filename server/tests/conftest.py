import pytest
from datetime import datetime
from starlette.testclient import TestClient
from server.main import app
from server.models import (
    CurrentWeather, ForecastPeriod, WeatherResponse,
    WavePeriod, SpotForecast, SurfResponse,
)
from server.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    cache._store.clear()
    yield
    cache._store.clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def weather_response():
    return WeatherResponse(
        current=CurrentWeather(
            location="North Shore",
            temp_c=18.5,
            wind_speed_kmh=20.0,
            wind_direction="SW",
            wind_gust_kmh=28.0,
            rain_rate_mmh=0.2,
            cloud_pct=60.0,
            humidity_pct=72.0,
            pressure_hpa=1013.0,
        ),
        forecast=[
            ForecastPeriod(
                time="2026-04-25T00:00:00Z",
                temp_c=18.5,
                wind_speed_kmh=20.0,
                wind_direction="SW",
            )
        ],
        fetched_at=datetime(2026, 4, 25, 8, 0, 0),
    )


@pytest.fixture
def spot_forecast():
    return SpotForecast(
        name="Piha",
        lat=-36.949,
        lon=174.463,
        periods=[
            WavePeriod(
                time="2026-04-25T00:00:00Z",
                wave_height_m=1.5,
                wave_period_s=10.0,
                wave_direction="SW",
                swell_height_m=1.2,
                swell_period_s=12.0,
                swell_direction="WSW",
            )
        ],
    )


@pytest.fixture
def surf_response(spot_forecast):
    return SurfResponse(spots=[spot_forecast], fetched_at=datetime(2026, 4, 25, 8, 0, 0))


# ── Sample API responses ──────────────────────────────────────────────────────

SAMPLE_WEATHER_API = {
    "dimensions": {
        "time": {"data": ["2026-04-25T00:00:00Z", "2026-04-25T03:00:00Z"]},
        "point": {"data": [{"lon": 174.75, "lat": -36.8}]},
    },
    "variables": {
        "air.temperature.at-2m":    {"data": [287.41, 289.95]},
        "wind.speed.at-10m":        {"data": [5.56, 5.0]},
        "wind.direction.at-10m":    {"data": [225.0, 210.0]},
        "wind.speed.gust.at-10m":   {"data": [7.78, 6.94]},
        "precipitation.rate":       {"data": [0.0001, 0.0]},
        "cloud.cover":              {"data": [0.6, 0.55]},
        "air.humidity.at-2m":       {"data": [0.72, 0.70]},
        "air.pressure.at-sea-level":{"data": [101300.0, 101400.0]},
    }
}

SAMPLE_WAVE_API = {
    "points": [
        {
            "variables": {
                "time":                          {"data": ["2026-04-25T00:00:00Z", "2026-04-25T03:00:00Z"]},
                "wave.height":                   {"data": [1.5, 1.8]},
                "wave.period.peak":              {"data": [10.0, 11.0]},
                "wave.direction.peak":           {"data": [225.0, 220.0]},
                "wave.height.primary-swell":     {"data": [1.2, 1.5]},
                "wave.period.primary-swell.peak":{"data": [12.0, 13.0]},
                "wave.direction.primary-swell.mean":{"data": [230.0, 225.0]},
                "wave.height.wind-sea":          {"data": [0.5, 0.6]},
                "wave.period.wind-sea.peak":     {"data": [5.0, 5.5]},
            }
        }
    ]
}
