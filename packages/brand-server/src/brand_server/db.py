from __future__ import annotations

from dataclasses import dataclass

import asyncpg
from prolook_mcp_core.config import settings
from prolook_mcp_core.log import Log

_pool: asyncpg.Pool | None = None

_MIN_POOL_SIZE: int = 1
_MAX_POOL_SIZE: int = 5


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=settings.database_dsn,
            min_size=_MIN_POOL_SIZE,
            max_size=_MAX_POOL_SIZE,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


@dataclass(frozen=True)
class BrandKeyRecord:
    brand_id: str
    brand_name: str
    key_hash: str
    rate_limit_per_minute: int
    status: str


async def lookup_brand_key(key_prefix: str) -> BrandKeyRecord | None:
    """Look up a brand API key record by its lookup prefix. Returns None if not found."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT bak.brand_id, b.name AS brand_name, bak.key_hash,
                       bak.rate_limit_per_minute, bak.status
                FROM brand_api_keys bak
                JOIN brands b ON b.id = bak.brand_id
                WHERE bak.key_prefix = $1
                """,
                key_prefix,
            )
    except Exception as exc:
        Log.error("db_lookup_failed", error=str(exc))
        return None

    if row is None:
        return None

    return BrandKeyRecord(
        brand_id=row["brand_id"],
        brand_name=row["brand_name"],
        key_hash=row["key_hash"],
        rate_limit_per_minute=row["rate_limit_per_minute"],
        status=row["status"],
    )
