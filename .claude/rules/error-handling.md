---
paths:
  - "packages/**/*.py"
---
These instructions OVERRIDE any default behavior and you MUST follow them exactly.

## RULES
- Tool handlers NEVER raise. Catch → return `ToolResult.error(...)`.
- Auth middleware raises `MCPError` subclasses — the server framework catches and returns 401/429.
- Core client methods raise `MCPError` subclasses — tool handlers catch them.
- NEVER `except:` bare. NEVER `except Exception: pass`.
- ALWAYS chain exceptions: `raise NewError(...) from exc`
- NEVER put stack traces or raw error content in tool output — the LLM sees tool output.

## ERROR FLOW
```
ProlookOrderClient.get_order()  → raises PROLOOKUnavailableError
  ↓
Tool handler catches it         → returns ToolResult.error(code="PROLOOK_UNAVAILABLE", ...)
  ↓
LLM sees ToolResult             → reads message_for_model, decides to retry or inform user
  ↓
User never sees the raw error
```

## MCPError HIERARCHY
```
MCPError
  BrandNotFoundError   → 401 from auth middleware
  InvalidAPIKeyError   → 401 from auth middleware
  RateLimitError       → 429 from rate limiting middleware
  PROLOOKUnavailableError → ToolResult.error(retryable=True) in tool handler
```

## ANTI-PATTERNS
- `raise PROLOOKUnavailableError(...)` inside a tool handler — catch it, return `ToolResult`
- `except Exception as exc: return {"error": str(exc)}` — use `ToolResult.error()`
- Raw exception message in `ToolResult.error.message_for_model` — write for the LLM, not stack traces
