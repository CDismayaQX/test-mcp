#!/usr/bin/env bash
CMD="${1:-}"
EXIT_CODE="${2:-0}"

if echo "$CMD" | grep -q "pytest" && [ "$EXIT_CODE" != "0" ]; then
  echo "⚠  Tests failed (exit $EXIT_CODE)." >&2
  echo "   Common causes in prolook-mcp:" >&2
  echo "     - Missing await on async client call" >&2
  echo "     - AsyncMock used where MagicMock needed (or vice versa)" >&2
  echo "     - BrandContext not passed to client mock" >&2
  echo "     - write_audit_event not awaited" >&2
  echo "   Run with detail: uv run pytest -x --tb=long -v" >&2
fi

if echo "$CMD" | grep -q "ruff check" && [ "$EXIT_CODE" != "0" ]; then
  echo "⚠  Ruff failed. Auto-fix: uv run ruff check --fix ." >&2
fi

if echo "$CMD" | grep -q "mypy" && [ "$EXIT_CODE" != "0" ]; then
  echo "⚠  Mypy failed. Common fixes:" >&2
  echo "     - Add from __future__ import annotations" >&2
  echo "     - Use X | None instead of Optional[X]" >&2
  echo "     - Add return type annotation" >&2
fi

if echo "$CMD" | grep -q "docker build" && [ "$EXIT_CODE" = "0" ]; then
  echo "✓ Docker image built." >&2
fi

exit 0
