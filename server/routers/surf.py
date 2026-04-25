from datetime import datetime
from fastapi import APIRouter, HTTPException
from ..config import SURF_SPOTS, WAVE_VARIABLES, FORECAST_INTERVAL, FORECAST_STEPS, SURF_TTL
from ..cache import cache
from ..models import SurfResponse, SpotForecast
from ..scrapers import metservice

router = APIRouter(prefix="/surf", tags=["surf"])


@router.get("", response_model=SurfResponse)
async def get_surf():
    cached = cache.get("surf")
    if cached:
        return cached
    try:
        spots = await metservice.fetch_waves(
            SURF_SPOTS, WAVE_VARIABLES, FORECAST_INTERVAL, FORECAST_STEPS
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    data = SurfResponse(spots=spots, fetched_at=datetime.now())
    cache.set("surf", data, SURF_TTL)
    return data


@router.get("/{spot_name}", response_model=SpotForecast)
async def get_spot(spot_name: str):
    match = next((s for s in SURF_SPOTS if s["name"].lower() == spot_name.lower()), None)
    if not match:
        names = [s["name"] for s in SURF_SPOTS]
        raise HTTPException(status_code=404, detail=f"Unknown spot. Available: {names}")
    try:
        results = await metservice.fetch_waves([match], WAVE_VARIABLES, FORECAST_INTERVAL, FORECAST_STEPS)
        return results[0]
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/refresh")
async def refresh_surf():
    cache.invalidate("surf")
    return {"status": "cache cleared"}


@router.get("/debug/raw")
async def debug_surf():
    """Return raw wave API response for the first spot — use to verify response structure."""
    try:
        return await metservice.fetch_raw(
            [SURF_SPOTS[0]], WAVE_VARIABLES[:3], FORECAST_INTERVAL, 3
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
