import time

import pytest

from app.core.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_init_defaults(self):
        rl = RateLimiter()
        assert rl.max_attempts == 5
        assert rl.window_seconds == 60

    def test_init_custom(self):
        rl = RateLimiter(max_attempts=3, window_seconds=30)
        assert rl.max_attempts == 3
        assert rl.window_seconds == 30

    def test_is_allowed_first_request(self):
        rl = RateLimiter(max_attempts=5, window_seconds=60)
        assert rl.is_allowed("192.168.1.1", "test@example.com") is True

    def test_is_allowed_under_limit(self):
        rl = RateLimiter(max_attempts=3, window_seconds=60)
        assert rl.is_allowed("10.0.0.1", "a@b.com") is True
        assert rl.is_allowed("10.0.0.1", "a@b.com") is True
        assert rl.is_allowed("10.0.0.1", "a@b.com") is True

    def test_is_blocked_when_exceeded(self):
        rl = RateLimiter(max_attempts=2, window_seconds=60)
        assert rl.is_allowed("10.0.0.2", "b@c.com") is True
        assert rl.is_allowed("10.0.0.2", "b@c.com") is True
        assert rl.is_allowed("10.0.0.2", "b@c.com") is False

    def test_different_keys_independent(self):
        rl = RateLimiter(max_attempts=2, window_seconds=60)
        assert rl.is_allowed("ip1", "a@a.com") is True
        assert rl.is_allowed("ip1", "a@a.com") is True
        assert rl.is_allowed("ip1", "a@a.com") is False
        assert rl.is_allowed("ip2", "a@a.com") is True
        assert rl.is_allowed("ip1", "b@b.com") is True

    def test_window_resets_after_time(self):
        rl = RateLimiter(max_attempts=2, window_seconds=1)
        assert rl.is_allowed("10.0.0.3", "c@d.com") is True
        assert rl.is_allowed("10.0.0.3", "c@d.com") is True
        assert rl.is_allowed("10.0.0.3", "c@d.com") is False
        time.sleep(1.1)
        assert rl.is_allowed("10.0.0.3", "c@d.com") is True

    def test_get_retry_after(self):
        rl = RateLimiter(max_attempts=1, window_seconds=60)
        rl.is_allowed("10.0.0.4", "d@e.com")
        attrs = rl.get_retry_after("10.0.0.4", "d@e.com")
        assert isinstance(attrs, int)
        assert 0 < attrs <= 60

    def test_get_retry_after_no_history(self):
        rl = RateLimiter(max_attempts=5, window_seconds=60)
        assert rl.get_retry_after("new.ip", "new@email.com") == 0

    def test_reset(self):
        rl = RateLimiter(max_attempts=2, window_seconds=60)
        rl.is_allowed("10.0.0.5", "e@f.com")
        rl.is_allowed("10.0.0.5", "e@f.com")
        rl.is_allowed("10.0.0.5", "e@f.com")
        assert rl.is_allowed("10.0.0.5", "e@f.com") is False
        rl.reset("10.0.0.5", "e@f.com")
        assert rl.is_allowed("10.0.0.5", "e@f.com") is True

    def test_sliding_window_expires_old_entries(self):
        rl = RateLimiter(max_attempts=2, window_seconds=2)
        assert rl.is_allowed("ip", "e@.com") is True
        time.sleep(1)
        assert rl.is_allowed("ip", "e@.com") is True
        time.sleep(1.1)
        assert rl.is_allowed("ip", "e@.com") is True
        assert rl.is_allowed("ip", "e@.com") is False
