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

---

# Ledger Lens technique-ceiling expertise notes

Date: 2026-08-04

## Calibrate review routing per extraction path

### Client trigger

- Job wording: confidence scores, human-in-the-loop review, production-ready
  extraction, low-error automation, or multiple OCR/model providers.
- System condition: text PDFs, scanned pages and model/VLM fallbacks feed one
  review queue but fail in different ways.

### Failure symptom or unanswered choice

Ledger's current field score largely inherits text/OCR routing confidence. That
score is useful for a demo but is not a calibrated probability that a field is
correct. One threshold can silently accept a high-confidence recognition or
schema error and over-review an easy text-layer field.

### Competing options

| Option | Why plausible | Main risk |
| --- | --- | --- |
| one global threshold | simple and already implemented | conflates OCR, extraction, validation and path-specific errors |
| path-specific deterministic evidence | cheap, auditable and uses existing completeness/provenance/business checks | may not rank interacting degradation failures well |
| calibrated small model | can combine correlated features and optimize risk/coverage | needs leakage-safe labelled data and monitoring |
| parser/model agreement | observable without field labels at inference | correlated systems can agree on the same wrong value |

### Controlled comparison

Freeze layout families before splitting data; pair clean pages with rotation,
blur, compression, contrast and crop variants. Measure automatic-accept error,
review coverage, risk-coverage area, Brier score and calibration error for each
extraction path. A policy passes only if no known incorrect document is marked
ready and review workload falls without a required-slice regression.

### Decision rule

Start with path-specific deterministic evidence. Add a small calibration model
only when deterministic features miss the frozen gate. Never present OCR token
confidence, LLM self-confidence or parser agreement as field correctness
without held-out calibration for that route.

### Delivery control

Version the policy, feature schema, calibration split and threshold. Route
missing required fields, validation failures, absent provenance and unsupported
layouts to review regardless of score. Recalibrate when the parser/model,
scanner distribution, language, target schema or review cost changes.

### Proposal-safe insight

I treat confidence as a routing decision, not a decorative model number. I
calibrate text, OCR and fallback paths separately against held-out layouts and
report the error that remains among automatically accepted fields alongside
the review workload.

### Evidence and interview follow-up

- Evidence: `TECHNIQUE_TAXONOMY.md`, `EVIDENCE_MATRIX.csv`,
  `BENCHMARK_DESIGN.md` L0 and `RESEARCH_DECISION.md`.
- Likely question: Why not choose 0.8 and review everything below it?
- Short answer: 0.8 has different meanings across OCR, deterministic parsing
  and VLM outputs. The delivery question is selective risk at a given review
  budget, measured on unseen layouts and acquisition failures.
- Central disposition: **new card** — `Calibrate review routing per extraction
  path`.

## Use model/VLM extraction as a routed escalation, not the document default

### Client trigger

- Job wording: changing layouts, visually complex documents, tables, many
  vendors, or an OCR/LLM/VLM pipeline.
- System condition: the cheap template path fails on representative layouts
  even though the needed information is visible.

### Failure symptom or unanswered choice

Broad document-model benchmarks tempt teams to replace a small reliable path
with one expensive parser or VLM. Current evidence is contradictory: some
business-document results find image-only models competitive with OCR-assisted
pipelines, while difficult and industrial document studies still expose OCR,
reading-order, layout and long-document failures. The winner depends on the
document and acceptance contract.

### Competing options

| Option | Good operating region | Main risk |
| --- | --- | --- |
| template + OCR | stable vendor layouts, CPU delivery | poor transfer to unseen structure |
| layout-aware parser | reading order, blocks and tables | parser integration does not itself solve schema KIE |
| direct-image VLM | visually varied pages and flexible schemas | cost, drift, hallucination, privacy and weak provenance |
| page retrieval then VLM | long documents with sparse relevant pages | retrieval misses become extraction misses |

### Decision rule

Retain the cheap measured path as control. Activate one maintained parser only
for predeclared layout/table failures. Activate a VLM only for residual cases it
can recover with schema validation and source evidence. Activate page retrieval
only for a measured long-document problem. No family becomes universal through
leaderboard rank alone.

### Delivery control

Pin each route and expose the selected method. Require explicit unsupported
outputs, identical typed schemas, provenance, repeated-run stability and
quality/cost slices. Do not integrate several broad parsers before one frozen
candidate closes the failure category.

### Proposal-safe insight

I use the smallest extraction path that meets the document's operating region,
then route only the failures that justify a layout model or VLM. That keeps the
review and export contract stable while making quality, latency and provider
cost directly comparable.

### Evidence and interview follow-up

- Evidence: `GITHUB_IMPLEMENTATION_AUDIT.md`, `BENCHMARK_DESIGN.md` L1–L3 and
  `RESEARCH_DECISION.md`.
- Likely question: Why not just send every page to the strongest VLM?
- Short answer: it hides easy deterministic wins, adds cost/privacy/version
  risk, and still needs validation and routing. The stronger claim is measured
  escalation on the failure set it actually fixes.
- Central disposition: **duplicate** of the existing `Detect document path
  before selecting extractor` and `Reuse focused parser before assembling
  document AI stack` cards; do not add another central card.

## Keep uncertainty routing and auditability coupled

### Client trigger

- Job wording: reviewer approval, correction audit, provenance, source
  highlights, export guarantees, or compliance-sensitive document processing.

### Failure symptom or unanswered choice

A review queue is not evidence of safe automation when fields lack source
references, corrections overwrite history, or exports ignore unresolved
status. Adding a more capable parser does not repair those product controls.

### Decision rule

Every extraction route must preserve source evidence, version/method, explicit
missing values, immutable corrections and export readiness. Quality candidates
that cannot normalize into those controls fail before UI or throughput work.

### Proposal-safe insight

I tie uncertain fields to evidence and an append-only correction trail, and I
block ready export until the review contract is satisfied. That makes a model
upgrade replaceable without weakening auditability.

### Evidence and disposition

- Evidence: `tests/test_api.py`, `tests/test_depth.py`,
  `docs/evidence/ledger_lens_benchmark.json` and
  `GITHUB_IMPLEMENTATION_AUDIT.md`.
- Central disposition: **duplicate** of `Route uncertain fields to review`; do
  not add another central card.
