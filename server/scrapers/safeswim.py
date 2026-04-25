import httpx
from datetime import datetime
from ..models import BeachQuality, SwimResponse
from ..config import SAFESWIM_SLUGS

SAFESWIM_URL = "https://safeswim.org.nz/api/locations"

_QUALITY_LABEL: dict[str, str] = {
    "GREEN": "OK",
    "RED":   "Iffy",
    "RED+":  "Poopoo",
    "BLACK": "Poopoo",
}


def _label(quality: str) -> str:
    return _QUALITY_LABEL.get(quality.upper(), "--")


async def fetch_swim() -> SwimResponse:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(SAFESWIM_URL)
        resp.raise_for_status()

    slug_set = set(SAFESWIM_SLUGS)
    slug_order = {s: i for i, s in enumerate(SAFESWIM_SLUGS)}

    beaches = []
    for loc in resp.json().get("locations", []):
        if loc.get("slug") in slug_set:
            quality = loc.get("state", {}).get("quality", "")
            beaches.append(BeachQuality(
                name=loc.get("name", loc["slug"]),
                slug=loc["slug"],
                quality=quality,
                quality_label=_label(quality),
            ))

    beaches.sort(key=lambda b: slug_order.get(b.slug, 99))
    return SwimResponse(beaches=beaches, fetched_at=datetime.now())
