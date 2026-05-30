from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import fastmcp
from prolook_mcp_core.types import ToolResult


def register_ping(mcp: fastmcp.FastMCP) -> None:
    @mcp.tool()
    async def ping(message: str = "") -> dict[str, Any]:
        """Health check tool. Returns server name, timestamp, and echoed message."""
        result = ToolResult.ok(
            data={
                "server": "prolook-internal",
                "timestamp": datetime.now(tz=UTC).isoformat(),
                "message": message or "pong",
            }
        )
        return result.model_dump()
