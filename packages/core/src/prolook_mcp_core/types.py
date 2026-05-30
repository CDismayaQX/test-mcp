from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class BrandContext(BaseModel):
    brand_id: str
    brand_name: str
    acting_user: str | None = None
    acting_on_behalf_of: str | None = None


class ToolError(BaseModel):
    code: str
    message_for_model: str
    retryable: bool = False


class ToolResult(BaseModel):
    status: Literal["ok", "partial", "error"]
    data: Any | None = None
    warnings: list[str] = []
    error: ToolError | None = None

    @classmethod
    def ok(cls, data: Any) -> ToolResult:
        return cls(status="ok", data=data)

    @classmethod
    def partial(cls, data: Any, warnings: list[str]) -> ToolResult:
        return cls(status="partial", data=data, warnings=warnings)

    @classmethod
    def fail(cls, code: str, message: str, retryable: bool = False) -> ToolResult:
        return cls(
            status="error",
            error=ToolError(code=code, message_for_model=message, retryable=retryable),
        )


class AuditEvent(BaseModel):
    request_id: str
    session_id: str | None = None
    user_id: str | None = None
    brand_id: str | None = None
    workspace_id: str | None = None
    tool_name: str
    tool_version: str
    input_args: dict[str, Any]
    output_summary: str
    output_size_bytes: int
    latency_ms: int
    status: str
    error_code: str | None = None
