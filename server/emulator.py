"""
E-ink emulator — polls the local server, renders to a PNG.
Run from iot_assistant/:  python -m server.emulator
                          python -m server.emulator --once
                          python -m server.emulator --once --alarm 07:00
"""
import argparse
import asyncio
import httpx
from datetime import datetime
from pathlib import Path

from .display import Renderer
from .config import SURF_SPOTS, DISPLAY_SURF_COUNT

SERVER   = "http://localhost:8000"
OUTPUT   = Path(__file__).parent / "preview.png"
INTERVAL = 300  # seconds between refreshes


async def _fetch(client: httpx.AsyncClient, path: str) -> dict:
    resp = await client.get(f"{SERVER}{path}", timeout=15.0)
    resp.raise_for_status()
    return resp.json()


async def update(renderer: Renderer, alarm: str | None) -> None:
    async with httpx.AsyncClient() as client:
        weather, surf, swim = await asyncio.gather(
            _fetch(client, "/weather"),
            _fetch(client, "/surf"),
            _fetch(client, "/swim"),
        )

    img = renderer.render(
        weather, surf,
        now=datetime.now(),
        next_alarm=alarm,
        surf_spot_meta=SURF_SPOTS[:DISPLAY_SURF_COUNT],
        swim=swim,
    )
    img.save(OUTPUT)
    print(f"[{datetime.now().strftime('%H:%M:%S')}]  saved → {OUTPUT}")


async def main(once: bool, alarm: str | None) -> None:
    renderer = Renderer()
    if once:
        await update(renderer, alarm)
        return

    print(f"Updating every {INTERVAL}s  →  {OUTPUT}")
    while True:
        try:
            await update(renderer, alarm)
        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(INTERVAL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once",  action="store_true", help="Render once and exit")
    parser.add_argument("--alarm", default=None,        help="Next alarm time e.g. 07:00")
    args = parser.parse_args()
    asyncio.run(main(args.once, args.alarm))
