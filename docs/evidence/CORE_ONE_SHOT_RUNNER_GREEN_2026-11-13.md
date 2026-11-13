# One-shot Core Runner — GREEN

Date: 2026-11-13
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/core-operational-proof-20261112`
Tested source SHA: `8f774d7103f54681497837c7e4fd7c2e1c38c754`
Status: **PASS — exact-SHA GitHub Actions GREEN; persistent runtime NOT VERIFIED**

## Scope and behavior
- Implements an explicitly invoked, single-cycle Core runner consuming only validated `CORE_DECISION_INPUT_BUNDLE` version `1.0.0`.
- CLI: `python -m core_runtime --config <paper-config.json> --run-once --bundle <bundle-v1.json>`.
- Reuses the existing RSI + ADX + Smart DCA producer, producer adapter and Core signal validator. Strategy Core itself was not modified.
- Before strategy execution, performs read-only PAPER preflight; checks AI execution disabled, no exchange credentials, existing isolated PaperLedger, account-wide risk readiness, Bundle v1 integrity, T1 snapshot contract, current account-risk snapshot equality and current Core paper-state equality.
- A stale account-risk or Core-state bundle is rejected before Ledger construction/submission.
- For actionable Core signals, calls the existing Core-scoped PaperLedger exactly once. PaperLedger applies the existing Shared Risk Engine, Kill Switch, 1% margin reservation and fill simulation. T1 input is enabled only for `STRATEGY_CORE`; AI and MANUAL paths retain their existing book-source restrictions.
- No signal means no PaperLedger construction or write. Risk rejection and submit/commit failure are reported distinctly.
- PaperLedger is opened with `apply_migrations=False`; Runner does not create or migrate schema.
- The runner is synchronous and one-shot. No daemon, scheduler, polling loop, AI Strategy invocation, exchange API call or live order path exists in this increment.

## Implementation files
- `core_runtime/preflight.py`: shared read-only PAPER preflight and strict configuration contract.
- `core_runtime/one_shot.py`: Bundle v1 validation, state/risk freshness fence, Core producer/validator orchestration, one PaperLedger submit and structured result.
- `core_runtime/__main__.py`: explicit `--run-once --bundle` CLI mode; existing preflight-only invocation remains available.
- `pipeline/test_core_runtime_one_shot.py`: 11 focused runner tests, including no-signal no-write, malformed/duplicate bundle rejection, stale risk/state rejection, missing risk limits, AI environment override, shared-risk rejection and commit failure.
- `paper_execution/test_core_first_operational.py`: real SQLite/PaperLedger integration through the CLI entrypoint, with Bundle v1 and validated T1 snapshot; verifies paper fill, AI ledger remains untouched and replay of stale bundle is rejected.

## Exact-SHA verification
- T1 → PaperLedger focused suite: run `43363662032`, SHA `3adf741f5a454d677c003c375141acdd179b37f5`, job `131682851514`: **100/100 PASS**.
- Runner-focused suite on tested source: run `43365609751`, SHA `8f774d7103f54681497837c7e4fd7c2e1c38c754`: **11/11 PASS**.
- Core operational integration on same SHA: **41/41 PASS**, including CLI → Bundle v1 → Core producer → Core signal validator → T1-aware PaperLedger integration and stale-bundle replay rejection.
- Additional exact-SHA CI suites on run `43365609751`:
  - Live-data probe: 4/4
  - Strategy Core + signal: 12/12
  - Preflight CLI: 5/5
  - Bundle v1 validator: 19/19
  - Producer adapter: 6/6
  - Account risk snapshot read-only: 3/3
  - Shared risk and PaperLedger: 34/34
  - T1/T2 Order Book, HTTP reader and integration: 49/49
- GitHub Actions run `43365609751`: **SUCCESS**, all 18 workflow steps completed successfully.
- Artifact ID `14010098776`, name `core-first-code-operational-proof-43365609751`, SHA256 `008a574ce79cb8ba4637f5b49ade49d95d6087e5e6ad2df408b2a7d3d183026b`.
- An intermediate CLI integration attempt at SHA `37b1d113bb452ec369cfb92d090e98c316d8e285` failed because the fixture's deterministic timestamp was not passed through the CLI test entrypoint. The test-only clock injection was added without exposing a CLI clock override; exact-SHA run `43365609751` confirms the corrected CLI integration PASS.
- Branch comparison from prior handoff checkpoint `90a5eb1dbaab8e3d204eb446b19758a91f8fa0af` to tested source: 16 ahead / 0 behind.

## Safety and limitations
- `AI_EXECUTION_ENABLED=false`; no exchange credentials; no real orders.
- CI used disposable fixtures only. No T0/T1 production data, VPS, service, systemd/autostart or persistent runtime was touched.
- Strategy Core, Shared Risk Engine policy, Kill Switch semantics, Ledger schema/migrations, reservation algorithm and fill simulation were not changed beyond the approved T1 input compatibility boundary.
- T1 → PaperLedger compatibility: **PASS**.
- One-shot Core Runner code and CLI: **PASS (CI)**.
- Persistent VPS/runtime execution: **NOT VERIFIED / NOT AUTHORIZED**.
- AI Strategy independent signal generation: **NOT PART OF THIS CORE-FIRST RUNNER INCREMENT**.

## Completion
The approved Core-first One-shot Runner scope is complete at code/CI level. Keep the current branch and preserve the no-runtime/no-live-order boundary. Any future runtime invocation or deployment requires a separate explicit authorization and a fresh operational plan.
