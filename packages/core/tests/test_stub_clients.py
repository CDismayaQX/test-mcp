from __future__ import annotations

from prolook_mcp_core.clients.stub import StubDocSearchClient, StubOrderClient, StubProductClient
from prolook_mcp_core.types import BrandContext


def make_brand_context(brand_id: str = "test-brand-001") -> BrandContext:
    return BrandContext(brand_id=brand_id, brand_name="Test Brand")


# ---------------------------------------------------------------------------
# StubOrderClient
# ---------------------------------------------------------------------------


async def test_stub_order_client_found_returns_ok_result() -> None:
    client = StubOrderClient()
    ctx = make_brand_context()
    order = await client.get_order("ORD-001", ctx)
    assert order is not None
    assert order["id"] == "ORD-001"
    assert order["brand_id"] == "test-brand-001"


async def test_stub_order_client_not_found_returns_none() -> None:
    client = StubOrderClient()
    ctx = make_brand_context()
    order = await client.get_order("ORD-404", ctx)
    assert order is None


async def test_stub_order_client_wrong_brand_returns_none() -> None:
    """Brand A must not receive Brand B's order — core brand-scoping contract."""
    client = StubOrderClient()
    ctx_b = make_brand_context(brand_id="other-brand")
    order = await client.get_order("ORD-001", ctx_b)
    assert order is None


# ---------------------------------------------------------------------------
# StubProductClient
# ---------------------------------------------------------------------------


async def test_stub_product_client_returns_designs_for_brand() -> None:
    client = StubProductClient()
    ctx = make_brand_context()
    designs = await client.list_designs(ctx)
    assert len(designs) > 0
    assert all(d["brand_id"] == "test-brand-001" for d in designs)


async def test_stub_product_client_other_brand_returns_empty() -> None:
    """A brand with no stub data must receive an empty list, not another brand's data."""
    client = StubProductClient()
    ctx = make_brand_context(brand_id="unknown-brand")
    designs = await client.list_designs(ctx)
    assert designs == []


# ---------------------------------------------------------------------------
# StubDocSearchClient
# ---------------------------------------------------------------------------


async def test_stub_doc_search_client_returns_results() -> None:
    client = StubDocSearchClient()
    results = await client.search("helmet specs", None, 5)
    assert len(results) > 0
    assert all("id" in r and "title" in r for r in results)


async def test_stub_doc_search_client_respects_top_k() -> None:
    client = StubDocSearchClient()
    results = await client.search("anything", None, 1)
    assert len(results) == 1


async def test_stub_doc_search_client_top_k_zero_returns_empty() -> None:
    client = StubDocSearchClient()
    results = await client.search("anything", None, 0)
    assert results == []
