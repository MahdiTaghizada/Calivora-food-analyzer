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