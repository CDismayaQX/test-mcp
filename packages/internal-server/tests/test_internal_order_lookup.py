from __future__ import annotations

from unittest.mock import AsyncMock, patch

import fastmcp
from internal_server.tools.order_lookup import _handle_order_lookup, register_order_lookup
from prolook_mcp_core.clients.interfaces import IOrderClient
from prolook_mcp_core.errors import PROLOOKUnavailableError
from prolook_mcp_core.types import BrandContext


def make_mock_client() -> AsyncMock:
    return AsyncMock(spec=IOrderClient)


_STUB_ORDER = {"id": "ORD-001", "brand_id": "prolook", "status": "processing"}


# ---------------------------------------------------------------------------
# _handle_order_lookup — logic tests
# ---------------------------------------------------------------------------


async def test_order_lookup_found_returns_ok_result() -> None:
    client = make_mock_client()
    client.get_order.return_value = _STUB_ORDER

    result = await _handle_order_lookup("ORD-001", None, client)

    assert result.status == "ok"
    assert result.data == _STUB_ORDER


async def test_order_lookup_found_with_brand_id_returns_ok_result() -> None:
    client = make_mock_client()
    order = {**_STUB_ORDER, "brand_id": "riddell"}
    client.get_order.return_value = order

    result = await _handle_order_lookup("ORD-001", "riddell", client)

    assert result.status == "ok"
    assert result.data["brand_id"] == "riddell"
    called_ctx: BrandContext = client.get_order.call_args[0][1]
    assert called_ctx.brand_id == "riddell"


async def test_order_lookup_not_found_returns_error_result() -> None:
    client = make_mock_client()
    client.get_order.return_value = None

    result = await _handle_order_lookup("ORD-404", None, client)

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "ORDER_NOT_FOUND"


async def test_order_lookup_prolook_unavailable_returns_retryable_error() -> None:
    client = make_mock_client()
    client.get_order.side_effect = PROLOOKUnavailableError("timeout")

    result = await _handle_order_lookup("ORD-001", None, client)

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "PROLOOK_UNAVAILABLE"
    assert result.error.retryable is True


async def test_order_lookup_unexpected_error_returns_generic_error() -> None:
    client = make_mock_client()
    client.get_order.side_effect = RuntimeError("unexpected")

    result = await _handle_order_lookup("ORD-001", None, client)

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

    server = fastmcp.FastMCP(name="test", version="0.0.0")
    register_order_lookup(server, client)

    with patch(
        "internal_server.tools.order_lookup.write_audit_event",
        new_callable=AsyncMock,
    ) as mock_audit:
        await server.call_tool("order_lookup", {"order_id": "ORD-001"})
        mock_audit.assert_awaited_once()
        event = mock_audit.call_args[0][0]
        assert event.tool_name == "order_lookup"
        assert event.status == "ok"
        assert event.error_code is None


async def test_order_lookup_audit_written_on_error_path() -> None:
    client = make_mock_client()
    client.get_order.return_value = None

    server = fastmcp.FastMCP(name="test", version="0.0.0")
    register_order_lookup(server, client)

    with patch(
        "internal_server.tools.order_lookup.write_audit_event",
        new_callable=AsyncMock,
    ) as mock_audit:
        await server.call_tool("order_lookup", {"order_id": "ORD-404"})
        mock_audit.assert_awaited_once()
        event = mock_audit.call_args[0][0]
        assert event.status == "error"
        assert event.error_code == "ORDER_NOT_FOUND"
