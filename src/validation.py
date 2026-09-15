import pytest
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
class ImageValidationError(ValueError):
    pass

def validate_image_type(content_type):
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ImageValidationError("Unsupported image type")
def validate_not_empty(image_bytes):
    if not image_bytes:
        raise ImageValidationError("Image file is empty")
def validate_size(image_bytes,max_size_mb):
    max_size_mb=max_size_mb*1024*1024
    if len(image_bytes)>max_size_mb:
        raise ImageValidationError("Image file is too large")
def validate_image_format(image_bytes): #heqiqeten format duzdu?
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return
    raise ImageValidationError("Invalid image format")
def validate_image(image_bytes,content_type,max_size_mb):   
    validate_not_empty(image_bytes)
    validate_size(image_bytes,max_size_mb)
    validate_image_type(content_type)
    validate_image_format(image_bytes)
    