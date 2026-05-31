from __future__ import annotations

import time
import uuid
from typing import Any

import fastmcp
from prolook_mcp_core.audit.logger import write_audit_event
from prolook_mcp_core.clients.interfaces import IOrderClient
from prolook_mcp_core.errors import PROLOOKUnavailableError
from prolook_mcp_core.log import Log
from prolook_mcp_core.types import AuditEvent, BrandContext, ToolResult

from brand_server.context import get_brand_context

_TOOL_NAME = "order_lookup"
_TOOL_VERSION = "1.0"


async def _handle_order_lookup(
    order_id: str,
    client: IOrderClient,
    brand_ctx: BrandContext,
) -> ToolResult:
    """Core logic for order lookup — directly testable without FastMCP.

    Falls back to split-order lookup when the regular endpoint returns nothing,
    so callers never need to know which order type an ID belongs to.
    """
    try:
        order = await client.get_order(order_id, brand_ctx)
        if order is None:
            order = await client.get_order_split(order_id, brand_ctx)
        if order is None:
            return ToolResult.fail(
                code="ORDER_NOT_FOUND",
                message=f"Order {order_id} not found for this brand.",
            )
        return ToolResult.ok(data=order)
    except PROLOOKUnavailableError as exc:
        Log.error("tool_error", tool=_TOOL_NAME, error=str(exc))
        return ToolResult.fail(
            code="PROLOOK_UNAVAILABLE",
            message="PROLOOK is temporarily unavailable. Retry in a moment.",
            retryable=True,
        )
    except Exception:
        Log.exception("tool_unexpected_error", tool=_TOOL_NAME)
        return ToolResult.fail(
            code="UNEXPECTED_ERROR",
            message="An unexpected error occurred.",
        )


def register_order_lookup(mcp: fastmcp.FastMCP, client: IOrderClient) -> None:
    @mcp.tool()
    async def order_lookup(order_id: str) -> dict[str, Any]:
        """Look up an order by ID (regular or split). Scoped to the authenticated brand."""
        started = time.monotonic()
        brand_ctx = get_brand_context()
        result = await _handle_order_lookup(order_id, client, brand_ctx)

        await write_audit_event(
            AuditEvent(
                request_id=str(uuid.uuid4()),
                brand_id=brand_ctx.brand_id,
                tool_name=_TOOL_NAME,
                tool_version=_TOOL_VERSION,
                input_args={"order_id": order_id},
                output_summary=f"status={result.status}",
                output_size_bytes=len(str(result.model_dump())),
                latency_ms=int((time.monotonic() - started) * 1000),
                status=result.status,
                error_code=result.error.code if result.error else None,
            )
        )

        return result.model_dump()
