# T2 AI Strategy Label and Direction Contract V1 — 2026-11-08

## Decision and scope

This document records the selected design direction for the independent Dual-Strategy AI model:

- Target family: **Regression-to-Direction**.
- Feature timeframes: **M15 and H1 are both actual model features**, not merely contextual metadata.
- Market: Binance BTCUSDT USDT perpetual.
- Research/runtime boundary: offline research and validation only; no training, OOS evaluation, backtest, paper runtime, exchange connection, or order execution is authorized by this contract document.
- The model is independent of the frozen legacy Phase22 candidate `chart-pro-okx-shadow-v1`. The legacy artifact must not be reused or promoted.

This is a design contract, not evidence that a model, feature matrix, or OOS result exists.

## V1 semantic contract

### 1. Prediction target

The model emits one finite scalar `predicted_return` for a registered forward horizon:

`(future_reference_price - decision_reference_price) / decision_reference_price`

Both reference prices, the candle source, price field, timestamp convention, horizon and outcome availability rule MUST be explicitly declared in the sealed protocol. The current candidate's four-M15-candle `close.shift(-4) / close - 1` implementation is discovery evidence only; it is not automatically adopted for this independent AI model.

Required protocol fields (no defaults):
- `label_horizon_m15_candles`: positive integer.
- `decision_price_basis`: registered price field and candle timestamp semantics.
- `outcome_price_basis`: registered price field and candle timestamp semantics.
- `label_end_rule`: exact mapping from decision candle to outcome candle.
- `outcome_available_at_rule`: when the outcome becomes observable, using UTC milliseconds and exclusive candle-close semantics.
- `label_formula_id` and `label_contract_version`.

Unknown, missing, inconsistent or non-causal values fail closed.

### 2. Direction decision

A separate deterministic Direction Decision Layer maps the scalar prediction to:
- `LONG` when `predicted_return >= long_threshold`.
- `SHORT` when `predicted_return <= short_threshold`.
- `ABSTAIN` otherwise.

The sealed protocol MUST contain finite thresholds with `short_threshold < long_threshold`; the neutral interval is therefore explicit. Thresholds MUST be selected using training/validation data only and sealed before OOS predictions/outcomes are inspected. No threshold is inferred from the OOS holdout, and no sign-only direction mapping is permitted.

Threshold values remain intentionally **UNSET** in this design document. The contract implementation must reject missing thresholds rather than silently selecting values.

### 3. Confidence and calibration

A regression value is not a calibrated probability. The raw predicted return MUST NOT be copied into a confidence/probability field.

Any confidence used for AI admission or dynamic leverage must come from a separately versioned calibration mapping fitted on permitted training/validation data and independently evaluated on OOS predictions. The calibration artifact, method, input/output domains, model identity, dataset identity and report hashes must be bound by the signed manifest.

Until the calibration gate is independently passed, AI confidence is unavailable and AI ENTRY/DCA must fail closed. This does not prevent CORE signals from being evaluated independently.

### 4. Feature contract

M15 and H1 are both declared as consumed model feature timeframes. Each prediction must bind exact consumed candle references for both:
- candle open time;
- candle close time (exclusive);
- first-observed availability time;
- closed status;
- validated data quality;
- dataset snapshot identity/fingerprint.

For each feature candle, availability must be no later than the prediction decision timestamp. The model feature builder must prove H1 values are actually present in the fit/inference matrix; a manifest declaration or cutoff record alone is insufficient.

The current `config.research.json` declares only M15 in `include_timeframes`. It does not satisfy this V1 feature contract. H1 must be implemented and verified in the actual feature pipeline before training. Do not start the config as a service; it currently declares `initial_state=running`.

### 5. Temporal/OOS protocol

A separately sealed split protocol must define:
- chronological train, validation and OOS boundaries;
- label horizon and label end/availability semantics;
- purge rule based on actual label end, not a guessed fixed gap;
- embargo rule and rationale, or an explicit signed statement that no additional embargo is required;
- model-fit cutoff and training completion;
- feature cutoff semantics for M15 and H1;
- prediction decision timestamp and outcome availability;
- dataset, model, feature-builder, label-contract and strategy versions.

At minimum, every training label used by a fitted model must be fully observable before the first validation/OOS decision boundary applicable to that fit. Exact strict inequalities and fold-specific purge logic must be executable and independently tested. A generic `train_end < oos_start` check is insufficient to certify label leakage absence.

Walk-forward inference may legitimately use earlier OOS-period candles as causal features for later predictions. Do not incorrectly require every feature candle to predate the initial OOS boundary; require only that each feature was closed, validated and available by that prediction's decision time, and that it was not used in model fitting contrary to the registered split.

### 6. Signed provenance binding

The signed manifest must bind immutable SHA-256 digests and byte sizes for at least:
- model artifact;
- training dataset;
- prediction rows;
- split protocol;
- calibration report;
- label/direction contract;
- feature schema and feature-builder source/build identity.

The split protocol, label contract and feature schema must be parsed and semantically reconciled with the signed manifest; opaque hash-only validation is not enough. The independent signer and trust-root custody must be separately established. A valid signature proves only that the configured key signed the bytes; it does not prove factual correctness or signer independence.

### 7. Admission and risk boundary

The AI candidate is only an intent. Before any paper admission it must pass:
- valid model and signed provenance;
- valid M15/H1 feature cutoffs;
- valid prediction and direction decision;
- independently passed calibration gate for confidence-dependent AI sizing;
- approved dynamic leverage bounds (1x–3x, linear mapping only after calibration);
- shared risk reservation, combined-equity 1% margin rule, gross exposure and Kill Switch.

Missing calibration, invalid confidence, out-of-domain confidence, leverage outside 1x–3x, or provenance failure rejects AI ENTRY/DCA. No live execution path is permitted.

## Implementation sequence

1. Add schema/parser and RED tests for the V1 label/direction/feature contract.
2. Implement strict validation and GREEN tests without choosing unapproved horizon or threshold values.
3. Extend the real FreqAI feature matrix to include H1 and prove the actual fit/inference matrices contain H1 features; add tests for closed/available H1 alignment.
4. Define and seal the new model's horizon, price basis, thresholds, purge/embargo and split protocol from training/validation design evidence.
5. Bind the contract and feature schema into the signed manifest and semantic leakage validator.
6. Only after those gates pass, consider an explicitly authorized offline training/backtest run. Calibration/OOS certification remains a separate gate.

## Current status

- Regression-to-Direction design: **SELECTED FOR V1 DESIGN**.
- H1 as an actual model feature: **SELECTED FOR V1 DESIGN**.
- Horizon, price basis, LONG/SHORT thresholds: **NOT SET / BLOCKED** pending training-only protocol design.
- Actual H1 fit/inference feature matrix: **NOT IMPLEMENTED / NOT VERIFIED**.
- Semantic label leakage validator: **NOT IMPLEMENTED**.
- Independent model artifact/training run/OOS predictions: **NOT PROVIDED**.
- Calibration and AI leverage authorization: **NOT ISSUED**.
- Paper runtime integration: **NOT AUTHORIZED / NOT IMPLEMENTED**.
- Live execution: **DISABLED** (`AI_EXECUTION_ENABLED=false`).

## Evidence inspected

- `freqai_bridge/ChartProFreqaiResearch.py` blob `0ddaabca32e678bd1c6e181146c2f1418941c133`.
- `freqai_bridge/config.research.json` blob `a777e018f457628150647064119435ce75dc3e29`.
- `freqai_bridge/exporter.py` blob `3b707174316d0c6b464ac947cbbe2d2fbee73682`.
- `quant_system/native_prediction_capture.py` blob `f92cae5ef041c4094225292854e9ade5f0ba5339`.
- `quant_system/native_research.py` blob `519e6acf861ad25ea7f8265c1631139863322421`.
- Discovery report `quant_system/T2_AI_TRAINING_LABEL_CONTRACT_DISCOVERY_2026-11-08.md` blob `97dea4f8f0248688d42b018673153601aa09a4f1`.

No code, tests, training, market data, T0/T1 runtime, paper runtime, or exchange services were changed or run in this increment.
