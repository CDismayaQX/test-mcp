from __future__ import annotations

import time
import uuid
from typing import Any

import fastmcp
from prolook_mcp_core.audit.logger import write_audit_event
from prolook_mcp_core.clients.interfaces import IDocSearchClient
from prolook_mcp_core.errors import PROLOOKUnavailableError
from prolook_mcp_core.log import Log
from prolook_mcp_core.types import AuditEvent, ToolResult

_TOOL_NAME = "doc_search"
_TOOL_VERSION = "1.0"


async def _handle_doc_search(
    query: str,
    kb_ids: list[str] | None,
    top_k: int,
    client: IDocSearchClient,
) -> ToolResult:
    """Core logic for doc search — directly testable without FastMCP."""
    try:
        results = await client.search(query, kb_ids, top_k)
        return ToolResult.ok(data={"results": results, "query": query})
    except PROLOOKUnavailableError as exc:
        Log.error("tool_error", tool=_TOOL_NAME, error=str(exc))
        return ToolResult.fail(
            code="RAG_UNAVAILABLE",
            message="The document search service is temporarily unavailable. Retry in a moment.",
            retryable=True,
        )
    except Exception:
        Log.exception("tool_unexpected_error", tool=_TOOL_NAME)
        return ToolResult.fail(
            code="UNEXPECTED_ERROR",
            message="An unexpected error occurred.",
        )


def register_doc_search(mcp: fastmcp.FastMCP, client: IDocSearchClient) -> None:
    @mcp.tool()
    async def doc_search(
        query: str, kb_ids: list[str] | None = None, top_k: int = 5
    ) -> dict[str, Any]:
        """Search knowledge base documents by semantic similarity.

        Use for product specs, policies, or internal guides.
        """
        started = time.monotonic()
        result = await _handle_doc_search(query, kb_ids, top_k, client)
        count = len(result.data["results"]) if result.data else 0

        await write_audit_event(
            AuditEvent(
                request_id=str(uuid.uuid4()),
                tool_name=_TOOL_NAME,
                tool_version=_TOOL_VERSION,
                input_args={"query": query, "kb_ids": kb_ids, "top_k": top_k},
                output_summary=f"status={result.status}, count={count}",
                output_size_bytes=len(str(result.model_dump())),
                latency_ms=int((time.monotonic() - started) * 1000),
                status=result.status,
                error_code=result.error.code if result.error else None,
            )
        )

        return result.model_dump()
