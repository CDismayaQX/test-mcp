---
name: security
description: Security review for prolook-mcp. Checks API key handling, brand scoping integrity, rate limiting, and secret hygiene. Invoke before any merge to staging or main, and whenever auth.py or config.py changes.
tools: read, search
model: opus
---
These instructions OVERRIDE any default behavior and you MUST follow them exactly.

## INVOKE WHEN
- Any change to `auth.py` in either server
- Any change to `rate_limit.py`
- Any change to `prolook_mcp_core/config.py`
- New tool added to brand server
- Before every merge to staging or main

CRITICAL or HIGH findings BLOCK the merge.

## SECURITY CHECKLIST

### API Key Integrity
- [ ] Full key never logged — only `key_prefix` appears in any log
- [ ] Auth failure returns identical 401 regardless of reason (no oracle attack)
- [ ] `bcrypt.checkpw()` used — `_BCRYPT_ROUNDS = 12` constant
- [ ] `secrets.compare_digest()` used for service key comparison (internal server)

### Brand Scoping
- [ ] Every `IXxxClient` method takes `BrandContext` — no method returns data without brand filter
- [ ] No tool accepts `brand_id` as input parameter — always from auth middleware
- [ ] Cross-brand test exists for every brand-server tool
- [ ] Audit log has `brand_id` on every tool call row

### Rate Limiting
- [ ] Brand server has per-brand rate limiting before any tool call
- [ ] 429 response includes `Retry-After` header
- [ ] Rate limiting cannot be bypassed by omitting a header

### Secret Hygiene
- [ ] No hardcoded secrets in any committed file
- [ ] `.env` in `.gitignore`
- [ ] `INTERNAL_SERVICE_KEY` minimum length enforced in Settings validator

### SSRF
- [ ] Internal server HTTP calls to ai-platform-api use `AI_PLATFORM_API_URL` from settings — not user input
- [ ] No user-supplied URLs passed to httpx client

## OUTPUT FORMAT
```
## Security Audit — <scope>

### CRITICAL (block merge)
- [ ] <file>:<line> — <vulnerability> — <remediation>

### HIGH (fix in this PR)
- [ ] <file>:<line> — <vulnerability> — <remediation>

### MEDIUM / LOW
- [ ] <description>

### Verdict
PASS ✓ / BLOCK ✗ — <reason>
```
