# LedgerLens depth execution checkpoint

## Shared OpenAPI consumer slice — 2026-08-06

- branch: `agent/toolbox-api-verification`
- isolated worktree: `portfolio_demos/worktrees/ledger_lens_api_toolbox`
- clean base: `638bb35e6fd5eeea1ee5fd187b9e9c10d91671df`
- reusable provider: AdapterProof
  `fa0296f4294b5149605c5fbf4e809adddba76e74`;
- security-specific work: postponed to the final toolbox backlog;
- license research: excluded by user direction.

Current gate: **LOCAL_CONSUMER_PASS_HOSTED_EXECUTION_PENDING**.

| Gate | Evidence | Status |
| --- | --- | --- |
| shared consumer contract | `adapterproof.openapi.json`; one selected health operation | PASS |
| real isolated execution | 8/8 generated cases; `NO_FINDINGS`; report SHA-256 `f8ea7e99...9bb05875` | PASS |
| committed receipt summary | `docs/evidence/adapterproof-openapi.json` | PASS |
| clean-environment project gate | Ruff; 5 passed, 1 skipped; 74% coverage; JSON/YAML parse | PASS |
| reusable hosted workflow | exact provider commit configured, but neither side has executed this slice on GitHub | PENDING |

Exact next action: publish AdapterProof snapshot candidate
`fa0296f4294b5149605c5fbf4e809adddba76e74` before publishing this consumer
workflow, then preserve the hosted run URL. Local reuse is proven; hosted reuse
must not be claimed yet.

Date: 2026-08-03

## Restart point

- repository: `portfolio_demos/document_extraction`
- baseline: clean `main` / `origin/main` at
  `f201c9066a771aa1577bdb4b38aae2e93b7136de`
- isolated worktree: `portfolio_demos/worktrees/ledger_lens_depth`
- branch: `agent/ledger-lens-depth`
- GitHub/component audit commit:
  `0fd3b54502236bcc09c649d04d73b465d6b388db`
- application commit: `81b75f0781b76be34329463bc173c694d6f40f2d`
- evidence commit: `60f181438a3cd254f90a4dec9d266ad28633bee1`
- closure commit: `8357938985e3cdc3286fdc3b6a4586eb5c994a1b`
- merge commit on local `main`: `a2220df7f07652877c7f4025631f05a657236371`
- scope stopped before: UI changes, visual polish, auth, deployment,
  client-specific templates, broad document models, or the next project

## Delivered boundary

- adopted invoice2data 1.0.1 for configurable templates, typed fields, and
  line-item parsing;
- adopted the coherent pypdfium2 5.12.1 dependency for text extraction and
  image-only PDF page rendering;
- retained/refitted the existing pytesseract boundary for image and rendered
  PDF OCR;
- added source page/line/method/template provenance for matched scalar fields
  and named line items;
- added field-level append-only SQLite correction history and API retrieval;
- added fixed upstream fixture hashes and a Docker benchmark CLI/report;
- preserved the existing review UI unchanged.

## Exit gate

| Gate | Evidence | Status |
| --- | --- | --- |
| foundation and component reuse audit precedes code | `0fd3b54` precedes `81b75f0`; pinned adopt/refit/custom table | PASS |
| fixed public inputs | three invoice2data fixtures and SHA-256 checks | PASS |
| text PDF fields and line items | Coolblue invoice/date/amount plus five named lines | PASS |
| real scanned-PDF path | Docker PDFium render + Tesseract 5.5.0 returns AWS invoice `42183017` and amount `4.11` | PASS |
| configurable schema | invoice2data built-in template plus two packaged YAML templates | PASS |
| source provenance | page, line, source text, method, and template assertions/report | PASS |
| correction history | two ordered prior/new records; export returns latest | PASS |
| explicit invalid behavior | unknown schema and invalid type tests return explicit failure | PASS |
| existing review/export regression | original API flow remains green | PASS |
| local static/test gate | Ruff format/check; 5 passed, 1 skipped only because Windows lacks Tesseract; 74% coverage | PASS |
| real OCR replacement for local skip | Docker benchmark exercises the same scanned path without mocking | PASS |
| package gate | fresh wheel/sdist build and Twine checks | PASS |
| live container API | health plus Coolblue PDF upload: PDFium, `nl.be.coolblue.yml`, five lines | PASS |
| detached clean-checkout gate | fresh install, Ruff, 5 passed/1 expected skip, build/Twine, Docker build, all-PASS benchmark at `60f1814` | PASS |
| claim safety | `CLAIM_LEDGER.md` and benchmark report boundaries | PASS |
| UI/polish stop | no HTML, JavaScript, CSS, screenshot, or visual change | PASS |

## Verification commands

```powershell
.\.venv\Scripts\ruff.exe format --check ledger_lens tests
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\pytest.exe --cov=ledger_lens --cov-report=term-missing
.\.venv\Scripts\python.exe -m build
.\.venv\Scripts\twine.exe check dist\*
docker build -t ledger-lens-depth:local .
docker run --rm --volume "<fixtures>:/fixtures:ro" `
  ledger-lens-depth:local ledger-lens-benchmark /fixtures
```

The detached checkout repeated the install/static/test/package/container ladder
at evidence commit `60f1814`. Its benchmark returned `PASS` for all five gates.

## Remaining limitations

- two public invoice layouts are evidence, not arbitrary document coverage;
- new vendors/layouts require representative client fixtures and configured
  templates;
- OCR confidence is a review-routing score, not a calibrated probability;
- provenance is page/line text, not bounding boxes;
- the correction log has no authenticated reviewer identity or tamper-proof
  guarantee;
- local Tesseract is absent on Windows, so the real scan is proven in the
  container and CI-style Linux environment;
- no auth, malware scanning, encryption/retention policy, remote deployment,
  monitoring, production accuracy, throughput, or client outcome is claimed.

## Handoff

This slice is merged with `--no-ff` into local LedgerLens `main` at `a2220df`.
This file's next commit is the final main checkpoint. The branch and main
worktrees were clean immediately before the checkpoint edit. Nothing was
pushed.

Do not start UI polish. The next portfolio decision is depth rank 6,
SignalRoom real-data feasibility, and it remains gated on a real, reusable
dataset/target plus foundation and component-level GitHub audits; do not start
blank or invent a target.
