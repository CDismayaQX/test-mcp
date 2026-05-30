from __future__ import annotations

import time
import uuid

import fastmcp
from prolook_mcp_core.audit.logger import write_audit_event
from prolook_mcp_core.clients.interfaces import IProductClient
from prolook_mcp_core.errors import PROLOOKUnavailableError
from prolook_mcp_core.log import Log
from prolook_mcp_core.types import AuditEvent, BrandContext, ToolResult

from brand_server.context import get_brand_context

_TOOL_NAME = "list_designs"
_TOOL_VERSION = "1.0"


async def _handle_list_designs(
    client: IProductClient,
    brand_ctx: BrandContext,
) -> ToolResult:
    """Core logic for list designs — directly testable without FastMCP."""
    try:
        designs = await client.list_designs(brand_ctx)
        return ToolResult.ok(data=designs)
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


def register_list_designs(mcp: fastmcp.FastMCP, client: IProductClient) -> None:
    @mcp.tool()
    async def list_designs() -> dict:
        """List all product designs available to the authenticated brand."""
        started = time.monotonic()
        brand_ctx = get_brand_context()
        result = await _handle_list_designs(client, brand_ctx)

        await write_audit_event(
            AuditEvent(
                request_id=str(uuid.uuid4()),
                brand_id=brand_ctx.brand_id,
                tool_name=_TOOL_NAME,
                tool_version=_TOOL_VERSION,
                input_args={},
                output_summary=f"status={result.status}",
                output_size_bytes=len(str(result.model_dump())),
                latency_ms=int((time.monotonic() - started) * 1000),
                status=result.status,
                error_code=result.error.code if result.error else None,
            )
        )

        return result.model_dump()
