# prolook-mcp

A Python monorepo containing two MCP servers and a shared core library.

- **`packages/core`** — shared library (types, client interfaces, audit logger,
  error helpers, logging, settings). Not a server.
- **`packages/internal-server`** — MCP server for internal use (the AI Studio
  chat app). Service-to-service key auth. Runs on **:8001**.
- **`packages/brand-server`** — MCP server for external brands (Riddell, New
  Balance, …). Per-brand API key auth, multi-tenant, rate limited. Runs on **:8002**.

Each server deploys as its own independent service. Transport is streamable-HTTP
(stateless, served at `/mcp`).

## Prerequisites

- Python 3.13
- [uv](https://github.com/astral-sh/uv)
- Docker (for building/running container images)

## Install

```bash
uv sync
```

## Run locally

Internal server (:8001):

```bash
uv run --package prolook-mcp-internal python -m internal_server.main
```

Brand server (:8002):

```bash
uv run --package prolook-mcp-brand python -m brand_server.main
```

## Test

```bash
uv run pytest
```

## Lint & format

```bash
uv run ruff check . && uv run ruff format --check .
```

## Environment variables

Set these in the environment (or a local `.env`). Names only — never commit values.

- `DB_HOST`
- `DB_PORT`
- `DB_DATABASE`
- `DB_USER`
- `DB_PASSWORD`
- `REDIS_URL`
- `INTERNAL_SERVICE_KEY`
- `AI_PLATFORM_API_URL`

## Ports

| Service          | Port |
| ---------------- | ---- |
| internal-server  | 8001 |
| brand-server     | 8002 |
