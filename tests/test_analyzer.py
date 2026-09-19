from io import BytesIO
from pathlib import Path
import pytest
from PIL import Image

from src.core.analyzer import analyze_meal, validate_image_path
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

    # Check that totals match expectation
    assert response.totals.kcal > 0
    assert response.totals.protein_g > 0
    assert response.totals.carbs_g > 0
    assert response.totals.fat_g > 0

    # Check individual ingredient result details
    rice = response.ingredients[0]
    assert rice.ingredient.name == "white rice (cooked)"
    assert rice.nutrition is not None
    assert rice.error is None
    assert rice.nutrition_source == "fake"
