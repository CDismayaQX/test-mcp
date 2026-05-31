from __future__ import annotations

from prolook_mcp_core.config import Settings
from pydantic_settings import SettingsConfigDict


class InternalSettings(Settings):
    """Settings for the internal MCP server (AI Studio chat app)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8001
    internal_service_key: str = ""


settings = InternalSettings()
