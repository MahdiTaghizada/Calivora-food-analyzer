"""TTL cache wrapper for the provider-agnostic nutrition interface."""

from __future__ import annotations

import threading
import time

from ai import NutritionFacts, NutritionProvider


class CachedNutritionProvider(NutritionProvider):
    """Cache successful lookups for a bounded amount of time.

    The lock protects the in-memory dictionary. The wrapped provider is called
    outside the lock so slow network requests do not block cache reads.
    """

    def __init__(self, wrapped: NutritionProvider, ttl_seconds: int = 86400) -> None:
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be non-negative")
        self._wrapped = wrapped
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[NutritionFacts, float]] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _key(ingredient_name: str) -> str:
        key = " ".join(ingredient_name.split()).casefold()
        if not key:
            raise ValueError("ingredient_name must be non-empty")
        return key

    def lookup(self, ingredient_name: str) -> NutritionFacts:
        key = self._key(ingredient_name)
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                facts, cached_at = cached
                if now - cached_at < self._ttl:
                    return facts
                self._cache.pop(key, None)

        facts = self._wrapped.lookup(ingredient_name)
        with self._lock:
            self._cache[key] = (facts, time.monotonic())
        return facts

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
