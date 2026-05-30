---
paths:
  - ".git/**"
---
These instructions OVERRIDE any default behavior and you MUST follow them exactly.

## RULES
- NEVER commit directly to `main`, `staging`, or `develop`
- NEVER force-push to `main`, `staging`, or `develop`
- NEVER commit `.env`, `*.pem`, `*.key`, API keys, passwords

## COMMIT FORMAT
```
<type>(<scope>): <description>

[optional body — WHY, not what]

Refs: #<issue>
```

### Types
`feat` · `fix` · `refactor` · `perf` · `test` · `docs` · `chore` · `ci`

### Scopes
`core` · `internal` · `brand` · `tools` · `auth` · `audit` · `config` · `deps` · `ci`

### Rules
- Subject line ≤ 72 chars, imperative mood, no trailing period
- One logical change per commit

## GOOD COMMITS
```
feat(tools): add order_lookup tool to internal server
fix(auth): return generic 401 on revoked brand API key
feat(brand): add Redis rate limiting per brand
chore(deps): upgrade fastmcp to 2.1.0
```

## PR CHECKLIST
- [ ] `make lint` passes
- [ ] `make test` passes
- [ ] `.env.example` updated if new env vars added
- [ ] No secrets in any committed file
- [ ] Narrow-tools justification in PR description for any new brand-server tool
