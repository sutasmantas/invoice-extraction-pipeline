from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    page: int = Field(ge=1)
    line: int = Field(ge=1)
    text: str
    method: str
    template: str


class ExtractedField(BaseModel):
    name: str
    label: str
    value: str
    normalized_value: str | float | None = None
    confidence: float = Field(ge=0, le=1)
    status: str
    source_text: str
    provenance: SourceReference | None = None


class ExtractedLineItem(BaseModel):
    values: dict[str, Any]
    provenance: SourceReference | None = None


class Document(BaseModel):
    id: str
    filename: str
    document_type: str
    status: str
    fields: list[ExtractedField]
    line_items: list[ExtractedLineItem] = Field(default_factory=list)
    schema_id: str = ""
    extraction_method: str = ""
    created_at: datetime


class Correction(BaseModel):
    value: str = Field(min_length=1, max_length=500)


class CorrectionRecord(BaseModel):
    id: int
    document_id: str
    field_name: str
    prior_value: str
    corrected_value: str
    created_at: datetime


class ExportPayload(BaseModel):
    document_id: str
    document_type: str
    review_complete: bool
    data: dict[str, Any]
