"""Retrying and logging wrappers around the immutable ai/ module."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from ai import Ingredient, NutritionFacts, NutritionProvider, identify_ingredients
from ai.providers.base import ProviderError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

P = ParamSpec("P")
T = TypeVar("T")


def _retry_decorator() -> Callable[[Callable[P, T]], Callable[P, T]]:
    return retry(
        retry=retry_if_exception_type(ProviderError),
        stop=stop_after_attempt(settings.retry_attempts),
        wait=wait_exponential(
            multiplier=settings.retry_min_wait_seconds,
            min=settings.retry_min_wait_seconds,
            max=settings.retry_max_wait_seconds,
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


@_retry_decorator()
def identify_with_retry(image_path: str, **kwargs: object) -> list[Ingredient]:
    logger.info("Identifying ingredients in %s", image_path)

    if settings.offline_mode:
        logger.info("OFFLINE_MODE enabled - using deterministic demo ingredients")

        return [
            Ingredient(
                name="sesame hamburger bun",
                estimated_grams=180.0,
                confidence=0.90,
            ),
            Ingredient(
                name="crispy chicken patty",
                estimated_grams=270.0,
                confidence=0.85,
            ),
            Ingredient(
                name="green leaf lettuce",
                estimated_grams=30.0,
                confidence=0.90,
            ),
            Ingredient(
                name="french fries",
                estimated_grams=100.0,
                confidence=0.90,
            ),
            Ingredient(
                name="ketchup",
                estimated_grams=30.0,
                confidence=0.85,
            ),
            Ingredient(
                name="burger sauce",
                estimated_grams=25.0,
                confidence=0.80,
            ),
            Ingredient(
                name="pickled peppers",
                estimated_grams=20.0,
                confidence=0.85,
            ),
            Ingredient(
                name="mixed pickled vegetables",
                estimated_grams=40.0,
                confidence=0.80,
            ),
        ]

    return identify_ingredients(image_path, **kwargs)


@_retry_decorator()
def lookup_with_retry(
    provider: NutritionProvider, ingredient_name: str
) -> NutritionFacts:
    logger.info("Looking up nutrition for %r", ingredient_name)
    return provider.lookup(ingredient_name)
