from fastapi import APIRouter, HTTPException
from ..cache import cache
from ..scrapers.safeswim import fetch_swim
from ..config import SWIM_TTL

router = APIRouter(prefix="/swim", tags=["swim"])


@router.get("")
async def get_swim():
    cached = cache.get("swim")
    if cached:
        return cached
    try:
        result = await fetch_swim()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    cache.set("swim", result, SWIM_TTL)
    return result


@router.post("/refresh")
async def refresh_swim():
    cache.invalidate("swim")
    return await get_swim()
