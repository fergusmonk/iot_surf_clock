import pytest
from server.scrapers.metservice import _col, _times, _safe, _compass, _k_to_c, _ms_to_kmh, _pa_to_hpa, _frac_to_pct
from .conftest import SAMPLE_WEATHER_API


# ── _col / _times ─────────────────────────────────────────────────────────────

def test_col_extracts_variable_data():
    assert _col(SAMPLE_WEATHER_API, "air.temperature.at-2m") == [287.41, 289.95]

def test_col_missing_returns_empty():
    assert _col(SAMPLE_WEATHER_API, "nonexistent") == []

def test_times_from_dimensions():
    assert _times(SAMPLE_WEATHER_API) == ["2026-04-25T00:00:00Z", "2026-04-25T03:00:00Z"]

def test_times_missing_returns_empty():
    assert _times({}) == []


# ── _safe ─────────────────────────────────────────────────────────────────────

def test_safe_returns_float():
    assert _safe([18.5, 17.8], 0) == 18.5

def test_safe_out_of_bounds():
    assert _safe([18.5], 5) is None

def test_safe_none_value():
    assert _safe([None, 17.8], 0) is None

def test_safe_empty_list():
    assert _safe([], 0) is None


# ── Unit conversions ──────────────────────────────────────────────────────────

def test_kelvin_to_celsius():
    assert _k_to_c(273.15) == 0.0
    assert _k_to_c(287.15) == 14.0

def test_kelvin_none():
    assert _k_to_c(None) is None

def test_ms_to_kmh():
    assert _ms_to_kmh(1.0) == 3.6
    assert _ms_to_kmh(10.0) == 36.0

def test_ms_none():
    assert _ms_to_kmh(None) is None

def test_pa_to_hpa():
    assert _pa_to_hpa(101300.0) == 1013.0

def test_frac_to_pct_fraction():
    assert _frac_to_pct(0.75) == 75.0

def test_frac_to_pct_already_percent():
    assert _frac_to_pct(72.0) == 72.0

def test_frac_to_pct_none():
    assert _frac_to_pct(None) is None


# ── _compass ──────────────────────────────────────────────────────────────────

def test_compass_cardinal():
    assert _compass(0)   == "N"
    assert _compass(90)  == "E"
    assert _compass(180) == "S"
    assert _compass(270) == "W"

def test_compass_none():
    assert _compass(None) is None

def test_compass_all_16():
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    for i, expected in enumerate(dirs):
        assert _compass(i * 22.5) == expected
