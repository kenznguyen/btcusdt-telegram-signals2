# Core One-shot Runner — RED Contract Test Evidence

Date: 2026-11-12  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Baseline source SHA: `2de2c09af99d782c0f0fa4884c21d2ee3abb3dee`  
Uploaded source archive SHA-256: `147433ac9a031e3cdc3cda6eb76119310b3adbcc80782877c6f4f4bedd1d9991`

## Scope recorded

- Add black-box CLI contract tests for `python -m core_runtime --config <paper-config>`.
- Require help output, explicit config, `mode=PAPER`, `ai_execution_enabled=false`, and an existing disposable ledger file before SQLite is opened.
- Require invalid mode, AI-enabled config, missing config, and missing ledger to fail closed with stable diagnostic identifiers.
- Extend the existing Core operational proof workflow to compile and verify the expected RED state, retaining logs in the existing artifact.

## Local verification

- `python -m unittest pipeline.test_core_strategy pipeline.test_core_signal -v`: **PASS**, 12 tests.
- `python -m unittest pipeline.test_core_runtime_contract -v`: **EXPECTED RED**, 5 failures because `core_runtime` does not exist at the baseline. The expected failure signature is `No module named core_runtime`.
- `python -m py_compile pipeline/test_core_runtime_contract.py`: **PASS**.
- Workflow YAML parse with PyYAML: **PASS**.
- Workflow static assertions for test inclusion and expected RED evidence: **PASS**.
- `git diff --check`: **NOT VERIFIED**; uploaded ZIP has no `.git` metadata, so a local Git worktree/diff is unavailable.

## Safety boundary

- No runner implementation, strategy change, risk-engine change, ledger schema change, leverage change, or AI execution.
- `AI_EXECUTION_ENABLED=false` in subprocess test environment.
- Tests use temporary directories only; no canonical T0 database or VPS access.
- No exchange credentials, network adapter, live order path, systemd, daemon, or deployment.

## Disposition

- RED contract: **PASS** (5 tests fail for the expected missing-runner condition).
- Existing Core strategy/signal regressions: **PASS** (12/12).
- GitHub Actions run #81: **PASS** — [run 43261623605](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43261623605), conclusion `success`, head SHA `60752460b5fbc50ae97fe3708698e20e72bd5144`.
- All 13 main workflow steps completed successfully, including Core-First end-to-end paper operational proof and shared risk/PaperLedger regressions.
- Artifact: `core-first-code-operational-proof-43261623605`, ID `13964625769`, size 5,095 bytes, SHA-256 `a08eb71dfb16c9ef68bc8e7c10a96b154ec8fa63c0679eda8c6795ebeee7758c`, expires `2026-11-19T16:42:41Z`.
- The workflow validates the intentional RED contract; it does **not** establish that `core_runtime` is implemented.
- Core one-shot runner: **NOT IMPLEMENTED**.

## Next bounded step

Implement only the smallest `core_runtime` CLI/config/preflight and producer-to-validator adapter needed to turn these contract tests GREEN. Keep the account-wide risk snapshot and transactional Shared Risk Engine/PaperLedger admission as separate gates. Preserve the Core strategy and existing Core leverage policy; do not add AI execution or persistent runtime behavior.
