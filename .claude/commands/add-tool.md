Command: /add-tool

Generate a complete tool implementation following the prolook-mcp pattern.

## Usage
```
/add-tool <tool_name> [internal|brand]
```

Examples:
```
/add-tool product_lookup brand
/add-tool doc_search internal
/add-tool shipment_status        # will ask which server
```

## What this command does

Given a tool name and target server, generate:
1. The tool handler file (`tools/<tool_name>.py`)
2. Updated `main.py` registration
3. A test file (`tests/test_<tool_name>.py`)

Then run `uv run ruff check .` and `uv run mypy` to verify.

---

## Execution instructions

### 0. Parse args
- `$TOOL_NAME` = first argument (snake_case)
- `$SERVER` = second argument: `internal` or `brand`. If missing, ask the user.

Derive:
- `$PKG` = `internal_server` if internal, `brand_server` if brand
- `$SERVER_DIR` = `packages/internal-server` if internal, `packages/brand-server` if brand
- `$CLIENT_IFACE` = ask the user: "Which client interface does this tool call? (e.g. IOrderClient, IProductClient, or 'new' to create one)"

If `$CLIENT_IFACE` is `new`, follow `.claude/skills/add-tool.md` Steps 2–3 to create the interface and stub first.

---

### 1. Create the tool handler

Write `$SERVER_DIR/src/$PKG/tools/$TOOL_NAME.py` using this exact template:

```python
from __future__ import annotations

import time
import uuid
from typing import Any

import fastmcp
from prolook_mcp_core.audit.logger import write_audit_event
from prolook_mcp_core.clients.interfaces import $CLIENT_IFACE
from prolook_mcp_core.errors import PROLOOKUnavailableError
from prolook_mcp_core.log import Log
from prolook_mcp_core.types import AuditEvent, BrandContext, ToolResult

_TOOL_NAME = "$TOOL_NAME"
_TOOL_VERSION = "1.0"


async def _handle_$TOOL_NAME(
    # ← replace with actual input params
    param: str,
    client: $CLIENT_IFACE,
) -> ToolResult:
    """Core logic — directly testable without FastMCP."""
    try:
        data = await client.method(param)  # ← replace with real client call
        if data is None:
            return ToolResult.fail(
                code="NOT_FOUND",
                message=f"Resource {param} not found.",
            )
        return ToolResult.ok(data=data)
    except PROLOOKUnavailableError as exc:
        Log.error("tool_error", tool=_TOOL_NAME, error=str(exc))
        return ToolResult.fail(
            code="PROLOOK_UNAVAILABLE",
            message="PROLOOK is temporarily unavailable. Retry in a moment.",
            retryable=True,
        )
    except Exception:
        Log.exception("tool_unexpected_error", tool=_TOOL_NAME)
        return ToolResult.fail(
            code="UNEXPECTED_ERROR",
            message="An unexpected error occurred.",
        )


def register_$TOOL_NAME(mcp: fastmcp.FastMCP, client: $CLIENT_IFACE) -> None:
    @mcp.tool()
    async def $TOOL_NAME(param: str) -> dict[str, Any]:  # ← replace params
        """<description for the LLM — what does this tool do and when to call it>"""
        started = time.monotonic()
        result = await _handle_$TOOL_NAME(param, client)

        await write_audit_event(
            AuditEvent(
                request_id=str(uuid.uuid4()),
                brand_id=None,  # ← brand server: use ctx.brand_context.brand_id
                tool_name=_TOOL_NAME,
                tool_version=_TOOL_VERSION,
                input_args={"param": param},
                output_summary=f"status={result.status}",
                output_size_bytes=len(str(result.model_dump())),
                latency_ms=int((time.monotonic() - started) * 1000),
                status=result.status,
                error_code=result.error.code if result.error else None,
            )
        )

        return result.model_dump()
```

**Brand server rules:**
- Do NOT accept `brand_id` as a parameter — it comes from middleware
- Pass `ctx: BrandContext` (resolved from auth) into the client call
- Set `brand_id=ctx.brand_id` in `AuditEvent`

**Internal server rules:**
- `brand_id` may be accepted as an optional parameter
- Set `brand_id=None` or pass the optional value in `AuditEvent`

---

### 2. Register in main.py

Add to `$SERVER_DIR/src/$PKG/main.py`:

```python
# import
from $PKG.tools.$TOOL_NAME import register_$TOOL_NAME

# client instantiation (top of file, before register calls)
_$TOOL_NAME_client = Stub$ClientClass()  # swap for real client later

# registration
register_$TOOL_NAME(mcp, _$TOOL_NAME_client)
```

Add `await _$TOOL_NAME_client.aclose()` in the `_lifespan` teardown block.

---

### 3. Write the test file

Write `$SERVER_DIR/tests/test_$TOOL_NAME.py` covering these five cases:

| Case | What to assert |
|------|----------------|
| `test_ok` | `result["status"] == "ok"` and data fields present |
| `test_not_found` | `result["status"] == "error"` and `error.code == "NOT_FOUND"` |
| `test_prolook_unavailable` | `result["status"] == "error"`, `retryable=True` |
| `test_audit_written` | `write_audit_event` called once with correct `tool_name` |
| `test_brand_scope` *(brand server only)* | Brand A key cannot retrieve Brand B's resource |

Use `Stub$ClientClass` — do not mock the database or HTTP layer directly.

---

### 4. Verify

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy packages/core/src packages/internal-server/src packages/brand-server/src
uv run pytest $SERVER_DIR/tests/test_$TOOL_NAME.py -v
```

Fix any errors before reporting done.

---

### 5. Summary

Report back:
- Files created/modified
- Test results (pass/fail counts)
- Any TODOs left (e.g. "swap StubClient for real ProlookXxxClient")
