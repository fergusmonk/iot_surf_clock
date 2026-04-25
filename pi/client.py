"""
Pi display client — fetches data from the home server and drives the
Waveshare 7.5" e-ink display (800×480 B&W).

Environment variables:
  SERVER_URL   Base URL of the home server  (default: http://localhost:8000)
  REFRESH_SEC  Seconds between display updates  (default: 300)
  NEXT_ALARM   Alarm time shown on screen e.g. "07:00"  (optional)
  SAVE_PNG     Set to any value to save a PNG instead of driving the display

Usage:
  python -m pi.client
  SERVER_URL=http://192.168.1.50:8000 python -m pi.client
  SERVER_URL=https://my-oracle-instance.com python -m pi.client
"""
import asyncio
import os
from datetime import datetime
from pathlib import Path

import httpx

from server.display import Renderer
from server.config import SURF_SPOTS, DISPLAY_SURF_COUNT

SERVER_URL  = os.environ.get("SERVER_URL", "http://localhost:8000").rstrip("/")
REFRESH_SEC = int(os.environ.get("REFRESH_SEC", "300"))
NEXT_ALARM  = os.environ.get("NEXT_ALARM")
SAVE_PNG    = bool(os.environ.get("SAVE_PNG"))
PNG_OUT     = Path(__file__).parent / "preview.png"

# Waveshare driver — only present on the Pi itself
try:
    from waveshare_epd import epd7in5_V2
    _HAS_EPD = True
except ImportError:
    _HAS_EPD = False


def _display(img) -> None:
    """Push a PIL image to the e-ink panel."""
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.display(epd.getbuffer(img))
    epd.sleep()


async def _fetch(client: httpx.AsyncClient, path: str) -> dict:
    resp = await client.get(f"{SERVER_URL}{path}", timeout=20.0)
    resp.raise_for_status()
    return resp.json()


async def update(renderer: Renderer) -> None:
    async with httpx.AsyncClient() as client:
        weather, surf, swim = await asyncio.gather(
            _fetch(client, "/weather"),
            _fetch(client, "/surf"),
            _fetch(client, "/swim"),
        )

    img = renderer.render(
        weather, surf,
        now=datetime.now(),
        next_alarm=NEXT_ALARM,
        surf_spot_meta=SURF_SPOTS[:DISPLAY_SURF_COUNT],
        swim=swim,
    )

    if _HAS_EPD and not SAVE_PNG:
        _display(img)
    else:
        img.save(PNG_OUT)
        print(f"[{datetime.now().strftime('%H:%M:%S')}]  saved → {PNG_OUT}")

    print(f"[{datetime.now().strftime('%H:%M:%S')}]  ok")


async def main() -> None:
    renderer = Renderer()
    if _HAS_EPD and not SAVE_PNG:
        print(f"Server: {SERVER_URL}  |  Output: e-ink display  |  Refresh: {REFRESH_SEC}s")
    else:
        print(f"Server: {SERVER_URL}  |  Output: {PNG_OUT}  |  Refresh: {REFRESH_SEC}s")
        if not _HAS_EPD:
            print("  (waveshare_epd not found — running in PNG mode)")

    while True:
        try:
            await update(renderer)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}]  error: {e}")
        await asyncio.sleep(REFRESH_SEC)


if __name__ == "__main__":
    asyncio.run(main())
