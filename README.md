# Ledger Lens

A working document-intelligence application for invoice extraction, confidence
routing, human correction, persistence, and normalized JSON export.

![Invoice field review](docs/screenshots/document-review.png)

![Persistent review queue](docs/screenshots/review-queue.png)

## What is implemented

- text extraction from PDFs with a text layer
- Tesseract OCR for PNG, JPG, WEBP, and TIFF images
- invoice field extraction with normalization and validation
- confidence-based routing to a review queue
- source-linked correction with SQLite persistence
- server-generated structured JSON export
- honest transcript rendering for uploaded documents
- FastAPI, automated tests, Docker, and GitHub Actions

The application seeds one fictional invoice so the review flow works
immediately. Uploaded source files are processed in a temporary directory and
are not retained.

## Run locally

Requirements: Python 3.11+ and Tesseract for image OCR.

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
uvicorn ledger_lens.main:app --reload
```

Open <http://localhost:8000>. API documentation is available at
<http://localhost:8000/docs>.

Text PDFs and text files work without Tesseract. On Windows, set
`LEDGER_TESSERACT_CMD` if `tesseract.exe` is not on `PATH`.

## Docker

```bash
docker compose up --build
```

The image installs Tesseract and persists review state in the `ledger-data`
volume.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/documents` | List extracted documents and fields |
| `POST` | `/api/documents` | Extract an uploaded document |
| `PATCH` | `/api/documents/{id}/fields/{name}` | Persist a reviewed value |
| `GET` | `/api/documents/{id}/export` | Return normalized structured data |

## Verification

```bash
ruff check .
pytest --cov=ledger_lens --cov-report=term-missing
```

Tests cover extraction, low-confidence routing, correction, persistence,
normalized monetary export, text upload, and invalid file handling.

## Architecture

See [docs/architecture.md](docs/architecture.md).

## Limitations

- The included schema targets invoices; additional document types need their
  own extractors and validators.
- Image-only PDFs are rejected with a clear error. Convert their pages to
  images or add PDF rasterization before OCR.
- OCR confidence is combined with deterministic validation; it is not a
  calibrated probability.
- Production deployments need authentication, malware scanning, encrypted
  storage, and retention policies.

## License

MIT
