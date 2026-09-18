import os


def get_database_url():
    database_url=os.getenv("DATABASE_URL")

    if database_url and database_url.startswith("postgresql+asyncpg://"):
        database_url=database_url.replace(
            "postgresql+asyncpg://",
            "postgresql://",
            1
        )

    return database_url


def get_max_image_size_mb():
    return int(os.getenv("MAX_IMAGE_SIZE_MB","5"))


def get_log_level():
    return os.getenv("LOG_LEVEL","INFO")
