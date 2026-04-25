"""
Open-Meteo weather provider (no API key required).
Uses the default ECMWF IFS model; passes same WeatherResponse shape as metservice.py.
Swap active provider in config.py: WEATHER_PROVIDER = "openmeteo" | "metservice"
"""
import httpx
from datetime import datetime, timezone
from typing import Optional

from ..models import CurrentWeather, ForecastPeriod, WeatherResponse

URL = "https://api.open-meteo.com/v1/forecast"

_DIRS = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
         "S","SSW","SW","WSW","W","WNW","NW","NNW"]


def _compass(deg: Optional[float]) -> Optional[str]:
    if deg is None:
        return None
    return _DIRS[round(deg / 22.5) % 16]


async def fetch_weather(location: dict) -> WeatherResponse:
    params = {
        "latitude":       location["lat"],
        "longitude":      location["lon"],
        "hourly":         ",".join([
            "temperature_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "precipitation",
            "cloud_cover",
            "relative_humidity_2m",
            "surface_pressure",
        ]),
        "wind_speed_unit": "kmh",
        "timezone":        "UTC",
        "forecast_days":   2,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(URL, params=params)
        resp.raise_for_status()

    h = resp.json()["hourly"]
    times: list[str] = h["time"]

    # Find the slot matching the current UTC hour
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
    cur_i = times.index(now_str) if now_str in times else 0

    def _v(key: str, i: int) -> Optional[float]:
        lst = h.get(key, [])
        v = lst[i] if i < len(lst) else None
        return float(v) if v is not None else None

    def _iso(i: int) -> str:
        # Normalise to MetOcean-compatible format "2026-04-26T09:00:00Z"
        return times[i] + ":00Z"

    def _period(i: int) -> ForecastPeriod:
        return ForecastPeriod(
            time=_iso(i),
            temp_c=_v("temperature_2m", i),
            wind_speed_kmh=_v("wind_speed_10m", i),
            wind_direction=_compass(_v("wind_direction_10m", i)),
            wind_gust_kmh=_v("wind_gusts_10m", i),
            rain_rate_mmh=_v("precipitation", i),   # mm/h == mm per hour slot
            cloud_pct=_v("cloud_cover", i),
            humidity_pct=_v("relative_humidity_2m", i),
            pressure_hpa=_v("surface_pressure", i),
        )

    # 24 × 1 h periods starting from the current hour
    idxs = [cur_i + j for j in range(24) if cur_i + j < len(times)]

    return WeatherResponse(
        current=CurrentWeather(
            location=location.get("name", ""),
            temp_c=_v("temperature_2m", cur_i),
            wind_speed_kmh=_v("wind_speed_10m", cur_i),
            wind_direction=_compass(_v("wind_direction_10m", cur_i)),
            wind_gust_kmh=_v("wind_gusts_10m", cur_i),
            rain_rate_mmh=_v("precipitation", cur_i),
            cloud_pct=_v("cloud_cover", cur_i),
            humidity_pct=_v("relative_humidity_2m", cur_i),
            pressure_hpa=_v("surface_pressure", cur_i),
        ),
        forecast=[_period(i) for i in idxs],
        fetched_at=datetime.now(),
    )
