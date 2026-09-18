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
            validate_image_format(b"not-an-image","image/png")


def test_valid_png_format():
    validate_image_format(
        b"\x89PNG\r\n\x1a\n",
        "image/png"
    )


def test_valid_jpeg_format():
    validate_image_format(
        b"\xff\xd8\xff",
        "image/jpeg"
    )


from src.validation import validate_image
def test_validate_image():
    validate_image(
        b"\x89PNG\r\n\x1a\n",
        "image/png",
        5
    )


def test_valid_png():
    image_bytes = b"\x89PNG\r\n\x1a\n"

    validate_image_format(image_bytes, "image/png")


def test_valid_jpeg():
    image_bytes = b"\xff\xd8\xff"

    validate_image_format(image_bytes, "image/jpeg")

def test_mime_does_not_match_image():
    image_bytes = b"\xff\xd8\xff"

    with pytest.raises(ImageValidationError):
        validate_image_format(image_bytes, "image/png")