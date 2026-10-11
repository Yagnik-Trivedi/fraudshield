import fakeredis

from fraudshield import __version__
from fraudshield.config import Settings


def test_package_imports():
    assert __version__


def test_settings_defaults():
    s = Settings(_env_file=None)
    assert s.fn_cost > s.fp_cost > 0
    assert s.kafka_bootstrap.endswith(":19092")


def test_window_semantics_reference():
    """Reference for Phase 3: Redis window counting must match the offline [t - w, t) definition."""
    r = fakeredis.FakeRedis()
    key, t = "card:1:tx", 100_000
    for ts in (t - 86_400, t - 600, t - 1, t):  # exactly 24h ago, exactly 10m ago, 1s ago, same instant
        r.zadd(key, {f"{ts}:x": ts})
    r.zremrangebyscore(key, "-inf", f"({t - 86_400}")  # exclusive: keeps the event exactly 24h old
    assert r.zcount(key, t - 86_400, f"({t}") == 3  # [t-24h, t): excludes same-instant event
    assert r.zcount(key, t - 600, f"({t}") == 2  # [t-10m, t)
