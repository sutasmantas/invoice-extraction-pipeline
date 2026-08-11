# Ledger Lens research decision

Date: 2026-08-04

## Decision

The systematic dossier is `PASS`; Ledger Lens's technique-ceiling experiment
gate remains `PARTIAL`. No candidate was implemented.

Retain the measured invoice2data/PDFium/Tesseract route for stable layouts and
as the mandatory control. Admit one first experiment: path-specific calibrated
selective review under layout and acquisition perturbations. A layout-aware
parser comparison, VLM escalation and long-document page retrieval remain
conditional follow-ups, not parallel work.

## Retained families

| Family | Status | Role |
| --- | --- | --- |
| invoice2data/PDFium/Tesseract | `established for frozen fixtures` | cheap stable-layout control and current default |
| Tesseract | `established` | CPU scan control behind text-layer detection |
| Docling | `established family`, `provisional fit` | first structured parser candidate if L1 activates |
| PaddleOCR/PP-Structure/PaddleOCR-VL | `provisional` | maintained OCR/layout/VLM challenger if host/profile gate passes |
| LayoutLMv3 | `established family`, `provisional fit` | supervised KIE only with sufficient labelled target layouts |
| Table Transformer | `established niche` | line-item/table challenger only after a structural failure |
| direct-image/VLM extraction | `contested default` | routed escalation only for residual layout failures |
| page retrieval before extraction | `provisional` | long-document composition only after its activation condition |
| calibrated selective review | `established need`, `unknown winner` | first experiment because current score is heuristic |
| human correction/provenance | `established control` | invariant for every route |

## Rejected or bounded choices

- Reject a universal VLM, Docling, PaddleOCR or other broad parser as the
  default. Different acquisition/layout regions require measured routing.
- Reject writing new OCR, layout, table, or document-model logic. GitHub has
  focused components; local work is limited to adapters, evaluation and policy.
- Reject Donut as a new implementation target: it remains important historical
  evidence but its reference repository and releases are comparatively quiet.
- Reject olmOCR for the default local profile because its documented local
  route needs GPU capacity absent from this host.
- Reject LayoutLMv3 fine-tuning until labelled target layouts demonstrate that
  supervised KIE is cheaper than parser/VLM routing.
- Reject one shared confidence threshold across text, OCR, parser and VLM paths.
- Exclude packet splitting, handwriting, tamper detection, production scale,
  active learning, client retention/security policy and visual polish from the
  present bought outcome.

## Exact first experiment

Run L0 from `BENCHMARK_DESIGN.md`. Freeze held-out layout families and paired
acquisition degradations, then compare the current threshold against
path-specific deterministic evidence features. Add a small calibrated model
only if the deterministic policy cannot meet the pre-registered risk/coverage
gate. Do not integrate Docling, PaddleOCR or a VLM in the same slice.

## External answers and unresolved questions

| Question | Evidence disposition | Result |
| --- | --- | --- |
| Is template extraction still defensible? | local measured evidence | closed `yes` for stable known layouts, not arbitrary documents |
| Should OCR run on every PDF? | local path benchmark plus pipeline evidence | closed `no`; retain text-layer detection |
| Does direct-image VLM extraction universally dominate OCR pipelines? | conflicting industrial evidence | closed `no` as a universal claim |
| Are layout/table methods distinct from OCR? | benchmark and architecture evidence | closed `yes`; activate only on matching failures |
| Can OCR confidence be treated as field correctness? | calibration evidence and local implementation audit | closed `no` |
| Which review policy fits Ledger's paths and costs? | thresholds are data/client specific | unresolved; L0 |
| Which maintained parser fits varied business documents on this CPU host? | benchmark transfer and runtime unresolved | unresolved; conditional L1 |
| Is a VLM escalation worth its cost? | model/task/host dependent | unresolved; conditional L2 |
| Does page retrieval help Ledger? | only long-document operating region | unresolved; conditional L3 |

## Systematic evidence gate

| Gate | Evidence | Status |
| --- | --- | --- |
| Problem decomposition | thirteen independent layers in `TECHNIQUE_TAXONOMY.md` | PASS |
| Search protocol | date, sites, window, rules and eight query iterations recorded | PASS |
| Survey coverage | 2024–2026 VRDU, multimodal-RAG, OCR/layout and document-intelligence surveys | PASS |
| Benchmark coverage | KIE, line items, layout, tables, OCR, multilingual, long-document, difficult-document, confidence and local acceptance map | PASS |
| Existing-answer search | each major question has an external/local closure or unresolved benchmark disposition | PASS |
| Technique-family saturation | iterations 6 and 7 added no new decision-relevant family | PASS |
| Candidate comparison | `EVIDENCE_MATRIX.csv` covers quality, cost, implementation health, strengths and failure regions | PASS |
| Contrary evidence | direct-image versus OCR-assisted conflict, difficult-domain transfer, parser/OCR separation and confidence limits recorded | PASS |
| Implementation evidence | `GITHUB_IMPLEMENTATION_AUDIT.md` pins maintained repos, runnable seams, defects and host constraints | PASS |
| Portfolio fit | stable-layout extraction, routed layout parsing, calibrated review and long-document localization have explicit operating regions | PASS |
| Review status | every conclusion is labelled; only accepted/conditional questions enter `BENCHMARK_DESIGN.md` | PASS |

## Expertise extraction

- Canonical notes: `docs/EXPERTISE_NOTES.md`.
- Central card added: **Calibrate review routing per extraction path**.
- Existing cards retained: **Detect document path before selecting extractor**,
  **Reuse focused parser before assembling document AI stack**, and **Route
  uncertain fields to review**.
- Notes that restate those rules are marked as duplicates rather than added to
  the central index.

## Boundary and next authorization

This dossier may authorize a later isolated L0 experiment only after the
portfolio checkpoint accepts the joint Atlas + Ledger research group and
ProofGrid's shared measurement work is reconciled. It does not authorize L0
automatically, parser/VLM integration, visual polish, a central portfolio site,
or another project.
