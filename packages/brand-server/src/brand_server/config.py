from __future__ import annotations

from prolook_mcp_core.config import Settings
from pydantic_settings import SettingsConfigDict


class BrandSettings(Settings):
    """Settings for the external brand-facing MCP server (multi-tenant)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8002
    rate_limit_per_minute: int = 120
    bcrypt_rounds: int = 12


settings = BrandSettings()
