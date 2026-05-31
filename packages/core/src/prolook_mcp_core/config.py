from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database — shared with ai-platform-api
    DB_HOST: str = "localhost"
    DB_PORT: int = 5433
    DB_DATABASE: str = "ai_assistant_dev"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    # Redis — shared with ai-platform-api
    REDIS_URL: str = "redis://:@localhost:6380/0"

    # Internal server — service-to-service auth
    INTERNAL_SERVICE_KEY: str = ""

    # Brand server — signing secret for API key hashing (bcrypt)
    # Each brand key is individually hashed; this is NOT a shared secret
    BRAND_KEY_BCRYPT_ROUNDS: int = 12

    # AI Platform API URL — internal server calls this for doc_search
    AI_PLATFORM_API_URL: str = "http://localhost:8000"

    # Prolook public API — open endpoint, no auth required
    PROLOOK_PUBLIC_API_URL: str = "https://api.prolook.com"

    # Environment
    ENV: str = "local"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_dsn(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
        )

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"

    @property
    def is_local(self) -> bool:
        return self.ENV == "local"


settings = Settings()
