from io import BytesIO
from pathlib import Path
import pytest
from PIL import Image

from src.core.analyzer import validate_image_path


def test_validate_image_path_nonexistent(tmp_path):
    missing = tmp_path / "not_found.png"
    with pytest.raises(ValueError, match="Image file does not exist"):
        validate_image_path(missing)


def test_validate_image_path_unsupported_extension(tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("hello")
    with pytest.raises(ValueError, match="Only JPEG and PNG images are supported"):
        validate_image_path(txt_file)


def test_validate_image_path_oversized(tmp_path):
    oversized = tmp_path / "large.png"
    oversized.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * (6 * 1024 * 1024))
    with pytest.raises(ValueError, match="Image exceeds the 5 MB size limit"):
        validate_image_path(oversized, max_size_mb=5)


def test_validate_image_path_valid(tmp_path):
    valid_png = tmp_path / "valid.png"
    img = Image.new("RGB", (2, 2), color="red")
    img.save(valid_png, format="PNG")

    result = validate_image_path(valid_png)
    assert isinstance(result, Path)
    assert result == valid_png
