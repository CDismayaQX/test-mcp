from __future__ import annotations

import fastmcp
import redis.asyncio as aioredis
import uvicorn
from prolook_mcp_core.clients.prolook import ProlookOrderClient, ProlookProductClient
from starlette.middleware import Middleware

from brand_server.config import settings
from brand_server.middleware import BrandAuthMiddleware
from brand_server.tools.list_designs import register_list_designs
from brand_server.tools.order_lookup import register_order_lookup
from brand_server.tools.ping import register_ping

mcp = fastmcp.FastMCP(name="prolook-brand", version="0.1.0")

_order_client = ProlookOrderClient()
_product_client = ProlookProductClient()

register_ping(mcp)
register_order_lookup(mcp, _order_client)
register_list_designs(mcp, _product_client)

if __name__ == "__main__":
    _redis = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=False)
    app = mcp.http_app(
        transport="sse",
        middleware=[
            Middleware(
                BrandAuthMiddleware,
                redis_client=_redis,
                rate_limit_per_minute=settings.rate_limit_per_minute,
            )
        ],
    )
    uvicorn.run(app, host=settings.host, port=settings.port)
