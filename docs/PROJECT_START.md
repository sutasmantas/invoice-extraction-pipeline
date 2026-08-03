# LedgerLens heterogeneous-document depth start

Date: 2026-08-03

## Restart boundary

- repository: `portfolio_demos/document_extraction`
- baseline branch and commit: `main` at
  `f201c9066a771aa1577bdb4b38aae2e93b7136de`
- isolated worktree: `portfolio_demos/worktrees/ledger_lens_depth`
- branch: `agent/ledger-lens-depth`
- baseline state: clean and equal to `origin/main`
- scope: depth slice 5 only; no UI, visual polish, deployment, auth, or new
  project work
- ContextSidecar boundary: owned and completed by another agent; never touch it
  from this worktree

## Bought outcome and evidence gap

The existing application turns text-layer invoices or images into reviewed
fields, but it hard-codes one regex schema, rejects image-only PDFs, does not
extract line items, exposes only a text snippet as provenance, and overwrites
corrections without history. The depth slice must establish a reusable,
defensible document-extraction decision on fixed public fixtures rather than
claim general document intelligence.

## GitHub foundation comparison

License was deliberately not researched, filtered, compared, or ranked. These
are private working projects and technical fit controls this decision.

| Candidate | Pin checked | Reusable central behavior | Integration cost/risk | Decision |
| --- | --- | --- | --- | --- |
| invoice-x/invoice2data | release `v1.0.1`, commit `0e1ff18b88979b30a1d7aac1e9a7614840f7b1c2`; current HEAD also inspected at `c4cb921087a932513b381245e20fbe124cce4c0e` | configurable YAML/JSON templates, typed regex extraction, input-reader cascade, line-item parser, structured results, public comparison fixtures | targeted invoice domain; requires a bounded adapter into LedgerLens review fields | **adopt 1.0.1** |
| docling-project/docling | `bbdc862be38c5a5c8d023ccdf2c6be5005cfbe4f` | broad document conversion, layout, tables, OCR, unified document model and provenance | large model/runtime and data-model migration for a small local benchmark | reject for this slice |
| Unstructured-IO/unstructured | `441b9d6895e2f07d9da1a8df61091be37bf5dc24` | broad partitioning, OCR/high-resolution PDF strategies and table inference | duplicates most of the current pipeline and adds a much broader dependency surface | reject for this slice |
| PaddlePaddle/PaddleOCR | `2661c7c0ef5c613e8f93c6e93b2e052399f0f854` | OCR and document/table model stacks | model downloads and runtime complexity are disproportionate to a CPU, no-key evidence slice | reject for this slice |

Selected central foundation: `invoice2data==1.0.1`, tied to the pinned release
commit above. Its template loader, regex/type parsers, line parser, PDFium input
reader, and public fixtures will be exercised. LedgerLens will not copy those
responsibilities into new custom parsers.

## Component-level GitHub reuse audit

This audit was completed before product implementation. Search included both
installable packages and bounded source/pattern reuse. `Adopt` uses a supported
interface; `refit` adapts a pinned implementation or pattern; `custom` is
permitted only where the replacement is tiny or total integration cost is
lower.

| Proposed component | GitHub candidates checked | Decision | Exact reused surface or custom boundary | Total integration-cost decision |
| --- | --- | --- | --- | --- |
| configurable schema and typed field extraction | invoice2data `0e1ff18`; Docling `bbdc862`; Unstructured `441b9d6` | **adopt** | invoice2data template loader plus regex/static/type parsers; LedgerLens only maps its structured result into review fields | one focused dependency replaces the hard-coded schema and parsing engine; the broad alternatives require a new document model |
| line-item/table extraction | invoice2data `0e1ff18`; pdfplumber `4c64b92`; Docling `bbdc862` | **adopt** | invoice2data `parser: lines` and its tested line normalization | adding pdfplumber or Docling would create a second extraction representation and reconciliation path |
| text-layer PDF extraction | invoice2data PDFium reader `0e1ff18`; pypdfium2 `b3e7e67`; pdfplumber `4c64b92` | **adopt** | invoice2data PDFium input path backed by exact `pypdfium2==5.12.1` | PDFium is already invoice2data's self-contained path and worked on the selected line-item fixture; no overlapping PDF parser is needed |
| image-only PDF rasterization | pypdfium2 release `5.12.1`, commit `b3e7e67a1e35c9436b52cb043d476b89ec8c38cb`; PyMuPDF `8a62977`; OCRmyPDF `aa6a32e` | **adopt** | `PdfDocument`, per-page `page.render(scale=...)`, and `PdfBitmap.to_pil()` feed the existing Pillow/pytesseract OCR boundary | reuses the same PDFium dependency as invoice2data; PyMuPDF overlaps it and OCRmyPDF adds a system pipeline when only page images are needed |
| OCR | existing pytesseract integration; invoice2data Tesseract reader `0e1ff18`; PaddleOCR `2661c7c` | **refit existing** | retain pytesseract and extend it from image files to PDFium-rendered pages; record page text and OCR confidence | invoice2data's PDF Tesseract path adds ImageMagick/pdftotext subprocess coupling; PaddleOCR adds model/runtime weight; the current boundary is already installed and testable |
| page/line provenance | Docling `bbdc862`; pdfplumber `4c64b92`; invoice2data result/template metadata `0e1ff18` | **custom bounded adapter over adopted APIs** | preserve extraction method and matched template from invoice2data, split per-page transcript, and locate returned values/line names in numbered source lines | a second document model solely for coordinates would create dual truth; the required source line/page record is small and sufficient for this benchmark, not a bbox claim |
| correction history | sqlite-history-json `53e66b2791a1ccc2efd19c1e24de9fd5afcc343b`; SQLAlchemy-Continuum `560369a` | **custom tiny table** | append one immutable row containing document, field, prior value, corrected value and timestamp in the existing raw-SQLite transaction | sqlite-history-json records the entire changed JSON blob and still needs field-level interpretation; Continuum requires an ORM migration; a single-purpose append/query is smaller and semantically exact |
| benchmark scoring and JSON report | invoice2data expected JSON fixtures; pytest-benchmark considered for timing | **custom tiny evaluator** | exact field/line-item assertions, provenance coverage, correction-history checks and elapsed milliseconds; no performance-ranking claim | pytest-benchmark measures runtime distributions but does not evaluate extraction correctness; exact case scoring is bounded test/report glue |

No overlapping candidate will be added merely to increase reuse count. New
custom logic discovered during implementation must be audited here before it is
written; otherwise the phase gate returns to `UNVERIFIED`.

## Frozen fixtures and pre-run decision rule

The benchmark sources come from invoice2data's public comparison corpus at
commit `c4cb921087a932513b381245e20fbe124cce4c0e`:

- `coolblue1.pdf`, SHA-256
  `3932539B71338F0C73D6ADE499A2A00CD2F9056C60F5A87B1EF623AF095E1607`,
  for a text-layer PDF with line items;
- `AmazonWebServices.png`, SHA-256
  `FEC56E365019C348986BFE1A6C16DB13B1D16FC5962BE83835BB4AC533466D6C`,
  converted deterministically to an image-only PDF for the rasterization/OCR
  path;
- `AmazonWebServices.pdf`, SHA-256
  `2E21D50F59A97B8C3778B238D14C9D7D15F74B8D021F819F1D2EDE1F5412F81B`,
  retained as the text-layer counterpart, not as a production corpus.

Promotion rule chosen before implementation:

1. the text PDF must match the pinned schema for invoice number, date, amount,
   and at least four named line items;
2. the image-only PDF must be rendered page by page and yield the pinned invoice
   number and amount through real Tesseract OCR in the container; a mocked OCR
   unit test is not benchmark evidence;
3. every exported scalar field and named line item must have non-empty page,
   line, method, template, and source-text provenance when a source match exists;
4. two successive corrections to one field must remain queryable in order with
   prior and corrected values while export returns only the latest value;
5. unsupported templates and unavailable OCR must fail explicitly, not emit a
   ready document;
6. existing upload/review/export tests must remain green.

## Visual boundary

This is a non-UI depth slice. The existing LedgerLens interface is already
structurally distinct and is frozen. No HTML, CSS, screenshots, responsive
work, or visual polish is authorized.

## Initial gate

| Gate | Evidence | Status |
| --- | --- | --- |
| clean isolated restart | branch/worktree/baseline above | PASS |
| GitHub foundation comparison | four pinned technical candidates | PASS |
| component-level reuse decisions | all planned substantial subsystems audited before code | PASS |
| fixed public fixtures and hashes | three sources recorded above | PASS |
| pre-run promotion rule | six observable conditions above | PASS |
| working implementation | closed later at application commit `81b75f0`; see the repository execution checkpoint and benchmark report | PASS |
| no visual/polish scope | explicit frozen boundary | PASS |

The table above was frozen as `UNVERIFIED` in foundation/audit commit
`0fd3b54`; this status update records the later implementation result without
changing the fact that the audit preceded the code.
