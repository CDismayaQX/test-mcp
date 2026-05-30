Command: /team

Act as Team Lead for prolook-mcp. Coordinate specialist agents, then produce one implementation plan.

## Usage
```
/team "add order_lookup tool to brand server"
/team "add doc_search tool to internal server"
/team "add new PROLOOK client interface for factory status"
```

## STEP 1 — Dispatch architect (always first)
Pass: tool description, which server(s) it goes on, relevant existing files.
Extract: tool design, client interface needed, brand scoping approach, narrow-tools verdict.

## STEP 2 — Always run security + tester + engineer
- `security`: pass list of files that will change
- `tester`: pass tool name, all error paths, client interface methods
- `engineer`: pass all files written

## STEP 3 — Synthesise
```
## Implementation Plan: <tool name>

### Tool surface: internal / brand / both
### Narrow-tools verdict: APPROVED / INTERNAL ONLY — <reason>

### Files to create
  1. packages/core/src/prolook_mcp_core/clients/interfaces.py  (update IXxxClient if needed)
  2. packages/core/src/prolook_mcp_core/clients/stub/xxx_client.py
  3. packages/{server}/src/{pkg}/tools/xxx.py
  4. packages/{server}/tests/unit/tools/test_xxx.py

### Tool spec
  Name: xxx
  Input: <fields>
  Output: ToolResult with data shape: <shape>
  Error codes: <list>
  Brand scoped: yes (brand server) / no (internal server, single-tenant)

### Test plan
  Cases: ok / not_found / unavailable / brand_scope / audit_written

### Implementation sequence
  1. Update IXxxClient interface in core/clients/interfaces.py
  2. Write StubXxxClient in core/clients/stub/
  3. Write tool handler in {server}/tools/xxx.py
  4. Register tool in {server}/main.py
  5. Write tests
  6. make test && make lint
  7. Commit: feat(tools): add xxx tool
```
