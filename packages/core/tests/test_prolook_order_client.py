from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from prolook_mcp_core.clients.prolook import ProlookOrderClient
from prolook_mcp_core.errors import PROLOOKUnavailableError
from prolook_mcp_core.types import BrandContext


def make_brand_context(brand_id: str = "test-brand-001") -> BrandContext:
    return BrandContext(brand_id=brand_id, brand_name="Test Brand")


_STUB_ORDER = {"id": "ORD-001", "brand_id": "test-brand-001", "status": "processing"}


def _mock_response(status_code: int, body: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    if body is not None:
        resp.json.return_value = body
    return resp


# ---------------------------------------------------------------------------
# ProlookOrderClient.get_order — brand scoping
# ---------------------------------------------------------------------------


async def test_get_order_matching_brand_returns_order() -> None:
    client = ProlookOrderClient()
    ctx = make_brand_context(brand_id="test-brand-001")
    with patch.object(
        client._http,
        "get",
        new_callable=AsyncMock,
        return_value=_mock_response(200, _STUB_ORDER),
    ):
        result = await client.get_order("ORD-001", ctx)
    assert result == _STUB_ORDER


async def test_get_order_wrong_brand_returns_none() -> None:
    """brand_id mismatch is silently blocked — cross-brand data never returned."""
    client = ProlookOrderClient()
    ctx = make_brand_context(brand_id="new-balance")
    with patch.object(
        client._http,
        "get",
        new_callable=AsyncMock,
        return_value=_mock_response(200, {"id": "ORD-001", "brand_id": "riddell"}),
    ):
        result = await client.get_order("ORD-001", ctx)
    assert result is None


async def test_get_order_not_found_returns_none() -> None:
    client = ProlookOrderClient()
    ctx = make_brand_context()
    with patch.object(
        client._http,
        "get",
        new_callable=AsyncMock,
        return_value=_mock_response(404),
    ):
        result = await client.get_order("ORD-404", ctx)
    assert result is None


async def test_get_order_server_error_raises_unavailable() -> None:
    client = ProlookOrderClient()
    ctx = make_brand_context()
    with (
        patch.object(
            client._http,
            "get",
            new_callable=AsyncMock,
            return_value=_mock_response(500),
        ),
        pytest.raises(PROLOOKUnavailableError),
    ):
        await client.get_order("ORD-001", ctx)


async def test_get_order_request_error_raises_unavailable() -> None:
    client = ProlookOrderClient()
    ctx = make_brand_context()
    with (
        patch.object(
            client._http,
            "get",
            new_callable=AsyncMock,
            side_effect=httpx.RequestError("connection refused"),
        ),
        pytest.raises(PROLOOKUnavailableError),
    ):
        await client.get_order("ORD-001", ctx)
