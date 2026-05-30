from __future__ import annotations

from unittest.mock import AsyncMock, patch

import fastmcp
from brand_server.context import _brand_ctx_var
from brand_server.tools.list_designs import _handle_list_designs, register_list_designs
from prolook_mcp_core.clients.interfaces import IProductClient
from prolook_mcp_core.errors import PROLOOKUnavailableError
from prolook_mcp_core.types import BrandContext


def make_brand_context(brand_id: str = "test-brand-001") -> BrandContext:
    return BrandContext(brand_id=brand_id, brand_name="Test Brand")


def make_mock_client() -> AsyncMock:
    return AsyncMock(spec=IProductClient)


_STUB_DESIGNS = [
    {"id": "DES-001", "brand_id": "test-brand-001", "name": "Helmet A"},
    {"id": "DES-002", "brand_id": "test-brand-001", "name": "Jersey B"},
]


# ---------------------------------------------------------------------------
# _handle_list_designs — logic tests
# ---------------------------------------------------------------------------


async def test_list_designs_found_returns_ok_result() -> None:
    client = make_mock_client()
    client.list_designs.return_value = _STUB_DESIGNS
    ctx = make_brand_context()

    result = await _handle_list_designs(client, ctx)

    assert result.status == "ok"
    assert result.data == _STUB_DESIGNS
    client.list_designs.assert_awaited_once_with(ctx)


async def test_list_designs_empty_returns_ok_with_empty_list() -> None:
    client = make_mock_client()
    client.list_designs.return_value = []
    ctx = make_brand_context()

    result = await _handle_list_designs(client, ctx)

    assert result.status == "ok"
    assert result.data == []


async def test_list_designs_wrong_brand_returns_empty() -> None:
    """Client enforces brand scoping by returning only this brand's designs."""
    client = make_mock_client()
    client.list_designs.return_value = []  # no designs for this brand
    ctx = make_brand_context(brand_id="other-brand")

    result = await _handle_list_designs(client, ctx)

    assert result.status == "ok"
    assert result.data == []


async def test_list_designs_prolook_unavailable_returns_retryable_error() -> None:
    client = make_mock_client()
    client.list_designs.side_effect = PROLOOKUnavailableError("timeout")
    ctx = make_brand_context()

    result = await _handle_list_designs(client, ctx)

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "PROLOOK_UNAVAILABLE"
    assert result.error.retryable is True


async def test_list_designs_unexpected_error_returns_generic_error() -> None:
    client = make_mock_client()
    client.list_designs.side_effect = RuntimeError("unexpected")
    ctx = make_brand_context()

    result = await _handle_list_designs(client, ctx)

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "UNEXPECTED_ERROR"


# ---------------------------------------------------------------------------
# Full tool — audit event verification
# ---------------------------------------------------------------------------


async def test_list_designs_audit_written_with_correct_fields() -> None:
    client = make_mock_client()
    client.list_designs.return_value = _STUB_DESIGNS
    brand_ctx = make_brand_context()

    server = fastmcp.FastMCP(name="test", version="0.0.0")
    register_list_designs(server, client)

    token = _brand_ctx_var.set(brand_ctx)
    try:
        with patch(
            "brand_server.tools.list_designs.write_audit_event",
            new_callable=AsyncMock,
        ) as mock_audit:
            await server.call_tool("list_designs", {})
            mock_audit.assert_awaited_once()
            event = mock_audit.call_args[0][0]
            assert event.brand_id == "test-brand-001"
            assert event.tool_name == "list_designs"
            assert event.status == "ok"
            assert event.error_code is None
    finally:
        _brand_ctx_var.reset(token)
