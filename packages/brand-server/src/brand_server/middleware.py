from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis
from prolook_mcp_core.errors import InvalidAPIKeyError, RateLimitError
from prolook_mcp_core.log import Log
from starlette.types import ASGIApp, Receive, Scope, Send

from brand_server.auth import resolve_brand_context
from brand_server.context import _brand_ctx_var
from brand_server.rate_limit import enforce_rate_limit

_AUTH_HEADER = b"authorization"
_API_KEY_HEADER = b"x-api-key"
_BEARER_PREFIX = "Bearer "


def _extract_api_key(headers: dict[bytes, bytes]) -> str | None:
    if _API_KEY_HEADER in headers:
        return headers[_API_KEY_HEADER].decode()
    auth = headers.get(_AUTH_HEADER, b"").decode()
    if auth.startswith(_BEARER_PREFIX):
        return auth[len(_BEARER_PREFIX) :]
    return None


async def _send_response(send: Send, status: int, body: dict[str, Any]) -> None:
    encoded = json.dumps(body).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(encoded)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": encoded})


class BrandAuthMiddleware:
    """Pure ASGI middleware: authenticates API key and enforces per-brand rate limit.

    Safe for SSE streaming — does not buffer the response body.
    """

    def __init__(
        self,
        app: ASGIApp,
        redis_client: aioredis.Redis,
        rate_limit_per_minute: int,
    ) -> None:
        self._app = app
        self._redis = redis_client
        self._rate_limit = rate_limit_per_minute

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        headers = {k.lower(): v for k, v in scope.get("headers", [])}
        api_key = _extract_api_key(headers)

        try:
            brand_ctx = await resolve_brand_context(api_key)
        except InvalidAPIKeyError:
            await _send_response(send, 401, {"error": "Unauthorized"})
            return

        try:
            await enforce_rate_limit(self._redis, brand_ctx.brand_id, self._rate_limit)
        except RateLimitError as exc:
            Log.warning("rate_limited", brand_id=brand_ctx.brand_id)
            await _send_response(
                send,
                429,
                {"error": "Rate limit exceeded", "retry_after": exc.retry_after},
            )
            return

        token = _brand_ctx_var.set(brand_ctx)
        try:
            await self._app(scope, receive, send)
        finally:
            _brand_ctx_var.reset(token)
