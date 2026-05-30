from __future__ import annotations

from contextvars import ContextVar

from prolook_mcp_core.types import BrandContext

_brand_ctx_var: ContextVar[BrandContext | None] = ContextVar("brand_ctx", default=None)


def get_brand_context() -> BrandContext:
    ctx = _brand_ctx_var.get()
    if ctx is None:
        raise RuntimeError("BrandContext not set — auth middleware did not run")
    return ctx


def set_brand_context(ctx: BrandContext) -> None:
    _brand_ctx_var.set(ctx)
