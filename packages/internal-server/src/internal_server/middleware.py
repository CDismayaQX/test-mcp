from __future__ import annotations

import json
from typing import Any

from prolook_mcp_core.errors import InvalidAPIKeyError
from starlette.types import ASGIApp, Receive, Scope, Send

from internal_server.auth import verify_service_key

_AUTH_HEADER = b"authorization"
_API_KEY_HEADER = b"x-api-key"
_BEARER_PREFIX = "Bearer "


def _extract_key(headers: dict[bytes, bytes]) -> str | None:
    if _API_KEY_HEADER in headers:
        return headers[_API_KEY_HEADER].decode()
    auth = headers.get(_AUTH_HEADER, b"").decode()
    if auth.startswith(_BEARER_PREFIX):
        return auth[len(_BEARER_PREFIX) :]
    return None


async def _send_401(send: Any) -> None:
    body = json.dumps({"error": "Unauthorized"}).encode()
    await send(
        {
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


class ServiceKeyMiddleware:
    """Pure ASGI middleware: validates the internal service-to-service API key.

    Safe for streaming responses — does not buffer the response body.
    """

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        headers = {k.lower(): v for k, v in scope.get("headers", [])}
        key = _extract_key(headers)

        try:
            verify_service_key(key)
        except InvalidAPIKeyError:
            await _send_401(send)
            return

        await self._app(scope, receive, send)
