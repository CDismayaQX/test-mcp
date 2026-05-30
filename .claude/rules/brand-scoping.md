---
paths:
  - "packages/**/*.py"
---
These instructions OVERRIDE any default behavior and you MUST follow them exactly.

## THE CORE RULE
Brand scoping is enforced in `packages/core/src/prolook_mcp_core/clients/`.
It is NEVER enforced in tool handlers. Even a buggy tool handler cannot leak
cross-brand data because the client layer filters by `brand_id` before returning.

## WHERE SCOPING LIVES
```
Tool handler           → calls client.get_order(order_id, brand_context)
IOrderClient           → interface, takes BrandContext
ProlookOrderClient     → WHERE THIS:
                          result = await prolook_api.get(f"/orders/{order_id}")
                          if result["brand_id"] != brand_context.brand_id:
                              return None   ← cross-brand access silently blocked
StubOrderClient        → same contract, fake data always matches the context brand
```

## RULES
- Every `IXxxClient` method takes `BrandContext` as a parameter
- Every client implementation filters results by `brand_context.brand_id`
- `BrandContext` is resolved by auth middleware from the API key — it is NEVER user-supplied input
- A tool on the brand server NEVER accepts `brand_id` as an input parameter
- On the internal server, `BrandContext` may be absent (PROLOOK is single-tenant internally)

## TESTING BRAND SCOPING
Every brand-server tool must have a test that verifies:
```python
# Brand A cannot get Brand B's data even with a valid Brand A key
ctx_a = BrandContext(brand_id="riddell", brand_name="Riddell")
ctx_b = BrandContext(brand_id="new-balance", brand_name="New Balance")
result_a = await client.get_order("ORD-NB-001", ctx_a)  # NB order, Riddell key
assert result_a is None  # must return None, not raise
```

## ANTI-PATTERNS
- `if brand_id == "riddell": return riddell_data` in a tool handler
- Trusting a `brand_id` field from the LLM's tool call arguments
- Skipping `brand_context` parameter on a new client method
