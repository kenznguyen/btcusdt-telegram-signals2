# Core Runner Hardening G2–G6 — 2026-11-14

## Owner approval and scope

Owner explicitly approved implementation of G2–G6 on the existing branch `feature/core-operational-proof-20261112`, using TDD, disposable SQLite fixtures and GitHub Actions only.

Authorized:
- Permit only a valid position-reducing Core `EXIT` when account `riskReady=false`; block `ENTRY` and `DCA`.
- Read `PAPER_MAX_DRAWDOWN_PCT`, `PAPER_MAX_DAILY_LOSS_USDT`, and `PAPER_MAX_EXPOSURE_USDT` as validated overrides for configured risk limits.
- Return distinct CLI exit classes for input rejection, risk unavailable, invalid signal, PaperLedger rejection and runtime failure.
- Test PAPER order outcomes `OPEN`, `PARTIALLY_FILLED`, `FILLED`, idempotency and transactional risk controls against temporary SQLite.

Not authorized: VPS/SSH operations, deployment, persistent process/autostart, T0 changes, exchange access or credentials, AI execution, live trading or real orders. `AI_EXECUTION_ENABLED=false` remains mandatory.

## Implementation and test evidence

- Initial test-first contracts were added in `core_runtime/test_runner_hardening.py`; the first RED run exposed the absent env override, risk-unready preflight path and CLI result mapping.
- Implementation commits on the same branch:
  - `57232bf12741d0ac17768de75d55c07633e9610c`: risk-aware preflight/one-shot path, environment risk limits and CLI exit mapping.
  - `34066f4f1d3781c3acc8d597dfcf0cb305882000`: fail closed on unknown risk-limit config keys and classify transactional risk-input unavailability separately.
- Added runner decision tests proving ENTRY is blocked and a valid position-reducing EXIT can reach the shared PAPER ledger while risk is unready.
- Added disposable SQLite integration tests for OPEN, PARTIALLY_FILLED, FILLED, idempotent retry, Kill Switch rejection, and risk-unready EXIT vs DCA.
- Full Core-First workflow at source `8b774bd33e7f2199dbf542e4788f35819bc6a26b`: run [43571155276](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43571155276), job `132375787785`, SUCCESS; 28/28 workflow steps succeeded. Focused runner-hardening tests 7/7 PASS; SQLite ledger integration command 26 tests PASS (20 existing Core-First regression tests plus 6 new integration tests). Artifact `14104865011`, name `core-first-code-operational-proof-43571155276`, SHA-256 `8a61c397ea30a88a1d9b44766b17297063028718754f4fd025f5b5417c7807ea`, expires 2026-11-21.
- The later source `34066f4f1d3781c3acc8d597dfcf0cb305882000` adds two final safeguards and their regression tests. Its Core workflow run [43571521270](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43571521270) was IN PROGRESS at this handoff update. Do not claim the latest source SHA GREEN until that exact run completes successfully.
- Intermediate failed RED/fixture runs are retained in GitHub Actions history; the OPEN/PARTIAL/FILLED fixture initially shared one database and correctly exposed PENDING_ORDER. The fixture was split into isolated test cases before the successful 8b run.

## Status at this handoff update

- G2 risk-unready decision gate: PASS at source 8b; latest transactional risk-unavailable classification addition is pending verification at source 34066.
- G3 environment risk limits: PASS at source 8b; latest unknown-key fail-closed addition is pending verification at source 34066.
- G4 CLI result classes: PASS at source 8b; latest transactional risk-unavailable classification addition is pending verification at source 34066.
- G5 order lifecycle: PASS at source 8b for OPEN/PARTIALLY_FILLED/FILLED disposable SQLite fixtures.
- G6 idempotency and risk controls: PASS at source 8b for idempotent retry, Kill Switch, risk-unready EXIT/DCA behavior; existing Core-First transactional contention/risk regression also passed in the full workflow.
- Overall G2–G6: CONDITIONAL PASS pending exact-SHA CI run 43571521270.
- Continuous Core C1–C8 remain previously CI-verified at their recorded source; no activation or VPS runtime is implied here.

## Next step

Read back run 43571521270 at exact source 34066f4f1d3781c3acc8d597dfcf0cb305882000, verify all jobs, test logs and artifact metadata, then update this report and handoff with final PASS/BLOCKED/NOT VERIFIED. No VPS or live execution is authorized by this approval.
