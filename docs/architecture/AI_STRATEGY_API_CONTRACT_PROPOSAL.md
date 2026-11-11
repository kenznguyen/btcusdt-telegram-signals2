# AI Strategy API Contract Proposal — Review Before GREEN

**Status:** PROPOSAL — OWNER REVIEW REQUIRED; not an implementation authorization  
**Date:** 2026-11-11  
**Baseline:** `aa7897520b5435ff4c981b3f2ab8a6710f811eea`  
**Scope:** Clarify the pure decision interface, policy/evidence snapshots, AI ledger admission and test acceptance. Documentation only.

## 1. Purpose and non-goals

This proposal makes the owner-approved `AI_STRATEGY_CONTRACT.md` implementable without coupling the decision function to environment variables, database state or mutable global configuration.

It does not authorize:
- GREEN implementation or production-source edits;
- choosing a numerical `C_min`, calibration sample minimum or calibration-period minimum;
- calibration training, model changes or OOS acceptance;
- schema migration, ledger cutover, backtest acceptance or feature activation;
- T0/T1/T2 runtime, VPS, deployment, exchange connectivity or live orders.

Strategy Core remains unchanged: RSI + ADX + Smart DCA, 13x leverage and existing ROE/entry/DCA/exit semantics. Existing shared risk authority remains final.

## 2. Proposed interface boundary

### 2.1 Keep the decision function pure

Current `pipeline.decision.evaluate(candle_window, intelligence, prediction, book, now_ms, *, target_base, threshold, max_input_age_ms)` is a pure-ish decision function. Do not make it open databases, read environment variables, instantiate ledgers or fetch account state.

Proposed extension: pass one immutable `admission_context` argument. It contains the policy, account-risk and instrument/AI-position snapshots needed to decide and size an AI intent. The decision function validates the snapshots and returns either a diagnostic WAIT/BLOCKED result or a fully specified PAPER intent.

Conceptual shape (not yet an implemented Python type):

```python
evaluate(
    candle_window, intelligence, prediction, book, now_ms,
    *,
    admission_context,
    threshold="0.002",
    max_input_age_ms=60_000,
)
```

The context must be a server-created value, never accepted from a public caller or from untrusted prediction fields. Its components are:

- `ai_policy`: `policyVersion`, `confidenceMin`, `minCalibrationSamples`, `minCalibrationPeriodMs`, `maxCalibrationAgeMs`, leverage mapping/version and allowed leverage bounds.
- `account_risk`: `riskReady`, positive `accountEquityQuote`, observation timestamp/freshness, reconciliation state/version, risk-config version and Kill Switch state.
- `instrument_rules`: symbol/market type, `lotSize`, tick-size and any venue minimum quantity/notional needed to avoid constructing an unexecutable paper intent; source/version/as-of timestamp.
- `ai_position`: current AI ledger signed position and ledger snapshot/version only. No Core position or Core DCA state may be supplied to AI sizing.

This is a proposal for the interface boundary, not a requirement to use these exact Python class names. The implementation may use frozen dataclasses or validated immutable mappings, but the fields and invariants must remain explicit.

### 2.2 Calibration artifact

Prediction carries a nested `calibration` object. The following are required and must be validated against a trusted calibration-artifact registry/manifest, not merely trusted because strings are present:

- `calibratedConfidence`: finite decimal, not bool, in [0,1].
- `calibrationVersion`, `calibrationMethod`, `calibrationArtifactHash` (SHA-256 format and verified artifact bytes/manifest).
- `calibrationDatasetVersion`, `calibrationSampleCount`, `calibrationStartMs`, `calibrationEndMs`, `calibratedAtMs`.
- `labelDefinition`, `forecastHorizonMs`.
- Match against prediction `modelVersion`, `strategyVersion`, `trainingDatasetVersion` and `trainedThroughMs`.

Temporal invariants proposed for owner confirmation:
1. `calibrationStartMs > trainedThroughMs`.
2. `calibrationEndMs >= calibrationStartMs`.
3. `calibratedAtMs >= calibrationEndMs`.
4. Prediction availability is not earlier than `calibratedAtMs`.
5. Calibration data is disjoint from model training data and the label horizon does not leak across the prediction cutoff.
6. Calibration age, minimum sample count and minimum period are enforced from explicit versioned policy fields. Missing policy values block intent.

The artifact registry/manifest source and the exact calibration freshness calculation still need to be selected. Hash-shape validation alone is not proof that an artifact exists or is trusted.

### 2.3 AI leverage policy

- `confidenceMin` must satisfy 0 <= `confidenceMin` < 1; no numeric value is selected in this proposal.
- Require `confidenceMin <= calibratedConfidence <= 1`.
- Use the already approved mapping:
  `L = 1 + 2 * (C - C_min) / (1 - C_min)`.
- The resulting leverage must be finite and within [1,3]. Do not silently clamp invalid confidence, policy or output.
- `policyVersion` and mapping version are mandatory and persisted with the reservation.
- AI ledger creation/admission must receive an explicit admitted AI leverage from this policy snapshot. It must never fall back to generic `LEVERAGE`.
- `PaperLedger` must independently reject AI leverage outside [1,3]. Core remains pinned to 13x.

### 2.4 Account risk and sizing

The server constructs the account snapshot from the reconciled account/equity path. AI intent creation requires:
- `riskReady is True`;
- account equity is reconciled, positive and fresh under the same shared freshness limit;
- Kill Switch permits new exposure;
- a versioned risk-config snapshot is available.

For each new ENTRY or exposure-increasing DCA:
- `marginBudget = accountEquityQuote * 0.01`;
- `targetNotional = marginBudget * admittedAiLeverage`;
- `incrementalQuantity = floor_to_lot(targetNotional / executionLimitPrice, lotSize)`;
- use the exact `executionLimitPrice` written to the intent and subsequently submitted to the ledger;
- ENTRY target is the signed incremental quantity;
- DCA target is current AI ledger position plus the signed incremental quantity in the same direction;
- zero/invalid quantity, invalid price/rules, stale equity, invalid leverage or risk denial means no intent.

The Shared Risk Engine must independently recompute the 1% budget at reservation time using the current reconciled equity, and may reject the candidate. A decision-time size is not a bypass of admission-time checks.

### 2.5 API and ledger handoff

Proposed flow:

1. API loads canonical market inputs, prediction and book as it does today.
2. API obtains trusted AI policy, account-risk snapshot, instrument rules and AI-ledger position from server-side providers.
3. API passes a single immutable admission context into `decision.evaluate`.
4. Decision returns WAIT or a PAPER intent containing signed target quantity, exact limit price, admitted leverage, margin budget and policy/calibration/equity/risk/instrument snapshot references.
5. API submits only to `AI_FREQAI` ledger with explicit admitted leverage and immutable policy version.
6. Ledger validates AI leverage domain, ownership and snapshot consistency, then Shared Risk Engine independently admits/rejects.
7. Reservation persists the values needed for replay/audit: equity basis and timestamp, leverage, confidence/calibration identity, AI policy and risk-config versions, limit price, lot metadata, computed quantity and intent identity.

The exact account-risk and instrument-rule provider functions are not specified here. They must be identified from existing project abstractions before implementation; no new database schema is implied or authorized.

## 3. TDD failure triage — exact observed failures

Source SHA: `aa7897520b5435ff4c981b3f2ab8a6710f811eea`  
Run: [42989566675](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42989566675)  
Result: 36 tests executed; 23 assertion failures; 0 runtime errors.

| Priority | RED failures | What they establish | Required GREEN behavior |
|---|---:|---|---|
| P0 — calibration fail-closed | 17 | Missing confidence (1), invalid/non-finite/bool confidence (6), missing calibration provenance fields (10) currently still allow BUY | Invalid/missing calibration must produce no AI intent; do not fallback to raw prediction |
| P0 — leverage isolation/bounds | 4 | AI ledger factory lacks explicit admitted leverage (1); ledger accepts 0.99x, 3.01x and 13x for AI (3) | Explicit AI policy leverage only; AI ledger enforces [1,3]; Core remains 13x |
| P0 — account equity sizing/readiness | 2 | Decision function has no account-risk sizing inputs; sizing and missing/stale-equity contracts cannot be exercised | Size from fresh reconciled equity and same execution limit; no intent on unavailable/stale/unready equity |

The two sizing/equity failures currently use function-signature introspection as a RED sentinel. This is useful to prove the expected interface is absent, but it is brittle as a permanent acceptance test. Replace it in the next test-only refinement with behavioral tests through the API/provider boundary and the immutable admission context. Do not weaken the behavior assertions.

The three subcases for AI leverage range are separate failures, as are the six confidence subcases and ten missing-provenance subcases. The 23 count is assertion failures, not 23 distinct feature areas.

## 4. Coverage still missing from the current RED suite

The current 36-test run does not yet demonstrate all requirements in the approved contract. Add separate test-only cases before GREEN:

1. Confidence below configured `C_min`; `C_min` absent, malformed, equal to 1 or out of range.
2. Exact leverage mapping at `C=C_min` (1x), `C=1` (3x), and a deterministic interior point; invalid/non-finite result.
3. Invalid SHA-256 hash, unknown/untrusted calibration artifact, model/dataset/strategy mismatch and horizon mismatch.
4. Temporal leakage, calibration start/end ordering, stale calibration, insufficient sample count and insufficient calibration duration.
5. AI ENTRY lot-step flooring, zero rounded quantity, invalid lot/tick/minimum notional and non-positive execution price.
6. AI DCA uses a fresh 1% budget and AI ledger position only; Core position/DCA changes must not affect AI quantity.
7. Shared Risk Engine and Kill Switch denial leave no reservation/fill/exposure increase.
8. Replay/idempotent retry preserves original calibration, leverage, equity, risk-policy and price snapshots.
9. Regression: Core remains 13x and its RSI/ADX/Smart-DCA and ROE behavior remain unchanged.

## 5. Owner decisions still required before GREEN

This proposal deliberately leaves the following unset:
- numerical `C_min`;
- minimum calibration sample count and minimum calibration period;
- maximum calibration age/freshness threshold;
- trusted calibration artifact registry/manifest and hash-verification source;
- exact calibration label/horizon compatibility rules for the active model;
- account-risk snapshot provider and its freshness/reconciliation fields;
- source/version of BTCUSDT lot/tick/minimum-notional rules;
- whether AI DCA is enabled in v1 and, if enabled, its trigger/eligibility rule (the sizing formula alone does not define a DCA strategy);
- whether the decision result carries the full immutable snapshot or opaque versioned references resolved by the reservation layer.

No defaults should be invented for these items. Missing mandatory policy or evidence remains fail-closed.

## 6. Approval boundary

This document is a proposal for owner review only. It does not amend the owner-approved contract, authorize test changes, or authorize GREEN implementation. The next safe step is owner review of the unresolved decisions and explicit approval of any test-only refinements. All runtime, migration, deployment and live-trading boundaries remain unchanged.
