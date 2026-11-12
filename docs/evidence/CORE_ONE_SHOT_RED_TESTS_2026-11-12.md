# Core One-shot Runner — RED Contract Test Evidence

Date: 2026-11-12  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Baseline source SHA: `2de2c09af99d782c0f0fa4884c21d2ee3abb3dee`  
Latest CI source SHA: `837f0bb718ec2f7c91543cf9ca3f0fdd17d76fe1`  
Uploaded source archive SHA-256: `147433ac9a031e3cdc3cda6eb76119310b3adbcc80782877c6f4f4bedd1d9991`

## Scope recorded

- Add black-box CLI contract tests for `python -m core_runtime --config <paper-config>`.
- Require help output, explicit config, `mode=PAPER`, `ai_execution_enabled=false`, and an existing disposable ledger file before SQLite is opened.
- Require invalid mode, AI-enabled config, missing config, and missing ledger to fail closed with stable diagnostic identifiers.
- Add producer-to-validator adapter contract tests: map only `BUY→LONG`, `SELL→SHORT`, `CLOSE→FLAT`, `WAIT→WAIT`; copy existing provenance only; reject action mismatch and missing provenance.
- Extend the existing Core operational proof workflow to compile and verify the expected RED states, retaining logs in the existing artifact.

## Local verification

- `python -m unittest pipeline.test_core_strategy pipeline.test_core_signal -v`: **PASS**, 12 tests.
- `python -m unittest pipeline.test_core_runtime_contract -v`: **EXPECTED RED**, 5 failures because `core_runtime` was not implemented at the tested baseline.
- `pipeline.test_core_runtime_adapter_contract`: **PASS**, 6/6 in GitHub Actions run #83 after implementing the pure producer adapter.
- `python -m py_compile pipeline/test_core_runtime_contract.py`: **PASS**.
- Workflow YAML parse with PyYAML: **PASS**.
- Workflow static assertions for test inclusion and expected RED evidence: **PASS**.
- `git diff --check`: **NOT VERIFIED**; uploaded ZIP has no `.git` metadata, so a local Git worktree/diff is unavailable.

## GitHub Actions evidence

- Run #81: **PASS** — [run 43261623605](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43261623605), head SHA `60752460b5fbc50ae97fe3708698e20e72bd5144`.
  - All 13 main workflow steps completed successfully.
  - Artifact: `core-first-code-operational-proof-43261623605`, ID `13964625769`, SHA-256 `a08eb71dfb16c9ef68bc8e7c10a96b154ec8fa63c0679eda8c6795ebeee7758c`, expires `2026-11-19T16:42:41Z`.
- Run #82: **PASS** — [run 43262274064](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43262274064), head SHA `299a9db209ce2380d743e11457f177ed0de74114`.
  - All 14 main workflow steps completed successfully, including both expected-RED contract checks, Core-First end-to-end paper operational proof, and shared risk/PaperLedger regressions.
  - Adapter check confirmed the six RED errors were the expected missing-module condition; it did not establish adapter implementation.
  - Artifact: `core-first-code-operational-proof-43262274064`, ID `13965040659`, size 6,158 bytes, SHA-256 `0ffc9857b8511fbf9f17c6ebc850915cc9b9b92f57f62f4799ee901b9c8d2dfe`, expires `2026-11-19T16:46:16Z`.
- Run #83: **PASS** — [run 43263188031](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43263188031), head SHA `c7f835c5780800f9f51801a0c69c83ec802b91dc`.
  - All 14 main workflow steps completed successfully, including compile, live-data probe, Core strategy/signal regressions, expected-RED runner contract, GREEN adapter tests, Core-First end-to-end paper proof, and shared risk/PaperLedger regressions.
  - Artifact: `core-first-code-operational-proof-43263188031`, ID `13964906864`, size 5,767 bytes, SHA-256 `34e90dc9d2eebaeaacbbad85dc2df5f338c0e89a88e1ca368c0f9cf693033750`, expires `2026-11-19T16:51:23Z`.

## Safety boundary

- Implemented only the pure Core producer adapter; no CLI runner implementation. Strategy, risk engine, ledger schema, leverage, and AI execution remain unchanged.
- `AI_EXECUTION_ENABLED=false` in subprocess test environment.
- Tests use temporary directories only; no canonical T0 database or VPS access.
- No exchange credentials, network adapter, live order path, systemd, daemon, or deployment.
- Workflow PASS means the intentional RED contracts and existing regression checks behaved as expected. It does **not** mean the Core runner or adapter is implemented.

## Disposition

- Core strategy/signal regressions: **PASS** (12/12).
- Core one-shot runner contract: **RED VERIFIED / NOT IMPLEMENTED** (5 expected failures).
- Core producer adapter contract: **PASS** (6/6).
- Core end-to-end paper operational proof and shared risk/PaperLedger regressions: **PASS** in run #82.
- Core one-shot runner: **NOT IMPLEMENTED**.
- Core producer-to-validator adapter: **IMPLEMENTED / CI PASS** at source SHA `c7f835c5780800f9f51801a0c69c83ec802b91dc`.

## Next bounded step

Next bounded step: implement the separately approved minimum Core one-shot CLI/config/preflight contract (`python -m core_runtime --config <paper-config>`). Preserve PAPER-only mode, `ai_execution_enabled=false`, explicit existing ledger path, read-only risk snapshot preflight, and fail-closed behavior before any ledger mutation. Do not add implicit SQLite creation/migrations. Keep Strategy Core logic, Core leverage, Shared Risk Engine, PaperLedger schema, AI, T0, and VPS unchanged.


## Core paper preflight CLI increment — 2026-11-12

- Implemented `core_runtime/__main__.py` as a **read-only preflight CLI**, not a completed Core decision-cycle runner.
- Config contract: explicit JSON file; exact allowed keys `mode`, `ai_execution_enabled`, `ledger_path`; requires `PAPER`, boolean false, and explicit ledger path.
- Fail-closed checks: config existence/schema, exchange credential environment variables, AI execution environment flag, ledger file existence, and ledger path equality with `MARKET_DATA_DB`.
- Reads `read_account_risk_snapshot()` only after confirming the ledger file exists. It does not construct `PaperLedger`, create a database, run migrations, or write ledger state.
- Successful output explicitly reports `status=PREFLIGHT_PASS` and `decisionCycle=NOT_RUN`. This must not be described as a trading signal, paper admission, fill, or complete runtime.
- CLI contract tests: **PASS 5/5** in run #85. The tests cover help, missing config, LIVE rejection, AI-enabled config rejection, and missing ledger rejection before SQLite creation.
- Run #84: **FAIL / SUPERSEDED WORKFLOW EXPECTATION** — source `aad101268733c008cfd2c8bd4f390d306b34d232`; the old workflow still expected the runner tests to be RED, but the new CLI tests passed, so the stale RED gate deliberately failed. No application regression was identified by this failure. Artifact ID `13964248211`, size 2,352 bytes, SHA-256 `acf464247d24c8ae017dcb9f6195e46b254920114cf76d34036f4a47a3c44c33`.
- Updated workflow gate in commit `837f0bb718ec2f7c91543cf9ca3f0fdd17d76fe1` to require the CLI contract GREEN and to report `CORE_RUNTIME_DECISION_CYCLE=NOT_IMPLEMENTED`.
- Run #85: **PASS** — [run 43263836471](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43263836471), exact head SHA `837f0bb718ec2f7c91543cf9ca3f0fdd17d76fe1`; all 14 workflow steps SUCCESS, including compile, live-data probe, Core regressions, CLI 5/5, adapter 6/6, Core-First operational proof and shared risk/PaperLedger regressions.
  - Artifact: `core-first-code-operational-proof-43263836471`, ID `13964263345`, size 5,313 bytes, SHA-256 `6348d70690f7b7fd78f218a97c9715e05a2a945a215e11bdf1c703eb43612564`, expires `2026-11-19T16:55:02Z`.

## Current disposition after run #85

- Core strategy/signal regressions: **PASS**.
- Producer-to-validator adapter: **IMPLEMENTED / PASS 6/6**.
- Core CLI safety contract: **PASS 5/5**.
- Core paper preflight CLI: **IMPLEMENTED / CI PASS**, read-only only.
- Actual Core decision cycle (load validated M15/H1/book inputs, call Strategy Core, validate and submit through PaperLedger): **NOT IMPLEMENTED**.
- Positive preflight against a fully initialized and risk-ready disposable dual-ledger database: **NOT VERIFIED** by this CLI contract test set.
- VPS runtime, persistent host installation, process supervision, scheduler/daemon and deployment: **NOT STARTED / NOT AUTHORIZED** in this increment.

## Next bounded step

Add isolated tests proving the preflight risk-snapshot path is read-only and fails closed on an existing but incomplete/corrupt disposable ledger without changing its bytes or schema. Separately establish a versioned input-bundle contract for the actual one-shot decision cycle before implementation. Keep Core strategy, leverage, Shared Risk Engine, PaperLedger schema, AI, T0, VPS and live execution unchanged.


## Account-wide risk snapshot read-only verification — 2026-11-12

- Added isolated contract suite: `paper_execution/test_account_risk_snapshot_read_only.py`.
- Test 1 — ready account: uses a disposable dual-ledger fixture with reconciled account-wide risk state; `read_account_risk_snapshot()` returns PAPER, `liveTradingSupported=false`, `riskReady=true`, equity `100`; SHA-256 of the SQLite file is identical before and after the read.
- Test 2 — incomplete existing SQLite file: reader fails closed when the migration table is absent; it does not create missing tables or mutate the existing database bytes.
- Test 3 — corrupt risk state: disposable fixture bypasses SQLite CHECK constraints only to create an invalid `risk_ready=7` row; reader rejects it as `ACCOUNT_RISK_STATE_MISSING_OR_CORRUPT`; database bytes remain identical across the read attempt.
- Initial run #86: **FAIL / TEST FIXTURE ASSUMPTIONS** — the test expected a normalized migration error although SQLite correctly returned `no such table`; its corruption setup was blocked by the schema CHECK constraint. No reader mutation was observed. The tests were corrected to assert fail-closed SQLite error semantics and use `PRAGMA ignore_check_constraints=ON` solely while constructing the disposable corrupt fixture.
- Run #87: **PASS** — [run 43265132670](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43265132670), exact source SHA `d182eccc16d982d8500818c4cdd6b9281f50ea93`; all 15 workflow steps SUCCESS, including the dedicated account-risk snapshot suite (3 tests), Core-First operational proof, shared risk and PaperLedger regressions.
  - Artifact: `core-first-code-operational-proof-43265132670`, ID `13966087498`, size 5,315 bytes, SHA-256 `e0c862e00376fb39e1bfe42bff0cf97c357502756c33cdc1ce3aae936005681d`, expires `2026-11-19T17:02:18Z`.
- Disposition: account-wide risk snapshot read path **PASS — READ-ONLY AND FAIL-CLOSED VERIFIED** for the tested ready, incomplete and corrupt disposable database cases. No changes to `paper_execution/ledger.py`, schema, migrations, strategy, leverage or risk policy were required.
- Safety: all data is disposable CI fixture data. Canonical T0, VPS, exchange credentials, network order paths and live trading were not accessed.

## Current disposition after account-risk snapshot test

- Account-wide risk snapshot: **PASS** (3/3 dedicated tests).
- Positive ready-state read: **PASS**, exact SQLite file digest unchanged.
- Incomplete existing DB: **PASS**, fails closed without initialization or mutation.
- Corrupt account-risk row: **PASS**, fails closed without mutation.
- Preflight CLI still only reports `decisionCycle=NOT_RUN`; actual Core decision cycle remains **NOT IMPLEMENTED**.
- VPS runtime/deployment remains **NOT STARTED / NOT AUTHORIZED**.

## Next step (not automatically executed)

Freeze and review a versioned input-bundle contract for the actual Core one-shot decision cycle. No implementation of that next phase is included in this approval.
