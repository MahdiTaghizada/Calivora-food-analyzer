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


def test_valid_image(monkeypatch, capsys):
    monkeypatch.delenv("DATABASE_URL",raising=False)
    
    monkeypatch.setattr(
        sys,
        "argv",
        ["foodanalyzer", "analyze", "data/bread_cheese.png"]
    )

    runpy.run_module("foodanalyzer", run_name="__main__")

    output = capsys.readouterr()

    assert "Analyzing: bread_cheese.png" in output.out
    assert "TOTAL" in output.out



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
    from foodanalyzer import cli

    fake_rows=[
        {
            "id":1,
            "image_path":"image.png",
            "created_at":"2026-09-19"
        }
    ]

    async def fake_init_pool():
        pass

    async def fake_create_table():
        pass

    async def fake_get_history():
        return fake_rows

    async def fake_close_pool():
        pass

    monkeypatch.setenv("DATABASE_URL","postgresql://test")
    monkeypatch.setattr(cli,"init_pool",fake_init_pool)
    monkeypatch.setattr(cli,"create_table",fake_create_table)
    monkeypatch.setattr(cli,"get_history",fake_get_history)
    monkeypatch.setattr(cli,"close_pool",fake_close_pool)

    monkeypatch.setattr(
        sys,
        "argv",
        ["foodanalyzer","history"]
    )

    cli.main()

    output=capsys.readouterr()

    assert "image.png" in output.out
    assert "2026-09-19" in output.out

