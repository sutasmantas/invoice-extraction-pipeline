# Architecture

```text
upload
  │
  ├── PDF text layer ──> PDFium page text
  ├── image-only PDF ──> PDFium page render ──> Tesseract OCR
  ├── image ──> Tesseract OCR
  └── TXT / Markdown ──> text
                                  │
                                  ▼
                pinned invoice2data template
                  + typed/line parsers
                         │
              normalization + source page/line
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
          confirmed             needs review
              │                     │
              └──────────┬──────────┘
                         ▼
                  SQLite document state
                    + correction log
                         │
                  normalized JSON export
```

Uploaded files live only in a temporary directory. SQLite stores extracted
values and line items, source references, routing confidence, review status,
and immutable field-level corrections—not the original files.

The adopted stack is deliberately coherent: invoice2data supplies template,
type, and line parsing, while its pypdfium2 dependency supplies both text pages
and OCR-ready page images. LedgerLens owns only the adapter into its review and
persistence contracts. It does not add pdfplumber, Docling, or a second
document representation.

The browser never manufactures an export. It downloads the server's normalized
payload, and a refresh reloads corrected values from SQLite.
