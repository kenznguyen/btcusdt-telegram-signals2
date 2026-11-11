# AI Strategy Contract — Independent Signal, Calibrated Risk and Sizing

**Status:** OWNER-APPROVED DESIGN CONTRACT; implementation not started  
**Date:** 2026-11-11  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Baseline source reviewed:** `6ef0d7456b2791fae73bfea8855ee30482774673`  
**Scope:** PAPER-only AI Strategy signal contract, leverage selection and equity-based sizing. Strategy Core remains unchanged.

## 1. Architecture and authority

- Strategy Core remains RSI + ADX + Smart DCA, with fixed 13x leverage and its existing ROE/entry/DCA/exit semantics.
- AI Strategy is an independent producer. It may produce LONG/SHORT while Strategy Core reports WAIT.
- Core and AI maintain separate strategy ledgers. AI intents are submitted only to `AI_FREQAI`.
- Every AI ENTRY and exposure-increasing DCA must pass the same account-scoped Shared Risk Engine and Kill Switch as Core. The Shared Risk Engine is the final admission authority and independently recomputes the reservation.
- Paper-only. No live order, exchange execution, migration, deployment, VPS activation or T0 changes are authorized by this contract.

## 2. Calibrated-confidence artifact

The AI prediction artifact must carry a calibrated-confidence object with, at minimum:

- `calibratedConfidence`: finite decimal in [0, 1], interpreted as calibrated probability that the predicted direction is correct.
- `calibrationVersion`, `calibrationMethod`, `calibrationArtifactHash`.
- `modelVersion`, `strategyVersion`, `trainingDatasetVersion`, `trainedThroughMs`.
- `calibrationDatasetVersion`, `calibrationSampleCount`, `calibrationStartMs`, `calibrationEndMs`, `calibratedAtMs`.
- A declared label definition and forecast horizon, compatible with the prediction's direction and horizon.

Validation requirements:

1. Calibration artifact hash and dataset provenance must validate; identifiers must be non-empty and versioned.
2. Calibration observations must be out-of-sample and temporally later than the model's training cutoff, with no overlap/leakage into the prediction's training data.
3. Sample count and calibration period must meet explicit configured minimums. No implicit defaults.
4. Confidence must be finite and within [0, 1]. Missing, stale, mismatched, uncalibrated or invalid calibration fails closed.
5. No fallback from calibrated confidence to raw predicted return, model score, taker flow or an uncalibrated probability.
6. The minimum accepted confidence `C_min` is a required versioned policy input. Its numerical value remains unset until OOS evidence supports it; absent configuration means no AI trade intent.

A missing/invalid calibration may still produce a diagnostic WAIT/BLOCKED signal, but never an ENTRY/DCA intent.

## 3. AI leverage policy

The approved leverage domain is [1x, 3x]. The mapping is:

`L = 1 + 2 × (C - C_min) / (1 - C_min)`

where `C` is calibrated confidence and `C_min` is the required minimum confidence policy. Clamp only for decimal representation tolerance after validating `C_min <= C <= 1`; do not silently clamp invalid inputs.

- At `C = C_min`, leverage is 1x.
- At `C = 1`, leverage is 3x.
- Values below `C_min`, above 1, non-finite values, missing policy, invalid denominator or calculated leverage outside [1, 3] fail closed.
- AI leverage is supplied by the AI policy/config snapshot, never inherited from generic `LEVERAGE`.
- The admitted leverage and policy version are immutable reservation inputs. Re-evaluation cannot silently change an existing reservation.
- Core remains pinned to 13x and is not affected by AI policy/configuration.

## 4. AI sizing contract

For each new ENTRY or exposure-increasing DCA:

- Require a fresh, reconciled account-risk snapshot with `riskReady=true`, positive `accountEquityQuote`, and a valid observation timestamp within the shared risk freshness limit.
- `marginBudget = accountEquityQuote × 0.01`.
- `targetNotional = marginBudget × admittedAiLeverage`.
- `incrementalQuantity = floor_to_lot(targetNotional / executionLimitPrice, lotSize)`.
- The execution limit price must be the same validated price used by the order/ledger admission path.
- For a flat ENTRY, signed target position equals incremental quantity in the signal direction. For DCA, add the incremental quantity to the current AI ledger position in the same direction; never use Core position or Core DCA state.
- Zero quantity after lot rounding, missing/invalid lot metadata, stale/unreconciled equity, non-positive price, invalid leverage or arithmetic overflow means no intent.
- Do not use fixed `PAPER_TARGET_BASE`, `PAPER_MAX_POSITION_BASE` as a substitute for risk sizing, or generic `LEVERAGE` as AI policy. Shared limits may still reject a correctly sized candidate.
- Persist the equity basis, leverage, calibration version, AI policy version, risk-config version, execution limit price, lot-size metadata and computed quantity with the reservation.

Each subsequent ENTRY/DCA obtains a fresh 1% budget from then-current reconciled account equity. The existing Dual Ledger contract's atomic reservation and shared exposure constraints remain authoritative.

## 5. Required fail-closed and isolation behavior

- AI BUY/SELL remains independently observable when Core is WAIT.
- AI order/intent ownership is always `AI_FREQAI`; Core state, position, DCA, PnL and orders are unchanged.
- Missing calibration, invalid provenance, below-threshold confidence, invalid leverage, stale/missing equity, zero rounded quantity, risk denial or Kill Switch => no AI fill and no exposure increase, with an explicit reason.
- Shared Risk Engine denial is final even when AI confidence and sizing are valid.
- Risk-reducing operations retain the existing Shared Risk Engine/Dual Ledger rules.

## 6. TDD acceptance matrix

RED tests must be written and demonstrated failing before any implementation:

1. Missing calibrated confidence blocks an otherwise valid prediction.
2. Confidence below `C_min`, above 1, NaN/infinity, bool, malformed decimal or missing calibration provenance blocks intent.
3. Wrong model/dataset/horizon, invalid artifact hash, stale calibration, insufficient sample count or temporal leakage blocks intent.
4. Leverage maps exactly to 1x at `C_min`, 3x at 1, and valid interior values; invalid/missing policy and out-of-range output fail closed.
5. AI ledger construction uses AI leverage policy; generic `LEVERAGE` cannot override it. Core remains 13x.
6. AI ENTRY quantity is derived from current reconciled equity, 1% margin, admitted leverage, same execution limit and lot-step floor.
7. AI DCA sizes only the incremental amount from a fresh equity snapshot and its own ledger position; Core position/DCA is irrelevant.
8. Stale/missing/unreconciled equity, invalid price/lot size, overflow and zero rounded quantity produce no intent.
9. E2E: AI BUY with Core WAIT writes only to `AI_FREQAI`; Core ledger remains unchanged.
10. E2E: valid AI candidate is rejected by Shared Risk Engine/Kill Switch when account-level controls deny it; no partial reservation/fill remains.
11. Replays/idempotent retries preserve the original calibration, leverage, equity and risk-policy snapshot.
12. Existing Core 13x sizing, RSI/ADX/Smart-DCA predicates and ROE semantics remain unchanged.

## 7. Approval boundary

Owner approval authorizes this design contract and preparation/execution of test-only RED work. It does not authorize GREEN implementation, calibration training or selection of a numerical `C_min`, production configuration, database migration/cutover, backtests/OOS acceptance, feature activation, VPS/runtime changes, deployment, exchange connectivity or live trading. Each requires separate explicit approval.
