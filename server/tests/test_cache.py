import time
import pytest
from server.cache import TTLCache


def test_set_and_get():
    c = TTLCache()
    c.set("k", "hello", ttl=60)
    assert c.get("k") == "hello"


def test_miss_returns_none():
    c = TTLCache()
    assert c.get("missing") is None


def test_expired_entry_returns_none():
    c = TTLCache()
    c.set("k", "value", ttl=0)
    time.sleep(0.01)
    assert c.get("k") is None


def test_invalidate_removes_entry():
    c = TTLCache()
    c.set("k", "value", ttl=60)
    c.invalidate("k")
    assert c.get("k") is None


def test_invalidate_missing_key_is_harmless():
    c = TTLCache()
    c.invalidate("nope")  # should not raise


def test_overwrite_resets_ttl():
    c = TTLCache()
    c.set("k", "first", ttl=0)
    time.sleep(0.01)
    c.set("k", "second", ttl=60)
    assert c.get("k") == "second"
