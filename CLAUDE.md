# CLAUDE.md

Guidance for working in the `prolook-mcp` monorepo.

## Package structure

Three packages in one uv workspace; each server deploys as its own service.

- **`packages/core`** (`prolook_mcp_core`) — shared library, **not** a server.
  Owns shared types (`BrandContext`, `ToolResult`, `ToolError`, `AuditEvent`),
  the `MCPError` hierarchy, the `Log` facade and structlog config, the
  pydantic-settings `Settings` base, the audit logger (`write_audit_event`),
  and the abstract PROLOOK client interfaces (`IOrderClient`, `IProductClient`).
- **`packages/internal-server`** (`internal_server`) — MCP server for internal
  use (the AI Studio chat app). Auth is a single service-to-service key.
- **`packages/brand-server`** (`brand_server`) — MCP server for external brands
  (Riddell, New Balance, …). Auth is an API key per brand. Narrow tool surface,
  multi-tenant, per-brand rate limiting.

## Layer rule

```
tool handler → core client interface → stub or real implementation
```

Tool handlers depend only on the **interfaces** in `prolook_mcp_core.clients`.
Brand scoping is enforced inside the core clients, **never** in tool handlers.
A handler never filters by brand itself — it passes the `BrandContext` down and
trusts the client to scope.

## Tool contract

1. **Every tool returns `ToolResult`.** Never raise out of a tool handler —
   catch exceptions and return `ToolResult.fail(...)`.
2. **Every tool call writes exactly one `AuditEvent`** via the core audit logger
   (`write_audit_event`).
3. **`BrandContext` comes from auth middleware**, never from tool arguments. A
   tool must not accept a `brand_id` argument that overrides the authenticated
   context.

## uv commands

- `uv sync` — install the whole workspace.
- `uv run pytest` — run all tests.
- `uv run ruff check .` — lint.
- `uv run ruff format --check .` — verify formatting.
- `uv run mypy packages/core/src packages/internal-server/src packages/brand-server/src` — typecheck.

## Adding a new tool

1. Copy `tools/ping.py` as a starting point.
2. Define input args (typed) and the output shape.
3. Call the relevant core **client interface** — never reach into a backend directly.
4. Wrap the body so every path returns a `ToolResult` (ok / partial / error).
5. Register it with the server's `mcp` instance in `main.py`.
6. Write the `AuditEvent` for the invocation.
7. Add tests covering the ok, error, and partial cases.

## Ports

- internal-server: **:8001**
- brand-server: **:8002**
