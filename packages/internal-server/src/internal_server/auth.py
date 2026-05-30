from __future__ import annotations

import hmac

from prolook_mcp_core.errors import InvalidAPIKeyError
from prolook_mcp_core.log import Log


def verify_service_key(presented_key: str | None) -> None:
    """Verify a service-to-service key for the internal server.

    Internal callers are trusted services, not per-brand tenants, so a
    single shared service key is used. Comparison is constant-time. On any
    failure a generic InvalidAPIKeyError is raised — callers must not learn
    whether the key was absent, malformed, or simply wrong.
    """
    from internal_server.config import settings

    expected = settings.internal_service_key
    if not expected or not presented_key:
        Log.warning("auth_failed", reason="missing_key")
        raise InvalidAPIKeyError()

    if not hmac.compare_digest(presented_key, expected):
        Log.warning("auth_failed", reason="mismatch")
        raise InvalidAPIKeyError()
