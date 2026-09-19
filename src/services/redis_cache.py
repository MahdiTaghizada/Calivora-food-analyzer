"""Redis-backed TTL cache wrapper for the provider-agnostic nutrition interface."""

from __future__ import annotations

import json
import logging
from typing import Any

from ai import NutritionFacts, NutritionProvider

logger = logging.getLogger(__name__)


class RedisCachedNutritionProvider(NutritionProvider):
    """Cache successful nutrition lookups in Redis with automatic TTL expiry.

    If Redis is unreachable, falls back transparently to the wrapped provider
    so that the application continues to function (graceful degradation).
    """

    def __init__(
        self,
        wrapped: NutritionProvider,
        redis_url: str = "redis://localhost:6379/0",
        ttl_seconds: int = 86400,
        key_prefix: str = "nutrition:",
        redis_client: Any | None = None,
    ) -> None:
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be non-negative")
        self._wrapped = wrapped
        self._ttl = ttl_seconds
        self._key_prefix = key_prefix
        self._redis: Any | None = redis_client
        if redis_client is None:
            self._connect(redis_url)

    def _connect(self, redis_url: str) -> None:
        """Attempt to connect to Redis. Failures are logged, not raised."""
        try:
            import redis

            self._redis = redis.Redis.from_url(
                redis_url, decode_responses=True
            )
            self._redis.ping()
            logger.info("Connected to Redis at %s", redis_url)
        except Exception:
            logger.warning(
                "Could not connect to Redis at %s — falling back to direct lookups",
                redis_url,
            )
            self._redis = None

    @staticmethod
    def _key(ingredient_name: str) -> str:
        key = " ".join(ingredient_name.split()).casefold()
        if not key:
            raise ValueError("ingredient_name must be non-empty")
        return key

    def _cache_key(self, ingredient_name: str) -> str:
        return f"{self._key_prefix}{self._key(ingredient_name)}"

    @staticmethod
    def _serialize(facts: NutritionFacts) -> str:
        return json.dumps({
            "name": facts.name,
            "kcal_per_100g": facts.kcal_per_100g,
            "protein_g_per_100g": facts.protein_g_per_100g,
            "carbs_g_per_100g": facts.carbs_g_per_100g,
            "fat_g_per_100g": facts.fat_g_per_100g,
            "source": facts.source,
        })

    @staticmethod
    def _deserialize(data: str) -> NutritionFacts:
        obj = json.loads(data)
        return NutritionFacts(
            name=obj["name"],
            kcal_per_100g=obj["kcal_per_100g"],
            protein_g_per_100g=obj["protein_g_per_100g"],
            carbs_g_per_100g=obj["carbs_g_per_100g"],
            fat_g_per_100g=obj["fat_g_per_100g"],
            source=obj.get("source"),
        )

    def lookup(self, ingredient_name: str) -> NutritionFacts:
        key = self._cache_key(ingredient_name)

        # Try reading from Redis cache
        if self._redis is not None:
            try:
                cached = self._redis.get(key)
                if cached is not None:
                    logger.debug("Redis cache hit for %r", ingredient_name)
                    return self._deserialize(cached)
            except Exception:
                logger.warning("Redis read failed for key %r", key)

        # Cache miss or Redis unavailable — query upstream provider
        facts = self._wrapped.lookup(ingredient_name)

        # Try writing to Redis cache
        if self._redis is not None:
            try:
                if self._ttl > 0:
                    self._redis.set(
                        key,
                        self._serialize(facts),
                        ex=self._ttl,
                    )
                    logger.debug("Cached %r in Redis (TTL=%ds)", ingredient_name, self._ttl)
            except Exception:
                logger.warning("Redis write failed for key %r", key)

        return facts

    def clear(self) -> None:
        """Delete all keys matching the cache prefix."""
        if self._redis is not None:
            try:
                cursor = 0
                while True:
                    cursor, keys = self._redis.scan(
                        cursor=cursor, match=f"{self._key_prefix}*", count=100
                    )
                    if keys:
                        self._redis.delete(*keys)
                    if cursor == 0:
                        break
                logger.info("Redis cache cleared (prefix=%s)", self._key_prefix)
            except Exception:
                logger.warning("Redis clear failed")
