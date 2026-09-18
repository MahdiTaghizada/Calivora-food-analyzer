import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL")
pool = None

async def init_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    return pool
async def create_table():
    async with pool.acquire() as connection:
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id SERIAL PRIMARY KEY,
                image_path TEXT NOT NULL,
                result TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

async def save_analysis(image_path, result):
    async with pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO analysis_history (image_path, result) VALUES ($1, $2)",
            image_path,
            result
        )

async def get_history():
    async with pool.acquire() as connection:
        rows = await connection.fetch(
            "SELECT * FROM analysis_history ORDER BY created_at DESC"
        )
        return rows
    
async def get_analysis(analysis_id):
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            "SELECT * FROM analysis_history WHERE id = $1",
            analysis_id
        )
        return row

async def close_pool():
    global pool

    if pool is not None:
        await pool.close()
        pool = None