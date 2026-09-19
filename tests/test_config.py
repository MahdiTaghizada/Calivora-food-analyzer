from src.config import Settings, get_settings
from src.storage import repository


def test_database_url_conversion(monkeypatch):
    monkeypatch.setattr(
        repository.settings,
        "database_url",
        "postgresql+asyncpg://postgres:dev@localhost:5432/foodanalyzer",
    )

    result = repository.get_database_url()
    assert result == "postgresql://postgres:dev@localhost:5432/foodanalyzer"


def test_normal_database_url(monkeypatch):
    monkeypatch.setattr(
        repository.settings,
        "database_url",
        "postgresql://postgres:dev@localhost:5432/foodanalyzer",
    )

    result = repository.get_database_url()
    assert result == "postgresql://postgres:dev@localhost:5432/foodanalyzer"


def test_default_settings(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.llm_provider == "anthropic"
    assert settings.llm_model == "claude-sonnet-4-6"
    assert settings.nutrition_provider == "usda"
    assert settings.log_level == "INFO"
    assert settings.max_image_size_mb == 5
    assert settings.http_port == 8000
    assert settings.nutrition_cache_ttl_seconds == 86400
    assert settings.max_nutrition_concurrency == 10
    assert settings.retry_attempts == 3
    assert settings.retry_min_wait_seconds == 1.0
    assert settings.retry_max_wait_seconds == 10.0
    assert settings.cache_backend == "memory"
    assert settings.redis_url == "redis://localhost:6379/0"


def test_settings_env_override(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("MAX_IMAGE_SIZE_MB", "10")
    monkeypatch.setenv("HTTP_PORT", "9000")
    monkeypatch.setenv("RETRY_ATTEMPTS", "5")
    monkeypatch.setenv("CACHE_BACKEND", "redis")
    monkeypatch.setenv("REDIS_URL", "redis://cache:6379/1")

    custom_settings = Settings()
    assert custom_settings.llm_provider == "openai"
    assert custom_settings.llm_model == "gpt-4o-mini"
    assert custom_settings.max_image_size_mb == 10
    assert custom_settings.http_port == 9000
    assert custom_settings.retry_attempts == 5
    assert custom_settings.cache_backend == "redis"
    assert custom_settings.redis_url == "redis://cache:6379/1"


def test_get_settings_cached():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
