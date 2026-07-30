from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    name: str
    label: str
    value: str
    normalized_value: str | float | None = None
    confidence: float = Field(ge=0, le=1)
    status: str
    source_text: str


class Document(BaseModel):
    id: str
    filename: str
    document_type: str
    status: str
    fields: list[ExtractedField]
    created_at: datetime


class Correction(BaseModel):
    value: str = Field(min_length=1, max_length=500)


class ExportPayload(BaseModel):
    document_id: str
    document_type: str
    review_complete: bool
    data: dict[str, Any]
