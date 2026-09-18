import asyncpg
import os
import logging


logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

pool = None


async def init_pool():
    global pool

    try:
        logger.info("Creating database pool")
        database_url=DATABASE_URL
        if database_url and database_url.startswith("postgresql+asyncpg://"):
            database_url=database_url.replace(
                "postgresql+asyncpg://",
                "postgresql://",
                1
            )

        pool=await asyncpg.create_pool(database_url)
        logger.info("Database pool created")
        return pool
    except Exception:
        logger.exception("Failed to create database pool")
        raise

async def create_table():
    try:
        logger.info("Creating analysis history table")

        async with pool.acquire() as connection:
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


async def save_analysis(image_path, result):
    try:
        logger.info(f"Saving analysis for: {image_path}")

        async with pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO analysis_history (image_path, result) VALUES ($1, $2)",
                image_path,
                result
            )

        logger.info("Analysis saved")

    except Exception:
        logger.exception("Failed to save analysis")
        raise


async def get_history():
    try:
        logger.info("Getting analysis history")

        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT * FROM analysis_history ORDER BY created_at DESC"
            )

        logger.info("Analysis history loaded")

        return rows

    except Exception:
        logger.exception("Failed to get analysis history")
        raise


async def get_analysis(analysis_id):
    try:
        logger.info(f"Getting analysis with id: {analysis_id}")

        async with pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT * FROM analysis_history WHERE id = $1",
                analysis_id
            )

        logger.info("Analysis loaded")

        return row

    except Exception:
        logger.exception("Failed to get analysis")
        raise


async def close_pool():
    global pool

    try:
        if pool is not None:
            logger.info("Closing database pool")

            await pool.close()
            pool = None

            logger.info("Database pool closed")

    except Exception:
        logger.exception("Failed to close database pool")
        raise