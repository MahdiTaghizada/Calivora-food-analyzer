import sys
import os
import mimetypes
import logging
import asyncio

from ai.providers.base import ProviderError


from src.core.analyzer import analyze_meal
from src.utils.images import validate_image,ImageValidationError
from src.logging_config import setup_logging
from src.config import settings
from src.storage.repository import PostgresAnalysisRepository


logger=logging.getLogger(__name__)


def render_table(response):
    headers=("ingredient","g","kcal","protein","carbs","fat")
    rows=[]

    for item in response.ingredients:
        if item.nutrition is None:
            continue

        rows.append((
            item.ingredient.name,
            f"{item.ingredient.estimated_grams:.0f}",
            f"{item.nutrition.kcal:.0f}",
            f"{item.nutrition.protein_g:.1f}",
            f"{item.nutrition.carbs_g:.1f}",
            f"{item.nutrition.fat_g:.1f}"
        ))

    totals=response.totals

    rows.append((
        "TOTAL",
        f"{sum(item.ingredient.estimated_grams for item in response.ingredients):.0f}",
        f"{totals.kcal:.0f}",
        f"{totals.protein_g:.1f}",
        f"{totals.carbs_g:.1f}",
        f"{totals.fat_g:.1f}"
    ))

    widths=[
        max(len(headers[i]),max(len(row[i]) for row in rows))
        for i in range(len(headers))
    ]

    def format_row(row):
        return "  ".join(
            value.ljust(widths[i])
            for i,value in enumerate(row)
        )

    output=[format_row(headers)]
    output.append("-"*(sum(widths)+2*(len(widths)-1)))

    for row in rows[:-1]:
        output.append(format_row(row))

    output.append("-"*(sum(widths)+2*(len(widths)-1)))
    output.append(format_row(rows[-1]))

    return "\n".join(output)


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

    try:
        response=asyncio.run(run_analysis())
    except ProviderError as error:
        logger.error(f"AI provider error: {error}")
        print("AI provider is not configured")
        sys.exit(1)

    print(render_table(response))

    logger.info(f"Analysis completed: {path}")
