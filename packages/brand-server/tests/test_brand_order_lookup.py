from __future__ import annotations

from unittest.mock import AsyncMock, patch

import fastmcp
from brand_server.context import _brand_ctx_var
from brand_server.tools.order_lookup import _handle_order_lookup, register_order_lookup
from prolook_mcp_core.clients.interfaces import IOrderClient
from prolook_mcp_core.errors import PROLOOKUnavailableError
from prolook_mcp_core.types import BrandContext


def make_brand_context(brand_id: str = "test-brand-001") -> BrandContext:
    return BrandContext(brand_id=brand_id, brand_name="Test Brand")


def make_mock_client() -> AsyncMock:
    return AsyncMock(spec=IOrderClient)


_STUB_ORDER = {"id": "ORD-001", "brand_id": "test-brand-001", "status": "processing"}


# ---------------------------------------------------------------------------
# _handle_order_lookup — logic tests (no FastMCP, no audit)
# ---------------------------------------------------------------------------


async def test_order_lookup_found_returns_ok_result() -> None:
    client = make_mock_client()
    client.get_order.return_value = _STUB_ORDER
    ctx = make_brand_context()

    result = await _handle_order_lookup("ORD-001", client, ctx)

    assert result.status == "ok"
    assert result.data == _STUB_ORDER
    client.get_order.assert_awaited_once_with("ORD-001", ctx)


async def test_order_lookup_not_found_returns_error_result() -> None:
    client = make_mock_client()
    client.get_order.return_value = None
    ctx = make_brand_context()

    result = await _handle_order_lookup("ORD-404", client, ctx)

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "ORDER_NOT_FOUND"
    assert result.error.retryable is False


async def test_order_lookup_wrong_brand_returns_not_found() -> None:
    """Client enforces brand scoping by returning None for cross-brand IDs."""
    client = make_mock_client()
    client.get_order.return_value = None  # client silently blocks cross-brand access
    ctx_a = make_brand_context(brand_id="riddell")

    result = await _handle_order_lookup("ORD-001", client, ctx_a)

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "ORDER_NOT_FOUND"


async def test_order_lookup_prolook_unavailable_returns_retryable_error() -> None:
    client = make_mock_client()
    client.get_order.side_effect = PROLOOKUnavailableError("timeout")
    ctx = make_brand_context()

    result = await _handle_order_lookup("ORD-001", client, ctx)

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "PROLOOK_UNAVAILABLE"
    assert result.error.retryable is True


async def test_order_lookup_unexpected_error_returns_generic_error() -> None:
    client = make_mock_client()
    client.get_order.side_effect = RuntimeError("unexpected")
    ctx = make_brand_context()

    result = await _handle_order_lookup("ORD-001", client, ctx)

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "UNEXPECTED_ERROR"
    assert result.error.retryable is False


# ---------------------------------------------------------------------------
# Full tool — audit event verification
# ---------------------------------------------------------------------------


async def test_order_lookup_audit_written_with_correct_fields() -> None:
    client = make_mock_client()
    client.get_order.return_value = _STUB_ORDER
    brand_ctx = make_brand_context()

    server = fastmcp.FastMCP(name="test", version="0.0.0")
    register_order_lookup(server, client)

    token = _brand_ctx_var.set(brand_ctx)
    try:
        with patch(
            "brand_server.tools.order_lookup.write_audit_event",
            new_callable=AsyncMock,
        ) as mock_audit:
            await server.call_tool("order_lookup", {"order_id": "ORD-001"})
            mock_audit.assert_awaited_once()
            event = mock_audit.call_args[0][0]
            assert event.brand_id == "test-brand-001"
            assert event.tool_name == "order_lookup"
            assert event.status == "ok"
            assert event.error_code is None
    finally:
        _brand_ctx_var.reset(token)


async def test_order_lookup_audit_written_on_error_path() -> None:
    client = make_mock_client()
    client.get_order.return_value = None
    brand_ctx = make_brand_context()

    server = fastmcp.FastMCP(name="test", version="0.0.0")
    register_order_lookup(server, client)

    token = _brand_ctx_var.set(brand_ctx)
    try:
        with patch(
            "brand_server.tools.order_lookup.write_audit_event",
            new_callable=AsyncMock,
        ) as mock_audit:
            await server.call_tool("order_lookup", {"order_id": "ORD-404"})
            mock_audit.assert_awaited_once()
            event = mock_audit.call_args[0][0]
            assert event.status == "error"
            assert event.error_code == "ORDER_NOT_FOUND"
    finally:
        _brand_ctx_var.reset(token)
