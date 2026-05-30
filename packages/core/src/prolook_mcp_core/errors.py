from __future__ import annotations


class MCPError(Exception):
    def __init__(self, message: str, code: str = "MCP_ERROR") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class BrandNotFoundError(MCPError):
    def __init__(self, detail: str = "Brand not found") -> None:
        super().__init__(detail, code="BRAND_NOT_FOUND")


class InvalidAPIKeyError(MCPError):
    def __init__(self) -> None:
        super().__init__("Invalid or revoked API key", code="INVALID_API_KEY")


class RateLimitError(MCPError):
    def __init__(self, retry_after: int = 60) -> None:
        super().__init__("Rate limit exceeded", code="RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after


class PROLOOKUnavailableError(MCPError):
    def __init__(self, detail: str = "PROLOOK system unavailable") -> None:
        super().__init__(detail, code="PROLOOK_UNAVAILABLE")
