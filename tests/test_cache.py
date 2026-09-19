import concurrent.futures
import pytest
from ai.schemas import NutritionFacts
from src.services.nutrition_cache import CachedNutritionProvider


class CountingProvider:
    def __init__(self):
        self.call_count = 0

    def lookup(self, name: str) -> NutritionFacts:
        self.call_count += 1
        return NutritionFacts(
            name=name,
            kcal_per_100g=100.0,
            protein_g_per_100g=10.0,
            carbs_g_per_100g=10.0,
            fat_g_per_100g=1.0,
            source="mock",
        )


def test_invalid_ttl():
    provider = CountingProvider()
    with pytest.raises(ValueError, match="ttl_seconds must be non-negative"):
        CachedNutritionProvider(provider, ttl_seconds=-1)


def test_cache_miss_and_hit():
    provider = CountingProvider()
    cached = CachedNutritionProvider(provider, ttl_seconds=60)

    facts1 = cached.lookup("apple")
    assert provider.call_count == 1
    assert facts1.name == "apple"

    facts2 = cached.lookup("apple")
    assert provider.call_count == 1
    assert facts2 is facts1


def test_cache_ttl_eviction(monkeypatch):
    provider = CountingProvider()
    cached = CachedNutritionProvider(provider, ttl_seconds=10)

    current_time = 1000.0
    monkeypatch.setattr("time.monotonic", lambda: current_time)

    cached.lookup("banana")
    assert provider.call_count == 1

    current_time = 1005.0
    cached.lookup("banana")
    assert provider.call_count == 1

    current_time = 1015.0  # Expired
    cached.lookup("banana")
    assert provider.call_count == 2


def test_cache_clear():
    provider = CountingProvider()
    cached = CachedNutritionProvider(provider, ttl_seconds=60)

    cached.lookup("orange")
    assert provider.call_count == 1

    cached.clear()
    cached.lookup("orange")
    assert provider.call_count == 2


def test_key_normalization():
    provider = CountingProvider()
    cached = CachedNutritionProvider(provider, ttl_seconds=60)

    cached.lookup("  White   Rice  ")
    assert provider.call_count == 1

    # Should hit cache because normalized key is 'white rice'
    cached.lookup("white rice")
    assert provider.call_count == 1

    cached.lookup("WHITE RICE")
    assert provider.call_count == 1


def test_empty_ingredient_name_raises():
    provider = CountingProvider()
    cached = CachedNutritionProvider(provider, ttl_seconds=60)

    with pytest.raises(ValueError, match="ingredient_name must be non-empty"):
        cached.lookup("   ")


def test_cache_thread_safety():
    provider = CountingProvider()
    cached = CachedNutritionProvider(provider, ttl_seconds=60)

    def worker(name):
        return cached.lookup(name)

    names = ["chicken", "broccoli", "rice", "chicken", "broccoli"] * 10
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(worker, names))

    assert len(results) == len(names)
    # The provider should only be called once per unique key
    assert provider.call_count == 3
