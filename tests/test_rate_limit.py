from app.rate_limit import SlidingWindowRateLimiter


def test_sliding_window_rate_limiter():
    limiter = SlidingWindowRateLimiter()
    assert limiter.allow(bucket="orders", identity="1.2.3.4", limit=2, window_seconds=10, now=100)
    assert limiter.allow(bucket="orders", identity="1.2.3.4", limit=2, window_seconds=10, now=101)
    assert not limiter.allow(bucket="orders", identity="1.2.3.4", limit=2, window_seconds=10, now=102)
    assert limiter.allow(bucket="orders", identity="1.2.3.4", limit=2, window_seconds=10, now=111)


def test_rate_limit_buckets_are_independent():
    limiter = SlidingWindowRateLimiter()
    assert limiter.allow(bucket="orders", identity="ip", limit=1, window_seconds=60, now=1)
    assert not limiter.allow(bucket="orders", identity="ip", limit=1, window_seconds=60, now=2)
    assert limiter.allow(bucket="shipping", identity="ip", limit=1, window_seconds=60, now=2)
