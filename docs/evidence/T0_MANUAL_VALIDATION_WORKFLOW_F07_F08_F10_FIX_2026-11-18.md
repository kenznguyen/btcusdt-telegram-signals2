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


## Exact-SHA CI validation update — 2026-11-18

### Run 44275608239 — initial workflow correction SHA

- Branch: `feature/core-operational-proof-20261112`.
- Exact run head SHA: `89c129fd3c68740398fd70792e46d376910859d1`.
- Event: `push`; run conclusion: **SUCCESS**.
- Jobs: lease/fencing PASS; recovery scope detector PASS; data-flow scope detector PASS; G4 scope detector PASS; recovery tests PASS; data-flow tests PASS; G4 contract tests PASS.
- P3 automatic job was **SKIPPED** because this commit did not change a P3 component path. This run does not validate execution of the new P3 automatic job.
- Artifacts (GitHub metadata; digests are provider-reported, not independently recomputed):
  - Lease/fencing ID `14415011583`, SHA-256 `83194dcc6b5e202f715188e444a16b72fa0f67c3661f803854fce849f1987f4e`.
  - Recovery ID `14415050371`, SHA-256 `7ec6048f8af8995c52e70a9c728da28d20728ca1f8cf5477c6bcd92d865627da`.
  - Data flow ID `14413992824`, SHA-256 `dbb3c19b34c8e86f05472ccbfa2425ac90a37a53c112f537b4c78ab12cc27068`.
  - G4 ID `14412984771`, SHA-256 `0da39abe58a1179938e8522ce094387c51ff67cef7d8ade411e0da4831f10c35`.

### Run 44275967382 — P3 auto-job exercise SHA

- Workflow adjustment: include the workflow file itself in the P3 change detector so a workflow edit exercises the newly added P3 automatic job.
- Branch: `feature/core-operational-proof-20261112`.
- Exact run head SHA: `0d792a1cba0ea4482d186e5c4a443b3f193cf733`.
- Event: `push`; run conclusion: **FAILURE**.
- Job conclusions:
  - Lease/fencing: PASS.
  - Recovery tests: PASS.
  - T0→T2 data-flow tests: PASS.
  - G4 read-only runtime contract tests: PASS.
  - P3 retry/health automatic tests: **FAILURE** at step `Run isolated retry and health component tests` (exit code 1).
  - Manual gate: SKIPPED, as expected for a push event.
  - Change-scope detectors: PASS.
- GitHub job page exposes only the generic exit-code annotation to the connected read-only view; detailed command output/raw logs could not be retrieved. The exact failing test and root cause are therefore **NOT VERIFIED**. Do not infer a code defect or alter application source without a separate scoped review.
- Artifacts (GitHub metadata; digests provider-reported, not independently recomputed):
  - P3 component artifact ID `14414252914`, SHA-256 `879beefcbbf49df52806a7ce9500fbcee7178e1393c71d31664dedc8ba0044ff`.
  - Lease/fencing artifact ID `14414457197`, SHA-256 `2fc04b19f71bee4dcaaee1ff070e581e533e7c0cf37e2075f4087cfef01dd78d`.
  - Recovery artifact ID `14414796722`, SHA-256 `a49370dc3e9a1cb49ee0f03095a4cb6b14ceccf526d89d481ea7ff511ad65c94`.
  - Data-flow artifact ID `14414393179`, SHA-256 `ddad904f3dbfb6ae6a1d52f78fe6424c704805fb09b7b3b455a785db87bfed05`.
  - G4 artifact ID `14415405293`, SHA-256 `a7b5d6b93d5a485cdabf6a8e601551e7405901945bdf7f1c8142cb137b764bdb`.

### Updated verdict

**PARTIAL / BLOCKED ON P3 FAILURE.** F-07 dependency correction is exercised by successful data-flow and G4 jobs on run 44275967382, alongside successful recovery and lease/fencing tests. F-08 push trigger is exercised by the successful workflow run on the active branch; PR trigger remains not exercised because no PR run was part of this validation. F-10 trigger and automatic P3 job are exercised, but the P3 test command failed and its detailed cause remains NOT VERIFIED. The workflow must not be treated as fully green until the P3 failure is diagnosed and corrected in an explicitly bounded scope, then rerun on a new exact SHA.

No live/VPS/T0 canonical database/exchange access occurred. No merge/deployment/trading authorization is implied.
