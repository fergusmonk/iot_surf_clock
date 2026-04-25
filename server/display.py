"""
E-ink display renderer — Waveshare 7.5" (800×480, B&W).
Produces a PIL Image from weather and surf API responses.
On the Pi, replace img.save() with epd.display(epd.getbuffer(img)).
"""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone
from typing import Optional
import os

W, H = 800, 480
BG, FG = 255, 0  # white background, black ink

# Layout zones (pixels)
CLOCK_W  = 275
HEADER_H = 155
GRAPH_H  = 100
PRECIP_H = 78
SURF_H   = H - HEADER_H - GRAPH_H - PRECIP_H  # 147

PAD = 8

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

_COMPASS_DEG = {
    "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5,
    "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
    "S": 180, "SSW": 202.5, "SW": 225, "WSW": 247.5,
    "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5,
}


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _compass_to_deg(compass: Optional[str]) -> Optional[float]:
    return _COMPASS_DEG.get(compass) if compass else None


def _angle_diff(a: float, b: float) -> float:
    """Smallest angle between two bearings (0-180°)."""
    d = abs(a - b) % 360
    return d if d <= 180 else 360 - d


def _is_offshore(wind_sea_dir: Optional[str], faces_deg: Optional[float]) -> Optional[bool]:
    """
    wind_sea_dir: direction wind waves come FROM (≈ wind direction).
    faces_deg:    direction the break faces (where swell comes from = onshore direction).
    Offshore = wind from the land side = ~180° from faces_deg.
    Returns True/False/None.
    """
    if wind_sea_dir is None or faces_deg is None:
        return None
    wsd = _compass_to_deg(wind_sea_dir)
    if wsd is None:
        return None
    offshore_bearing = (faces_deg + 180) % 360
    return _angle_diff(wsd, offshore_bearing) < 60


def _best_period_idx(periods: list[dict], faces_deg: Optional[float]) -> int:
    """
    Score each 3-hour period across the day and return the index of the best one.
    Scoring priorities:
      1. Long swell period (quality indicator)
      2. Wave height in a good range (0.6–2.5m)
      3. High swell-to-total ratio (clean, not choppy)
      4. Offshore wind bonus
    """
    best_score, best_idx = -1.0, 0
    for i, p in enumerate(periods[:8]):  # first 24h only
        score = 0.0

        # Swell period — primary quality signal
        sp = p.get("swell_period_s") or 0
        score += min(sp / 2.0, 6.0)  # 0–6 pts (caps at 12s)

        # Wave height — sweet spot 0.6–2.5m
        wh = p.get("wave_height_m") or 0
        if 0.8 <= wh <= 2.0:
            score += 4.0
        elif 0.6 <= wh <= 2.5:
            score += 2.0
        elif wh > 0.3:
            score += 0.5

        # Cleanliness — swell fraction of total wave height
        sh = p.get("swell_height_m") or 0
        if wh > 0:
            score += (sh / wh) * 3.0  # 0–3 pts

        # Offshore wind bonus
        if _is_offshore(p.get("wind_sea_direction"), faces_deg):
            score += 3.0

        if score > best_score:
            best_score, best_idx = score, i

    return best_idx


def _period_hours(forecast: list[dict]) -> float:
    """Detect forecast interval in hours from the first two period timestamps."""
    if len(forecast) < 2:
        return 3.0
    try:
        t0 = datetime.fromisoformat(forecast[0]["time"].replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(forecast[1]["time"].replace("Z", "+00:00"))
        return (t1 - t0).total_seconds() / 3600.0
    except Exception:
        return 3.0


class Renderer:
    def __init__(self):
        self.f_clock = _font(84)
        self.f_temp  = _font(50)
        self.f_large = _font(30)
        self.f_med   = _font(22)
        self.f_small = _font(17)
        self.f_tiny  = _font(13)

    def render(
        self,
        weather: dict,
        surf: dict,
        now: Optional[datetime] = None,
        next_alarm: Optional[str] = None,
        surf_spot_meta: Optional[list[dict]] = None,
        swim: Optional[dict] = None,
    ) -> Image.Image:
        if now is None:
            now = datetime.now()

        img  = Image.new("L", (W, H), BG)
        draw = ImageDraw.Draw(img)

        self._clock(draw, now, next_alarm)
        self._conditions(draw, weather)
        self._temp_graph(draw, weather)
        self._precip_bars(draw, weather)
        self._surf(draw, surf, surf_spot_meta or [], weather)
        if swim:
            self._swim(draw, swim)
        self._dividers(draw)

        return img

    # ── Clock panel ───────────────────────────────────────────────────────────

    def _clock(self, draw, now, next_alarm):
        cx = CLOCK_W // 2
        draw.text((cx, 12), now.strftime("%H:%M"),
                  font=self.f_clock, fill=FG, anchor="mt")
        draw.text((cx, 108), now.strftime("%A %-d %b"),
                  font=self.f_small, fill=FG, anchor="mt")
        if next_alarm:
            draw.text((cx, 130), f"Alarm  {next_alarm}",
                      font=self.f_small, fill=FG, anchor="mt")

    # ── Current conditions ────────────────────────────────────────────────────

    def _conditions(self, draw, weather):
        x   = CLOCK_W + PAD * 2
        cur = weather.get("current", {})

        temp = cur.get("temp_c")
        draw.text((x, 8), f"{temp:.1f}°C" if temp is not None else "--°C",
                  font=self.f_temp, fill=FG, anchor="lt")

        spd  = cur.get("wind_speed_kmh")
        gust = cur.get("wind_gust_kmh")
        wdir = cur.get("wind_direction", "")
        wind = f"{wdir}  {spd:.0f} km/h" if spd else ""
        if gust:
            wind += f"  (gusts {gust:.0f})"
        draw.text((x, 70), wind, font=self.f_med, fill=FG, anchor="lt")

        cloud = cur.get("cloud_pct")
        humid = cur.get("humidity_pct")
        pres  = cur.get("pressure_hpa")
        detail = "  ·  ".join(filter(None, [
            f"Cloud {cloud:.0f}%" if cloud is not None else None,
            f"Humidity {humid:.0f}%" if humid is not None else None,
            f"{pres:.0f} hPa" if pres is not None else None,
        ]))
        draw.text((x, 100), detail, font=self.f_small, fill=FG, anchor="lt")

        forecast  = weather.get("forecast", [])
        ph        = _period_hours(forecast)
        total_mm  = sum((p.get("rain_rate_mmh") or 0) * ph for p in forecast[:24])
        draw.text((x, 118), f"Rain today  ~{total_mm:.1f} mm",
                  font=self.f_small, fill=FG, anchor="lt")

    # ── Temperature graph ─────────────────────────────────────────────────────

    def _temp_graph(self, draw, weather):
        y0 = HEADER_H
        y1 = HEADER_H + GRAPH_H
        gx0, gx1 = 48, W - PAD * 2
        gy0, gy1 = y0 + 22, y1 - 18

        draw.text((PAD, y0 + 3), "Temperature  °C",
                  font=self.f_tiny, fill=FG, anchor="lt")

        forecast = weather.get("forecast", [])[:24]
        ph       = _period_hours(forecast)
        # Label every N slots so ~4 x-axis labels appear regardless of interval
        step = max(1, round(6 / ph))  # 6h spacing: step=6 for 1h, step=2 for 3h

        # Build (temp, local_time_label) pairs, skipping periods with no temp
        pairs: list[tuple[float, str]] = []
        for p in forecast:
            t = p.get("temp_c")
            if t is None:
                continue
            try:
                dt = datetime.fromisoformat(p["time"].replace("Z", "+00:00"))
                lbl = dt.astimezone().strftime("%H:%M")
            except Exception:
                lbl = ""
            pairs.append((t, lbl))

        if not pairs:
            return

        temps  = [v for v, _ in pairs]
        xlbls  = [l for _, l in pairs]

        t_min, t_max = min(temps), max(temps)
        span = max(t_max - t_min, 2.0)
        t_lo = t_min - span * 0.25
        t_hi = t_max + span * 0.25

        # Slot centres align with rainfall bar centres below
        n      = len(temps)
        slot_w = (gx1 - gx0) // n

        def tx(i):
            return gx0 + i * slot_w + slot_w // 2

        def ty(t):
            return int(gy1 - (t - t_lo) / (t_hi - t_lo) * (gy1 - gy0))

        # Line
        pts = [(tx(i), ty(t)) for i, t in enumerate(temps)]
        if len(pts) >= 2:
            draw.line(pts, fill=FG, width=2)

        # Dots — always; floating temp label every `step` slots
        for i, (t, (px, py)) in enumerate(zip(temps, pts)):
            draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=FG)
            if i % step == 0:
                offset = -14 if (i // step) % 2 == 0 else 6
                draw.text((px, py + offset), f"{t:.1f}",
                          font=self.f_tiny, fill=FG, anchor="mt")

        # X-axis: actual local time every `step` slots
        for i, lbl in enumerate(xlbls):
            if i % step == 0 and lbl:
                draw.text((tx(i), gy1 + 2), lbl,
                          font=self.f_tiny, fill=FG, anchor="mt")

    # ── Precipitation bars ────────────────────────────────────────────────────

    def _precip_bars(self, draw, weather):
        y0 = HEADER_H + GRAPH_H
        y1 = HEADER_H + GRAPH_H + PRECIP_H
        bx0, bx1 = 48, W - PAD * 2
        by0, by1 = y0 + 26, y1 - 18

        forecast = weather.get("forecast", [])[:24]
        ph       = _period_hours(forecast)
        step     = max(1, round(6 / ph))
        interval_lbl = "hr" if ph <= 1 else f"{ph:.0f} hr"
        draw.text((PAD, y0 + 3), f"Rainfall  mm / {interval_lbl}",
                  font=self.f_tiny, fill=FG, anchor="lt")

        rains = [(p.get("rain_rate_mmh") or 0) * ph for p in forecast]
        n     = len(rains)
        if not n:
            return

        # Actual local hour label per bar
        xlbls = []
        for p in forecast:
            try:
                dt = datetime.fromisoformat(p["time"].replace("Z", "+00:00"))
                xlbls.append(dt.astimezone().strftime("%H"))
            except Exception:
                xlbls.append("")

        max_r  = max(rains) if max(rains) > 0.05 else 1.0
        slot_w = (bx1 - bx0) // n
        bar_w  = max(slot_w - 2, 1)

        for i, r in enumerate(rains):
            x  = bx0 + i * slot_w
            bh = int((r / max_r) * (by1 - by0))
            if bh > 0:
                draw.rectangle([x, by1 - bh, x + bar_w, by1], fill=FG)
            if i % step == 0 and i < len(xlbls) and xlbls[i]:
                draw.text((x + slot_w // 2, by1 + 2), xlbls[i],
                          font=self.f_tiny, fill=FG, anchor="mt")

        if max_r > 0.05:
            draw.text((bx0 - 4, by0), f"{max_r:.1f}",
                      font=self.f_tiny, fill=FG, anchor="rb")

    # ── Surf section ──────────────────────────────────────────────────────────

    def _surf(self, draw, surf, spot_meta: list[dict], weather: dict):
        y0    = HEADER_H + GRAPH_H + PRECIP_H
        # limit to whichever is smaller: spots returned or spot_meta count
        limit = len(spot_meta) if spot_meta else 4
        spots = surf.get("spots", [])[:limit]
        n     = len(spots)
        if not n:
            return

        col_w = W // n

        # Build a lookup for faces_deg from spot metadata
        faces_lookup = {s["name"]: s.get("faces") for s in spot_meta}

        # Index weather forecast by UTC time string for wind lookup
        wx_by_time = {p.get("time", ""): p for p in weather.get("forecast", [])}

        for i, spot in enumerate(spots):
            x0        = i * col_w + PAD
            name      = spot.get("name", "")
            periods   = spot.get("periods", [])
            faces_deg = faces_lookup.get(name)

            # Convert periods list to plain dicts (handles both dict and Pydantic)
            plist = [p if isinstance(p, dict) else p.model_dump() for p in periods]

            best_i  = _best_period_idx(plist, faces_deg)
            best_p  = plist[best_i] if plist else {}
            best_t  = best_p.get("time", "")

            # Parse UTC time to local hour display
            try:
                dt_utc  = datetime.fromisoformat(best_t.replace("Z", "+00:00"))
                dt_local = dt_utc.astimezone()
                time_lbl = dt_local.strftime("%H:%M")
            except Exception:
                time_lbl = best_t[11:16] if len(best_t) > 15 else "??"

            # ── Name + best time ──
            draw.text((x0, y0 + 8), name,
                      font=self.f_med, fill=FG, anchor="lt")
            draw.text((x0, y0 + 40), f"Peak  {time_lbl}",
                      font=self.f_tiny, fill=FG, anchor="lt")

            # ── Wave summary ──
            wh = best_p.get("wave_height_m")
            wp = best_p.get("wave_period_s")
            wave_str = f"{wh:.1f}m  {wp:.0f}s" if wh and wp else "--"
            draw.text((x0, y0 + 65), wave_str,
                      font=self.f_small, fill=FG, anchor="lt")

            # ── Swell direction (fall back to peak wave if decomposition unavailable) ──
            sd = best_p.get("swell_direction") or best_p.get("wave_direction", "")
            sh = best_p.get("swell_height_m") or best_p.get("wave_height_m")
            sp = best_p.get("swell_period_s") or best_p.get("wave_period_s")
            parts = [f"Swell  {sd}" if sd else "Swell  --"]
            if sh:
                parts.append(f"{sh:.1f}m")
            if sp:
                parts.append(f"{sp:.0f}s")
            draw.text((x0, y0 + 92), "  ".join(parts),
                      font=self.f_tiny, fill=FG, anchor="lt")

            # ── Wind: use weather forecast at the best period time ──
            wx        = wx_by_time.get(best_t, {})
            wind_dir  = wx.get("wind_direction") or weather.get("current", {}).get("wind_direction")
            wind_spd  = wx.get("wind_speed_kmh")  or weather.get("current", {}).get("wind_speed_kmh")
            offshore  = _is_offshore(wind_dir, faces_deg)
            shore_lbl = "  OFFSH" if offshore is True else ("  onsh" if offshore is False else "")
            if wind_dir and wind_spd:
                draw.text((x0, y0 + 120),
                          f"Wind  {wind_dir}  {wind_spd:.0f} km/h{shore_lbl}",
                          font=self.f_tiny, fill=FG, anchor="lt")
            elif wind_dir:
                draw.text((x0, y0 + 120), f"Wind  {wind_dir}{shore_lbl}",
                          font=self.f_tiny, fill=FG, anchor="lt")

    # ── Swim ratings ─────────────────────────────────────────────────────────

    def _swim(self, draw, swim: dict):
        beaches = swim.get("beaches", [])
        if not beaches:
            return
        parts = [f"{b['name']}: {b['quality_label']}" for b in beaches]
        x = CLOCK_W + PAD * 2
        draw.text((x, 136), "  ·  ".join(parts), font=self.f_tiny, fill=FG, anchor="lt")

    # ── Section dividers ──────────────────────────────────────────────────────

    def _dividers(self, draw):
        for y in [HEADER_H, HEADER_H + GRAPH_H, HEADER_H + GRAPH_H + PRECIP_H]:
            draw.line([(0, y), (W, y)], fill=FG, width=1)
        draw.line([(CLOCK_W, 0), (CLOCK_W, HEADER_H)], fill=FG, width=1)
        y_surf = HEADER_H + GRAPH_H + PRECIP_H
        n = 4
        for j in range(1, n):
            x = j * W // n
            draw.line([(x, y_surf), (x, H)], fill=FG, width=1)
