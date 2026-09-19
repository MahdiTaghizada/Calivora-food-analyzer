from ai.schemas import NutritionFacts
from ai.nutrition import NutritionProvider

from src.config import settings
from src.services.cache_factory import get_cached_provider
from src.services.nutrition_cache import CachedNutritionProvider
from src.services.redis_cache import RedisCachedNutritionProvider


class StubProvider(NutritionProvider):
    def lookup(self, ingredient_name: str) -> NutritionFacts:
        return NutritionFacts(
            name=ingredient_name,
            kcal_per_100g=1,
            protein_g_per_100g=1,
            carbs_g_per_100g=1,
            fat_g_per_100g=1,
            source="stub",
        )


def test_memory_backend_returns_memory_provider(monkeypatch):
    monkeypatch.setattr(settings, "cache_backend", "memory")

    cached = get_cached_provider(StubProvider())

    assert isinstance(cached, CachedNutritionProvider)


def test_redis_backend_returns_redis_provider(monkeypatch):
    monkeypatch.setattr(settings, "cache_backend", "redis")
    monkeypatch.setattr(settings, "redis_url", "redis://localhost:6379/0")

    cached = get_cached_provider(StubProvider())

    assert isinstance(cached, RedisCachedNutritionProvider)
