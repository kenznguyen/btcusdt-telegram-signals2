# T2 AI Label/Direction Parser V1 — Implementation Evidence — 2026-11-08

## Scope

Implemented a strict, fail-closed parser for the selected independent AI Strategy V1 contract:
- Regression-to-Direction with a distinct neutral `ABSTAIN` interval.
- M15 and H1 are both required as declared model feature timeframes.
- Confidence must reference a separate calibration artifact; raw predicted return cannot be represented as calibrated confidence.
- Binance BTCUSDT USDT perpetual identity is explicit.
- Horizon, price bases, label end rule, outcome availability rule, thresholds and feature cutoff semantics are mandatory inputs. No defaults are supplied.

## Changes

- `quant_system/ai_label_direction_contract.py`: immutable parsed contract dataclass, strict exact-key schema, UTF-8 JSON parsing with duplicate-key rejection, finite Decimal threshold parsing, positive integer horizon checks, ordered threshold validation, exact M15+H1 feature set, closed/validated/first-observed availability semantics, separate calibration source requirement, and rejection of legacy frozen model ID `chart-pro-okx-shadow-v1`.
- `quant_system/test_ai_label_direction_contract.py`: 14 unit tests.
- `.github/workflows/t2-dual-signal-coordinator.yml`: new test invocation and py_compile coverage; offline boundary remains enforced.

## TDD evidence

- RED test-first commit: `56dcdcb013466941beaba527da438fec6d06e8ed`.
- RED workflow: [42462726856](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42462726856), job `128675296702`; failed as expected because `quant_system.ai_label_direction_contract` did not exist. The import failure proves the test preceded implementation.
- Parser implementation commit: `d1a467005090309c7b37f868100fd277da19acf5`.
- Workflow/compile coverage commit and exact tested branch source: `294a1f5d6522d80d4a4ed4f69c00fde0b2945e23`.
- Parser blob: `db889f0b4b81470eac4469fe4d35baa5c37530c7`.
- Test blob: `2b5b74bf9210e41f13b139762a6af58fd7343e1c`.
- Workflow blob: `f45a45e037ea934725544629bcd49b3874dde491`.
- GREEN exact-source push workflow: [42462787953](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42462787953), job `128675483092`, SUCCESS.
- PR-context workflow: [42462792780](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42462792780), SUCCESS.
- Test invocations: label/direction parser 14/14; provenance 38/38; calibration 16/16; dynamic leverage 14/14; coordinator 11/11; dual ledger 23/23; Phase 2 20/20; Phase 3 11/11; PaperLedger 18/18. Total 165/165 PASS. py_compile PASS.
- Artifact ID `13610591980`; SHA-256 `a2ce3a539b306dea2e7c5bba27fc3ac2dba5df0f5587793bfb6742b6021af213`.

## What this does NOT prove

- Parser acceptance is only syntactic/structural contract validation. It does not prove the label formula, horizon-to-candle mapping, price basis, or availability rule matches the actual training pipeline.
- It does not prove thresholds were selected only on training/validation data or sealed before OOS inspection.
- It does not bind this contract into the Ed25519 signed provenance manifest yet.
- It does not prove H1 is present in actual FreqAI fit/inference matrices; current research config remains M15-only.
- It does not certify split, purge/embargo, label leakage, model training, calibration, OOS performance or AI admission.
- No model training, OOS, backtest, paper runtime, exchange connection, T0/T1 DB/feeder or order activity was run.
- `AI_EXECUTION_ENABLED=false`; PR #95 remains OPEN / DRAFT / NOT MERGED.

## Status and next step

- Parser contract and tests: **PASS**.
- Semantic label/horizon validation: **BLOCKED / NOT IMPLEMENTED**.
- Training-only threshold provenance: **NOT VERIFIED**.
- Actual H1 feature matrix: **NOT VERIFIED**.
- Signed manifest semantic binding: **NOT IMPLEMENTED**.

Next: define and test the semantic label calculator against closed M15 candle fixtures and explicit UTC outcome availability, then reconcile the label/feature contract into the signed manifest. Do not start training or inspect OOS holdout until split and purge protocol are sealed.
