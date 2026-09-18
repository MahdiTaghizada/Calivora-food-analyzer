import sys
import os
import mimetypes
import logging
import asyncio


from src.core.analyzer import analyze_meal
from src.utils.images import validate_image,ImageValidationError
from src.logging_config import setup_logging
from src.config import settings
from src.storage.repository import PostgresAnalysisRepository


logger=logging.getLogger(__name__)


async def show_history():
    repository=PostgresAnalysisRepository()

    try:
        await repository.init_pool()
        await repository.create_table()

        rows=await repository.get_history()

        if not rows:
            print("No analysis history")
        else:
            for row in rows:
                print(
                    f"{row['id']} | "
                    f"{row['image_path']} | "
                    f"{row['created_at']}"
                )
    finally:
        await repository.close_pool()

def main():
    setup_logging()

    if len(sys.argv)<2:
        print("Usage: python -m foodanalyzer analyze <path>")
        print("       python -m foodanalyzer history")
        sys.exit(1)

    command=sys.argv[1]

    if command=="history":
        if not os.getenv("DATABASE_URL"):
            print("DATABASE_URL is not set")
            sys.exit(1)

        asyncio.run(show_history())
        return

    if command!="analyze":
        logger.warning(f"Unknown command: {command}")
        print("Unknown command")
        sys.exit(1)

    if len(sys.argv)<3:
        print("Usage: python -m foodanalyzer analyze <path>")
        sys.exit(1)

    path=sys.argv[2]

    if not os.path.isfile(path):
        logger.warning(f"File not found: {path}")
        print("File not found")
        sys.exit(1)

    try:
        with open(path,"rb") as file:
            image_bytes=file.read()
    except OSError as error:
        logger.error(f"Failed to read file: {error}")
        print("Could not read file")
        sys.exit(1)

    content_type=mimetypes.guess_type(path)[0]
    max_size_mb=settings.max_image_size_mb

    try:
        logger.info(f"Validating image: {path}")
        validate_image(
            image_bytes,
            content_type,
            max_size_mb
        )
    except ImageValidationError as error:
        logger.warning(f"Image validation failed: {error}")
        print(error)
        sys.exit(1)

    logger.info(f"Starting analysis: {path}")

    async def run_analysis():
        repository=PostgresAnalysisRepository()

        try:
            await repository.init_pool()
            await repository.create_table()

            response=await analyze_meal(
                path,
                repository=repository
            )

            return response
        finally:
            await repository.close_pool()

    response=asyncio.run(run_analysis())
    result=response.model_dump_json(indent=2)

    print(result)

    logger.info(f"Analysis completed: {path}")
