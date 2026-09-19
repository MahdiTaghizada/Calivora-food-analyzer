import pytest
from ai.schemas import Ingredient, NutritionFacts
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
