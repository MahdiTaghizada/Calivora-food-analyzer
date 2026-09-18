import sys
import os
from src.validation import validate_image, ImageValidationError
import mimetypes

from demo_ai import run_demo

if len(sys.argv) < 3:
    print("Usage: python -m foodanalyzer analyze <path>")
    sys.exit(1)
command=sys.argv[1]
if command!="analyze":
    print("Unknown command")
    sys.exit(1)
path = sys.argv[2]
if not os.path.exists(path):
    print("File not found")
    sys.exit(1)
with open(path, "rb") as file:
    image_bytes=file.read()

content_type=mimetypes.guess_type(path)[0]
max_size_mb=int(os.getenv("MAX_IMAGE_SIZE_MB","5"))
try:
    validate_image(image_bytes, content_type, max_size_mb)
except ImageValidationError as error:
    print(error)
    sys.exit(1)
run_demo(True, path)