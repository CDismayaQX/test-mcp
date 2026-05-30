---
paths:
  - "packages/**/*.py"
---
These instructions OVERRIDE any default behavior and you MUST follow them exactly.

## RULES
- `from prolook_mcp_core.log import Log` — ALWAYS. NEVER `print()`, `logging.getLogger()`, or structlog directly
- `Log.exception()` when re-raising — captures full traceback
- NEVER log: API keys, brand data content, tool output content, PII

## LOG LEVELS
```python
Log.error()      # tool execution failure, auth failure, PROLOOK unavailable
Log.warning()    # rate limit hit, retryable transient error
Log.info()       # tool executed successfully, server started, brand connected
Log.debug()      # detailed tracing (only in local/dev)
```

## STRUCTURED LOGGING PATTERNS
```python
Log.info("tool_executed", tool="order_lookup", brand_id=ctx.brand_id, latency_ms=42)
Log.warning("rate_limit_hit", brand_id=brand_id, limit=100)
Log.error("prolook_unavailable", tool="order_lookup", error=str(exc))

# NEVER log content
Log.info("tool_executed", result=order_data)        # ✗ may contain PII/business data
Log.info("tool_executed", order_id=order_id)        # ✓ log the key, not the value
```

## AUDIT LOG IS NOT THE APPLICATION LOG
- `write_audit_event()` is the compliance record — structured, DB-persisted
- `Log.*()` is the operational log — structured JSON to stdout
- Both are required. They serve different purposes.
