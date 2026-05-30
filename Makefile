.PHONY: install dev-internal dev-brand test lint fix db-migrate

install:
	uv sync

dev-internal:
	uv run --package prolook-mcp-internal python -m internal_server.main

dev-brand:
	uv run --package prolook-mcp-brand python -m brand_server.main

test:
	uv run pytest -v

lint:
	uv run ruff check . && uv run ruff format --check .
	uv run mypy packages/core/src packages/internal-server/src packages/brand-server/src

fix:
	uv run ruff check --fix . && uv run ruff format .

db-migrate:
	@echo "Running MCP table migrations against $$DB_DATABASE on $$DB_HOST:$$DB_PORT"
	PGPASSWORD=$$DB_PASSWORD psql -h $$DB_HOST -p $$DB_PORT -U $$DB_USER -d $$DB_DATABASE \
	  -f scripts/create_tables.sql
