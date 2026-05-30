#!/usr/bin/env bash
set -euo pipefail
FILE="${1:-}"

# Block: secret files
for pattern in "\.env$" "\.env\." "\.pem$" "\.key$" "id_rsa" "id_ed25519"; do
  if echo "$FILE" | grep -qE "$pattern"; then
    echo "✗ BLOCKED: Cannot edit '$FILE' — matches secret file pattern." >&2
    echo "  Edit .env.example instead." >&2
    exit 1
  fi
done

# Block: lock files
if echo "$FILE" | grep -qE "uv\.lock$"; then
  echo "✗ BLOCKED: Cannot hand-edit uv.lock — it is auto-generated." >&2
  echo "  To update: edit pyproject.toml then run: uv sync" >&2
  exit 1
fi

# Warn: high-risk files
for path in \
  "packages/core/src/prolook_mcp_core/config.py" \
  "packages/core/src/prolook_mcp_core/clients/interfaces.py" \
  "packages/internal-server/src/internal_server/auth.py" \
  "packages/brand-server/src/brand_server/auth.py" \
  "packages/brand-server/src/brand_server/rate_limit.py" \
  ".claude/settings.json"; do
  if echo "$FILE" | grep -q "$path"; then
    echo "⚠  WARNING: '$FILE' is high-risk." >&2
    echo "   - Do not break existing interface contracts" >&2
    echo "   - Run: make lint && make test after changes" >&2
    echo "   - Invoke security agent if auth or API key logic is affected" >&2
    break
  fi
done

# Warn: client interface changed — all implementations must still satisfy it
if echo "$FILE" | grep -q "clients/interfaces.py"; then
  echo "⚠  WARNING: Client interface changed." >&2
  echo "   Verify all concrete implementations (stub/ and prolook/) still satisfy the interface." >&2
  echo "   Run: uv run mypy packages/core/src --strict" >&2
fi

exit 0
