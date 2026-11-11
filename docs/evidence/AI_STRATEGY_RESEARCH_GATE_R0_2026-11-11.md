# AI Strategy Research Gate R0 — Scope and Evidence

**Date:** 2026-11-11  
**Repository:** `kenznguyen/btcusdt-telegram-signals2`  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Status:** R0 DOCUMENTATION RECORDED / R1 OWNER REVIEW REQUIRED

## 1. Owner authorization

The owner approved the proposed next workstream: offline research and evaluation of an AI Strategy that independently generates BTCUSDT LONG/SHORT signals, including when Strategy Core is WAIT. The approved scope is research protocol and evaluation design, not implementation or experiment execution.

## 2. Deliverable

- Added `docs/architecture/AI_STRATEGY_RESEARCH_EVALUATION_CONTRACT.md`.
- Contract defines signal independence, point-in-time data requirements, T0 read-only boundary, label/horizon requirements, chronological train/validation/calibration/holdout partitions, purge/embargo, baselines, statistical/economic metrics, calibration separation, invalidation criteria and staged research gates R0–R4.
- Commit: `cc64603fe944d1f7a7aa63ce70e03d6899000b2a`.

## 3. Scope and constraints preserved

- Strategy Core RSI + ADX + Smart DCA remains unchanged.
- AI is a separate signal producer; its signal generation must not depend on Core position/order/ledger state.
- AI DCA remains disabled in v1.
- T0 remains canonical and independent; no canonical DB access or mutation was performed.
- No production code, tests, workflow, model training, calibration training, backtest, dataset export, database/schema/migration, T0/T1/T2 runtime, VPS, deployment, exchange request, feature activation or order was performed.
- No data was deleted or altered.
- Paper-only remains in force; `AI_EXECUTION_ENABLED=false`.

## 4. Verification

- Documentation file creation succeeded on the existing branch.
- No test or GitHub Actions workflow was run because this increment changes documentation only.
- No experiment artifact or workflow run exists.
- Research protocol is a proposal for R1 review; no dataset, feature set, label/horizon, split dates, execution-cost model or numerical acceptance threshold has been frozen.

## 5. Status

| Gate | Status | Notes |
|---|---|---|
| R0 protocol design | RECORDED | Contract added |
| R1 owner review/freeze | PENDING | Exact data/features/labels/splits/costs/thresholds |
| R2 offline experiment | NOT AUTHORIZED | Requires R1 freeze and separate bounded execution approval |
| R3 evidence review | NOT STARTED | Depends on R2 |
| R4 next-stage decision | NOT STARTED | Owner decision required |
| GREEN-1..5 | NOT AUTHORIZED | Unchanged |
| Calibration `C_min` / statistical thresholds | NOT SET | Must be evidence-based and separately approved |

## 6. Next step

Review R1 choices before running any experiment: exact immutable research bundle(s), point-in-time feature inventory, primary label and horizon, chronological split schedule with purge/embargo, conservative fee/spread/slippage/funding/fill assumptions, and pre-registered acceptance thresholds. No R2 work until those choices are frozen and execution scope is separately approved.
