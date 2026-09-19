import sys
import runpy
import pytest


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


def test_valid_image(monkeypatch,capsys):
    from src import cli

    class FakeResponse:
        def model_dump_json(self,indent=2):
            return '{"image_name":"bread_cheese.png"}'

    class FakeRepository:
        async def init_pool(self):
            pass

        async def create_table(self):
            pass

        async def close_pool(self):
            pass

    async def fake_analyze_meal(path,repository=None):
        return FakeResponse()

    monkeypatch.setattr(
        cli,
        "PostgresAnalysisRepository",
        FakeRepository
    )

    monkeypatch.setattr(
        cli,
        "analyze_meal",
        fake_analyze_meal
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["foodanalyzer","analyze","data/bread_cheese.png"]
    )

    runpy.run_module("foodanalyzer",run_name="__main__")

    output=capsys.readouterr()

    assert "bread_cheese.png" in output.out


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

def test_history_command(monkeypatch,capsys):
    from src import cli

    fake_rows=[
        {
            "id":1,
            "image_path":"image.png",
            "created_at":"2026-09-19"
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

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://test"
    )

    monkeypatch.setattr(
        cli,
        "PostgresAnalysisRepository",
        FakeRepository
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["foodanalyzer","history"]
    )

    cli.main()

    output=capsys.readouterr()

    assert "image.png" in output.out
    assert "2026-09-19" in output.out

