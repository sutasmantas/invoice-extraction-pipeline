# Ledger Lens GitHub implementation audit

Date checked: 2026-08-04

## Decision rule

Search GitHub before writing any substantial parser, OCR, layout, table, KIE,
confidence, or review subsystem. Adopt or refit a component only when it removes
one complete responsibility through a stable seam. Reject whole applications
that duplicate Ledger Lens's upload API, schema, review store, correction
history, or export contract. Tiny adapters, scoring glue, and product-specific
validation remain local when importing a framework would cost more than the
behavior it replaces.

The
user's private portfolio use makes implementation fitness the relevant filter.

## Host and baseline

- Ledger Lens baseline: `638bb35e6fd5eeea1ee5fd187b9e9c10d91671df`.
- Host: Intel Core Ultra 7 155U, 32 GB RAM, no NVIDIA runtime detected.
- Existing seams: `read_document`, `ExtractionResult`, Pydantic field/source
  models, review threshold, `DocumentStore`, correction API, export API, and
  `ledger_lens.benchmark`.
- Existing reusable foundation: invoice2data 1.0.1, pypdfium2 5.12.1,
  pytesseract/Tesseract, FastAPI, Pydantic, SQLite and pytest.

## Pinned implementation snapshot

| Repository | Pin / release | Health observed | Runnable surface | Ledger decision |
| --- | --- | --- | --- | --- |
| `tesseract-ocr/tesseract` | `64ed93b68c01f359d924fc1bfcf0d5931eb77211`; v5.5.3 | pushed 2026-08-03; current issues include training extraction and packaged-binary gaps | CLI/API recognition, TSV/hOCR confidences and coordinates | retain as CPU OCR control; do not treat mean OCR confidence as field probability |
| `docling-project/docling` | `9b454c9e88454d95fd04d538c552a3c07bc3c04d`; v2.118.0 | pushed 2026-08-03; issue #3936 reports a v2.118 hyphenated-label crash | `DocumentConverter` and structured `DoclingDocument` export | refit through one parser adapter in a future comparison; pin below affected release until defect is reproduced/closed |
| `PaddlePaddle/PaddleOCR` | `2661c7c0ef5c613e8f93c6e93b2e052399f0f854`; v3.7.0 | pushed 2026-07-22; open ROCm, Torch and ONNX compatibility reports | PaddleOCR, PP-Structure and PaddleOCR-VL pipelines | primary maintained challenger for OCR/layout/VLM operating regions; isolate environment and output adapter |
| `microsoft/unilm` | `833df7e7832e5064a281131ee64a481afa8e5b95` | pushed 2026-01-23; broad research monorepo | LayoutLMv3 model/config/examples | reuse pretrained model only if labelled held-out layouts justify fine-tuning; no first integration |
| `microsoft/table-transformer` | `16d124f616109746b7785f03085100f1f6247575`; v1.0.0 | last push 2024-06-24; release dates to 2023 | table detection and structure-recognition models | focused candidate only after line-item failures show missing row/column structure; retain separate OCR boundary |
| `clovaai/donut` | `4cfcf972560e1a0f26eb3e294c8fc88a0d336626` | last push 2024-07-11; latest release 2022 | OCR-free encoder-decoder inference/fine-tuning | reject current integration; use as historical family evidence, not a maintained default |
| `allenai/olmocr` | `f7cfe4c22098b154c76b6ec950d1c0a464eecf8d`; v0.4.27 | pushed 2026-03-25 | 7B-VLM document conversion and benchmark tooling | reject on this CPU host; reconsider only with an authorized >=12 GB GPU or service |
| `opendatalab/MinerU` | `79d6d8d79fb8f3ddba5cc34c07a16f0ec36f56c7`; v3.4.4 | pushed 2026-07-30 | CPU/GPU pipeline and VLM document parsing | inspect only if Docling/Paddle fail the same accepted case; do not integrate three broad parsers |
| `datalab-to/surya` | `f2c45daaf67be28dfe09c602eb62a0df99a022a8`; v0.22.1 | pushed 2026-07-23; current vLLM, grammar and benchmark-reproduction questions | OCR, layout, reading order and table recognition | secondary focused challenger; do not run in parallel without a failure-driven reason |

## Component-level reuse decisions

| Needed behavior | GitHub reuse result | Exact seam | Integration-cost decision |
| --- | --- | --- | --- |
| text/scan path detection | retain/refit current PDFium probe | `read_document` decides text layer versus per-page raster/OCR | tiny and already tested; importing another router would not remove a complete responsibility |
| stable-layout invoice KIE | retain invoice2data | template loader, typed parsers and line parser map into `ExtractionResult` | already replaces custom regex/schema machinery and passed the fixed benchmark |
| varied-layout parsing | compare Docling and one Paddle profile | adapt normalized page text, elements, coordinates and method metadata behind `ReadResult`/a successor parser protocol | component reuse is justified; replacing the app or store is not |
| character OCR | retain Tesseract control; Paddle challenger only on failure strata | normalized page transcripts plus word/box confidence when available | isolates OCR so layout/KIE results are not mislabelled as recognition wins |
| table structure | Table Transformer only if activated | rows/cells converted to the existing line-item schema with source coordinates | no integration until template line parsing fails because structure is lost |
| flexible schema extraction | reuse a constrained model/provider adapter later | input is selected page/evidence; output must validate against existing Pydantic schema | no provider is selected by literature alone; deterministic validation stays local |
| long-document localization | reuse Atlas retrieval contracts later | page/block IDs and scores feed only accepted pages to the extractor | avoids building a second search subsystem; deferred until long-document cases exist |
| calibration | custom bounded evaluator over sklearn/scipy only if needed | field/path features in, correctness/risk-coverage report out | calibration policy is product-specific; a large MLOps framework would add no core algorithm |
| review/corrections | retain local store/API | immutable correction row, current value and review status | exact product behavior is already smaller than adopting an ORM audit framework |
| benchmark scoring | extend local evaluator | case manifest, exact fields/line items/localization, perturbation labels, risk/coverage, time/RAM/VRAM | benchmark packages do not define Ledger's correctness contract; local glue is appropriate |

## Rejected integration patterns

- Do not replace Ledger Lens with Docling, MinerU, PaddleOCR, Unstructured, or
  another full document application. Reuse a parser/model surface only.
- Do not integrate several broad parsers before a single frozen comparison.
- Do not write a new OCR engine, table detector, layout model, or document VLM.
- Do not promote repository activity or a headline benchmark without a
  Ledger-shaped held-out case and failure-category report.
- Do not use one confidence number across text-PDF, scan-OCR, layout-parser and
  VLM paths. Path-specific calibration is an acceptance requirement.

## Minimal future integration checks

No dependency was added in this dossier. If a candidate is later authorized,
the first commit must prove only its seam:

1. pin the exact dependency/model/revision and record download/runtime size;
2. parse one accepted text page and one relevant difficult page without the UI;
3. normalize values and evidence into Ledger's existing Pydantic contract;
4. preserve page/line or page/bounding-box provenance and explicit failures;
5. run the unchanged invoice2data/Tesseract controls;
6. capture wall time, peak RAM and any VRAM/service cost; and
7. remove the candidate if the seam cannot pass before product orchestration is
   changed.

## Audit conclusion

GitHub contains mature components for every substantial proposed subsystem.
The next Ledger work is therefore a controlled comparison and calibration
slice, not custom model or parser development. The only justified custom code
is a bounded adapter, evaluator, and product-specific decision policy around
adopted components.
