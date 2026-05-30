#!/usr/bin/env bash
CMD="${1:-}"

# Block: destructive SQL on production
if echo "$CMD" | grep -qiE "(DROP TABLE|DROP DATABASE|TRUNCATE)" && \
   echo "$CMD" | grep -qi "prod"; then
  echo "✗ BLOCKED: Destructive SQL targeting production — execute manually." >&2
  exit 1
fi

# Block: secret exposure
if echo "$CMD" | grep -qE "cat\s+\.env\b|echo.*API_KEY|echo.*SECRET|echo.*PASSWORD|printenv.*KEY"; then
  echo "✗ BLOCKED: Command may expose secrets." >&2
  exit 1
fi

# Block: editing .env directly
if echo "$CMD" | grep -qE "(nano|vim|vi|sed -i|echo .*>>?)\s+\.env\b"; then
  echo "✗ BLOCKED: Do not edit .env directly. Edit .env.example instead." >&2
  exit 1
fi

# Block: force-push to protected branches
if echo "$CMD" | grep -qE "git push.*--force.*origin.*(main|staging|develop)"; then
  echo "✗ BLOCKED: Force-push to protected branch is not allowed." >&2
  exit 1
fi

# Block: direct commit to protected branches
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")
if echo "$CMD" | grep -q "git commit" && \
   echo "$CURRENT_BRANCH" | grep -qE "^(main|staging|develop)$"; then
  echo "✗ BLOCKED: Direct commit to '$CURRENT_BRANCH' is not allowed." >&2
  echo "  Create a feature branch: git checkout -b feat/your-feature" >&2
  exit 1
fi

# Warn: uv add without version pin
if echo "$CMD" | grep -qE "uv add [^=@]" && ! echo "$CMD" | grep -qE "(==|>=|@)"; then
  echo "⚠  WARNING: Consider pinning the version in pyproject.toml." >&2
fi

# Warn: push to main
if echo "$CMD" | grep -qE "git push.*origin main"; then
  echo "⚠  WARNING: Pushing to main. Ensure PR approved, CI green, staging healthy." >&2
fi

exit 0
