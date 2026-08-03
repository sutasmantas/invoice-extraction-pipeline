# LedgerLens heterogeneous-document decision note

## Client trigger

- Job wording: extract structured invoice/document fields, scanned PDFs, line
  items, source evidence, and review corrections.
- Measured demand: structured extraction appears in 234 of 4,910 audited jobs
  (4.8%); accuracy/quality requirements appear in 715 (14.6%).
- Existing reusable project: LedgerLens review queue, SQLite store, FastAPI API,
  image OCR, and export contract.

## Failure symptom or unanswered choice

The existing regex-only extractor cannot show that one coherent implementation
handles text PDFs, image-only PDFs, configurable layouts, line items,
provenance, and correction history. Building all of those mechanisms locally
would duplicate mature GitHub work and weaken delivery speed.

## Competing options

| Option | Why plausible | Main cost or failure risk |
| --- | --- | --- |
| existing pypdf plus custom regex | already runs | one schema, no scanned PDF or line-item solution, growing custom parser |
| invoice2data plus shared PDFium/Tesseract boundary | targeted templates, parsers, public fixtures, small dependencies | template-based scope; OCR still needs a system Tesseract runtime |
| Docling/Unstructured/PaddleOCR stack | broad layout/OCR/document capabilities | large runtime and migration surface for a bounded CPU benchmark |

## Controlled comparison

- Cases: pinned `coolblue1` text PDF and Amazon Web Services text/image sources
  recorded in `docs/PROJECT_START.md`.
- Metrics: exact scalar fields, line-item count/names, scanned-PDF OCR success,
  provenance completeness, correction-history order, explicit failure behavior,
  and elapsed time as an observation only.
- Runtime: Python 3.11 local and Docker CPU; invoice2data 1.0.1; pypdfium2
  5.12.1; Tesseract version will be captured by the final report.
- Outside comparison: arbitrary document generalization, handwriting, provider
  OCR quality, calibrated confidence, throughput/scale, and visual polish.

## Pre-run decision rule

Promote the coherent invoice2data/PDFium/Tesseract path only if every condition
in `docs/PROJECT_START.md` passes. Otherwise retain the current extractor and
record the failing fixture/category; do not claim heterogeneous-document
support from partial output.

## Result

The Docker CPU benchmark passed every frozen gate:

- fixture hashes matched the pinned upstream sources;
- the Coolblue text PDF returned invoice `993548900`, date `2014-04-19`, amount
  `717.97`, five named line items, and source references;
- the Amazon image source was converted to an image-only PDF, rasterized through
  PDFium, and processed by real Tesseract 5.5.0, returning invoice `42183017`
  and amount `4.11`;
- two corrections remained ordered with prior/new values and export returned
  only the latest value;
- observed container times were 81.3 ms for the text PDF and 5,881.4 ms for the
  scanned PDF. These are single-run observations, not throughput claims.

Raw case evidence: `docs/evidence/ledger_lens_benchmark.json`.

## Decision rule

Use the invoice2data/PDFium/Tesseract path when the client can provide stable
invoice layouts, representative scans, target fields, and acceptance examples.
Start with PDFium text; render and OCR only image-only pages. Add or revise a
template against held-out client examples instead of adding another extraction
framework. Reconsider a layout-aware/ML stack only when representative failures
cannot be expressed safely in templates or source-line provenance is
insufficient.

## Delivery control

Pin the template and fixture versions, verify fixture hashes, route unmatched or
low-confidence records to review, keep correction history, and make a real OCR
case part of the delivery gate. Never export an unmatched template as ready.

## Reuse boundary

- Reusable without client data: configurable templates, PDF rasterization,
  review-field mapping, source-line provenance, correction history, and the
  benchmark harness.
- Requires client data: template creation, acceptance fields, representative
  scan quality, language packs, confidence thresholds, retention/auth policy.
- Unsupported claim: general document AI, production OCR accuracy, arbitrary
  layout support, calibrated probability, or client-scale performance.

## Proposal-safe insight

I can start document extraction with a configurable, reviewable template stack
instead of spending client time rebuilding parsers. I validate both text and
scanned PDFs on fixed examples, retain the source page/line and correction
history, and treat new layouts and scan quality as acceptance inputs rather
than assuming benchmark accuracy transfers.

## Evidence

- Code: `ledger_lens/extractor.py`, `ledger_lens/store.py`, and
  `ledger_lens/benchmark.py`.
- Tests: `tests/test_api.py` and `tests/test_depth.py`.
- Raw comparison: `docs/evidence/ledger_lens_benchmark.json`.
- Reproduction: build the Docker image, then run
  `ledger-lens-benchmark /fixtures` with the pinned fixture directory mounted.

## Interview follow-up

- Likely question: Why not use Docling or an OCR model for everything?
- Short answer: the target was stable invoice layouts on CPU. One targeted
  template/parser foundation plus the same PDFium dependency for text and
  rasterization removed more custom work with much less integration surface.
- Deeper evidence: open `docs/PROJECT_START.md` for the component audit and the
  benchmark JSON for case-level results and claim limits.
