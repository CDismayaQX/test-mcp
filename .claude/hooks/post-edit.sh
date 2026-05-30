#!/usr/bin/env bash
FILE="${1:-}"

if ! echo "$FILE" | grep -q "\.py$"; then
  exit 0
fi

echo "→ Post-edit: $FILE"

if command -v ruff >/dev/null 2>&1; then
  if ruff check "$FILE" --quiet 2>/dev/null; then
    echo "  ✓ Ruff: clean"
  else
    echo "  ⚠  Ruff: issues found — auto-fixing..."
    ruff check "$FILE" --fix --quiet 2>/dev/null && echo "  ✓ Ruff: fixed" || echo "  ✗ Ruff: manual fix needed"
  fi
fi

echo "  → Run: make test to verify"

# auth.py changed — invoke security agent
if echo "$FILE" | grep -qE "(internal_server/auth|brand_server/auth|brand_server/rate_limit)"; then
  echo "  ⚠  Auth/rate-limit file changed — invoke security agent before merging." >&2
fi

# config.py changed — update .env.example
if echo "$FILE" | grep -q "config.py"; then
  echo "  ⚠  config.py changed — update .env.example if a new env var was added." >&2
fi

# Tool file changed — verify ToolResult envelope
if echo "$FILE" | grep -q "/tools/"; then
  echo "  ⚠  Tool file changed — verify:" >&2
  echo "     1. Handler returns ToolResult (never raises)" >&2
  echo "     2. BrandContext comes from middleware, not from tool input" >&2
  echo "     3. write_audit_event() is called for every execution path" >&2
fi

# Client interface changed
if echo "$FILE" | grep -q "clients/interfaces.py"; then
  echo "  ⚠  Client interface changed — verify stub and real implementations still match." >&2
fi

exit 0
