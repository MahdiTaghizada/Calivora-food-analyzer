import sys
import os
import mimetypes
import logging
from demo_ai import run_demo
from src.validation import validate_image, ImageValidationError
from src.logging_config import setup_logging


setup_logging()

logger = logging.getLogger(__name__)


if len(sys.argv) < 3:
    logger.warning("Not enough command arguments")
    print("Usage: python -m foodanalyzer analyze <path>")
    sys.exit(1)

command = sys.argv[1]
if command != "analyze":
    logger.warning(f"Unknown command: {command}")
    print("Unknown command")
    sys.exit(1)

path = sys.argv[2]
if not os.path.isfile(path):  # if not os.path.exists(path):
    logger.warning(f"File not found: {path}")
    print("File not found")
    sys.exit(1)

try:
    with open(path, "rb") as file:
        image_bytes = file.read()

except OSError as error:
    logger.error(f"Failed to read file: {error}")
    print("Could not read file")
    sys.exit(1)     
content_type = mimetypes.guess_type(path)[0]
max_size_mb = int(os.getenv("MAX_IMAGE_SIZE_MB", "5"))

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
run_demo(True, path)
logger.info(f"Analysis completed: {path}")