# SIMULATED-only Equity Initialization V1 — implementation and verification

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Implementation source HEAD: `d083f39e5a1071f4f41c6d6195a8535608c77127`

## Owner approval and scope

The owner approved the additive SIMULATED-only equity-origin/cutover and readiness path. The existing funded-account Bootstrap, funding reconciliation and equity cutover path must remain unchanged.

Approved contract remains `SIMULATED_CAPITAL_V1`: initial capital 100 USDT; PAPER/SIMULATED; max drawdown 10%; max daily loss 2 USDT; max order margin 1% of current portfolio equity per order; shared exposure ceiling 10 USDT; no auto top-up or restart reset; live trading and AI execution disabled.

## Implemented behavior

- A genuinely new ledger can seed `paper_account_config.initial_capital=100` from the validated simulated contract inside the caller-owned `BEGIN IMMEDIATE` transaction.
- An existing legacy account configuration without a matching immutable simulated origin is rejected; it is not reclassified as synthetic capital.
- Account migration, simulated origin, distinct append-only seed event, simulated equity-origin record, HWM=100 and initial UTC daily baseline=100 are composed in the same transaction. Failure rolls back the transaction.
- Synthetic seed remains outside `paper_funding_events`; the simulated path does not create funded-account coverage or equity-cutover evidence.
- Persisted origin, seed and equity provenance are verified before simulated account marks can establish readiness. Mixed funding/cutover evidence fails closed.
- Initial risk state remains `risk_ready=0` until a valid account-wide market mark is accepted. A valid first mark on the initialized UTC day sets `risk_ready=1` without requiring funded-account cutover.
- Restart preserves the original seed, initialization time, equity origin and evolved risk state.
- A mark after UTC-day rollover currently fails closed with `ACCOUNT_RISK_DAILY_BASELINE_UNAVAILABLE`; simulated daily-baseline rollover is not implemented in this increment.

## Exact source evidence

| File | Git blob SHA |
|---|---|
| `paper_execution/simulated_equity.py` | `34ae0400b93a25fa0694c1e398da10566ccf5b08` |
| `paper_execution/account_equity.py` | `f31ff634a1b89b87ae1bdcc92fa1b9fa6d00068e` |
| `paper_execution/ledger.py` | `33346a4cac9b2b885924784fda8b8768c8235864` |
| `paper_execution/test_simulated_equity.py` | `6d97d0aa75acb6cfe6c6b6cb30cecc7afdcc303b` |
| `.github/workflows/simulated-capital-v1-contract.yml` | `f3b54ada1d7726070a0d73570251d21cf13b31dc` |
| `.github/workflows/paper-ledger-t1-compatibility.yml` | `9971c3671f8d503fc6615ba15bbd174d2f3df13b` |

## Verification

Both final workflows checked out the exact implementation source SHA `d083f39e5a1071f4f41c6d6195a8535608c77127`.

1. Simulated Capital V1 Contract: [run 43604585984](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43604585984) — SUCCESS. Python compilation and JSON parsing passed; 23/23 contract, origin, simulated equity initialization, rollback, restart, first-mark readiness and UTC-rollover fail-closed tests passed. Job: `132476372401`.
2. Paper Ledger T1 Compatibility: [run 43604586001](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43604586001) — SUCCESS. 135 tests passed across `test_ledger`, `test_dual_ledger_red`, `test_simulated_equity`, `test_dual_ledger_bootstrap`, `test_risk_limits` and `test_risk_control`. Job: `132476372366`.

No artifacts were uploaded by either run. Intermediate RED/fix runs remain visible in Actions history; no failures were hidden.

## Disposition

- SIMULATED-only account configuration + account/origin/seed/equity-origin atomic initialization: **PASS WITHIN TEST SCOPE**.
- Initial HWM and UTC daily baseline: **PASS WITHIN TEST SCOPE**.
- First valid account mark can establish simulated equity readiness without funding cutover: **PASS WITHIN TEST SCOPE**.
- Existing legacy/funded account reclassification guard: **PASS WITHIN TEST SCOPE**.
- Funded-account Bootstrap/funding/cutover regression: **PASS within the 135-test compatibility suite**.
- Simulated daily-baseline rollover: **NOT IMPLEMENTED; fail-closed behavior tested**.
- Contract-bound 1% per-order margin admission and complete runtime shared-risk enforcement: **NOT IMPLEMENTED / NOT VERIFIED**.
- PAPER Ledger overall readiness: **BLOCKED / NOT VERIFIED**.
- Bootstrap activation and Runner: **NOT AUTHORIZED**.

## Safety boundary

All new integration tests used disposable temporary SQLite databases. No existing operational database, VPS, T0, exchange endpoint, credential, Bootstrap runtime, Runner, AI execution, live order or real trading was accessed or changed. No deployment or database migration was run against an operational account.

## Next permitted step

Implement and test SIMULATED-only UTC daily-baseline rollover with immutable provenance, then separately wire the approved contract risk limits—especially the 1% per-order margin ceiling—into atomic shared order admission. Keep the funded-account Bootstrap/cutover path unchanged. Do not activate Bootstrap or Runner until all required gates are independently proven and separately authorized.
