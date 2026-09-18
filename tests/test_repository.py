import asyncio
from src import repository


def test_init_pool(monkeypatch):
    fake_pool = object()

    async def fake_create_pool(url):
        return fake_pool

    monkeypatch.setattr(repository.asyncpg, "create_pool", fake_create_pool)

    result = asyncio.run(repository.init_pool())

    assert result is fake_pool
    assert repository.pool is fake_pool


def test_create_table(monkeypatch):
    queries = []

    class FakeConnection:
        async def execute(self, query):
            queries.append(query)

    class FakeAcquire:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class FakePool:
        def acquire(self):
            return FakeAcquire()

    monkeypatch.setattr(repository, "pool", FakePool())

    asyncio.run(repository.create_table())

    assert "CREATE TABLE" in queries[0]


def test_save_analysis(monkeypatch):
    saved_data = []

    class FakeConnection:
        async def execute(self, query, image_path, result):
            saved_data.append((query, image_path, result))

    class FakeAcquire:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class FakePool:
        def acquire(self):
            return FakeAcquire()

    monkeypatch.setattr(repository, "pool", FakePool())

    asyncio.run(
        repository.save_analysis(
            "image.png",
            "test result"
        )
    )

    assert "INSERT INTO analysis_history" in saved_data[0][0]
    assert saved_data[0][1] == "image.png"
    assert saved_data[0][2] == "test result"


def test_get_history(monkeypatch):
    fake_rows = [
        {
            "id": 1,
            "image_path": "image.png",
            "result": "test result"
        }
    ]

    class FakeConnection:
        async def fetch(self, query):
            return fake_rows

    class FakeAcquire:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class FakePool:
        def acquire(self):
            return FakeAcquire()

    monkeypatch.setattr(repository, "pool", FakePool())

    result = asyncio.run(repository.get_history())

    assert result == fake_rows


def test_close_pool(monkeypatch):
    class FakePool:
        def __init__(self):
            self.closed = False

        async def close(self):
            self.closed = True

    fake_pool = FakePool()

    monkeypatch.setattr(repository, "pool", fake_pool)

    asyncio.run(repository.close_pool())

    assert fake_pool.closed is True
    assert repository.pool is None





def test_get_analysis(monkeypatch):
    fake_row = {
        "id": 1,
        "image_path": "image.png",
        "result": "test result"
    }

    class FakeConnection:
        async def fetchrow(self, query, analysis_id):
            return fake_row

    class FakeAcquire:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class FakePool:
        def acquire(self):
            return FakeAcquire()

    monkeypatch.setattr(repository, "pool", FakePool())

    result = asyncio.run(repository.get_analysis(1))

    assert result == fake_row