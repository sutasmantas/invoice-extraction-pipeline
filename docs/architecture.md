# Architecture

```text
upload
  │
  ├── PDF text layer ──> text
  ├── image ──> Tesseract OCR ──> text
  └── TXT / Markdown ──> text
                         │
                         ▼
                field extraction
                         │
                 normalization + validation
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
          confirmed             needs review
              │                     │
              └──────────┬──────────┘
                         ▼
                  SQLite document state
                         │
                  normalized JSON export
```

Uploaded files live only in a temporary directory. SQLite stores extracted
values, source matches, confidence, review status, and corrections—not the
original files.

The browser never manufactures an export. It downloads the server's normalized
payload, and a refresh reloads corrected values from SQLite.
