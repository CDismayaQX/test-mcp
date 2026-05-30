---
paths:
  - "packages/**/*.py"
---
These instructions OVERRIDE any default behavior and you MUST follow them exactly.

## API KEY RULES
- Full API key is NEVER logged — only `key_prefix` appears in logs
- Auth failures always return generic 401 — never reveal whether prefix was unknown, hash was wrong, or key was revoked
- `import bcrypt` — `_BCRYPT_ROUNDS: int = 12` — never reduce rounds
- Key lookup: split prefix from secret at last underscore, look up prefix, verify hash

## BRAND SCOPING AS SECURITY
- See `.claude/rules/brand-scoping.md` — cross-brand data leak is a P0 security failure
- Zero is the acceptable count of cross-brand leaks in the audit log

## RATE LIMITING
- Per-brand rate limiting on brand server is required — no brand goes live without it
- On limit exceeded: 429 with `Retry-After` header — never silently drop the request

## LOGGING
- Never log: API keys, brand data content, tool input/output content, PII
- Always log: `key_prefix` (non-secret), `brand_id`, `tool_name`, `latency_ms`, `status`
- Use `Log.error()` before returning error results
- Use `Log.exception()` (not `Log.error()`) when re-raising to capture traceback

## ANTI-PATTERNS
- Logging the full API key at any level
- Returning different 401 messages based on why auth failed (timing/oracle attacks)
- Accepting `brand_id` from tool input — always from auth middleware
- Skipping rate limiting "temporarily" — it must exist before any brand goes live
