from __future__ import annotations

from abc import ABC, abstractmethod

from prolook_mcp_core.types import BrandContext


class IOrderClient(ABC):
    @abstractmethod
    async def get_order(self, order_id: str, brand_context: BrandContext) -> dict | None: ...


class IProductClient(ABC):
    @abstractmethod
    async def list_designs(self, brand_context: BrandContext) -> list[dict]: ...
