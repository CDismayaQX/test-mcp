from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from prolook_mcp_core.types import BrandContext


class IOrderClient(ABC):
    @abstractmethod
    async def get_order(
        self, order_id: str, brand_context: BrandContext
    ) -> dict[str, Any] | None: ...


class IProductClient(ABC):
    @abstractmethod
    async def list_designs(self, brand_context: BrandContext) -> list[dict[str, Any]]: ...


class IDocSearchClient(ABC):
    @abstractmethod
    async def search(
        self, query: str, kb_ids: list[str] | None, top_k: int
    ) -> list[dict[str, Any]]: ...
