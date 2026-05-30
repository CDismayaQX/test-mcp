from __future__ import annotations

import httpx

from prolook_mcp_core.clients.interfaces import IOrderClient, IProductClient
from prolook_mcp_core.config import settings
from prolook_mcp_core.errors import PROLOOKUnavailableError
from prolook_mcp_core.log import Log
from prolook_mcp_core.types import BrandContext

_TIMEOUT_SECONDS: float = 10.0


class ProlookOrderClient(IOrderClient):
    """HTTP client for order data via the AI Platform API. Enforces brand scoping."""

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(
            base_url=settings.AI_PLATFORM_API_URL,
            timeout=_TIMEOUT_SECONDS,
        )

    async def get_order(self, order_id: str, brand_context: BrandContext) -> dict | None:
        try:
            response = await self._http.get(f"/api/orders/{order_id}")
        except httpx.RequestError as exc:
            raise PROLOOKUnavailableError(str(exc)) from exc

        if response.status_code == 404:
            return None
        if response.status_code != 200:
            Log.error(
                "prolook_order_error",
                order_id=order_id,
                status=response.status_code,
            )
            raise PROLOOKUnavailableError(f"Unexpected status {response.status_code}")

        order = response.json()
        if order.get("brand_id") != brand_context.brand_id:
            Log.warning(
                "brand_scope_blocked",
                order_id=order_id,
                brand_id=brand_context.brand_id,
            )
            return None
        return order


class ProlookProductClient(IProductClient):
    """HTTP client for product/design data via the AI Platform API. Enforces brand scoping."""

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(
            base_url=settings.AI_PLATFORM_API_URL,
            timeout=_TIMEOUT_SECONDS,
        )

    async def list_designs(self, brand_context: BrandContext) -> list[dict]:
        try:
            response = await self._http.get(
                "/api/designs",
                params={"brand_id": brand_context.brand_id},
            )
        except httpx.RequestError as exc:
            raise PROLOOKUnavailableError(str(exc)) from exc

        if response.status_code != 200:
            Log.error(
                "prolook_designs_error",
                brand_id=brand_context.brand_id,
                status=response.status_code,
            )
            raise PROLOOKUnavailableError(f"Unexpected status {response.status_code}")

        designs: list[dict] = response.json()
        return [d for d in designs if d.get("brand_id") == brand_context.brand_id]
