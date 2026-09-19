import time

import fakeredis
import pytest
from ai.schemas import NutritionFacts

from src.services.redis_cache import RedisCachedNutritionProvider


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


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis(decode_responses=True)


def test_cache_miss_and_hit(redis_client):
    provider = CountingProvider()
    cached = RedisCachedNutritionProvider(provider, redis_client=redis_client, ttl_seconds=60)

    first = cached.lookup("apple")
    second = cached.lookup("apple")

    assert provider.call_count == 1
    assert second == first
    assert 0 < redis_client.ttl("nutrition:apple") <= 60


def test_ttl_eviction(redis_client):
    provider = CountingProvider()
    cached = RedisCachedNutritionProvider(provider, redis_client=redis_client, ttl_seconds=1)

    cached.lookup("banana")
    time.sleep(1.1)
    cached.lookup("banana")

    assert provider.call_count == 2


def test_key_normalization(redis_client):
    provider = CountingProvider()
    cached = RedisCachedNutritionProvider(provider, redis_client=redis_client, ttl_seconds=60)

    cached.lookup("  White   Rice  ")
    cached.lookup("WHITE rice")

    assert provider.call_count == 1
    assert redis_client.exists("nutrition:white rice")


def test_clear(redis_client):
    provider = CountingProvider()
    cached = RedisCachedNutritionProvider(provider, redis_client=redis_client, ttl_seconds=60)

    cached.lookup("orange")
    cached.clear()
    cached.lookup("orange")

    assert provider.call_count == 2


def test_connection_failure_falls_back_to_provider(monkeypatch):
    provider = CountingProvider()

    def fail_connection(_url):
        raise ConnectionError("Redis unavailable")

    monkeypatch.setattr("redis.Redis.from_url", fail_connection)
    cached = RedisCachedNutritionProvider(provider, redis_url="redis://unavailable", ttl_seconds=60)

    result = cached.lookup("apple")

    assert result.name == "apple"
    assert provider.call_count == 1


def test_serialization_round_trip(redis_client):
    provider = CountingProvider()
    cached = RedisCachedNutritionProvider(provider, redis_client=redis_client, ttl_seconds=60)

    expected = cached.lookup("apple")
    restored = RedisCachedNutritionProvider(
        CountingProvider(), redis_client=redis_client, ttl_seconds=60
    ).lookup("apple")

    assert restored == expected


def test_empty_ingredient_name_raises(redis_client):
    cached = RedisCachedNutritionProvider(
        CountingProvider(), redis_client=redis_client, ttl_seconds=60
    )

    with pytest.raises(ValueError, match="ingredient_name must be non-empty"):
        cached.lookup("   ")
