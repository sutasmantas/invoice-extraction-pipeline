# LedgerLens claim ledger

## Defensible now

| Claim | Evidence | Boundary |
| --- | --- | --- |
| Integrated a pinned GitHub invoice-extraction foundation instead of rebuilding schema and line parsers | invoice2data 1.0.1 / `0e1ff18`; component audit in `PROJECT_START.md`; exercised templates and line parser | targeted invoice/template behavior, not arbitrary documents |
| Handles text-layer and image-only PDFs in one review pipeline | PDFium text/page rendering, real Tesseract 5.5.0 container benchmark, API upload path | fixed public fixtures on CPU; not production accuracy or throughput |
| Extracts configurable scalar fields and line items with source evidence | Coolblue fixture exact fields, five named items, page/line/method/template provenance | source-line provenance, not bounding boxes or semantic explanations |
| Preserves human corrections as ordered audit records | two-step correction test and benchmark; latest value exported | local SQLite, no multi-user identity or tamper-proof audit claim |
| Ships reproducible API/package/container evidence | Ruff, tests, wheel/sdist/Twine, Docker benchmark and live API smoke | local verification only; no remote deployment or production operations |

## Do not claim

- general document AI or support for arbitrary layouts;
- calibrated OCR confidence, benchmark transfer, or production accuracy;
- handwriting, multilingual OCR, client-specific field coverage, or scale;
- bounding-box provenance, authenticated reviewer identity, tamper-proof audit,
  malware scanning, encryption, or retention compliance;
- deployment, monitoring, high availability, or client outcomes.

