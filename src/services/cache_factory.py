"""Factory that selects the appropriate cache backend for nutrition lookups."""

from __future__ import annotations

import logging

from ai import NutritionProvider

from src.config import settings
from src.services.nutrition_cache import CachedNutritionProvider
from src.services.redis_cache import RedisCachedNutritionProvider

logger = logging.getLogger(__name__)


def get_cached_provider(provider: NutritionProvider) -> NutritionProvider:
    """Wrap *provider* with the cache backend configured via ``CACHE_BACKEND``.

    Supported values:
    - ``"memory"`` (default): in-memory TTL cache
    - ``"redis"``: Redis-backed TTL cache

    If the provider is already a cached wrapper, it is returned as-is.
    """
    if isinstance(provider, (CachedNutritionProvider, RedisCachedNutritionProvider)):
        return provider

    backend = settings.cache_backend.strip().lower()

    if backend == "redis":
        logger.info("Using Redis cache backend (url=%s)", settings.redis_url)
        return RedisCachedNutritionProvider(
            wrapped=provider,
            redis_url=settings.redis_url,
            ttl_seconds=settings.nutrition_cache_ttl_seconds,
        )

    if backend != "memory":
        logger.warning(
            "Unknown cache backend %r — falling back to in-memory cache", backend
        )

    logger.info("Using in-memory cache backend (TTL=%ds)", settings.nutrition_cache_ttl_seconds)
    return CachedNutritionProvider(
        wrapped=provider,
        ttl_seconds=settings.nutrition_cache_ttl_seconds,
    )
