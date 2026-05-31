from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import fastmcp
import uvicorn
from prolook_mcp_core.audit.logger import close_pool as close_audit_pool
from prolook_mcp_core.audit.logger import init_pool as init_audit_pool
from prolook_mcp_core.clients.prolook import ProlookDocSearchClient, ProlookOrderClient
from prolook_mcp_core.log import Log
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount

from internal_server.config import settings
from internal_server.middleware import ServiceKeyMiddleware
from internal_server.tools.doc_search import register_doc_search
from internal_server.tools.order_lookup import register_order_lookup
from internal_server.tools.ping import register_ping

mcp = fastmcp.FastMCP(name="prolook-internal", version="0.1.0")

_order_client = ProlookOrderClient()
_doc_search_client = ProlookDocSearchClient()

register_ping(mcp)
register_order_lookup(mcp, _order_client)
register_doc_search(mcp, _doc_search_client)

_mcp_app = mcp.http_app(
    transport="sse",
    middleware=[Middleware(ServiceKeyMiddleware)],
)


@asynccontextmanager
async def _lifespan(app: Starlette) -> AsyncGenerator[None, None]:
    await init_audit_pool()
    Log.info("server_started", server="prolook-internal")
    yield
    await close_audit_pool()
    await _order_client.aclose()
    await _doc_search_client.aclose()
    Log.info("server_stopped", server="prolook-internal")


app = Starlette(lifespan=_lifespan, routes=[Mount("/", app=_mcp_app)])

if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port)
