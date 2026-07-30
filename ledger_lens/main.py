from __future__ import annotations

import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse

from ledger_lens.config import PROJECT_ROOT, Settings
from ledger_lens.extractor import extract_invoice, read_text
from ledger_lens.schemas import Correction, Document, ExportPayload
from ledger_lens.store import DocumentStore

SAMPLE_DOCUMENTS = (
    (
        "cloud-harbor-invoice.txt",
        """INVOICE # CH-2026-041
From: Cloud Harbor Systems Ltd
VAT ID: GB123456789
Invoice date: 2026-07-22
Purchase order: PO-8841
Terms: Net 15 days
Subtotal: $8,420.00
Tax: $1,684.00
Total due: $10,104.00
""",
    ),
    (
        "meridian-platforms-invoice.txt",
        """INVOICE # MP-73018
From: Meridian Platforms SAS
VAT ID: FR12345678901
Invoice date: 24 Jul 2026
Purchase order: PO-7301
Terms: Net 45 days
Subtotal: €21,600.00
Tax: €4,320.00
Total due: €25,920.00
""",
    ),
    (
        "westline-renewal-invoice.txt",
        """INVOICE # WL-2026-882
From: Westline Operations GmbH
VAT ID: DE123456789
Invoice date: 27 Jul 2026
Terms: Net 30 days
Subtotal: €6,800.00
Tax: €1,292.00
Total due: €8,092.00
""",
    ),
    (
        "sample-invoice.txt",
        """INVOICE # INV-2026-1048
From: Northstar Technology Services GmbH
VAT ID: DE27844590I
Invoice date: 18 Jul 2026
Purchase order: PO-7712
Terms: Net 30 days
Subtotal: $13,200.00
Tax: $1,080.00
Total due: $14,280.00
""",
    ),
)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        store = DocumentStore(resolved.sqlite_path)
        for filename, source_text in SAMPLE_DOCUMENTS:
            if not store.has_filename(filename):
                store.add(filename, extract_invoice(source_text, resolved.review_threshold))
        application.state.store = store
        yield
        store.close()

    app = FastAPI(title="Ledger Lens", version="2.0.0", lifespan=lifespan)

    def store(request: Request) -> DocumentStore:
        return request.app.state.store

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "ocr": "tesseract"}

    @app.get("/api/documents", response_model=list[Document])
    def documents(request: Request) -> list[Document]:
        return store(request).list()

    @app.post("/api/documents", response_model=Document, status_code=status.HTTP_201_CREATED)
    async def upload(request: Request, file: UploadFile = File(...)) -> Document:
        safe_name = Path(file.filename or "document").name
        maximum = resolved.max_upload_mb * 1024 * 1024
        with tempfile.TemporaryDirectory(prefix="ledger-upload-") as directory:
            path = Path(directory) / safe_name
            size = 0
            with path.open("wb") as destination:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > maximum:
                        raise HTTPException(status_code=413, detail="Upload exceeds size limit.")
                    destination.write(chunk)
            try:
                text = read_text(path, resolved.tesseract_cmd)
                fields = extract_invoice(text, resolved.review_threshold)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
        return store(request).add(safe_name, fields)

    @app.patch(
        "/api/documents/{document_id}/fields/{field_name}",
        response_model=Document,
    )
    def correct(
        document_id: str, field_name: str, payload: Correction, request: Request
    ) -> Document:
        try:
            return store(request).correct(document_id, field_name, payload.value)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Document or field not found.") from exc

    @app.get("/api/documents/{document_id}/export", response_model=ExportPayload)
    def export(document_id: str, request: Request) -> ExportPayload:
        try:
            return store(request).export(document_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Document not found.") from exc

    @app.get("/", include_in_schema=False)
    def frontend() -> FileResponse:
        return FileResponse(PROJECT_ROOT / "index.html")

    @app.get("/app.js", include_in_schema=False)
    def script() -> FileResponse:
        return FileResponse(PROJECT_ROOT / "app.js", media_type="text/javascript")

    @app.get("/styles.css", include_in_schema=False)
    def styles() -> FileResponse:
        return FileResponse(PROJECT_ROOT / "styles.css", media_type="text/css")

    return app


app = create_app()
