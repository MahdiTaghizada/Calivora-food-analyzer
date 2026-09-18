import asyncpg
import logging

from src.config import settings
from src.models import AnalysisRecord


logger=logging.getLogger(__name__)

def get_database_url():
    database_url=settings.database_url

    if database_url.startswith("postgresql+asyncpg://"):
        database_url=database_url.replace(
            "postgresql+asyncpg://",
            "postgresql://",
            1
        )

    return database_url

def row_to_record(row):
    if row is None:
        return None

    return AnalysisRecord(
        id=row["id"],
        timestamp=row["created_at"],
        image_path=row["image_path"],
        ingredients_json=row["ingredients_json"],
        totals_kcal=row["totals_kcal"],
        totals_protein_g=row["totals_protein_g"],
        totals_carbs_g=row["totals_carbs_g"],
        totals_fat_g=row["totals_fat_g"]
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
                        result TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ingredients_json TEXT,
                        totals_kcal DOUBLE PRECISION,
                        totals_protein_g DOUBLE PRECISION,
                        totals_carbs_g DOUBLE PRECISION,
                        totals_fat_g DOUBLE PRECISION
                    )
                """)

                await connection.execute("""
                    ALTER TABLE analysis_history
                    ALTER COLUMN result DROP NOT NULL
                """)

                await connection.execute("""
                    ALTER TABLE analysis_history
                    ADD COLUMN IF NOT EXISTS ingredients_json TEXT,
                    ADD COLUMN IF NOT EXISTS totals_kcal DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS totals_protein_g DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS totals_carbs_g DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS totals_fat_g DOUBLE PRECISION
                """)

            logger.info("Analysis history table ready")
        except Exception:
            logger.exception("Failed to create analysis history table")
            raise

    async def save(self,record):
        try:
            logger.info(f"Saving structured analysis for: {record.image_path}")

            async with self.pool.acquire() as connection:
                await connection.execute(
                    """
                    INSERT INTO analysis_history (
                        image_path,
                        ingredients_json,
                        totals_kcal,
                        totals_protein_g,
                        totals_carbs_g,
                        totals_fat_g,
                        created_at
                    )
                    VALUES ($1,$2,$3,$4,$5,$6,$7)
                    """,
                    record.image_path,
                    record.ingredients_json,
                    record.totals_kcal,
                    record.totals_protein_g,
                    record.totals_carbs_g,
                    record.totals_fat_g,
                    record.timestamp
                )

            logger.info("Structured analysis saved")
            return record
        except Exception:
            logger.exception("Failed to save structured analysis")
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
