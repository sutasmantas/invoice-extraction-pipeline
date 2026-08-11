# Ledger Lens technique-ceiling benchmark design

Date: 2026-08-04

Status: design only. No candidate implementation or benchmark run is
authorized by this document.

## Objective

Resolve only the questions external evidence cannot answer for Ledger Lens:

1. can the existing path-specific review score be replaced by a calibrated
   selective-review policy that survives acquisition and layout shift;
2. which one maintained layout-aware parser adds useful evidence on varied
   business documents without breaking the CPU delivery envelope; and
3. when, if ever, a VLM escalation is worth its compute/cost over the cheap
   path and parser challenger.

The existing invoice2data/PDFium/Tesseract route remains the control. Public
leaderboards establish technique families, not a Ledger winner.

## Frozen case protocol before code

Create a versioned manifest containing source URL, upstream revision, file
hash, permitted use, target schema, field/line-item truth, page or region truth
where available, acquisition class and layout-family label. Freeze three
groups before implementing a challenger:

- **control:** the current Coolblue text PDF and AWS image-only PDF;
- **held-out invoices:** at least 24 documents from at least six unseen public
  layouts, with text-layer and scanned examples and at least eight documents
  containing line items;
- **degradation pairs:** at least 40 deterministic variants across rotation,
  blur, downscale, JPEG compression, low contrast, background noise and crop,
  always paired with the clean source.

Deduplicate by document/template family, not filename. No document, vendor
layout, or synthetic sibling may cross a calibration/test boundary.

## Common outputs and metrics

Every path must return the same typed artifact or an explicit unsupported/error
result:

- normalized scalar fields and line items;
- per-field correctness and missing/spurious status;
- page plus source line or bounding box for every returned field;
- parser/model/template/version and extraction path;
- field-level review decision and its score/features;
- wall time, peak RAM, VRAM if used, model/download size and external cost.

Report exact match and normalized field F1, line-item F1, provenance coverage
and localization, unsupported/error rate, document-ready precision/recall,
review coverage, selective risk, expected review workload, p50/p95 time and
resource peaks. Slice every quality metric by layout, text/scan path,
degradation, language if present and seen/unseen template family. Never report
one aggregate accuracy without those slices.

## Invariants for every experiment

- The current control fixtures and correction-history tests remain passing.
- No unvalidated output is exported as `ready`.
- Missing/unsupported values are not guessed.
- Source evidence and method/version remain attached after correction/export.
- Review thresholds are fitted on calibration data only.
- A quality gain cannot be promoted when its 95% bootstrap interval includes a
  material regression on a required slice.
- Hosted inputs, retention and cost must be explicitly authorized before any
  service-backed VLM run.

## L0 — calibrated selective review

### Candidates

1. current fixed threshold and mean OCR routing score;
2. deterministic path-specific features: text-layer presence, OCR token
   confidence distribution, required-field completeness, template match,
   arithmetic/date/currency checks and source-localization completeness;
3. candidate 2 plus disagreement between the control and one already-admitted
   challenger, only if L1 exists;
4. a small calibrated model over the same frozen features only if monotonic or
   rule-based scores miss the gate.

### Primary decision metrics

- field error among automatically accepted fields;
- document error among records marked ready;
- review coverage and false-review rate;
- area under the risk-coverage curve, calibration error and Brier score,
  reported separately per extraction path.

### Promotion gate

Promote the simplest policy that simultaneously:

- produces zero known incorrect `ready` documents in the frozen test set;
- reduces unnecessary review by at least 20% relative to the current threshold
  without increasing field error in any required acquisition slice;
- preserves 100% review routing for missing required fields, validation
  failures, unsupported templates and absent provenance; and
- shows no more than a five-point calibration-error deterioration on any
  predeclared degradation slice.

If no policy meets every gate, retain the current conservative review route and
record which failure feature is missing. Do not tune on the test set.

## L1 — cheap path versus layout-aware parser

### Candidates

- invoice2data/PDFium/Tesseract control;
- one pinned Docling profile;
- one pinned PaddleOCR/PP-Structure or PaddleOCR-VL profile only if its local
  CPU or explicitly authorized accelerator envelope is reproducible.

Docling and Paddle are not both integrated by default. A one-page smoke probe
selects the first candidate whose output seam and host budget pass; the second
is used only if the first cannot represent an activated failure category.

### Acceptance gate

Promote a routed parser only if it:

- improves macro field/line-item F1 by at least 5 absolute points on unseen
  layouts or recovers a predeclared table/reading-order failure category;
- preserves control-fixture values, explicit failure behavior and provenance;
- stays below 4 GB peak RAM and 15 seconds p95 per page on the local CPU path,
  unless a separate accelerator profile was authorized; and
- adds no new required manual step between upload and review.

Otherwise keep the template route and record that broader parsing did not buy
enough correctness in this operating region.

## L2 — VLM escalation

Run only if L1 leaves at least ten labelled failures caused by layout variance,
not merely OCR character errors or missing business rules.

Compare the L1 winner with one pinned VLM parser/extractor on only those failure
cases plus matched controls. Require schema-constrained output, evidence
localization, explicit missing values and repeated-run stability. Promote only
as a routed escalation if it recovers at least half the residual correctable
fields, introduces no unsupported ready output, and documents per-document
latency and cost. A universal VLM default is outside the decision space.

## L3 — long-document page localization

Run only when a real bought outcome includes documents over 20 pages or a
measured full-document context/cost failure. Compare full-document extraction
with Atlas-reused page retrieval followed by the L1/L2 extractor. Measure page
recall before extraction accuracy; if required pages are missed, the method
fails regardless of downstream field score.

## Resource envelope

- Default local profile: CPU, 32 GB host RAM, no NVIDIA GPU.
- Required CPU comparison limit: 4 GB incremental peak RAM and 15 seconds p95
  per page for an interactive route.
- Offline/batch candidates may exceed that only under a separately labelled
  profile with measured delivery value.
- GPU or hosted VLM candidates are conditional profiles, never hidden in the
  CPU result. Capture accelerator, VRAM, quantization, model revision, tokens
  and monetary cost.

## Stop rules

- Stop integrating a candidate if its normalized output seam cannot pass the
  two control documents before app/store changes.
- Stop L0 at the simplest policy meeting every gate; added model complexity
  without lower selective risk is rejected.
- Stop L1 after one candidate meets the gate; do not build a parser zoo.
- Stop L2/L3 when their activating failure set does not exist.
- Any test leakage, missing provenance, guessed unsupported value, unpinned
  model, or unrecorded external cost makes the result `FAIL`.

## Exact next authorized experiment

After portfolio checkpoint approval, run **L0 only**. Freeze the manifest and
perturbation generator, then compare the existing threshold against
path-specific deterministic evidence features. L1–L3 remain blocked until L0
is closed and their activation conditions are met.
