# IoT Home Server

FastAPI service that scrapes MetService NZ and surf-forecast.com and exposes the data as a local REST API for the Pi Zero alarm clock.

Runs on a separate, more capable machine (Orange Pi 4, spare Pi, etc.) on your LAN.

---

## Install

```bash
cd iot_assistant/server
pip install -r requirements.txt
```

---

## Run

Run from the **parent** directory (`iot_assistant/`) so Python can resolve the `server` package:

```bash
cd iot_assistant
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API docs: `http://<server-ip>:8000/docs`

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| GET | `/weather` | Current conditions + multi-day forecast (North Shore) |
| POST | `/weather/refresh` | Bust the weather cache |
| GET | `/weather/debug` | Raw `__NEXT_DATA__` JSON from MetService — use when tuning the parser |
| GET | `/surf` | Forecast for all configured spots |
| GET | `/surf/{spot_name}` | Single spot by name (e.g. `/surf/Piha`) |
| POST | `/surf/refresh` | Bust the surf cache |
| GET | `/surf/debug/{slug}` | Raw HTML from surf-forecast.com — use when tuning the parser |

Responses are cached: weather for 30 min, surf for 2 hours.

---

## Configuration

All tunable values are in `config.py`:

```python
METSERVICE_URL   # North Shore forecast page URL
SURF_SPOTS       # List of {name, slug} dicts — slug must match surf-forecast.com URL
SURFFORECAST_BASE
WEATHER_TTL      # Cache TTL in seconds (default 1800)
SURF_TTL         # Cache TTL in seconds (default 7200)
```

### Checking/fixing slugs

surf-forecast.com URLs look like:
`https://www.surf-forecast.com/breaks/Te-Arai-Point/forecasts/latest`

The part after `/breaks/` is the slug. If a spot returns a 404, find the correct slug by searching the site and updating `SURF_SPOTS` in `config.py`.

---

## Tuning the parsers

The scrapers will almost certainly need selector tweaks the first time you run them against the live sites.

**MetService** stores its data in a `__NEXT_DATA__` JSON blob (Next.js SSR). Hit the debug endpoint to inspect it:

```bash
curl http://localhost:8000/weather/debug | python3 -m json.tool | less
```

Find the key path to the forecast data and update `_parse()` in `scrapers/metservice.py`.

**surf-forecast.com** uses an HTML table with CSS class names on each row. Hit the debug endpoint to see what the classes actually look like:

```bash
curl http://localhost:8000/surf/debug/Piha
```

If the class names don't match the `_ROW_KEYS` dict in `scrapers/surfforecast.py`, add the correct fragments there.

---

## Tests

```bash
cd iot_assistant
pytest server/tests/ -v
```

The tests use mocked scrapers — no network calls, no live site dependency.

---

## Deploy (Orange Pi / Pi)

```bash
# Install deps
pip install -r requirements.txt

# Run in the background with auto-restart on crash
nohup uvicorn server.main:app --host 0.0.0.0 --port 8000 &

# Or with systemd — create /etc/systemd/system/iot-server.service:
# ExecStart=/usr/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000
# WorkingDirectory=/home/<user>/iot_assistant
# Restart=always
```

The Pi Zero then hits `http://<server-ip>:8000/weather` and `/surf`.
