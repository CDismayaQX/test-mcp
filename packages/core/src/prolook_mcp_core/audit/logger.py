from __future__ import annotations

import json
from typing import TYPE_CHECKING

from prolook_mcp_core.config import settings
from prolook_mcp_core.log import Log
from prolook_mcp_core.types import AuditEvent

if TYPE_CHECKING:
    import asyncpg

try:
    import asyncpg as _asyncpg_mod

    _ASYNCPG_AVAILABLE = True
except ImportError:
    _ASYNCPG_AVAILABLE = False

_pool: asyncpg.Pool | None = None

_TRUNCATE_SUMMARY_CHARS: int = 500


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        if not _ASYNCPG_AVAILABLE:
            raise RuntimeError("asyncpg is required for audit logging")
        _pool = await _asyncpg_mod.create_pool(
            dsn=settings.database_dsn,
            min_size=1,
            max_size=5,
        )
    return _pool


async def write_audit_event(event: AuditEvent) -> None:
    """Write one audit row. Never raises — audit failures must not break tool calls."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO mcp_audit_log (
                    request_id, session_id, user_id, brand_id, workspace_id,
                    tool_name, tool_version, input_args_json, output_summary,
                    output_size_bytes, latency_ms, status, error_code
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7, $8::jsonb, $9,
                    $10, $11, $12, $13
                )
                """,
                event.request_id,
                event.session_id,
                event.user_id,
                event.brand_id,
                event.workspace_id,
                event.tool_name,
                event.tool_version,
                json.dumps(event.input_args),
                event.output_summary[:_TRUNCATE_SUMMARY_CHARS],
                event.output_size_bytes,
                event.latency_ms,
                event.status,
                event.error_code,
            )
    except Exception as exc:
        # Audit failures are logged but never propagated — a broken audit
        # connection must not take down tool calls.
        Log.error("audit_write_failed", error=str(exc))


async def close_pool() -> None:
    """Call at server shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
