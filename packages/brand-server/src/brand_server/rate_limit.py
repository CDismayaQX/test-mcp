from __future__ import annotations

import redis.asyncio as redis
from prolook_mcp_core.errors import RateLimitError
from prolook_mcp_core.log import Log

_WINDOW_SECONDS = 60


async def enforce_rate_limit(
    client: redis.Redis,
    brand_id: str,
    limit_per_minute: int,
) -> None:
    """Per-brand fixed-window rate limit backed by Redis.

    Increments a per-brand counter keyed to the current minute window. On the
    first increment the key is given a TTL equal to the window length. If the
    count exceeds the limit, a RateLimitError is raised with a retry hint.
    """
    key = f"ratelimit:{brand_id}:{_WINDOW_SECONDS}"
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, _WINDOW_SECONDS)

    if count > limit_per_minute:
        ttl = await client.ttl(key)
        retry_after = ttl if ttl and ttl > 0 else _WINDOW_SECONDS
        Log.warning("rate_limited", brand_id=brand_id, retry_after=retry_after)
        raise RateLimitError(retry_after=retry_after)
