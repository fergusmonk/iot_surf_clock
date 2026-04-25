from unittest.mock import AsyncMock, patch
from server.cache import cache
from server.models import SpotForecast, WavePeriod


def _make_spot(name: str, lat: float, lon: float) -> SpotForecast:
    return SpotForecast(
        name=name, lat=lat, lon=lon,
        periods=[WavePeriod(time="2026-04-25T00:00:00Z", wave_height_m=1.5)],
    )


def test_get_surf_returns_all_spots(client, surf_response):
    all_spots = [_make_spot(s["name"], s["lat"], s["lon"])
                 for s in __import__("server.config", fromlist=["SURF_SPOTS"]).SURF_SPOTS]
    with patch("server.routers.surf.metservice.fetch_waves", new=AsyncMock(return_value=all_spots)):
        resp = client.get("/surf")
    assert resp.status_code == 200
    assert len(resp.json()["spots"]) == 6


def test_get_surf_is_cached(client):
    from server.config import SURF_SPOTS
    all_spots = [_make_spot(s["name"], s["lat"], s["lon"]) for s in SURF_SPOTS]
    mock = AsyncMock(return_value=all_spots)
    with patch("server.routers.surf.metservice.fetch_waves", new=mock):
        client.get("/surf")
        client.get("/surf")
    assert mock.call_count == 1


def test_get_surf_api_error_returns_502(client):
    with patch("server.routers.surf.metservice.fetch_waves",
               new=AsyncMock(side_effect=RuntimeError("timeout"))):
        resp = client.get("/surf")
    assert resp.status_code == 502


def test_get_single_spot(client, spot_forecast):
    with patch("server.routers.surf.metservice.fetch_waves", new=AsyncMock(return_value=[spot_forecast])):
        resp = client.get("/surf/Piha")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Piha"


def test_get_single_spot_case_insensitive(client, spot_forecast):
    with patch("server.routers.surf.metservice.fetch_waves", new=AsyncMock(return_value=[spot_forecast])):
        resp = client.get("/surf/piha")
    assert resp.status_code == 200


def test_get_unknown_spot_returns_404(client):
    assert client.get("/surf/Bondi").status_code == 404


def test_refresh_clears_cache(client, surf_response):
    cache.set("surf", surf_response, ttl=60)
    client.post("/surf/refresh")
    assert cache.get("surf") is None


def test_debug_endpoint(client):
    with patch("server.routers.surf.metservice.fetch_raw", new=AsyncMock(return_value={"points": []})):
        resp = client.get("/surf/debug/raw")
    assert resp.status_code == 200
