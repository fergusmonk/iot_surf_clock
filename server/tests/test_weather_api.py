from unittest.mock import AsyncMock, patch
from server.cache import cache


def test_health(client):
    assert client.get("/health").status_code == 200


def test_get_weather_success(client, weather_response):
    with patch("server.routers.weather.metservice.fetch_weather", new=AsyncMock(return_value=weather_response)):
        resp = client.get("/weather")
    assert resp.status_code == 200
    data = resp.json()
    assert data["current"]["temp_c"] == 18.5
    assert data["current"]["wind_direction"] == "SW"
    assert len(data["forecast"]) == 1


def test_get_weather_is_cached(client, weather_response):
    mock = AsyncMock(return_value=weather_response)
    with patch("server.routers.weather.metservice.fetch_weather", new=mock):
        client.get("/weather")
        client.get("/weather")
    assert mock.call_count == 1


def test_get_weather_error_returns_502(client):
    with patch("server.routers.weather.metservice.fetch_weather",
               new=AsyncMock(side_effect=RuntimeError("API down"))):
        resp = client.get("/weather")
    assert resp.status_code == 502
    assert "API down" in resp.json()["detail"]


def test_refresh_clears_cache(client, weather_response):
    cache.set("weather", weather_response, ttl=60)
    client.post("/weather/refresh")
    assert cache.get("weather") is None


def test_debug_endpoint(client):
    with patch("server.routers.weather.metservice.fetch_raw", new=AsyncMock(return_value={"variables": {}})):
        resp = client.get("/weather/debug")
    assert resp.status_code == 200
