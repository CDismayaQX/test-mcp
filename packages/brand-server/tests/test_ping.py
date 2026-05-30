from __future__ import annotations

import fastmcp
import pytest
from brand_server.tools.ping import register_ping


@pytest.fixture
def mcp() -> fastmcp.FastMCP:
    server = fastmcp.FastMCP(name="test-brand", version="0.0.0")
    register_ping(server)
    return server


async def test_ping_registers(mcp: fastmcp.FastMCP) -> None:
    tools = await mcp.list_tools()
    assert any(t.name == "ping" for t in tools)
