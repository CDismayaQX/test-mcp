from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import fastmcp
import redis.asyncio as aioredis
import uvicorn
from prolook_mcp_core.audit.logger import close_pool as close_audit_pool
from prolook_mcp_core.audit.logger import init_pool as init_audit_pool
from prolook_mcp_core.clients.prolook import ProlookOrderClient, ProlookProductClient
from prolook_mcp_core.log import Log
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount

from brand_server.config import settings
from brand_server.db import close_pool as close_db_pool
from brand_server.db import init_pool as init_db_pool
from brand_server.middleware import BrandAuthMiddleware
from brand_server.tools.list_designs import register_list_designs
from brand_server.tools.order_lookup import register_order_lookup
from brand_server.tools.order_split_lookup import register_order_split_lookup
from brand_server.tools.ping import register_ping

mcp = fastmcp.FastMCP(name="prolook-brand", version="0.1.0")

_order_client = ProlookOrderClient()
_product_client = ProlookProductClient()
_redis = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=False)

register_ping(mcp)
register_order_lookup(mcp, _order_client)
register_order_split_lookup(mcp, _order_client)
register_list_designs(mcp, _product_client)

_mcp_app = mcp.http_app(
    transport="http",
    stateless_http=True,
    middleware=[
        Middleware(
            BrandAuthMiddleware,
            redis_client=_redis,
            rate_limit_per_minute=settings.rate_limit_per_minute,
        )
    ],
)


@asynccontextmanager
async def _lifespan(app: Starlette) -> AsyncGenerator[None, None]:
    await init_db_pool()
    await init_audit_pool()
    Log.info("server_started", server="prolook-brand")
    async with _mcp_app.lifespan(app):
        yield
    await close_db_pool()
    await close_audit_pool()
    await _order_client.aclose()
    await _product_client.aclose()
    await _redis.aclose()
    Log.info("server_stopped", server="prolook-brand")


app = Starlette(lifespan=_lifespan, routes=[Mount("/", app=_mcp_app)])

if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port)
