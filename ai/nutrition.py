"""Nutrition lookup providers.

We define an abstract `NutritionProvider` and ship one concrete adapter for
the USDA FoodData Central API (free, requires a key from api.data.gov).

Students may add other adapters (Edamam, Nutritionix) by subclassing
`NutritionProvider`.

This module is *synchronous*. The reason: it is one HTTP call per lookup
and many SE-layer choices (retry policy, parallelism, caching) belong in
the student's wrapper code. We deliberately do not impose them here.
"""

from __future__ import annotations

import abc
import os
from typing import Any

from ai.providers.base import ProviderError
from ai.schemas import NutritionFacts


# USDA FoodData Central nutrient names used by the application.
_USDA_NUTRIENT_NAMES = {
    "Energy",
    "Protein",
    "Carbohydrate, by difference",
    "Total lipid (fat)",
}


class NutritionProvider(abc.ABC):
    """Contract for an ingredient -> NutritionFacts lookup service."""

    @abc.abstractmethod
    def lookup(self, ingredient_name: str) -> NutritionFacts:
        """Look up per-100g facts for `ingredient_name`.

        Raises
        ------
        ProviderError
            If the ingredient cannot be found or the call fails.
        """
        raise NotImplementedError


class USDAProvider(NutritionProvider):
    """USDA FoodData Central API adapter."""

    BASE_URL = "https://api.nal.usda.gov/fdc/v1"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        timeout: float = 10.0,
    ) -> None:
        self._api_key = api_key or os.getenv("USDA_API_KEY")

        if not self._api_key:
            raise ProviderError(
                "USDA_API_KEY is not set. Get a free key from "
                "https://fdc.nal.usda.gov/api-key-signup and export it."
            )

        try:
            import requests  # type: ignore
        except ImportError as e:
            raise ProviderError(
                "The `requests` package is required. "
                "Install with `pip install requests`."
            ) from e

        self._requests = requests
        self._timeout = timeout

    def lookup(self, ingredient_name: str) -> NutritionFacts:
        """Look up nutrition information for an ingredient."""

        if not ingredient_name.strip():
            raise ValueError("ingredient_name must be non-empty")

        try:
            search_resp = self._requests.get(
                f"{self.BASE_URL}/foods/search",
                params={
                    "query": ingredient_name,
                    "pageSize": 100,
                    "dataType": ["Foundation", "SR Legacy"],
                    "api_key": self._api_key,
                },
                timeout=self._timeout,
            )
            search_resp.raise_for_status()

        except Exception as e:  # pragma: no cover - network path
            raise ProviderError(
                f"USDA search failed for {ingredient_name!r}: {e}"
            ) from e

        body = search_resp.json()
        foods = body.get("foods") or []

        if not foods:
            raise ProviderError(
                f"USDA: no match for {ingredient_name!r}"
            )

        match = foods[0]

        nutrients = _extract_nutrients(
            match.get("foodNutrients") or []
        )

        return NutritionFacts(
            name=match.get("description", ingredient_name),
            kcal_per_100g=nutrients.get("Energy", 0.0),
            protein_g_per_100g=nutrients.get("Protein", 0.0),
            carbs_g_per_100g=nutrients.get(
                "Carbohydrate, by difference",
                0.0,
            ),
            fat_g_per_100g=nutrients.get(
                "Total lipid (fat)",
                0.0,
            ),
            source="USDA",
        )


def _extract_nutrients(
    food_nutrients: list[dict[str, Any]],
) -> dict[str, float]:
    """Extract USDA nutrient values.

    Energy values are normalized to kcal.

    USDA responses may contain Energy in either:
    - KCAL
    - KJ

    When both are available, KCAL is preferred.
    """

    out: dict[str, float] = {}

    for nutrient in food_nutrients:
        name = nutrient.get("nutrientName")

        if name not in _USDA_NUTRIENT_NAMES:
            continue

        try:
            value = float(nutrient.get("value", 0.0))
        except (TypeError, ValueError):
            continue

        unit = str(
            nutrient.get("unitName", "")
        ).upper()

        # USDA may return Energy in kJ or kcal.
        if name == "Energy":
            if unit == "KCAL":
                # Prefer the native kcal value when available.
                out["Energy"] = value

            elif unit == "KJ":
                # Only use converted kJ when kcal has not
                # already been found.
                if "Energy" not in out:
                    out["Energy"] = value / 4.184

            continue

        out[name] = value

    return out


def get_nutrition_provider() -> NutritionProvider:
    """Factory for the configured nutrition provider."""

    name = os.getenv(
        "NUTRITION_PROVIDER",
        "usda",
    ).lower().strip()

    if name == "usda":
        return USDAProvider()

    raise ProviderError(
        f"Unknown NUTRITION_PROVIDER={name!r}. "
        "Only 'usda' is shipped. "
        "Add your own adapter by subclassing NutritionProvider."
    )
