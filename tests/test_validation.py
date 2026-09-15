import pytest
from src.validation import ImageValidationError, validate_not_empty

def test_empty_image():
    with pytest.raises(ImageValidationError):
            validate_not_empty(b"")


from src.validation import ImageValidationError, validate_not_empty, validate_size
def test_image_too_large():
      with pytest.raises(ImageValidationError):
            big_file = b"a" * (6 * 1024 * 1024)
            validate_size(big_file,5)


from src.validation import validate_image_type
def test_unsupported_image_type():
      with pytest.raises(ImageValidationError):
            validate_image_type("image/gif")


from src.validation import validate_image_format
def test_invalid_image_format():
      with pytest.raises(ImageValidationError):
            validate_image_format(b"not-an-image")


def test_valid_png_format():
    validate_image_format(b"\x89PNG\r\n\x1a\n")

def test_valid_jpeg_format():
    validate_image_format(b"\xff\xd8\xff")


from src.validation import validate_image
def test_validate_image():
    validate_image(
        b"\x89PNG\r\n\x1a\n",
        "image/png",
        5
    )