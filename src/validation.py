import logging
from io import BytesIO
from PIL import Image


logger=logging.getLogger(__name__)
ALLOWED_IMAGE_TYPES={"image/jpeg","image/png"}

class ImageValidationError(ValueError):
    pass

def validate_image_type(content_type):
    if content_type not in ALLOWED_IMAGE_TYPES:
        logger.warning(f"Unsupported image type: {content_type}")
        raise ImageValidationError("Unsupported image type")

def validate_not_empty(image_bytes):
    if not image_bytes:
        logger.warning("Image file is empty")
        raise ImageValidationError("Image file is empty")

def validate_size(image_bytes,max_size_mb):
    max_size_mb=max_size_mb*1024*1024
    if len(image_bytes)>max_size_mb:
        logger.warning("Image file is too large")
        raise ImageValidationError("Image file is too large")

def validate_image_format(image_bytes,content_type):
    if content_type=="image/png" and image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return
    if content_type=="image/jpeg" and image_bytes.startswith(b"\xff\xd8\xff"):
        return
    logger.warning("Image content does not match MIME type")
    raise ImageValidationError("Invalid image format")

def validate_image_content(image_bytes):
    try:
        image=Image.open(BytesIO(image_bytes))
        image.verify()
    except Exception:
        logger.warning("Corrupted image file")
        raise ImageValidationError("Corrupted image file")

def validate_image(image_bytes,content_type,max_size_mb):
    logger.info("Image validation started")
    validate_not_empty(image_bytes)
    validate_size(image_bytes,max_size_mb)
    validate_image_type(content_type)
    validate_image_format(image_bytes,content_type)
    validate_image_content(image_bytes)
    logger.info("Image validation completed")