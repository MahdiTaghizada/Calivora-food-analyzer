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