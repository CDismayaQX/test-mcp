"""End-to-end MCP handshake smoke test for the internal server.

Run while the internal server is up:
  uv run python scripts/smoke_test_mcp.py

Expected output:
  Initialize OK: ...
  Tools: ['ping', 'order_lookup', 'order_split_lookup', 'doc_search']
"""

from __future__ import annotations

import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

_SERVICE_KEY = "a72c0a768741577a77f677e4aa2af181cc2517cfd41ed4db42a1740302b75910"
_MCP_URL = "http://localhost:8001/mcp"
_TIMEOUT_SECONDS = 10.0


async def main() -> None:
    async with streamablehttp_client(
        _MCP_URL,
        headers={"X-Api-Key": _SERVICE_KEY},
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            result = await asyncio.wait_for(session.initialize(), timeout=_TIMEOUT_SECONDS)
            print("Initialize OK:", result)
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])


asyncio.run(main())
