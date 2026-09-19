import asyncio
from datetime import datetime,timezone

from src.models import AnalysisRecord
from src.storage import repository


def test_init_pool(monkeypatch):
    fake_pool=object()

    async def fake_create_pool(url):
        assert url=="postgresql://test"
        return fake_pool

    monkeypatch.setattr(repository,"get_database_url",lambda:"postgresql://test")
    monkeypatch.setattr(repository.asyncpg,"create_pool",fake_create_pool)

    repo=repository.PostgresAnalysisRepository()

    result=asyncio.run(repo.init_pool())

    assert result is fake_pool
    assert repo.pool is fake_pool


def test_create_table():
    queries=[]

    class FakeConnection:
        async def execute(self,query,*args):
            queries.append(query)

    class FakeAcquire:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self,exc_type,exc,tb):
            pass

    class FakePool:
        def acquire(self):
            return FakeAcquire()

    repo=repository.PostgresAnalysisRepository()
    repo.pool=FakePool()

    asyncio.run(repo.create_table())

    assert len(queries)==3
    assert "CREATE TABLE IF NOT EXISTS analysis_history" in queries[0]
    assert "ingredients_json" in queries[0]


def test_save():
    saved={}

    class FakeConnection:
        async def execute(self,query,*args):
            saved["args"]=args

    class FakeAcquire:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self,exc_type,exc,tb):
            pass

    class FakePool:
        def acquire(self):
            return FakeAcquire()

    repo=repository.PostgresAnalysisRepository()
    repo.pool=FakePool()

    record=AnalysisRecord(
        image_path="image.png",
        ingredients_json="[]",
        totals_kcal=280,
        totals_protein_g=12.9,
        totals_carbs_g=29.8,
        totals_fat_g=11.8
    )

    result=asyncio.run(repo.save(record))

    assert result is record
    assert saved["args"][0]=="image.png"
    assert saved["args"][1]=="[]"
    assert saved["args"][2]==280


def test_get_history():
    fake_rows=[
        {
            "id":1,
            "image_path":"image.png",
            "created_at":"2026-09-19"
        }
    ]

    class FakeConnection:
        async def fetch(self,query):
            return fake_rows

    class FakeAcquire:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self,exc_type,exc,tb):
            pass

    class FakePool:
        def acquire(self):
            return FakeAcquire()

    repo=repository.PostgresAnalysisRepository()
    repo.pool=FakePool()

    result=asyncio.run(repo.get_history())

    assert result==fake_rows


def test_close_pool():
    class FakePool:
        def __init__(self):
            self.closed=False

        async def close(self):
            self.closed=True

    fake_pool=FakePool()

    repo=repository.PostgresAnalysisRepository()
    repo.pool=fake_pool

    asyncio.run(repo.close_pool())

    assert fake_pool.closed is True
    assert repo.pool is None


def test_get_analysis():
    fake_row={"id":1,"image_path":"image.png"}

    class FakeConnection:
        async def fetchrow(self,query,analysis_id):
            assert analysis_id==1
            return fake_row

    class FakeAcquire:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self,exc_type,exc,tb):
            pass

    class FakePool:
        def acquire(self):
            return FakeAcquire()

    repo=repository.PostgresAnalysisRepository()
    repo.pool=FakePool()

    result=asyncio.run(repo.get_analysis(1))

    assert result==fake_row


def test_row_to_record():
    timestamp=datetime.now(timezone.utc)

    fake_row={
        "id":1,
        "created_at":timestamp,
        "image_path":"image.png",
        "ingredients_json":"[]",
        "totals_kcal":280,
        "totals_protein_g":12.9,
        "totals_carbs_g":29.8,
        "totals_fat_g":11.8
    }

    record=repository.row_to_record(fake_row)

    assert record.id==1
    assert record.image_path=="image.png"
    assert record.ingredients_json=="[]"
    assert record.totals_kcal==280


def test_get_analysis_record():
    timestamp=datetime.now(timezone.utc)

    fake_row={
        "id":1,
        "created_at":timestamp,
        "image_path":"image.png",
        "ingredients_json":"[]",
        "totals_kcal":280,
        "totals_protein_g":12.9,
        "totals_carbs_g":29.8,
        "totals_fat_g":11.8
    }

    class FakeConnection:
        async def fetchrow(self,query,analysis_id):
            return fake_row

    class FakeAcquire:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self,exc_type,exc,tb):
            pass

    class FakePool:
        def acquire(self):
            return FakeAcquire()

    repo=repository.PostgresAnalysisRepository()
    repo.pool=FakePool()

    record=asyncio.run(repo.get_analysis_record(1))

    assert record.id==1
    assert record.image_path=="image.png"
    assert record.totals_kcal==280
