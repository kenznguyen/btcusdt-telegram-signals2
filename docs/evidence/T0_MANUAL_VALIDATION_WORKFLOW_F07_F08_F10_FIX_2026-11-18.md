# T0 Manual Validation Workflow — F-07 / F-08 / F-10 Fix

Date: 2026-11-18 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/core-operational-proof-20261112`

## Authorization and scope

The owner approved the minimal workflow correction for F-07, F-08 and F-10, followed by exact-SHA CI validation. Work was limited to `.github/workflows/t0-manual-validation.yml`. No application source, T0 canonical data, VPS/runtime, deployment, exchange credentials, or trading execution was accessed or changed.

## Changes

### F-07 — independent scoped jobs

- Removed `sqlite-recovery-auto` as a prerequisite of `sqlite-data-flow-auto`.
- Removed both `sqlite-recovery-auto` and `sqlite-data-flow-auto` as prerequisites of `sqlite-g4-runtime-contract-auto`.
- Kept the common SQLite lease/fencing job as a required prerequisite for data-flow and G4 jobs; its failure still blocks those jobs.
- Each scoped gate continues to require its own change-detection job to complete successfully and report `changed=true`.
- This prevents an unrelated scope job being skipped from suppressing an independent test gate; actual required-gate failures remain fail-closed.

### F-08 — reachable PR and current-branch triggers

- Added `pull_request` trigger targeting `main` with the existing T0-relevant path filter.
- Added the active Core First branch `feature/core-operational-proof-20261112` to the push trigger while retaining the legacy T0 branch.
- The existing `workflow_dispatch` manual gate is preserved.
- PR runs use GitHub's event SHA/checkout semantics; the checked-out SHA must be recorded from CI logs and distinguished from PR head SHA when reporting evidence.

### F-10 — automatic P3 retry/health gate

- Added the P3 component paths (`app.py`, `market_data/feeder.py`, and retry/health test modules) to push and PR path filters.
- Added a dedicated change-scope detector and isolated automatic job running:
  - `market_data.test_feeder_retry`
  - `market_data.test_feeder_health`
  - `market_data.test_feeder_health_api`
  - `py_compile` for `market_data/feeder.py`, `market_data/store.py`, and `app.py`
- Kept the existing manual P3 gate and its selection unchanged.
- P3 automatic evidence is fixture-only; no canonical database or external exchange is configured.

## Source identity

- First workflow change commit: `a125bfec531d840a76eea20eb436d437ecb35737`.
- Follow-up artifact-list cleanup commit: `89c129fd3c68740398fd70792e46d376910859d1`.
- Final workflow blob SHA after cleanup: `9b0ba4424e3674486f082bc7d884492f2d7cb8ac`.
- Final workflow path: `.github/workflows/t0-manual-validation.yml`.

## Verification

Static content assertions performed against the fetched final workflow:

| Check | Result |
|---|---|
| PR trigger targets `main` | PASS |
| Push trigger includes active Core First branch | PASS |
| Data-flow gate no longer depends on recovery auto job | PASS |
| G4 gate no longer depends on recovery/data-flow auto jobs | PASS |
| P3 automatic component job and three test modules present | PASS |
| Existing manual dispatch gate retained | PASS |
| P3 artifact upload references only files created in that job | PASS |

No local YAML parser, GitHub Actions workflow run, job log, or artifact result was available/verified during this update. GitHub combined commit-status queries returned no status entries for the two workflow commits. Therefore YAML parser validation and exact-SHA CI execution are **NOT VERIFIED**, not PASS. Workflow run ID, checked-out SHA, artifact ID, and artifact digest: **NOT AVAILABLE / NOT VERIFIED**.

## Safety and limits

- `AI_EXECUTION_ENABLED=false` remains unchanged.
- No live or paper orders were sent.
- No T0 canonical database, VPS, persistent runtime, exchange endpoint, or credentials were accessed.
- No merge, rebase, reset, cherry-pick, force-push, or new branch/PR was performed.
- Main integration remains BLOCKED / NOT AUTHORIZED.
- This workflow correction does not close Core First, certify T0 production readiness, or authorize Dual-Strategy Intelligence implementation.

## Verdict

**PARTIAL — workflow edits committed; static content assertions PASS; YAML syntax and exact-SHA CI NOT VERIFIED.**

Next: verify the GitHub Actions run for final workflow/source commit `89c129fd3c68740398fd70792e46d376910859d1`, confirm the workflow's checked-out SHA from logs, inspect all job conclusions and the P3/data-flow/G4 artifacts, and record artifact IDs plus independently computed digests. Do not claim CI PASS until those exact-SHA facts are established.
