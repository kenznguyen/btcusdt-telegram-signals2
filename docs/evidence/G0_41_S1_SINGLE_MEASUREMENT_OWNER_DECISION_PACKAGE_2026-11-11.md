# G0.41 — S1 Single In-Memory Measurement Owner Decision Package

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD: `377023bbd56b651879d5a57e341a94a4b431e159`  
Baseline handoff blob: `58f676d97104852d231fc276a9997ad0fffefe45`  
G0.40-B results report blob: `cc9894cc3d48f4df5f98b62ab7608359e1b7366e`  
G0.40-B verified source commit: `0e757114e738a2330ad4cc96b6cf8d9da7d17c7b`  
Type: owner decision package; documentation only  
Current disposition: **READY FOR OWNER DECISION — no G0.41 measurement authorized or run**

## 1. Purpose

Request a separate, explicit owner decision for exactly one execution of the corrected G0.40-B in-memory S1 synthetic corpus measurement.

G0.40-B closed R1–R3 within its bounded static-source/report-integrity scope. Its final verification run [43050706119](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43050706119) checked out source `0e757114e738a2330ad4cc96b6cf8d9da7d17c7b`, passed 29/29 focused tests and `py_compile`, and verified the exact source blobs recorded below. That verification did not execute a standalone G0.41 measurement.

This package does not create a corpus, call the runner, compute measurement values, or select numeric resource limits. It asks the owner to authorize one bounded measurement workflow.

## 2. Exact decision requested

Approve or reject the following as one indivisible scope:

1. Add exactly one workflow file: `.github/workflows/g041-s1-single-measurement.yml`.
2. Add a narrowly scoped D14 amendment permitting that exact workflow path for this one G0.41 measurement only.
3. On the single push that adds the approved workflow, allow it to execute exactly one call to the existing `tools.s1_measurement_runner.prepare_preflight(...)` against the exact source checkout.
4. Persist only a bounded JSON measurement report as one GitHub Actions artifact. Do not persist raw parser-input bytes, oracle payloads, corpus files, temporary fixture files, caches or intermediate source copies.
5. Record the exact source SHA, four source Git blobs, workflow run/job, test/measurement disposition and artifact metadata in the evidence report and session handoff.

The authorization is one-shot. It does not authorize a second measurement attempt, workflow rerun, repair-and-rerun, retry, or reuse of a failed/incomplete result. A failed run after the measurement invocation begins consumes the authorization. A failure before the measurement invocation (for example, checkout or exact-source assertion failure) means no measurement was started; stop and return for a new owner decision rather than editing or rerunning under this approval.

## 3. Frozen inputs and exact source identities

Baseline repository HEAD: `377023bbd56b651879d5a57e341a94a4b431e159`.

The verified G0.40-B source checkout was `0e757114e738a2330ad4cc96b6cf8d9da7d17c7b`. Its frozen blobs are:

| Source | Exact Git blob |
|---|---|
| `tools/s1_measurement_harness.py` | `e8db71c11e0503ea6d9a2480d75470185c4d5100` |
| `tools/s1_measurement_runner.py` | `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a` |
| `tools/test_s1_measurement_runner.py` | `d06a5b533af14378ed284051e5b057cf57377876` |
| `.github/workflows/g040-b-exact-source-verification.yml` | `d42b57e78cd545099474e9256381f8c428997b1e` |

The G0.41 workflow must assert the same three Python source blobs before invocation. It must also assert that the checkout is the exact event SHA on the active branch. The G0.41 workflow's own blob and resulting checkout SHA must be recorded after the approved workflow commit exists; they cannot be pre-guessed in this package.

No modification to the frozen harness, runner or focused tests is included. If any frozen source blob differs, fail before measurement and stop.

## 4. Measurement contract

The one authorized invocation, if approved, is the existing runner's `prepare_preflight` function with:

- `harness_source_bytes`: actual bytes read from the checked-out `tools/s1_measurement_harness.py`;
- `frozen_harness_sha256`: SHA-256 recomputed over those exact bytes;
- `runner_source_bytes`: actual bytes read from the checked-out `tools/s1_measurement_runner.py`;
- `frozen_runner_sha256`: SHA-256 recomputed over those exact bytes;
- `source_commit`: the exact checked-out GitHub event SHA;
- `expected_source_commit`: the independently supplied GitHub event SHA, which must equal `source_commit`;
- `command`: the exact invocation string recorded in the resulting report.

The runner constructs the frozen 22-fixture recipe in memory, validates the 11-value D10 inventory and five approved SYN case IDs, keeps oracle metadata outside parser-input bytes, validates D05 outcomes, performs two deterministic measurement passes within this single invocation, evaluates A-01–A-13, serializes and reads back the report, and checks report measurements against the canonical ordered 22 parser-input byte sequences.

The two passes are part of one measurement attempt, not two attempts. No third pass or second invocation is permitted.

## 5. Exact execution environment and workflow constraints

The proposed workflow must be constrained as follows:

- Trigger: one `push` event on `feature/t0-centralized-data-feeder-p1-20261101` caused by adding the exact approved G0.41 workflow file. No `workflow_dispatch`, schedule, pull-request, tag or default-branch trigger.
- Permissions: `contents: read` only; no secrets, write token, deployment environment or external credentials.
- Checkout: exact `github.sha`, shallow checkout, `persist-credentials: false`.
- Runtime: Python 3.14.4, matching the verified G0.40-B run.
- Network: no application-level network calls; no external service, package installation, provider, database, VPS, exchange or market-data access. The workflow uses only the runner image's preinstalled Python and Git checkout.
- Execution: one bounded measurement invocation, no retry strategy, timeout no greater than five minutes, concurrency must not cancel or duplicate an in-progress run.
- Source checks: exact branch, `HEAD == GITHUB_SHA`, and exact three Python Git blob IDs asserted before the invocation.
- Persistence: one JSON report only. No raw corpus bytes, oracle payloads, fixture files or caches uploaded or persisted.
- Artifact: one report artifact with seven-day retention; record GitHub-reported digest and expiry. Do not claim independent payload hashing unless bytes are separately downloaded and hashed.
- No rerun button or manual rerun is authorized. If GitHub's automatic retry/re-run is not controllably disabled, stop and report the limitation before execution.

The wrapper may read the three approved source files and GitHub-provided checkout metadata. It must not read secrets, arbitrary environment variables, local user files, clock state or external resources. Any workflow or environment behavior that cannot satisfy these constraints is a stop condition.

## 6. Expected report-only output

The artifact may contain only a JSON report with:

- report schema and corpus revision;
- exact checkout SHA and exact source Git blob/SHA-256 identities;
- exact invocation command, Python version and platform;
- fixture count and approved SYN case counts;
- parser-input corpus digest (digest only, not raw inputs);
- per-fixture measurement rows and aggregate maxima for the specified dimensions;
- both pass outputs and explicit equality result;
- A-01–A-13 boolean results;
- report readback validity;
- empty persistence/external-access execution trace;
- explicit statement that all fixtures are synthetic and no D11 limits were selected.

Do not include parser-input payloads, oracle mappings, secret/environment values, raw host metadata beyond the minimum platform string, or unrelated workflow logs in the report artifact.

## 7. Measurement dimensions and policy boundary

Report the existing harness dimensions only:

- raw parser-input bytes;
- maximum JSON nesting depth;
- maximum object members;
- maximum array items;
- maximum UTF-8 string value bytes;
- maximum UTF-8 string key bytes;
- scalar node count;
- fixture count, total raw bytes and corpus digest.

The current harness does not separately implement the G0.32 diagnostic-output maximum as an independently measured dimension. It reports fixed parser/contract reason codes per fixture. This G0.41 scope must not invent or infer a diagnostic-count ceiling. If diagnostic-output measurement is required as a separate numeric dimension, stop and prepare a later decision package; do not change the harness under this approval.

**D11 remains measurement-first.** Observed maxima may be recorded, but this package does not request or authorize any safety margin, candidate numeric ceiling, enforcement threshold, default, parser limit or owner ratification. Numeric D11 decisions require a separate owner package after valid measurement evidence exists.

## 8. Acceptance and stop conditions

The one attempt is complete only if all conditions hold:

1. Exact event checkout and frozen source blob assertions pass.
2. Actual source bytes and SHA-256 values are bound into preflight provenance.
3. Frozen 22-fixture inventory, exact five case IDs and all 11 D10 types validate.
4. D05 positive/negative outcomes and independent oracle separation validate.
5. Two independent constructions and two measurement passes are equal.
6. A-01–A-13 are all present and true; no hardcoded success, missing evidence or swallowed exception.
7. Report readback validates exact canonical fixture order, per-fixture rows, aggregates and digest against parser-input bytes.
8. Execution trace shows no persistence events and no external-access events.
9. Exactly one report artifact is uploaded; no raw corpus/oracle bytes are included.
10. Workflow/job conclusions and artifact metadata are recorded against the exact checkout SHA.

Any failed assertion, mismatch, exception, source drift, non-determinism, incomplete report, non-empty trace, unauthorized access, artifact upload failure or unexpected workflow action results in **G0.41 FAILED/INCOMPLETE**. If invocation has begun, the one-shot authorization is consumed. No repair-and-rerun.

## 9. Explicit exclusions

Not authorized by this package:

- A second invocation, retry, rerun or replacement corpus attempt.
- Raw corpus/oracle payload persistence, fixture files, cache, external storage or additional artifacts.
- Numeric D11 ceiling proposal, ratification or enforcement.
- Changes to `tools/s1_measurement_harness.py`, `tools/s1_measurement_runner.py`, tests or dependencies.
- Parser/verifier production implementation, cryptography, DSSE/Ed25519, trust roots, keys, revocation, registry, adapter or executor.
- Any other CI workflow, broad CI changes, secrets, write permissions or deployment.
- Any filesystem inventory or operation beyond checkout/source reads and report-only artifact creation.
- T0/T1/T2, canonical data, market data, model/training, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, exchange, provider, network or database operations.
- Any retention, cleanup, archive, deletion, compaction, VACUUM or destructive operation.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 10. Owner decision register

| Decision | Requested disposition |
|---|---|
| One G0.41 in-memory 22-fixture measurement invocation | PENDING EXPLICIT OWNER APPROVAL |
| Add `.github/workflows/g041-s1-single-measurement.yml` | PENDING exact-path approval |
| Narrow D14 amendment for that exact workflow path and one run | PENDING explicit approval |
| Existing harness/runner/tests modification | NOT REQUESTED / NOT AUTHORIZED |
| Report-only artifact creation | Included only if the one-shot scope is approved |
| Retry, rerun or second attempt | NOT AUTHORIZED |
| D11 numeric ceilings | OPEN / NOT RATIFIED |
| Production parser/verifier, cryptography or trust implementation | NOT AUTHORIZED |
| T0/T1/T2, ledgers, runtime, VPS, provider/database/network or destructive actions | NOT AUTHORIZED |

## 11. Current disposition and next action

**G0.41 OWNER DECISION PACKAGE READY — MEASUREMENT NOT AUTHORIZED / NOT RUN.**

This report is documentation-only. No corpus generation, measurement function, benchmark, test, workflow dispatch or runtime operation was performed while preparing it.

Next action requires an explicit owner decision on the exact one-shot scope in Sections 2 and 5–10. A generic “continue” does not authorize the measurement. If approved, implement only the exact workflow and D14 amendment, freeze the final workflow/source commit, and allow exactly one push-triggered measurement run. After that run, record evidence and stop before any D11 numeric ceiling proposal.
