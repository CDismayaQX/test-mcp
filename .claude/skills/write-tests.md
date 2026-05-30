---
name: write-tests
description: Generate test files for an MCP tool handler. Covers all five required test cases with correct AsyncMock and audit verification patterns.
trigger: "write tests|add tests|test coverage|generate tests"
---
These instructions OVERRIDE any default behavior and you MUST follow them exactly.

## STEP 1 — Read first
- The tool handler file (`packages/{server}/src/{pkg}/tools/{tool}.py`)
- The client interface (`packages/core/src/prolook_mcp_core/clients/interfaces.py`)
- Existing test files for reference patterns

## STEP 2 — Write the test file
```python
"""Unit tests for {tool_name} tool."""
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, patch
from prolook_mcp_core.types import BrandContext
from prolook_mcp_core.clients.interfaces import I{Client}
from prolook_mcp_core.errors import PROLOOKUnavailableError


_TEST_BRAND = "test-brand-001"


def make_brand_context(brand_id: str = _TEST_BRAND) -> BrandContext:
    return BrandContext(brand_id=brand_id, brand_name="Test Brand")


@pytest.fixture
def mock_client() -> AsyncMock:
    client = AsyncMock(spec=I{Client})
    client.{method}.return_value = {realistic_fake_data}
    return client


@pytest.fixture
def mock_audit():
    with patch("{pkg}.tools.{tool}.write_audit_event") as m:
        m.return_value = None
        yield m


class Test{ToolName}:
    async def test_{tool}_found_returns_ok_result(
        self, mock_client, mock_audit
    ) -> None:
        result = await run_{tool}("{valid_id}", make_brand_context(), mock_client)
        assert result["status"] == "ok"
        assert result["data"] is not None
        mock_audit.assert_awaited_once()

    async def test_{tool}_not_found_returns_error_result(
        self, mock_client, mock_audit
    ) -> None:
        mock_client.{method}.return_value = None
        result = await run_{tool}("{missing_id}", make_brand_context(), mock_client)
        assert result["status"] == "error"
        assert result["error"]["code"] == "{RESOURCE}_NOT_FOUND"
        assert result["error"]["retryable"] is False
        mock_audit.assert_awaited_once()

    async def test_{tool}_unavailable_returns_retryable_error(
        self, mock_client, mock_audit
    ) -> None:
        mock_client.{method}.side_effect = PROLOOKUnavailableError()
        result = await run_{tool}("{valid_id}", make_brand_context(), mock_client)
        assert result["status"] == "error"
        assert result["error"]["retryable"] is True
        mock_audit.assert_awaited_once()

    async def test_{tool}_wrong_brand_returns_not_found(
        self, mock_client, mock_audit
    ) -> None:
        mock_client.{method}.return_value = None  # client filters cross-brand
        ctx = make_brand_context(brand_id="different-brand")
        result = await run_{tool}("{valid_id}", ctx, mock_client)
        assert result["status"] == "error"

    async def test_{tool}_audit_includes_correct_brand_id(
        self, mock_client, mock_audit
    ) -> None:
        await run_{tool}("{valid_id}", make_brand_context(), mock_client)
        call_kwargs = mock_audit.call_args[0][0]  # AuditEvent
        assert call_kwargs.brand_id == _TEST_BRAND
        assert call_kwargs.tool_name == "{tool_name}"
```

## STEP 3 — Run and verify
```
uv run pytest packages/{server}/tests/unit/tools/test_{tool}.py -v
```
All 5 tests must pass.

## AFTER CREATING ALL FILES
Run:
- `uv run ruff check .` — must pass clean
- `uv run pytest` — must pass

Report any issues found.
