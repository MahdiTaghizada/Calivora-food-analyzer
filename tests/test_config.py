from src.storage import repository


def test_database_url_conversion(monkeypatch):
    monkeypatch.setattr(
        repository.settings,
        "database_url",
        "postgresql+asyncpg://postgres:dev@localhost:5432/foodanalyzer"
    )

    result=repository.get_database_url()

    assert result=="postgresql://postgres:dev@localhost:5432/foodanalyzer"


def test_normal_database_url(monkeypatch):
    monkeypatch.setattr(
        repository.settings,
        "database_url",
        "postgresql://postgres:dev@localhost:5432/foodanalyzer"
    )

    result=repository.get_database_url()

    assert result=="postgresql://postgres:dev@localhost:5432/foodanalyzer"
