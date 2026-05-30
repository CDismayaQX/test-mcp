from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from brand_server.rate_limit import enforce_rate_limit
from prolook_mcp_core.errors import RateLimitError


def _make_redis(count: int, ttl: int = 30) -> AsyncMock:
    redis = AsyncMock()
    redis.incr.return_value = count
    redis.expire.return_value = True
    redis.ttl.return_value = ttl
    return redis


async def test_enforce_rate_limit_under_limit_does_not_raise() -> None:
    redis = _make_redis(count=1)
    await enforce_rate_limit(redis, "riddell", limit_per_minute=100)
    redis.incr.assert_awaited_once()


async def test_enforce_rate_limit_first_request_sets_expiry() -> None:
    redis = _make_redis(count=1)
    await enforce_rate_limit(redis, "riddell", limit_per_minute=100)
    redis.expire.assert_awaited_once()


async def test_enforce_rate_limit_subsequent_request_does_not_reset_expiry() -> None:
    redis = _make_redis(count=5)
    await enforce_rate_limit(redis, "riddell", limit_per_minute=100)
    redis.expire.assert_not_awaited()


async def test_enforce_rate_limit_at_limit_does_not_raise() -> None:
    redis = _make_redis(count=100)
    await enforce_rate_limit(redis, "riddell", limit_per_minute=100)


async def test_enforce_rate_limit_over_limit_raises_rate_limit_error() -> None:
    redis = _make_redis(count=101, ttl=45)
    with pytest.raises(RateLimitError) as exc_info:
        await enforce_rate_limit(redis, "riddell", limit_per_minute=100)
    assert exc_info.value.retry_after == 45


async def test_enforce_rate_limit_uses_brand_id_in_key() -> None:
    redis = _make_redis(count=1)
    await enforce_rate_limit(redis, "brand-abc", limit_per_minute=50)
    call_args = redis.incr.call_args[0][0]
    assert "brand-abc" in call_args
