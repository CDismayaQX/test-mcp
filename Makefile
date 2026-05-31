.PHONY: install dev-internal dev-brand test lint fix build-internal build-brand

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

build-internal:
	docker build -t prolook-mcp-internal:latest -f packages/internal-server/Dockerfile .

build-brand:
	docker build -t prolook-mcp-brand:latest -f packages/brand-server/Dockerfile .
