"""Application configuration loaded from environment variables and .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-6"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    nutrition_provider: str = "usda"
    usda_api_key: str = ""

    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://foodanalyzer:dev@localhost:5432/foodanalyzer"
    nutrition_cache_ttl_seconds: int = 86400
    max_image_size_mb: int = 5
    http_port: int = 8000
    max_nutrition_concurrency: int = 10
    retry_attempts: int = 3
    retry_min_wait_seconds: float = 1.0
    retry_max_wait_seconds: float = 10.0
    cache_backend: str = "memory"
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
