from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CurrentWeather(BaseModel):
    location: str
    temp_c: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_direction: Optional[str] = None
    wind_gust_kmh: Optional[float] = None
    rain_rate_mmh: Optional[float] = None
    cloud_pct: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None


class ForecastPeriod(BaseModel):
    time: str
    temp_c: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_direction: Optional[str] = None
    wind_gust_kmh: Optional[float] = None
    rain_rate_mmh: Optional[float] = None
    cloud_pct: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None


class WeatherResponse(BaseModel):
    current: CurrentWeather
    forecast: list[ForecastPeriod]
    fetched_at: datetime


class WavePeriod(BaseModel):
    time: str
    wave_height_m: Optional[float] = None
    wave_period_s: Optional[float] = None
    wave_direction: Optional[str] = None
    swell_height_m: Optional[float] = None
    swell_period_s: Optional[float] = None
    swell_direction: Optional[str] = None
    wind_sea_height_m: Optional[float] = None
    wind_sea_period_s: Optional[float] = None
    wind_sea_direction: Optional[str] = None  # proxy for local wind direction


class SpotForecast(BaseModel):
    name: str
    lat: float
    lon: float
    periods: list[WavePeriod]


class SurfResponse(BaseModel):
    spots: list[SpotForecast]
    fetched_at: datetime


class BeachQuality(BaseModel):
    name: str
    slug: str
    quality: str        # raw: GREEN, RED, RED+, BLACK
    quality_label: str  # display: OK, Iffy, Poopoo


class SwimResponse(BaseModel):
    beaches: list[BeachQuality]
    fetched_at: datetime
