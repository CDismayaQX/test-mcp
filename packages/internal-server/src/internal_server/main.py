from __future__ import annotations

import fastmcp
import uvicorn
from prolook_mcp_core.clients.prolook import ProlookOrderClient
from starlette.middleware import Middleware

from internal_server.config import settings
from internal_server.middleware import ServiceKeyMiddleware
from internal_server.tools.order_lookup import register_order_lookup
from internal_server.tools.ping import register_ping

mcp = fastmcp.FastMCP(name="prolook-internal", version="0.1.0")

_order_client = ProlookOrderClient()

register_ping(mcp)
register_order_lookup(mcp, _order_client)

if __name__ == "__main__":
    app = mcp.http_app(
        transport="sse",
        middleware=[Middleware(ServiceKeyMiddleware)],
    )
    uvicorn.run(app, host=settings.host, port=settings.port)
