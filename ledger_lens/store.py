from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from ledger_lens.schemas import Document, ExportPayload, ExtractedField


class DocumentStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY, filename TEXT NOT NULL, document_type TEXT NOT NULL,
                status TEXT NOT NULL, fields_json TEXT NOT NULL, created_at TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0])

    def has_filename(self, filename: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM documents WHERE filename = ? LIMIT 1",
            (filename,),
        ).fetchone()
        return row is not None

    def add(self, filename: str, fields: list[ExtractedField]) -> Document:
        document_id = uuid.uuid4().hex
        created_at = datetime.now(UTC)
        status = self._status(fields)
        self.connection.execute(
            "INSERT INTO documents VALUES (?, ?, 'invoice', ?, ?, ?)",
            (
                document_id,
                filename,
                status,
                json.dumps([field.model_dump() for field in fields]),
                created_at.isoformat(),
            ),
        )
        self.connection.commit()
        return self.get(document_id)

    def list(self) -> list[Document]:
        rows = self.connection.execute(
            "SELECT * FROM documents ORDER BY created_at DESC"
        ).fetchall()
        return [self._document(row) for row in rows]

    def get(self, document_id: str) -> Document:
        row = self.connection.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
        if not row:
            raise KeyError(document_id)
        return self._document(row)

    def correct(self, document_id: str, field_name: str, value: str) -> Document:
        document = self.get(document_id)
        found = False
        fields = []
        for field in document.fields:
            if field.name == field_name:
                found = True
                field = field.model_copy(
                    update={
                        "value": value,
                        "normalized_value": value,
                        "confidence": 1.0,
                        "status": "confirmed",
                    }
                )
            fields.append(field)
        if not found:
            raise KeyError(field_name)
        self.connection.execute(
            "UPDATE documents SET status = ?, fields_json = ? WHERE id = ?",
            (
                self._status(fields),
                json.dumps([field.model_dump() for field in fields]),
                document_id,
            ),
        )
        self.connection.commit()
        return self.get(document_id)

    def export(self, document_id: str) -> ExportPayload:
        document = self.get(document_id)
        return ExportPayload(
            document_id=document.id,
            document_type=document.document_type,
            review_complete=document.status == "ready",
            data={
                field.name: (
                    field.normalized_value if field.normalized_value is not None else field.value
                )
                for field in document.fields
            },
        )

    @staticmethod
    def _status(fields: list[ExtractedField]) -> str:
        return (
            "needs_review" if any(field.status == "needs_review" for field in fields) else "ready"
        )

    @staticmethod
    def _document(row: sqlite3.Row) -> Document:
        raw = dict(row)
        return Document(
            id=raw["id"],
            filename=raw["filename"],
            document_type=raw["document_type"],
            status=raw["status"],
            fields=[
                ExtractedField.model_validate(field) for field in json.loads(raw["fields_json"])
            ],
            created_at=datetime.fromisoformat(raw["created_at"]),
        )
