# Ledger Lens technique taxonomy

Date: 2026-08-04

Status: systematic research dossier; no implementation is authorized by this
file. Conclusions use `established`, `provisional`, `contested`, or `unknown`.

## Decision boundary

Ledger Lens turns an invoice or bounded business document into validated,
reviewable structured fields and line items with source provenance and
correction history. The current proof covers two pinned public invoice layouts,
text-layer and image-only PDFs, invoice2data templates, PDFium, real Tesseract,
page/line provenance, and a SQLite review/export contract.

The research question is not "which OCR is best?" It is which combination of
recognition, layout, extraction, validation, and selective review fits a given
document population without replacing a cheap reliable path with an expensive
general model.

## Problem decomposition

| Layer | Independent decision | Serious method families | Current boundary |
| --- | --- | --- | --- |
| Intake | file limits, type detection, page count, malware/privacy boundary | single document; packet split/classification; asynchronous batch | bounded upload; original files are temporary |
| Path detection | decide whether usable text/layout already exists | PDF text-layer probe; image-only/scan detector; quality/layout signals | PDFium text if present, otherwise raster/OCR |
| Image normalization | improve acquisition before recognition | orientation; deskew; dewarp; denoise; contrast; crop; resolution policy | Pillow/PDFium raster path; no perturbation-calibrated preprocessing |
| Text recognition | recover characters/words and coordinates | Tesseract; PaddleOCR; lightweight specialist OCR; OCR-VLM | Tesseract with language/runtime boundary |
| Layout and reading order | recover blocks, roles, hierarchy, coordinates | heuristics; Docling; PP-Structure; learned layout detector; VLM parser | line/page transcript only; no bounding-box or hierarchy claim |
| Tables and line items | detect table, cells, rows/columns and normalize items | invoice2data line regex; Table Transformer; PP-Structure/table models; end-to-end parser/VLM | invoice2data templates and line parser |
| Key information extraction | map evidence to a client schema | regex/template; token+layout encoder (LayoutLMv3); generative OCR-free model (Donut); OCR+LLM/VLM; direct image VLM | pinned invoice2data typed templates |
| Multi-page context | connect fields/tables across pages and document packets | page-local; document hierarchy; page retrieval then extraction; long-context VLM | page/line source transcript; invoice fixtures are short |
| Normalization and validation | enforce types and cross-field consistency | typed parsers; arithmetic/date/currency/vendor rules; schema constraints | typed invoice2data fields plus bounded normalization |
| Confidence and routing | decide ready/review/escalate and cheap/expensive path | raw OCR confidence; calibrated field confidence; consistency features; parser disagreement; selective-risk policy | heuristic routing confidence; not calibrated probability |
| Human review | expose uncertainty and preserve correction | field queue; source highlight; append-only corrections; active-learning feedback | field review and ordered correction history; no bbox highlight |
| Output and provenance | export exact values with traceability | page/line; bounding box; element hierarchy; model/template/version; artifact retention | page/line/source text/method/template; no tamper-proof identity |
| Evaluation | measure recognition, extraction, structure, calibration and operations | CER/WER; field F1; localization; GriTS/TEDS; reading order; review risk/coverage; latency/RAM/VRAM/cost | exact fixed-fixture benchmark; no broad layout/language/shift evidence |

## Technique families and operating regions

### Template and deterministic validation — `established`

- invoice2data remains the fast structured profile when layouts are stable and
  representative templates/acceptance examples exist. It already removes
  custom schema/type/line parsing and passed the pinned text/scanned fixtures.
- Deterministic normalization and cross-field constraints remain mandatory
  after every neural or VLM candidate. Schema-valid output is not evidence that
  an amount, date, vendor, or line-item relationship is correct.
- The family does not generalize zero-shot to unseen layouts. Template creation
  and held-out layout coverage are client inputs, not defects to hide.

### Classical and lightweight OCR — `established`

- Tesseract is still actively maintained and provides a small CPU baseline,
  language packs, and explicit page text/confidence. It is not a layout/KIE
  model.
- PaddleOCR now exposes lightweight multilingual recognition as well as
  separate structure/KIE/VLM products. The coherent maintained repository is a
  serious challenger, but its broad Paddle/PaddleX dependency and backend
  matrix require an integration check on the actual deployment target.
- OCR quality must be evaluated on photographed/degraded and target-language
  samples. 2026 multilingual and industrial benchmarks show large transfer
  losses despite strong clean/common benchmark results.

### Layout-aware pipelines — `established family`, `provisional winner`

- Docling and PP-Structure recover reading order, tables, figures and hierarchy
  before downstream extraction. Table Transformer is a focused table detector/
  structure model and requires separate text/OCR for cell content.
- LayoutLMv3 remains an important supervised text+layout+image baseline for KIE
  and classification, but its original Microsoft repository is broad and its
  production path is now more practical through maintained Transformers model
  APIs. It requires labelled target schemas/layouts.
- Recent real-world analyses warn that benchmark annotation shortcuts and
  manually supplied semantic groups can overstate layout-model transfer.

### OCR-free and end-to-end document models — `established family`, `contested default`

- Donut established OCR-free generative document understanding, but the
  reference repository and release are stale relative to current models.
- Current maintained families include PaddleOCR-VL, olmOCR, MinerU and Surya,
  with specialized and general VLMs. They can unify recognition, reading order,
  tables and structured generation; some require 12–24 GB GPU memory or a
  heavyweight server.
- 2026 business-document evidence finds powerful image-only MLLMs can match
  OCR-enhanced pipelines in some settings, while other industrial/multilingual
  evidence finds direct end-to-end use unreliable and page localization/routed
  pipelines materially better. The family is therefore a specialized profile,
  not a replacement for the template/OCR control.

### Retrieval before extraction for long documents — `provisional`

- For long documents with sparse relevant pages, page localization followed by
  compact VLM/KIE can outperform passing the full document directly. This is a
  composition with Atlas visual/text retrieval, not another Ledger-specific RAG
  platform.
- It is outside the first invoice benchmark unless multi-page cases contain
  irrelevant pages and cross-page dependencies.

### Confidence-calibrated selective review — `established need`, `unknown winner`

- Raw OCR or verbalized VLM confidence is not a calibrated probability of
  normalized field correctness. Separate perceptual, extraction, schema, and
  consistency failures matter.
- ConfBench (posted 2026-08-03) directly targets KIE calibration under 20
  degradation pipelines and reports large model differences. Because it is a
  new preprint, its exact numerical ranking is `provisional`; its controlled
  degradation and review-budget framing reinforce an already established
  deployment need.
- Promotion is based on selective risk, coverage/review rate, calibration,
  catastrophic error rate, and field/case strata—not mean accuracy alone.

### Human correction and feedback — `established control`

- Append-only corrections remain delivery evidence and must not contaminate the
  held-out benchmark. A future learning loop needs explicit train/replay splits,
  reviewer identity/approval policy, and model/template versioning.
- Active learning or fine-tuning is not admitted until enough representative
  labelled errors exist and a simpler template/routing change cannot contain
  them.

## Benchmark map and limitations

| Workload | Public evidence | Limitation |
| --- | --- | --- |
| invoice KIE and line items | DocILE KILE/LIR, ReceiptBench, SROIE | SROIE is small/receipt-specific; model/layout leakage and schema mismatch require care |
| layout and reading order | DocLayNet, OmniDocBench, Dr. DocBench, reading-order studies | common pages can be saturated; expert/cross-page documents transfer poorly |
| tables | PubTables-1M/GriTS, FinTabNet, OmniDocBench/TEDS | scientific/financial table distributions differ; OCR text remains a separate dependency |
| OCR/VLM literacy | OCRBench v2, CC-OCR v2, olmOCR-Bench | bilingual/English or model-owner bias; OCR scores do not equal KIE/export correctness |
| multilingual parsing | MDPBench and target-language fixtures | 17-language coverage still may omit Lithuanian business documents |
| long documents | LongDocURL, multi-page DocVQA/DUDE | QA and page-retrieval tasks are not invoice field extraction |
| difficult document parsing | Dr. DocBench, industrial OCR-RAG benchmarks | intentionally hard domains exceed Ledger's invoice outcome; useful for failure categories, not aggregate promotion |
| confidence/review | ConfBench plus selective-prediction metrics | newest evidence is provisional; thresholds remain model/data/client-cost specific |
| local acceptance | pinned invoice2data fixtures plus new held-out public layouts | directly reproducible but too small to generalize |

Leakage/saturation controls: split by vendor/template/document, never by page
alone; keep synthetic derivatives of one source in one split; record model
training disclosures; use private/held-out benchmark splits where offered; do
not tune on leaderboard test labels; report per-field/layout/language/acquisition
results and catastrophic failure rates.

## Search protocol

- Search date: 2026-08-04.
- Sources: ACL Anthology, arXiv, official benchmark/model documentation,
  maintained GitHub repositories and their release/issue APIs.
- Main time window: 2024–2026; seminal LayoutLMv3, Donut, Table Transformer,
  DocILE, and Tesseract sources were retained because their families or
  maintained implementations remain decision-relevant.
- Included: surveys, controlled comparisons, real-world/shift benchmarks,
  contrary evidence, official repositories with runnable surfaces.
- Excluded: marketing roundups, popularity-only rankings, unreleased code as an
  adoption candidate, handwriting-only or scientific-LaTeX systems unless they
  expose a transferable failure category, and all license research/ranking.

### Reproducible query iterations

| Iteration | Query families | New decision-relevant families |
| ---: | --- | --- |
| 0 | `document AI survey OCR layout document understanding VLM benchmarks`; `RAG systematic survey multimodal documents` | pipeline decomposition; OCR/layout/OCR-free/VLM families |
| 1 | `OmniDocBench OCRBench v2 document parsing`; `invoice KIE DocILE SROIE`; `multilingual OCR` | benchmark/shift map and confidence/routing need |
| 2 | official GitHub searches for Tesseract, PaddleOCR, Docling, LayoutLMv3, Table Transformer, Donut, olmOCR, MinerU and Surya | no new family; separated focused, maintained and stale implementations |
| 3 | `document business extraction OCR or not`; `real-world layout model failure`; `reading order` | direct-image versus OCR+VLM conflict; reading-order layer |
| 4 | `document KIE confidence calibration selective routing`; `schema extraction VLM` | calibrated selective-review experiment |
| 5 | `long scanned financial document page retrieval VLM`; `packet splitting` | page-localization composition; packet splitting recorded as adjacent intake scope |
| 6 | 2026 surveys and `OCR layout table KIE VLM confidence human review` plus implementation-reference expansion | no new family; newer methods compose OCR, layout, routing, retrieval and VLM families |
| 7 | benchmark criticism/failure searches for multilingual, acquisition shift, annotation leakage, OCR-to-RAG transfer and VLM failures | no new family; added contrary evidence and failure strata only |

Iterations 6 and 7 add no new decision-relevant family, satisfying the dated
saturation rule.

## Survey and benchmark anchors

- [MLLM-based VRDU survey (ACL 2026)](https://aclanthology.org/2026.findings-acl.652/)
- [Scaling Beyond Context (ACL 2026)](https://aclanthology.org/2026.acl-long.204/)
- [Deep-learning VRDU survey](https://arxiv.org/abs/2408.01287)
- [OCR or Not?](https://aclanthology.org/2026.eacl-industry.28/)
- [DocILE](https://arxiv.org/abs/2302.05658)
- [OmniDocBench](https://arxiv.org/abs/2412.07626)
- [Dr. DocBench](https://arxiv.org/abs/2606.01393)
- [MDPBench](https://arxiv.org/abs/2603.28130)
- [When Good OCR Is Not Enough](https://aclanthology.org/2026.acl-industry.60/)
- [ConfBench](https://arxiv.org/abs/2608.01792)

