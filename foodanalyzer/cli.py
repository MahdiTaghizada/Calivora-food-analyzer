import sys
import os
import mimetypes
import logging
import asyncio

from io import StringIO
from contextlib import redirect_stdout

from demo_ai import run_demo
from foodanalyzer.utils.images import validate_image,ImageValidationError
from foodanalyzer.logging_config import setup_logging
from foodanalyzer.config import get_max_image_size_mb
from foodanalyzer.storage.repository import init_pool,create_table,save_analysis,get_history,close_pool


logger=logging.getLogger(__name__)


async def show_history():
    await init_pool()
    await create_table()

    rows=await get_history()

    if not rows:
        print("No analysis history")
    else:
        for row in rows:
            print(
                f"{row['id']} | "
                f"{row['image_path']} | "
                f"{row['created_at']}"
            )

    await close_pool()


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
    max_size_mb=get_max_image_size_mb()

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

    output=StringIO()

    with redirect_stdout(output):
        run_demo(True,path)

    result=output.getvalue()

    print(result,end="")

    logger.info(f"Analysis completed: {path}")

    async def save_result():
        await init_pool()
        await create_table()
        await save_analysis(path,result)
        await close_pool()

    if os.getenv("DATABASE_URL"):
        try:
            asyncio.run(save_result())
            logger.info("Analysis saved to database")
        except Exception as error:
            logger.error(f"Database save failed: {error}")
    else:
        logger.warning("DATABASE_URL is not set, database save skipped")
