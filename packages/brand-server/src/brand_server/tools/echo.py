from __future__ import annotations

import time
import uuid
from typing import Any

import fastmcp
from prolook_mcp_core.audit.logger import write_audit_event
from prolook_mcp_core.log import Log
from prolook_mcp_core.types import AuditEvent, BrandContext, ToolResult

from brand_server.context import get_brand_context

_TOOL_NAME = "echo"
_TOOL_VERSION = "1.0"


async def _handle_echo(message: str, force_error: bool, brand_ctx: BrandContext) -> ToolResult:
    """Core logic for echo — directly testable without FastMCP."""
    if force_error:
        Log.error("tool_error", tool=_TOOL_NAME, reason="force_error=True")
        return ToolResult.fail(code="FORCED_ERROR", message="Forced error for testing.")
    return ToolResult.ok(data={"echo": message, "brand_id": brand_ctx.brand_id})


def register_echo(mcp: fastmcp.FastMCP) -> None:
    @mcp.tool()
    async def echo(message: str, force_error: bool = False) -> dict[str, Any]:
        """Echo the message back with brand_id. Set force_error=true to test the error path."""
        started = time.monotonic()
        brand_ctx = get_brand_context()
        result = await _handle_echo(message, force_error, brand_ctx)

        await write_audit_event(
            AuditEvent(
                request_id=str(uuid.uuid4()),
                brand_id=brand_ctx.brand_id,
                tool_name=_TOOL_NAME,
                tool_version=_TOOL_VERSION,
                input_args={"message": message, "force_error": force_error},
                output_summary=f"status={result.status}",
                output_size_bytes=len(str(result.model_dump())),
                latency_ms=int((time.monotonic() - started) * 1000),
                status=result.status,
                error_code=result.error.code if result.error else None,
            )
        )

        return result.model_dump()
