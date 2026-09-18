from dataclasses import dataclass
from datetime import datetime


@dataclass
class AnalysisRecord:
    image_path: str
    result: str
    id: int | None = None
    created_at: datetime | None = None
