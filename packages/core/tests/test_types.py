from __future__ import annotations

from prolook_mcp_core.types import ToolResult


def test_tool_result_ok() -> None:
    result = ToolResult.ok(data={"key": "value"})
    assert result.status == "ok"
    assert result.data == {"key": "value"}
    assert result.error is None


def test_tool_result_error() -> None:
    result = ToolResult.fail(
        code="ORDER_NOT_FOUND",
        message="Order not found",
        retryable=False,
    )
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "ORDER_NOT_FOUND"
    assert result.error.retryable is False


def test_tool_result_partial() -> None:
    result = ToolResult.partial(data={"items": []}, warnings=["some results omitted"])
    assert result.status == "partial"
    assert result.warnings == ["some results omitted"]
