import sys
import runpy
import pytest
from ai.providers.base import ProviderError
from ai.schemas import Ingredient, Nutrition
from src.models import AnalysisResponse, IngredientResult
from src import cli


def test_wrong_command(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["foodanalyzer", "test", "data/bread_cheese.png"]
    )

    with pytest.raises(SystemExit):
        runpy.run_module("foodanalyzer", run_name="__main__")

    output = capsys.readouterr()
    assert "Unknown command" in output.out


def test_file_not_found(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["foodanalyzer", "analyze", "data/yoxdur.png"]
    )

    with pytest.raises(SystemExit):
        runpy.run_module("foodanalyzer", run_name="__main__")

    output = capsys.readouterr()
    assert "File not found" in output.out


def test_valid_image(monkeypatch, capsys):
    class FakeRepository:
        async def init_pool(self):
            pass

        async def create_table(self):
            pass

        async def close_pool(self):
            pass

    async def fake_analyze_meal(path, repository=None):
        return object()

    monkeypatch.setattr(cli, "PostgresAnalysisRepository", FakeRepository)
    monkeypatch.setattr(cli, "analyze_meal", fake_analyze_meal)
    monkeypatch.setattr(
        cli,
        "render_table",
        lambda response: "ingredient  g  kcal\nTOTAL       90  280"
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["foodanalyzer", "analyze", "data/bread_cheese.png"]
    )

    runpy.run_module("foodanalyzer", run_name="__main__")
    output = capsys.readouterr()

    assert "TOTAL" in output.out
    assert "280" in output.out


def test_directory_path(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["foodanalyzer", "analyze", "data"]
    )

    with pytest.raises(SystemExit):
        runpy.run_module("foodanalyzer", run_name="__main__")

    output = capsys.readouterr()
    assert "File not found" in output.out


def test_file_read_error(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["foodanalyzer", "analyze", "data/bread_cheese.png"]
    )

    def fake_open(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr("builtins.open", fake_open)

    with pytest.raises(SystemExit):
        runpy.run_module("foodanalyzer", run_name="__main__")

    output = capsys.readouterr()
    assert "Could not read file" in output.out


def test_history_command(monkeypatch, capsys):
    fake_rows = [
        {
            "id": 1,
            "image_path": "image.png",
            "created_at": "2026-09-19"
        }
    ]

    class FakeRepository:
        async def init_pool(self):
            pass

        async def create_table(self):
            pass

        async def get_history(self):
            return fake_rows

        async def close_pool(self):
            pass

    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    monkeypatch.setattr(cli, "PostgresAnalysisRepository", FakeRepository)
    monkeypatch.setattr(sys, "argv", ["foodanalyzer", "history"])

    cli.main()
    output = capsys.readouterr()

    assert "image.png" in output.out
    assert "2026-09-19" in output.out


def test_history_empty(monkeypatch, capsys):
    class FakeEmptyRepository:
        async def init_pool(self):
            pass

        async def create_table(self):
            pass

        async def get_history(self):
            return []

        async def close_pool(self):
            pass

    monkeypatch.setattr(cli, "PostgresAnalysisRepository", FakeEmptyRepository)
    monkeypatch.setattr(sys, "argv", ["foodanalyzer", "history"])

    cli.main()
    output = capsys.readouterr()
    assert "No analysis history" in output.out


def test_render_table():
    response = AnalysisResponse(
        image_name="plate.png",
        meal_recognized=True,
        status="completed",
        ingredients=[
            IngredientResult(
                ingredient=Ingredient(name="chicken", estimated_grams=150.0, confidence=0.9),
                nutrition=Nutrition(kcal=250.0, protein_g=40.0, carbs_g=0.0, fat_g=5.0),
            ),
            IngredientResult(
                ingredient=Ingredient(name="mystery sauce", estimated_grams=20.0, confidence=0.5),
                nutrition=None,
            ),
        ],
        totals=Nutrition(kcal=250.0, protein_g=40.0, carbs_g=0.0, fat_g=5.0),
    )

    table = cli.render_table(response)
    assert "ingredient" in table
    assert "chicken" in table
    assert "TOTAL" in table
    assert "250" in table


def test_cli_no_args(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["foodanalyzer"])
    with pytest.raises(SystemExit):
        cli.main()
    output = capsys.readouterr()
    assert "Usage: python -m foodanalyzer" in output.out


def test_cli_analyze_missing_path(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["foodanalyzer", "analyze"])
    with pytest.raises(SystemExit):
        cli.main()
    output = capsys.readouterr()
    assert "Usage: python -m foodanalyzer" in output.out


def test_cli_provider_error_handling(monkeypatch, capsys, tmp_path):
    from PIL import Image

    valid_img = tmp_path / "valid.png"
    Image.new("RGB", (10, 10)).save(valid_img, format="PNG")

    class FakeRepository:
        async def init_pool(self):
            pass

        async def create_table(self):
            pass

        async def close_pool(self):
            pass

    async def fake_failing_analyze(*args, **kwargs):
        raise ProviderError("Authentication failed")

    monkeypatch.setattr(cli, "PostgresAnalysisRepository", FakeRepository)
    monkeypatch.setattr(cli, "analyze_meal", fake_failing_analyze)
    monkeypatch.setattr(sys, "argv", ["foodanalyzer", "analyze", str(valid_img)])

    with pytest.raises(SystemExit):
        cli.main()

    output = capsys.readouterr()
    assert "AI provider is not configured" in output.out
