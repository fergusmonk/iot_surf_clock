from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")  # server/.env

from fastapi import FastAPI
from .routers import weather, surf, swim

app = FastAPI(title="IoT Home Server", version="0.1.0")

app.include_router(weather.router)
app.include_router(surf.router)
app.include_router(swim.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
