# G0.40-B — Exact-Source Assurance Corrections Results

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Owner approval: explicit approval of the G0.40-B four-path package in this conversation  
Package commit: `8f273495b334c8dca35a2dfaa1d59bea12b27867`  
Verification source commit: `0e757114e738a2330ad4cc96b6cf8d9da7d17c7b`

## 1. Scope completed

Implemented the approved G0.40-B corrections in exactly these four paths:

1. `tools/s1_measurement_harness.py`
2. `tools/s1_measurement_runner.py`
3. `tools/test_s1_measurement_runner.py`
4. `.github/workflows/g040-b-exact-source-verification.yml`

No other source, configuration, workflow, dependency, runtime or production path was changed in this implementation increment.

## 2. Findings and acceptance

### R1 — Actual source provenance: CLOSED for the bounded CI contract

- Focused regression tests read the actual checked-out harness and runner bytes from their source files and compute SHA-256 over those exact bytes; placeholder snippets are no longer used as the sole provenance proof.
- The test passes the actual source bytes and their computed digests into preflight validation.
- The workflow checks out `github.sha`, asserts `git rev-parse HEAD == GITHUB_SHA`, checks the approved branch and asserts the exact harness, runner and test Git blob IDs before running tests.
- The workflow-provided checkout SHA is passed as the source commit; preflight rejects a source commit that differs from its independently supplied expected checkout commit.
- Negative tests cover altered source digests and mismatched source/checkout commit identity.

### R2 — Capability boundary: CLOSED with an explicitly bounded assurance claim

- Replaced the incomplete denylist with a conservative AST import/syntax allowlist for the exact harness and runner modules.
- Unknown imports, relative imports, unsupported import-from names and selected dynamic execution/reflection constructs fail closed.
- Negative probes cover aliased `io.open`, `zipfile` extraction, `tarfile` extraction and `smtplib`, in addition to existing direct `open` and `socket` probes.
- Both actual frozen source modules pass the policy in the exact-source regression test.

**Limitation:** this is static source-policy validation, not an operating-system sandbox or proof of runtime isolation. It does not establish that arbitrary execution environments cannot persist data or access external services. The assertion is deliberately limited to the checked source syntax/import boundary.

### R3 — Report-to-corpus integrity: CLOSED for the frozen S1 inventory

- Readback requires the canonical ordered inventory `syn-fixture-001` through `syn-fixture-022`, exactly 22 IDs, with no duplicates or substitutions.
- Parser-input keys must equal that exact inventory and every parser input must be bytes.
- Readback recomputes the complete measurement from the supplied parser-input bytes and ordered IDs, then compares the entire report measurement, including row order, every row field, aggregates and length-prefixed corpus SHA-256.
- Tests reject duplicate IDs, reordered rows, missing/extra rows, modified raw-byte counts even when the aggregate is adjusted, altered corpus digests and noncanonical expected inventories.

## 3. Exact source and verification evidence

Frozen source checkout: `0e757114e738a2330ad4cc96b6cf8d9da7d17c7b`

| Path | Git blob |
|---|---|
| `tools/s1_measurement_harness.py` | `e8db71c11e0503ea6d9a2480d75470185c4d5100` |
| `tools/s1_measurement_runner.py` | `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a` |
| `tools/test_s1_measurement_runner.py` | `d06a5b533af14378ed284051e5b057cf57377876` |
| `.github/workflows/g040-b-exact-source-verification.yml` | `d42b57e78cd545099474e9256381f8c428997b1e` |

- Workflow run: [43050706119](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43050706119)
- Event: `push`; run number: 11; exact checkout SHA: `0e757114e738a2330ad4cc96b6cf8d9da7d17c7b`
- Job: `130626755285`; conclusion: **SUCCESS**
- Python: 3.14.4
- Focused unit tests: **29/29 PASS**
- Focused `py_compile` for harness, runner and tests: **PASS**
- Exact checkout, branch and three source-blob assertions: **PASS**
- Artifact: `g040-b-exact-source-verification`, ID `13869536480`, size 1,469 bytes
- GitHub-reported ZIP SHA-256: `9ba9734367b41a3e677fb547cf23d91c5d8cef53a4c1f4db1a7dc71e40c74c23`
- Artifact expiry: `2026-11-18T15:40:29Z`

Artifact metadata is recorded as reported by GitHub. The artifact payload was not independently downloaded and re-hashed; independent payload hash verification is **NOT VERIFIED**.

## 4. Failed intermediate verification attempts retained

- Run `43050375099`: test module syntax failure caused by duplicate `expected_source_commit` keyword arguments. Corrected in the test source.
- Run `43050453674`: exact-source identity step rejected a stale pinned test blob. Workflow pin corrected.
- Run `43050625804`: exact-source identity step rejected a stale pinned harness blob after the canonical inventory hardening. Workflow pin corrected.
- Run `43050692431`: exact-source identity step rejected a stale pinned test blob after adding the noncanonical-inventory negative test. Workflow pin corrected.
- Final run `43050706119` checked out the final exact source and passed all assertions, 29 tests and compile checks. Failed runs remain in Actions history and are not hidden.

TDD tests were committed before implementation, but a separate pre-implementation RED run was not captured. TDD RED evidence remains **NOT VERIFIED**.

## 5. Scope review and limits

Compare from pre-implementation handoff HEAD `a81a92bda4eca626ca002b8399ef008d3526c46e` to verification source `0e757114e738a2330ad4cc96b6cf8d9da7d17c7b`: ahead 15 / behind 0; exactly the four approved paths changed.

- G0.40-B implementation, focused regression verification and exact-source CI: **PASS**.
- R1–R3: **CLOSED** for the bounded static-source and frozen S1-report contract described above.
- Artifact payload independent hash: **NOT VERIFIED**.
- Independent reviewer sign-off: **NOT PERFORMED**; the exact diff was checked against the four-path approval boundary.
- G0.41 corpus generation/measurement: **NOT AUTHORIZED / NOT RUN**. No standalone measurement attempt was performed.
- D11 numeric ceilings: **OPEN / NOT RATIFIED**; no numeric ceiling proposal was produced.
- Parser/verifier production implementation, cryptographic profile, trust-root/key changes, broad CI and runtime isolation: **NOT AUTHORIZED / NOT ESTABLISHED**.
- T0, T1, T2, market data, model/training, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch, VPS/runtime, external provider/database/network operations and lifecycle/destructive operations: **UNCHANGED / NOT AUTHORIZED**.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 6. Next gate

Prepare a separate G0.41 owner decision package using the corrected exact-source harness. Do not generate or measure the corpus, propose/ratify D11 numeric ceilings, or invoke `prepare_preflight` as a standalone measurement until the separate G0.41 scope is explicitly approved.
