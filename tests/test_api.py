from io import BytesIO
import pytest
from PIL import Image
from httpx import ASGITransport, AsyncClient

from ai.providers.base import ProviderError
from ai.schemas import Ingredient, Nutrition
from src.api import app
from src.models import AnalysisResponse, IngredientResult


@pytest.fixture
def valid_png_bytes() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (20, 20), color="blue")
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def valid_jpeg_bytes() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (20, 20), color="yellow")
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_analyze_endpoint_valid_image(valid_png_bytes, monkeypatch):
    mock_response = AnalysisResponse(
        image_name="test_meal.png",
        meal_recognized=True,
        status="completed",
        ingredients=[
            IngredientResult(
                ingredient=Ingredient(name="broccoli", estimated_grams=50.0, confidence=0.9),
                nutrition=Nutrition(kcal=17.0, protein_g=1.4, carbs_g=3.5, fat_g=0.2),
                nutrition_source="fake",
            )
        ],
        totals=Nutrition(kcal=17.0, protein_g=1.4, carbs_g=3.5, fat_g=0.2),
        warnings=[],
    )

    async def fake_analyze_meal(path, **kwargs):
        return mock_response

    monkeypatch.setattr("src.api.analyze_meal", fake_analyze_meal)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        files = {"image": ("test_meal.png", valid_png_bytes, "image/png")}
        response = await client.post("/analyze", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["meal_recognized"] is True
        assert data["status"] == "completed"
        assert len(data["ingredients"]) == 1
        assert data["totals"]["kcal"] == 17.0


@pytest.mark.asyncio
async def test_analyze_unsupported_content_type():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        files = {"image": ("test.txt", b"not an image", "text/plain")}
        response = await client.post("/analyze", files=files)

        assert response.status_code == 415
        assert "Only JPEG and PNG images are supported" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analyze_empty_file():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        files = {"image": ("empty.png", b"", "image/png")}
        response = await client.post("/analyze", files=files)

        assert response.status_code == 400
        assert "No image was provided" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analyze_oversized_file():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        oversized = b"a" * (6 * 1024 * 1024)
        files = {"image": ("big.png", oversized, "image/png")}
        response = await client.post("/analyze", files=files)

        assert response.status_code == 413
        assert "size limit" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analyze_provider_error_handling(valid_png_bytes, monkeypatch):
    async def fake_failing_analyze(path, **kwargs):
        raise ProviderError("Underlying VLM service timed out")

    monkeypatch.setattr("src.api.analyze_meal", fake_failing_analyze)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        files = {"image": ("meal.png", valid_png_bytes, "image/png")}
        response = await client.post("/analyze", files=files)

        assert response.status_code == 503
        assert "AI provider temporarily unavailable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analyze_value_error_handling(valid_png_bytes, monkeypatch):
    async def fake_invalid_analyze(path, **kwargs):
        raise ValueError("Corrupted image header")

    monkeypatch.setattr("src.api.analyze_meal", fake_invalid_analyze)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        files = {"image": ("meal.png", valid_png_bytes, "image/png")}
        response = await client.post("/analyze", files=files)

        assert response.status_code == 400
        assert "Corrupted image header" in response.json()["detail"]
