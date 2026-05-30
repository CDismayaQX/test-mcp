---
paths:
  - "packages/internal-server/**/*.py"
  - "packages/brand-server/**/*.py"
---
These instructions OVERRIDE any default behavior and you MUST follow them exactly.

## THE CORE RULE
Every tool handler MUST return a `ToolResult`. NEVER raise out of a tool handler.
Catch all exceptions, return `ToolResult.error(...)`.

## TOOL HANDLER PATTERN
```python
def register_order_lookup(mcp: fastmcp.FastMCP, client: IOrderClient) -> None:
    @mcp.tool()
    async def order_lookup(order_id: str, ctx: RequestContext) -> dict:
        """Look up an order by ID, scoped to the calling brand."""
        started = time.monotonic()
        try:
            order = await client.get_order(order_id, ctx.brand_context)
            if order is None:
                result = ToolResult.error(
                    code="ORDER_NOT_FOUND",
                    message=f"Order {order_id} not found",
                    retryable=False,
                )
            else:
                result = ToolResult.ok(data=order)
        except PROLOOKUnavailableError as exc:
            result = ToolResult.error(
                code="PROLOOK_UNAVAILABLE",
                message="PROLOOK system is temporarily unavailable. Try again.",
                retryable=True,
            )
            Log.error("tool_prolook_unavailable", tool="order_lookup", error=str(exc))
        except Exception as exc:
            result = ToolResult.error(
                code="UNEXPECTED_ERROR",
                message="An unexpected error occurred.",
                retryable=False,
            )
            Log.exception("tool_unexpected_error", tool="order_lookup")

        await write_audit_event(AuditEvent(
            request_id=ctx.request_id,
            brand_id=ctx.brand_context.brand_id if ctx.brand_context else None,
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

## RULES
- `BrandContext` comes from `ctx` (injected by auth middleware) — NEVER from tool input arguments
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
- Accepting `brand_id` as a tool input parameter
- Skipping `write_audit_event()` on the error path
- Putting brand-scoping logic inside the tool handler — it belongs in `core/clients/`
