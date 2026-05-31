from __future__ import annotations

from typing import Any, cast

import httpx

from prolook_mcp_core.clients.interfaces import IDocSearchClient, IOrderClient, IProductClient
from prolook_mcp_core.config import settings
from prolook_mcp_core.errors import PROLOOKUnavailableError
from prolook_mcp_core.log import Log
from prolook_mcp_core.types import BrandContext

_TIMEOUT_SECONDS: float = 10.0
_RETRY_ATTEMPTS: int = 2


class ProlookOrderClient(IOrderClient):
    """HTTP client for order data via the AI Platform API. Enforces brand scoping."""

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(
            base_url=settings.AI_PLATFORM_API_URL,
            timeout=_TIMEOUT_SECONDS,
            transport=httpx.AsyncHTTPTransport(retries=_RETRY_ATTEMPTS),
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def get_order(self, order_id: str, brand_context: BrandContext) -> dict[str, Any] | None:
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

        order = cast(dict[str, Any], response.json())
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
            transport=httpx.AsyncHTTPTransport(retries=_RETRY_ATTEMPTS),
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def list_designs(self, brand_context: BrandContext) -> list[dict[str, Any]]:
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

        designs = cast(list[dict[str, Any]], response.json())
        return [d for d in designs if d.get("brand_id") == brand_context.brand_id]


class ProlookDocSearchClient(IDocSearchClient):
    """HTTP client for RAG doc search via the AI Platform API's internal endpoint."""

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(
            base_url=settings.AI_PLATFORM_API_URL,
            headers={"X-Service-Key": settings.INTERNAL_SERVICE_KEY},
            timeout=_TIMEOUT_SECONDS,
            transport=httpx.AsyncHTTPTransport(retries=_RETRY_ATTEMPTS),
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def search(
        self, query: str, kb_ids: list[str] | None, top_k: int
    ) -> list[dict[str, Any]]:
        try:
            response = await self._http.post(
                "/internal/rag/search",
                json={"query": query, "kb_ids": kb_ids, "top_k": top_k},
            )
        except httpx.RequestError as exc:
            raise PROLOOKUnavailableError(str(exc)) from exc

        if response.status_code != 200:
            Log.error("rag_search_error", status=response.status_code)
            raise PROLOOKUnavailableError(f"Unexpected status {response.status_code}")

        results = cast(list[dict[str, Any]], response.json())
        return results
