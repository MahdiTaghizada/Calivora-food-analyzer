import asyncpg
import logging

from foodanalyzer.config import get_database_url
from foodanalyzer.models import AnalysisRecord


logger=logging.getLogger(__name__)

def row_to_record(row):
    if row is None:
        return None

    return AnalysisRecord(
        id=row["id"],
        image_path=row["image_path"],
        result=row["result"],
        created_at=row["created_at"]
    )



class PostgresAnalysisRepository:
    def __init__(self):
        self.pool=None

    async def init_pool(self):
        try:
            logger.info("Creating database pool")
            database_url=get_database_url()
            self.pool=await asyncpg.create_pool(database_url)
            logger.info("Database pool created")
            return self.pool
        except Exception:
            logger.exception("Failed to create database pool")
            raise

    async def create_table(self):
        try:
            logger.info("Creating analysis history table")

            async with self.pool.acquire() as connection:
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_history (
                        id SERIAL PRIMARY KEY,
                        image_path TEXT NOT NULL,
                        result TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

            logger.info("Analysis history table ready")
        except Exception:
            logger.exception("Failed to create analysis history table")
            raise

    async def save_analysis(self,image_path,result):
        try:
            logger.info(f"Saving analysis for: {image_path}")

            async with self.pool.acquire() as connection:
                await connection.execute(
                    "INSERT INTO analysis_history (image_path, result) VALUES ($1, $2)",
                    image_path,
                    result
                )

            logger.info("Analysis saved")
        except Exception:
            logger.exception("Failed to save analysis")
            raise

    async def get_history(self):
        try:
            logger.info("Getting analysis history")

            async with self.pool.acquire() as connection:
                rows=await connection.fetch(
                    "SELECT * FROM analysis_history ORDER BY created_at DESC"
                )

            logger.info("Analysis history loaded")
            return rows
        except Exception:
            logger.exception("Failed to get analysis history")
            raise

    async def get_analysis(self,analysis_id):
        try:
            logger.info(f"Getting analysis with id: {analysis_id}")

            async with self.pool.acquire() as connection:
                row=await connection.fetchrow(
                    "SELECT * FROM analysis_history WHERE id = $1",
                    analysis_id
                )

            logger.info("Analysis loaded")
            return row
        except Exception:
            logger.exception("Failed to get analysis")
            raise

    async def get_analysis_record(self,analysis_id):
        row=await self.get_analysis(analysis_id)
        return row_to_record(row)

    async def close_pool(self):
        try:
            if self.pool is not None:
                logger.info("Closing database pool")
                await self.pool.close()
                self.pool=None
                logger.info("Database pool closed")
        except Exception:
            logger.exception("Failed to close database pool")
            raise


_default_repository=PostgresAnalysisRepository()
pool=None


async def init_pool():
    global pool
    result=await _default_repository.init_pool()
    pool=_default_repository.pool
    return result


async def create_table():
    _default_repository.pool=pool
    return await _default_repository.create_table()


async def save_analysis(image_path,result):
    _default_repository.pool=pool
    return await _default_repository.save_analysis(image_path,result)


async def get_history():
    _default_repository.pool=pool
    return await _default_repository.get_history()


async def get_analysis(analysis_id):
    _default_repository.pool=pool
    return await _default_repository.get_analysis(analysis_id)


async def close_pool():
    global pool
    _default_repository.pool=pool
    await _default_repository.close_pool()
    pool=_default_repository.pool
