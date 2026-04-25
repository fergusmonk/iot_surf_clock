from fastapi import APIRouter, HTTPException
from ..config import (
    WEATHER_PROVIDER, WEATHER_LOCATION,
    WEATHER_VARIABLES, FORECAST_INTERVAL, FORECAST_STEPS,
    WEATHER_TTL,
)
from ..cache import cache
from ..models import WeatherResponse

router = APIRouter(prefix="/weather", tags=["weather"])


async def _fetch_weather() -> WeatherResponse:
    """Dispatch to the configured weather provider."""
    if WEATHER_PROVIDER == "openmeteo":
        from ..scrapers.openmeteo import fetch_weather
        return await fetch_weather(WEATHER_LOCATION)
    # fallback: MetOcean / MetService
    from ..scrapers import metservice
    return await metservice.fetch_weather(
        WEATHER_LOCATION, WEATHER_VARIABLES, FORECAST_INTERVAL, FORECAST_STEPS
    )


@router.get("", response_model=WeatherResponse)
async def get_weather():
    cached = cache.get("weather")
    if cached:
        return cached
    try:
        data = await _fetch_weather()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    cache.set("weather", data, WEATHER_TTL)
    return data


@router.post("/refresh")
async def refresh_weather():
    cache.invalidate("weather")
    return await get_weather()


@router.get("/debug")
async def debug_weather():
    """Raw provider response — useful for verifying field names and values."""
    try:
        if WEATHER_PROVIDER == "openmeteo":
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": WEATHER_LOCATION["lat"],
                        "longitude": WEATHER_LOCATION["lon"],
                        "hourly": "temperature_2m,wind_speed_10m,wind_direction_10m,cloud_cover",
                        "wind_speed_unit": "kmh",
                        "timezone": "UTC",
                        "forecast_days": 1,
                    },
                )
                r.raise_for_status()
                return r.json()
        from ..scrapers import metservice
        return await metservice.fetch_raw(
            [WEATHER_LOCATION], WEATHER_VARIABLES[:2], FORECAST_INTERVAL, 3
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
