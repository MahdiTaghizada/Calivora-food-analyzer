"""Bounded parallel nutrition lookups for synchronous provider contracts."""

from __future__ import annotations

import asyncio
import logging

from ai import Ingredient, NutritionFacts, NutritionProvider

from src.services.ai_service import lookup_with_retry

logger = logging.getLogger(__name__)


async def parallel_nutrition_lookup(
    ingredients: list[Ingredient],
    provider: NutritionProvider,
    max_concurrent: int = 10,
) -> dict[str, NutritionFacts]:
    facts, _ = await parallel_nutrition_lookup_with_errors(
        ingredients, provider, max_concurrent=max_concurrent
    )
    return facts


async def parallel_nutrition_lookup_with_errors(
    ingredients: list[Ingredient],
    provider: NutritionProvider,
    max_concurrent: int = 10,
) -> tuple[dict[str, NutritionFacts], dict[str, str]]:
    if max_concurrent < 1:
        raise ValueError("max_concurrent must be at least 1")
    semaphore = asyncio.Semaphore(max_concurrent)

    async def lookup_one(name: str) -> tuple[str, NutritionFacts | None, str | None]:
        async with semaphore:
            try:
                facts = await asyncio.to_thread(lookup_with_retry, provider, name)
                return name, facts, None
            except Exception as exc:
                logger.warning("Nutrition lookup failed for %r: %s", name, exc)
                return name, None, str(exc)

    results = await asyncio.gather(*(lookup_one(ing.name) for ing in ingredients))
    facts_by_name = {
        name: facts for name, facts, error in results if facts is not None and error is None
    }
    errors = {
        name: error for name, facts, error in results if facts is None and error is not None
    }
    return facts_by_name, errors
