"""Business orchestration for meal analysis."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Protocol

from ai import (
    Nutrition,
    NutritionProvider,
    compute_totals,
    get_nutrition_provider,
)
from ai.providers.base import ProviderError

from src.concurrency.pipeline import parallel_nutrition_lookup_with_errors
from src.config import settings
from src.models import AnalysisRecord, AnalysisResponse, IngredientResult
from src.services.ai_service import identify_with_retry
from src.services.cache_factory import get_cached_provider
from src.utils.images import validate_image

logger = logging.getLogger(__name__)


class AnalysisRepository(Protocol):
    async def save(self, record: AnalysisRecord) -> object:
        ...


def validate_image_path(image_path: str | Path, max_size_mb: int | None = None) -> Path:
    path = Path(image_path)

    if not path.is_file():
        raise ValueError("Image file does not exist")

    suffix=path.suffix.casefold()

    if suffix not in {".jpg",".jpeg",".png"}:
        raise ValueError("Only JPEG and PNG images are supported")

    limit=settings.max_image_size_mb if max_size_mb is None else max_size_mb

    if path.stat().st_size>limit*1024*1024:
        raise ValueError(f"Image exceeds the {limit} MB size limit")

    content_type="image/png" if suffix==".png" else "image/jpeg"

    with path.open("rb") as image:
        image_bytes=image.read()

    validate_image(image_bytes,content_type,limit)

    return path


async def analyze_meal(
    image_path: str | Path,
    *,
    vlm: object | None = None,
    nutrition_provider: NutritionProvider | None = None,
    repository: AnalysisRepository | None = None,
) -> AnalysisResponse:
    path = validate_image_path(image_path)
    logger.info("Analyzing image: %s", path.name)

    kwargs = {"vlm": vlm} if vlm is not None else {}
    try:
        ingredients = await asyncio.to_thread(identify_with_retry, str(path), **kwargs)
    except ProviderError:
        logger.exception("Ingredient identification failed for %s", path.name)
        raise

    if not ingredients:
        response = AnalysisResponse(
            image_name=path.name,
            meal_recognized=False,
            status="unknown_meal",
            totals=Nutrition(),
        )
        logger.info("No meal recognized in %s", path.name)
        return response

    provider = nutrition_provider or get_nutrition_provider()
    cached_provider = get_cached_provider(provider)
    facts_by_name, errors = await parallel_nutrition_lookup_with_errors(
        ingredients,
        cached_provider,
        max_concurrent=settings.max_nutrition_concurrency,
    )
    totals = compute_totals(ingredients, facts_by_name)
    results = []
    warnings = []
    for ingredient in ingredients:
        facts = facts_by_name.get(ingredient.name)
        error = errors.get(ingredient.name)
        nutrition = facts.for_grams(ingredient.estimated_grams) if facts else None
        if error:
            warnings.append(f"{ingredient.name}: nutrition lookup failed")
        results.append(
            IngredientResult(
                ingredient=ingredient,
                nutrition=nutrition,
                nutrition_source=facts.source if facts else None,
                error=error,
            )
        )

    status = "completed_with_warnings" if warnings else "completed"
    response = AnalysisResponse(
        image_name=path.name,
        meal_recognized=True,
        status=status,
        ingredients=results,
        totals=totals,
        warnings=warnings,
    )
    if repository is not None:
        record = AnalysisRecord(
            image_path=str(path),
            ingredients_json=json.dumps([item.model_dump(mode="json") for item in results]),
            totals_kcal=totals.kcal,
            totals_protein_g=totals.protein_g,
            totals_carbs_g=totals.carbs_g,
            totals_fat_g=totals.fat_g,
        )
        await repository.save(record)
    logger.info("Analysis completed for %s with %d ingredients", path.name, len(ingredients))
    return response
