"""FastAPI HTTP surface for meal analysis."""

from __future__ import annotations

import tempfile
from pathlib import Path

from ai.providers.base import ProviderError
from fastapi import FastAPI, File, HTTPException, UploadFile

from src.config import settings
from src.core.analyzer import analyze_meal
from src.models import AnalysisResponse

app = FastAPI(title="Calivora AI Food Analyzer", version="1.0.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(image: UploadFile = File(...)) -> AnalysisResponse:
    if image.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(415, "Only JPEG and PNG images are supported")
    content = await image.read()
    max_bytes = settings.max_image_size_mb * 1024 * 1024
    if not content:
        raise HTTPException(400, "No image was provided")
    if len(content) > max_bytes:
        raise HTTPException(413, f"Image exceeds the {settings.max_image_size_mb} MB size limit")

    suffix = ".jpg" if image.content_type == "image/jpeg" else ".png"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary:
            temporary.write(content)
            temporary_path = Path(temporary.name)
        return await analyze_meal(temporary_path)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(503, "AI provider temporarily unavailable") from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
