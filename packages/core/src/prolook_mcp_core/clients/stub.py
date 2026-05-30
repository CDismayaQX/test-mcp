from __future__ import annotations

from typing import Any

from prolook_mcp_core.clients.interfaces import IDocSearchClient, IOrderClient, IProductClient
from prolook_mcp_core.types import BrandContext

_STUB_ORDERS: dict[str, dict[str, Any]] = {
    "ORD-001": {
        "id": "ORD-001",
        "brand_id": "test-brand-001",
        "status": "processing",
        "created_at": "2026-01-15T10:00:00Z",
        "line_items": [{"sku": "HELM-RED-L", "qty": 2}],
    },
    "ORD-ERR": {
        "id": "ORD-ERR",
        "brand_id": "test-brand-001",
        "status": "error",
        "created_at": "2026-01-15T11:00:00Z",
        "line_items": [],
    },
}

_STUB_DESIGNS: list[dict[str, Any]] = [
    {
        "id": "DES-001",
        "brand_id": "test-brand-001",
        "name": "Helmet Design A",
        "sport": "football",
    },
    {
        "id": "DES-002",
        "brand_id": "test-brand-001",
        "name": "Jersey Design B",
        "sport": "baseball",
    },
]


class StubOrderClient(IOrderClient):
    """In-memory stub for local dev and unit tests. Enforces brand scoping."""

    async def get_order(self, order_id: str, brand_context: BrandContext) -> dict[str, Any] | None:
        order = _STUB_ORDERS.get(order_id)
        if order is None:
            return None
        if order["brand_id"] != brand_context.brand_id:
            return None
        return order


class StubProductClient(IProductClient):
    """In-memory stub for local dev and unit tests. Enforces brand scoping."""

    async def list_designs(self, brand_context: BrandContext) -> list[dict[str, Any]]:
        return [d for d in _STUB_DESIGNS if d["brand_id"] == brand_context.brand_id]


_STUB_SEARCH_RESULTS: list[dict[str, Any]] = [
    {"id": "DOC-001", "title": "Helmet Customization Guide", "score": 0.95},
    {"id": "DOC-002", "title": "Jersey Sizing Standards", "score": 0.82},
]


class StubDocSearchClient(IDocSearchClient):
    """In-memory stub for local dev and unit tests."""

    async def search(
        self, query: str, kb_ids: list[str] | None, top_k: int
    ) -> list[dict[str, Any]]:
        return _STUB_SEARCH_RESULTS[:top_k]
