# Core One-shot Runner — RED Contract Test Evidence

Date: 2026-11-12  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Baseline source SHA: `2de2c09af99d782c0f0fa4884c21d2ee3abb3dee`  
Latest CI source SHA: `c7f835c5780800f9f51801a0c69c83ec802b91dc`  
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
