---
paths:
  - "packages/internal-server/**/*.py"
  - "packages/brand-server/**/*.py"
---
These instructions OVERRIDE any default behavior and you MUST follow them exactly.

## THE CORE RULE
Every tool handler MUST return a `ToolResult`. NEVER raise out of a tool handler.
Catch all exceptions, return `ToolResult.fail(...)`.

## TOOL HANDLER PATTERN
```python
def register_order_lookup(mcp: fastmcp.FastMCP, client: IOrderClient) -> None:
    @mcp.tool()
    async def order_lookup(order_id: str) -> dict[str, Any]:
        """Look up an order by ID, scoped to the authenticated brand."""
        started = time.monotonic()
        brand_ctx = get_brand_context()  # brand server: ContextVar set by auth middleware
        try:
            order = await client.get_order(order_id, brand_ctx)
            if order is None:
                result = ToolResult.fail(
                    code="ORDER_NOT_FOUND",
                    message=f"Order {order_id} not found",
                    retryable=False,
                )
            else:
                result = ToolResult.ok(data=order)
        except PROLOOKUnavailableError as exc:
            Log.error("tool_prolook_unavailable", tool="order_lookup", error=str(exc))
            result = ToolResult.fail(
                code="PROLOOK_UNAVAILABLE",
                message="PROLOOK system is temporarily unavailable. Try again.",
                retryable=True,
            )
        except Exception:
            Log.exception("tool_unexpected_error", tool="order_lookup")
            result = ToolResult.fail(
                code="UNEXPECTED_ERROR",
                message="An unexpected error occurred.",
                retryable=False,
            )

        await write_audit_event(AuditEvent(
            request_id=str(uuid.uuid4()),
            brand_id=brand_ctx.brand_id,  # None for internal server tools
            tool_name="order_lookup",
            tool_version="1.0",
            input_args={"order_id": order_id},
            output_summary=f"status={result.status}",
            output_size_bytes=len(str(result.model_dump())),
            latency_ms=int((time.monotonic() - started) * 1000),
            status=result.status,
            error_code=result.error.code if result.error else None,
        ))

        return result.model_dump()
```

Brand server tools import and call `get_brand_context()` inside the tool handler:
```python
from brand_server.context import get_brand_context
```
Internal server tools omit `get_brand_context()` and pass `brand_id=None` to `AuditEvent`.

## RULES
- `BrandContext` comes from `get_brand_context()` (ContextVar set by auth middleware — `from brand_server.context import get_brand_context`) — NEVER from tool input arguments
- Tool input must never accept `brand_id` as a parameter — that would allow tenancy bypass
- Write one `AuditEvent` per tool execution — on ALL paths (ok, partial, error)
- Use `Log.error()` before returning an error result. Use `Log.exception()` when re-raising is not possible.
- `write_audit_event()` never raises — it is safe to await without try/except
- Tool names are snake_case. Tool descriptions are written for the LLM, not for humans.

## HOW TO ADD A NEW TOOL
See `.claude/skills/add-tool.md`

## ANTI-PATTERNS
- `raise Exception(...)` inside a tool handler
- Returning raw dicts without going through `ToolResult`
- Calling `ToolResult.error(...)` — the method is `ToolResult.fail(...)`
- Accepting `brand_id` as a tool input parameter
- Skipping `write_audit_event()` on the error path
- Putting brand-scoping logic inside the tool handler — it belongs in `core/clients/`
- Using `ctx: RequestContext` as a tool parameter — there is no `RequestContext` type; use `get_brand_context()` instead
