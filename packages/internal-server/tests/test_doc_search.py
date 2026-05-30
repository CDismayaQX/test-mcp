from __future__ import annotations

from unittest.mock import AsyncMock, patch

import fastmcp
from internal_server.tools.doc_search import _handle_doc_search, register_doc_search
from prolook_mcp_core.clients.interfaces import IDocSearchClient
from prolook_mcp_core.errors import PROLOOKUnavailableError

_STUB_RESULTS = [
    {"id": "DOC-001", "title": "Helmet Customization Guide", "score": 0.95},
    {"id": "DOC-002", "title": "Jersey Sizing Standards", "score": 0.82},
]


def make_mock_client() -> AsyncMock:
    return AsyncMock(spec=IDocSearchClient)


# ---------------------------------------------------------------------------
# _handle_doc_search — logic tests (no FastMCP, no audit)
# ---------------------------------------------------------------------------


async def test_doc_search_returns_ok_result() -> None:
    client = make_mock_client()
    client.search.return_value = _STUB_RESULTS

    result = await _handle_doc_search("helmets", None, 5, client)

    assert result.status == "ok"
    assert result.data is not None
    assert result.data["results"] == _STUB_RESULTS
    assert result.data["query"] == "helmets"
    client.search.assert_awaited_once_with("helmets", None, 5)


async def test_doc_search_empty_results_returns_ok() -> None:
    client = make_mock_client()
    client.search.return_value = []

    result = await _handle_doc_search("nothing matches", None, 5, client)

    assert result.status == "ok"
    assert result.data is not None
    assert result.data["results"] == []


async def test_doc_search_with_kb_ids_passes_them_to_client() -> None:
    client = make_mock_client()
    client.search.return_value = _STUB_RESULTS

    await _handle_doc_search("query", ["kb-1", "kb-2"], 3, client)

    client.search.assert_awaited_once_with("query", ["kb-1", "kb-2"], 3)


async def test_doc_search_rag_unavailable_returns_retryable_error() -> None:
    client = make_mock_client()
    client.search.side_effect = PROLOOKUnavailableError("timeout")

    result = await _handle_doc_search("helmets", None, 5, client)

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "RAG_UNAVAILABLE"
    assert result.error.retryable is True


async def test_doc_search_unexpected_error_returns_generic_error() -> None:
    client = make_mock_client()
    client.search.side_effect = RuntimeError("unexpected")

    result = await _handle_doc_search("helmets", None, 5, client)

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "UNEXPECTED_ERROR"
    assert result.error.retryable is False


# ---------------------------------------------------------------------------
# Full tool — audit event verification
# ---------------------------------------------------------------------------


async def test_doc_search_audit_written_with_correct_fields() -> None:
    client = make_mock_client()
    client.search.return_value = _STUB_RESULTS

    server = fastmcp.FastMCP(name="test", version="0.0.0")
    register_doc_search(server, client)

    with patch(
        "internal_server.tools.doc_search.write_audit_event",
        new_callable=AsyncMock,
    ) as mock_audit:
        await server.call_tool("doc_search", {"query": "helmets"})
        mock_audit.assert_awaited_once()
        event = mock_audit.call_args[0][0]
        assert event.tool_name == "doc_search"
        assert event.status == "ok"
        assert event.error_code is None
        assert "count=2" in event.output_summary


async def test_doc_search_audit_written_on_error_path() -> None:
    client = make_mock_client()
    client.search.side_effect = PROLOOKUnavailableError("down")

    server = fastmcp.FastMCP(name="test", version="0.0.0")
    register_doc_search(server, client)

    with patch(
        "internal_server.tools.doc_search.write_audit_event",
        new_callable=AsyncMock,
    ) as mock_audit:
        await server.call_tool("doc_search", {"query": "helmets"})
        mock_audit.assert_awaited_once()
        event = mock_audit.call_args[0][0]
        assert event.status == "error"
        assert event.error_code == "RAG_UNAVAILABLE"
