import os

from foodanalyzer.config import get_database_url


def test_database_url_conversion(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:dev@localhost:5432/foodanalyzer"
    )

    result=get_database_url()

    assert result=="postgresql://postgres:dev@localhost:5432/foodanalyzer"


def test_normal_database_url(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://postgres:dev@localhost:5432/foodanalyzer"
    )

    result=get_database_url()

    assert result=="postgresql://postgres:dev@localhost:5432/foodanalyzer"
