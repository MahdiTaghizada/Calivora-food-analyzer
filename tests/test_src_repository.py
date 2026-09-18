import asyncio

from src.models import AnalysisRecord
from src.storage.repository import PostgresAnalysisRepository


def test_save_structured_analysis():
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

    repo=PostgresAnalysisRepository()
    repo.pool=FakePool()

    record=AnalysisRecord(
        image_path="image.png",
        ingredients_json="[]",
        totals_kcal=280,
        totals_protein_g=12.9,
        totals_carbs_g=29.8,
        totals_fat_g=11.8
    )

    asyncio.run(repo.save(record))

    assert saved["args"][0]=="image.png"
    assert saved["args"][1]=="[]"
    assert saved["args"][2]==280
    assert saved["args"][3]==12.9
    assert saved["args"][4]==29.8
    assert saved["args"][5]==11.8
