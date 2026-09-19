import json
from io import BytesIO
from pathlib import Path
import pytest
from PIL import Image

from ai.providers.base import ProviderError
from src.core.analyzer import analyze_meal, validate_image_path
from src.models import AnalysisRecord
from tests.conftest import FakeNutrition, FakeVLM


@pytest.fixture
def valid_meal_image(tmp_path) -> str:
    path = tmp_path / "valid_meal.png"
    img = Image.new("RGB", (50, 50), color="green")
    img.save(path, format="PNG")
    return str(path)


def test_validate_image_path_nonexistent(tmp_path):
    missing = tmp_path / "not_found.png"
    with pytest.raises(ValueError, match="Image file does not exist"):
        validate_image_path(missing)


def test_validate_image_path_unsupported_extension(tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("hello")
    with pytest.raises(ValueError, match="Only JPEG and PNG images are supported"):
        validate_image_path(txt_file)


def test_validate_image_path_oversized(tmp_path):
    oversized = tmp_path / "large.png"
    oversized.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * (6 * 1024 * 1024))
    with pytest.raises(ValueError, match="Image exceeds the 5 MB size limit"):
        validate_image_path(oversized, max_size_mb=5)


def test_validate_image_path_valid(valid_meal_image):
    result = validate_image_path(valid_meal_image)
    assert isinstance(result, Path)
    assert result == Path(valid_meal_image)


@pytest.mark.asyncio
async def test_analyze_meal_happy_path(valid_meal_image, fake_vlm, fake_nutrition):
    response = await analyze_meal(
        valid_meal_image,
        vlm=fake_vlm,
        nutrition_provider=fake_nutrition,
    )

    assert response.meal_recognized is True
    assert response.status == "completed"
    assert len(response.ingredients) == 3
    assert len(response.warnings) == 0

    assert response.totals.kcal > 0
    assert response.totals.protein_g > 0
    assert response.totals.carbs_g > 0
    assert response.totals.fat_g > 0

    rice = response.ingredients[0]
    assert rice.ingredient.name == "white rice (cooked)"
    assert rice.nutrition is not None
    assert rice.error is None
    assert rice.nutrition_source == "fake"


@pytest.mark.asyncio
async def test_analyze_meal_unknown_meal(valid_meal_image, fake_nutrition):
    empty_vlm = FakeVLM(payload={"meal_recognized": False, "ingredients": []})

    response = await analyze_meal(
        valid_meal_image,
        vlm=empty_vlm,
        nutrition_provider=fake_nutrition,
    )

    assert response.meal_recognized is False
    assert response.status == "unknown_meal"
    assert len(response.ingredients) == 0
    assert response.totals.kcal == 0
    assert response.totals.protein_g == 0
    assert response.totals.carbs_g == 0
    assert response.totals.fat_g == 0


@pytest.mark.asyncio
async def test_analyze_meal_provider_error(valid_meal_image, monkeypatch):
    def fake_identify_failing(*args, **kwargs):
        raise ProviderError("VLM rate limit exceeded")

    monkeypatch.setattr("src.core.analyzer.identify_with_retry", fake_identify_failing)

    with pytest.raises(ProviderError, match="VLM rate limit exceeded"):
        await analyze_meal(valid_meal_image)


@pytest.mark.asyncio
async def test_analyze_meal_with_nutrition_lookup_failures(valid_meal_image, fake_vlm):
    class FailingNutrition:
        def lookup(self, name: str):
            raise ProviderError(f"lookup failed for {name}")

    response = await analyze_meal(
        valid_meal_image,
        vlm=fake_vlm,
        nutrition_provider=FailingNutrition(),
    )

    assert response.meal_recognized is True
    assert response.status == "completed_with_warnings"
    assert len(response.warnings) == 3
    for ing_result in response.ingredients:
        assert ing_result.nutrition is None
        assert ing_result.error is not None


@pytest.mark.asyncio
async def test_analyze_meal_saves_to_repository(valid_meal_image, fake_vlm, fake_nutrition):
    saved_records = []

    class MockRepository:
        async def save(self, record: AnalysisRecord):
            saved_records.append(record)
            return record

    repo = MockRepository()
    response = await analyze_meal(
        valid_meal_image,
        vlm=fake_vlm,
        nutrition_provider=fake_nutrition,
        repository=repo,
    )

    assert len(saved_records) == 1
    record = saved_records[0]
    assert record.image_path == valid_meal_image
    assert record.totals_kcal == response.totals.kcal
    assert record.totals_protein_g == response.totals.protein_g
    assert record.totals_carbs_g == response.totals.carbs_g
    assert record.totals_fat_g == response.totals.fat_g

    # Parse saved json
    data = json.loads(record.ingredients_json)
    assert len(data) == 3
    assert data[0]["ingredient"]["name"] == "white rice (cooked)"
