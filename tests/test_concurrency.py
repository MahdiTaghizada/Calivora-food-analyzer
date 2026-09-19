import asyncio
import pytest
from ai.schemas import Ingredient, NutritionFacts
from ai.providers.base import ProviderError
from tests.conftest import FakeNutrition
from src.concurrency.pipeline import (
    parallel_nutrition_lookup,
    parallel_nutrition_lookup_with_errors,
)


@pytest.mark.asyncio
async def test_parallel_nutrition_lookup_success(fake_nutrition):
    ingredients = [
        Ingredient(name="white rice (cooked)", estimated_grams=200.0, confidence=0.9),
        Ingredient(name="grilled chicken breast", estimated_grams=150.0, confidence=0.85),
        Ingredient(name="broccoli", estimated_grams=80.0, confidence=0.8),
    ]

    facts_by_name = await parallel_nutrition_lookup(
        ingredients, fake_nutrition, max_concurrent=5
    )

    assert len(facts_by_name) == 3
    assert "white rice (cooked)" in facts_by_name
    assert "grilled chicken breast" in facts_by_name
    assert "broccoli" in facts_by_name
    assert facts_by_name["white rice (cooked)"].kcal_per_100g == 130
    assert facts_by_name["grilled chicken breast"].kcal_per_100g == 165
    assert facts_by_name["broccoli"].kcal_per_100g == 34


@pytest.mark.asyncio
async def test_parallel_nutrition_lookup_empty(fake_nutrition):
    facts = await parallel_nutrition_lookup([], fake_nutrition)
    assert facts == {}


@pytest.mark.asyncio
async def test_parallel_nutrition_lookup_invalid_max_concurrent(fake_nutrition):
    ingredients = [Ingredient(name="broccoli", estimated_grams=50.0, confidence=0.8)]
    with pytest.raises(ValueError, match="max_concurrent must be at least 1"):
        await parallel_nutrition_lookup(ingredients, fake_nutrition, max_concurrent=0)


@pytest.mark.asyncio
async def test_parallel_nutrition_lookup_partial_errors(fake_nutrition):
    ingredients = [
        Ingredient(name="broccoli", estimated_grams=80.0, confidence=0.8),
        Ingredient(name="unknown_space_food", estimated_grams=100.0, confidence=0.5),
    ]

    facts, errors = await parallel_nutrition_lookup_with_errors(
        ingredients, fake_nutrition, max_concurrent=5
    )

    assert "broccoli" in facts
    assert "unknown_space_food" not in facts
    assert "unknown_space_food" in errors
    assert "unknown ingredient" in errors["unknown_space_food"]


@pytest.mark.asyncio
async def test_parallel_semaphore_concurrency_bounding():
    class SlowProvider:
        def __init__(self):
            self.current_in_flight = 0
            self.max_observed_in_flight = 0

        def lookup(self, name: str) -> NutritionFacts:
            import time
            self.current_in_flight += 1
            if self.current_in_flight > self.max_observed_in_flight:
                self.max_observed_in_flight = self.current_in_flight
            time.sleep(0.02)
            self.current_in_flight -= 1
            return NutritionFacts(
                name=name,
                kcal_per_100g=100.0,
                protein_g_per_100g=5.0,
                carbs_g_per_100g=5.0,
                fat_g_per_100g=1.0,
                source="mock",
            )

    provider = SlowProvider()
    ingredients = [
        Ingredient(name=f"item_{i}", estimated_grams=100.0, confidence=0.9)
        for i in range(12)
    ]

    facts = await parallel_nutrition_lookup(ingredients, provider, max_concurrent=3)
    assert len(facts) == 12
    assert provider.max_observed_in_flight <= 3
