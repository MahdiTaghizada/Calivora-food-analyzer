"""Pydantic models shared by the API and analysis service."""

from datetime import datetime, timezone
from typing import Literal

from ai.schemas import Ingredient, Nutrition
from pydantic import BaseModel, Field


class IngredientResult(BaseModel):
    ingredient: Ingredient
    nutrition: Nutrition | None = None
    nutrition_source: str | None = None
    error: str | None = None


class AnalysisResponse(BaseModel):
    image_name: str
    meal_recognized: bool
    status: Literal["completed", "completed_with_warnings", "unknown_meal"]
    ingredients: list[IngredientResult] = Field(default_factory=list)
    totals: Nutrition
    warnings: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnalysisRecord(BaseModel):
    id: int | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    image_path: str
    ingredients_json: str
    totals_kcal: float
    totals_protein_g: float
    totals_carbs_g: float
    totals_fat_g: float
