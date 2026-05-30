#!/usr/bin/env bash
FILE="${1:-}"

for folder in \
  "packages/core/src/prolook_mcp_core" \
  "packages/internal-server/src/internal_server" \
  "packages/brand-server/src/brand_server"; do
  if echo "$FILE" | grep -q "^${folder}/"; then
    if echo "$FILE" | grep -q "CLAUDE\.md$"; then
      break
    fi
    echo "REMINDER: If this change alters a documented pattern in CLAUDE.md" >&2
    echo "  (tool registration, auth flow, brand scoping, audit pattern)," >&2
    echo "  update CLAUDE.md as part of this PR." >&2
    break
  fi
done

exit 0
