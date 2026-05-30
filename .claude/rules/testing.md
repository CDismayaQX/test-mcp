---
paths:
  - "packages/**/tests/**/*.py"
---
These instructions OVERRIDE any default behavior and you MUST follow them exactly.

## STRUCTURE
- `packages/{pkg}/tests/unit/` — mock all I/O, no DB
- `packages/{pkg}/tests/integration/` — real DB on port 5433

## NAMING
`test_<what>_<condition>_<expected_outcome>`
```
✓ test_order_lookup_found_returns_ok_result
✓ test_order_lookup_not_found_returns_error_result
✓ test_order_lookup_wrong_brand_returns_not_found
✓ test_ping_valid_service_key_returns_ok
✓ test_ping_invalid_service_key_returns_401
✗ test_order_lookup     (missing condition + expected)
✗ test_error_case       (too vague)
```

## TOOL TEST COVERAGE — REQUIRED FOR EVERY TOOL
```
1. ok path         — valid input, returns ToolResult.ok(...)
2. not_found path  — ID doesn't exist, returns ToolResult.error(code="X_NOT_FOUND")
3. error path      — client raises PROLOOKUnavailableError, returns ToolResult.error(retryable=True)
4. brand_scope     — brand-server tool: wrong brand context returns not_found, not other brand's data
5. audit_written   — write_audit_event was called with correct brand_id and status
```

## MOCK PATTERNS
```python
# IOrderClient mock
mock_client = AsyncMock(spec=IOrderClient)
mock_client.get_order.return_value = {"id": "ORD-001", "brand_id": "riddell", ...}

# write_audit_event mock
with patch("internal_server.tools.order_lookup.write_audit_event") as mock_audit:
    mock_audit.return_value = None
    result = await run_tool(...)
    mock_audit.assert_awaited_once()

# BrandContext factory
def make_brand_context(brand_id: str = "test-brand-001") -> BrandContext:
    return BrandContext(brand_id=brand_id, brand_name="Test Brand")
```

## HARDCODED IDS
- Test brand ID allowed: `"test-brand-001"`
- Test order IDs: `"ORD-001"` (found), `"ORD-404"` (not found), `"ORD-ERR"` (error)
- All other IDs: generate with `uuid4()` or `f"ORD-{uuid4().hex[:6]}"`

## ANTI-PATTERNS
- Testing that a tool raises — tools never raise. Test that they return `ToolResult.error()`.
- Not verifying audit event was written
- Skipping the brand-scope test case for brand-server tools
