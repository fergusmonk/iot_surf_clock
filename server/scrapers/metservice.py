import httpx
from datetime import datetime, timezone
from typing import Optional
from ..models import CurrentWeather, ForecastPeriod, WeatherResponse, WavePeriod, SpotForecast
from ..config import METSERVICE_API_KEY, METSERVICE_BASE_URL


def _headers() -> dict:
    return {"x-api-key": METSERVICE_API_KEY}


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00:00Z")


def _build_body(points: list[dict], variables: list[str], interval: str, steps: int) -> dict:
    return {
        "points": [{"lon": p["lon"], "lat": p["lat"]} for p in points],
        "variables": variables,
        "time": {
            "from": _now_utc(),
            "interval": interval,
            "repeat": steps,
        },
    }


async def _post(body: dict) -> dict:
    url = f"{METSERVICE_BASE_URL}/point/time"
    async with httpx.AsyncClient(headers=_headers(), timeout=20.0) as client:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
    return resp.json()


def _col(data: dict, name: str) -> list:
    return data.get("variables", {}).get(name, {}).get("data", [])


def _times(data: dict) -> list[str]:
    return data.get("dimensions", {}).get("time", {}).get("data", [])


# ── Unit conversions ──────────────────────────────────────────────────────────

def _k_to_c(k: Optional[float]) -> Optional[float]:
    return round(k - 273.15, 1) if k is not None else None

def _ms_to_kmh(v: Optional[float]) -> Optional[float]:
    return round(v * 3.6, 1) if v is not None else None

def _pa_to_hpa(v: Optional[float]) -> Optional[float]:
    return round(v / 100.0, 1) if v is not None else None

def _frac_to_pct(v: Optional[float]) -> Optional[float]:
    # cloud.cover and humidity may come as 0-1 fraction or 0-100; normalise to 0-100
    if v is None:
        return None
    return round(v * 100, 1) if v <= 1.0 else round(v, 1)


# ── Fetchers ──────────────────────────────────────────────────────────────────

async def fetch_weather(location: dict, variables: list[str], interval: str, steps: int) -> WeatherResponse:
    body = _build_body([location], variables, interval, steps)
    raw = await _post(body)

    times = _times(raw)
    if not times:
        raise RuntimeError(
            f"MetService API: no time dimension in response. Keys: {list(raw.keys())} "
            "— check GET /weather/debug for the raw response."
        )

    temp  = [_k_to_c(_safe(_col(raw, "air.temperature.at-2m"), i))       for i in range(len(times))]
    wspd  = [_ms_to_kmh(_safe(_col(raw, "wind.speed.at-10m"), i))         for i in range(len(times))]
    wdir  = [_safe(_col(raw, "wind.direction.at-10m"), i)                  for i in range(len(times))]
    gust  = [_ms_to_kmh(_safe(_col(raw, "wind.speed.gust.at-10m"), i))    for i in range(len(times))]
    rain  = [_safe(_col(raw, "precipitation.rate"), i)                     for i in range(len(times))]
    cloud = [_frac_to_pct(_safe(_col(raw, "cloud.cover"), i))              for i in range(len(times))]
    humid = [_frac_to_pct(_safe(_col(raw, "air.humidity.at-2m"), i))       for i in range(len(times))]
    pres  = [_pa_to_hpa(_safe(_col(raw, "air.pressure.at-sea-level"), i))  for i in range(len(times))]

    def _period(i: int) -> ForecastPeriod:
        return ForecastPeriod(
            time=times[i],
            temp_c=temp[i],
            wind_speed_kmh=wspd[i],
            wind_direction=_compass(wdir[i]),
            wind_gust_kmh=gust[i],
            rain_rate_mmh=rain[i],
            cloud_pct=cloud[i],
            humidity_pct=humid[i],
            pressure_hpa=pres[i],
        )

    return WeatherResponse(
        current=CurrentWeather(
            location=location["name"],
            temp_c=temp[0],
            wind_speed_kmh=wspd[0],
            wind_direction=_compass(wdir[0]),
            wind_gust_kmh=gust[0],
            rain_rate_mmh=rain[0],
            cloud_pct=cloud[0],
            humidity_pct=humid[0],
            pressure_hpa=pres[0],
        ),
        forecast=[_period(i) for i in range(len(times))],
        fetched_at=datetime.now(),
    )


async def fetch_waves(spots: list[dict], variables: list[str], interval: str, steps: int) -> list[SpotForecast]:
    results = []
    for spot in spots:
        body = _build_body([spot], variables, interval, steps)
        raw  = await _post(body)
        times = _times(raw)

        periods = [
            WavePeriod(
                time=times[i],
                wave_height_m=_safe(_col(raw, "wave.height"), i),
                wave_period_s=_safe(_col(raw, "wave.period.peak"), i),
                wave_direction=_compass(_safe(_col(raw, "wave.direction.peak"), i)),
                swell_height_m=_safe(_col(raw, "wave.height.primary-swell"), i),
                swell_period_s=_safe(_col(raw, "wave.period.primary-swell.peak"), i),
                swell_direction=_compass(_safe(_col(raw, "wave.direction.primary-swell.mean"), i)),
                wind_sea_height_m=_safe(_col(raw, "wave.height.wind-sea"), i),
                wind_sea_period_s=_safe(_col(raw, "wave.period.wind-sea.peak"), i),
                wind_sea_direction=_compass(_safe(_col(raw, "wave.direction.wind-sea.mean"), i)),
            )
            for i in range(len(times))
        ]
        results.append(SpotForecast(name=spot["name"], lat=spot["lat"], lon=spot["lon"], periods=periods))

    return results


async def fetch_raw(points: list[dict], variables: list[str], interval: str, steps: int) -> dict:
    body = _build_body(points, variables, interval, steps)
    return await _post(body)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe(lst: list, idx: int) -> Optional[float]:
    try:
        v = lst[idx]
        return float(v) if v is not None else None
    except (IndexError, TypeError, ValueError):
        return None


def _compass(degrees: Optional[float]) -> Optional[str]:
    if degrees is None:
        return None
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return dirs[round(degrees / 22.5) % 16]
