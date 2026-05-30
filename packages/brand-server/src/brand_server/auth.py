from __future__ import annotations

import bcrypt
from prolook_mcp_core.errors import InvalidAPIKeyError
from prolook_mcp_core.log import Log
from prolook_mcp_core.types import BrandContext

from brand_server.db import lookup_brand_key

_KEY_ACTIVE_STATUS = "active"


def key_prefix(api_key: str) -> str:
    """Return the first 8 chars of the key — safe to put in logs."""
    return api_key[:8] if api_key else ""


def _lookup_prefix(api_key: str) -> str:
    """Split at the last underscore to get the DB lookup prefix."""
    if "_" not in api_key:
        return api_key
    return api_key.rsplit("_", 1)[0]


def verify_api_key(presented_key: str | None, stored_hash: str | None) -> bool:
    """Constant-time verification of a full API key against its bcrypt hash."""
    if not presented_key or not stored_hash:
        return False
    try:
        return bcrypt.checkpw(presented_key.encode(), stored_hash.encode())
    except ValueError:
        return False


async def resolve_brand_context(presented_key: str | None) -> BrandContext:
    """Resolve a presented API key to a BrandContext.

    On ANY failure raises the same generic InvalidAPIKeyError to prevent
    oracle attacks — callers must never learn which check failed.
    """
    log_prefix = key_prefix(presented_key or "")

    if not presented_key:
        Log.warning("auth_failed", key_prefix=log_prefix, reason="generic")
        raise InvalidAPIKeyError()

    lookup = _lookup_prefix(presented_key)
    record = await lookup_brand_key(lookup)

    if record is None or record.status != _KEY_ACTIVE_STATUS:
        Log.warning("auth_failed", key_prefix=log_prefix, reason="generic")
        raise InvalidAPIKeyError()

    if not verify_api_key(presented_key, record.key_hash):
        Log.warning("auth_failed", key_prefix=log_prefix, reason="generic")
        raise InvalidAPIKeyError()

    Log.info("auth_ok", key_prefix=log_prefix, brand_id=record.brand_id)
    return BrandContext(brand_id=record.brand_id, brand_name=record.brand_name)
