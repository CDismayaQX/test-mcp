Command: /review

Full code review: static analysis, tool pattern compliance, security, and coverage.

## Usage
```
/review                          # review all changes vs develop
/review packages/brand-server/   # review specific package
/review --pr staging             # review for PR to staging (invokes security)
```

## Execution

### 1. Commit Messages
```
git log develop..HEAD --oneline
```
Flag violations of `type(scope): description` format.

### 2. Static Analysis
```
uv run ruff check .
uv run mypy packages/core/src packages/internal-server/src packages/brand-server/src --strict
```

### 3. Tool Pattern Compliance
- [ ] Every tool returns `ToolResult` — never raises
- [ ] `BrandContext` from middleware, not from tool input
- [ ] `write_audit_event()` called on all paths
- [ ] Error codes are typed strings, not raw exception text

### 4. Brand Scoping
- [ ] Brand filtering in `core/clients/`, not in tool handlers
- [ ] No tool accepts `brand_id` as input parameter
- [ ] Cross-brand test exists for every brand-server tool

### 5. Security
Invoke security agent if `auth.py`, `rate_limit.py`, or `config.py` changed.
Always invoke for PRs targeting staging or main.

### 6. Tests
```
make test
```

## Output Format
```
## Review: <scope> (<branch> → <target>)

### Commit Messages: PASS ✓ / VIOLATIONS: <list>
### Static Analysis: Ruff PASS ✓ | Mypy PASS ✓
### Tool Pattern: PASS ✓ / VIOLATIONS: <list>
### Brand Scoping: PASS ✓ / VIOLATIONS: <list>
### Security: PASS ✓ / Escalated ✓
### Coverage: PASS ✓ / FAIL ✗

### Verdict
APPROVE ✓ / REQUEST CHANGES ✗ — <blockers>
```
