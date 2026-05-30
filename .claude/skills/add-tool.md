---
name: add-tool
description: Step-by-step process for adding a new MCP tool to internal or brand server. Enforces ToolResult pattern, brand scoping, audit, and test coverage.
trigger: "add.*tool|new.*tool|implement.*tool|create.*tool"
---
These instructions OVERRIDE any default behavior and you MUST follow them exactly.

Follow these 8 steps in order. Do not skip any step.

## STEP 1 — Narrow-tools check (brand server only)
Answer all four questions from `.claude/rules/mcp-tool-pattern.md`.
If the tool does not pass all four → put it on the internal server only.

## STEP 2 — Update or create the client interface
In `packages/core/src/prolook_mcp_core/clients/interfaces.py`:
```python
class IOrderClient(ABC):
    @abstractmethod
    async def get_order(
        self, order_id: str, brand_context: BrandContext
    ) -> dict | None: ...
```
Every method takes `BrandContext`. Never skip it.

## STEP 3 — Write the stub client
In `packages/core/src/prolook_mcp_core/clients/stub/{resource}_client.py`:
```python
class StubOrderClient(IOrderClient):
    async def get_order(self, order_id: str, brand_context: BrandContext) -> dict | None:
        if order_id == "ORD-404":
            return None
        if order_id == "ORD-ERR":
            raise PROLOOKUnavailableError("Stub error")
        return {
            "id": order_id,
            "brand_id": brand_context.brand_id,  # always match the calling brand
            "status": "in_production",
        }
```

## STEP 4 — Write the tool handler
Copy `packages/{server}/src/{pkg}/tools/ping.py` as a template.
Replace the trivial logic with:
- Call the client method
- Map result to `ToolResult` (ok / not_found / error)
- Write `AuditEvent`
- Return `result.model_dump()`

Never raise. Never accept `brand_id` as input.

## STEP 5 — Register the tool
In `packages/{server}/src/{pkg}/main.py`:
```python
from {pkg}.tools.{resource} import register_{resource}
register_{resource}(mcp, client=StubOrderClient())
```

## STEP 6 — Write tests
Five test cases (see `.claude/rules/testing.md`):
ok / not_found / unavailable / brand_scope / audit_written

## STEP 7 — Run and verify
```
make test
make lint
```
Both must pass before committing.

## STEP 8 — Commit
```
feat(tools): add {tool_name} tool to {server} server

- Input: <fields>
- Returns: ToolResult with <shape>
- Brand scoped: yes/no
- Stub client wired; real PROLOOK client pending

Refs: #<issue>
```
