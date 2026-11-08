# T2 Independent AI Training Pipeline and Label Contract Discovery — 2026-11-08

## Scope

Read-only inspection of the existing FreqAI bridge, native research runner, data import contract, and frozen Phase22 research line. This increment does not install dependencies, run Freqtrade, access market databases/T0, train or infer a model, run backtests, access exchange endpoints, or enable any runtime.

## Candidate pipeline found

The repository contains a separate research pipeline candidate:
- Strategy: `freqai_bridge/ChartProFreqaiResearch.py`, blob `0ddaabca32e678bd1c6e181146c2f1418941c133`.
- Binance research config: `freqai_bridge/config.research.json`, blob `a777e018f457628150647064119435ce75dc3e29`.
- Native runner: `quant_system/native_research.py`, blob `519e6acf861ad25ea7f8265c1631139863322421`.
- Native prediction capture: `quant_system/native_prediction_capture.py`, blob `f92cae5ef041c4094225292854e9ade5f0ba5339`.
- FreqAI exporter: `freqai_bridge/exporter.py`, blob `3b707174316d0c6b464ac947cbbe2d2fbee73682`.
- Native dataset importer: `quant_system/native_dataset.py`, blob `fb08bcd9ab9f8623d50711641a6f3b6d201d2d0f`.

The Binance research config uses model family identifier `chart-pro-shadow-v1`, BTC/USDT perpetual, M15, LightGBMRegressor, 30-day train window, 7-day backtest window, 20% chronological non-shuffled internal split, and `label_period_candles=4`. Its target in the strategy is `close.shift(-horizon) / close - 1`, exposed as `&-future_return`.

This candidate is distinct in name and venue/config from the frozen legacy Phase22 model `chart-pro-okx-shadow-v1`; however, a different identifier alone does not prove a distinct immutable trained artifact or training lineage.

## What the code actually establishes

1. The strategy's current target is a scalar future return, not explicit LONG/SHORT labels or calibrated class probabilities.
2. The native capture stores actual FreqAI `predicted_return`, `do_predict`, model identifier, pair and candle OHLCV. It explicitly describes itself as a trace, not a signed training-cutoff/OOS certificate.
3. The bridge publishes `predictedReturn` only when FreqAI accepts the prediction. It requires a trainer-provided provenance sidecar with modelVersion, strategyVersion, trainingDatasetVersion, trainedThroughMs and trainingCompletedAtMs. The code does not fabricate these fields.
4. The README explicitly states model files and exchange credentials are not bundled; example commands do not prove that training was run or that a model artifact exists.
5. The native research runner can invoke offline Freqtrade backtesting with FreqAI and captures actual predictions for its historical OKX path. It sets `freqai_oos_verified=false` and `native_orders_enabled=false`; prediction capture is not an OOS certification.
6. The research config currently includes `initial_state=running` and periodic retraining settings. Do not start this config as a service. The documented offline backtest command is a different execution path, but no run is authorized in this audit.

## Contract gaps for Dual-Strategy Intelligence

| Required contract | Existing evidence | Disposition |
|---|---|---|
| Independent model ID | `chart-pro-shadow-v1` in Binance config | Candidate only; immutable artifact/version not evidenced |
| Venue/market | Binance USDT perpetual in config and exporter | Source-declared; actual dataset/run lineage not provided |
| Timeframe | M15 | Declared |
| Feature schema | M15 features: relative price/volume, pct change, raw volume, weekday/hour, shifted features | Source-level only; no new independent training run/fit matrix |
| H1 context | No H1 feature timeframe in Binance FreqAI config | MISSING if the new AI contract requires H1 features |
| Target | Four-candle forward close return | Source-declared legacy candidate target; not approved for new AI |
| LONG/SHORT mapping | No threshold, deadband, abstention band or side mapping in this model code | NOT DEFINED |
| Confidence/probability | Scalar regression output only | NOT DEFINED; cannot feed calibrated confidence directly |
| Price basis | Candle close-to-close in strategy source | Declared close basis; exact venue candle semantics and outcome resolution contract not independently sealed |
| Label end/availability | Implied by 4 M15 bars in code/config | Needs explicit UTC open/close and outcome availability semantics in signed protocol |
| Train/validation/OOS | Internal 20% chronological split in config | Not an independent prospective OOS protocol |
| Purge/embargo | No independent AI-specific signed split protocol in this candidate | NOT DEFINED / NOT VERIFIED |
| Training lineage | Required sidecar fields are documented/consumed | Actual sidecar, model bytes, fit logs and signed manifest not provided |
| Calibration | Existing evaluator can assess prediction rows after strict provenance validation | No actual accepted OOS prediction set |

## Key architecture finding

The existing `chart-pro-shadow-v1` pipeline is a plausible research starting point, but it is **not yet an admissible AI Strategy model**:
- It predicts a scalar return, while the Dual Strategy contract requires independent LONG/SHORT intents. A directional mapping cannot be inferred from the sign alone without a pre-registered threshold, no-trade band, and outcome/side semantics.
- It does not currently declare H1 as a FreqAI feature timeframe. The signed prediction validator currently requires M15 and H1 feature cutoffs; this is stricter than the model's visible M15-only feature schema and needs a deliberate, consistent model contract.
- Its four-candle horizon is code/config evidence for this candidate only, not user-approved for the new AI strategy.
- There is no actual model artifact, training run, trainer-generated provenance sidecar, signed split protocol, or actual OOS predictions in the inspected source evidence.

## Recommendation

Keep the independent-model architecture decision. Treat `chart-pro-shadow-v1` as an **unaccepted candidate**, not as an already existing approved AI model.

Before writing the semantic leakage validator, make one explicit model-contract choice:
- **Regression-to-direction:** retain scalar future-return prediction, but pre-register the label horizon, price basis, outcome availability, LONG/SHORT thresholds, neutral/abstention band and confidence derivation; or
- **Direct directional model:** define a class/target contract for LONG/SHORT/ABSTAIN and the corresponding probability/calibration semantics.

Do not choose thresholds, horizon, or class boundaries from the OOS holdout. Derive them from a training-only design and seal the protocol before OOS observations are consumed. Also decide whether H1 is a required model feature or only a separately recorded contextual cutoff; do not claim model consumption of H1 if it is not in the actual feature matrix.

## Status

- Existing candidate research code identified: **PASS**.
- Independent AI model identity/artifact: **NOT VERIFIED**.
- Actual training run and trainer provenance sidecar: **NOT PROVIDED / NOT VERIFIED**.
- LONG/SHORT mapping and confidence semantics: **NOT DEFINED**.
- H1 feature-consumption contract: **NOT DEFINED**.
- Label horizon/price basis/outcome availability for the new AI Strategy: **NOT APPROVED**.
- Signed split/purge/embargo and semantic OOS leakage: **BLOCKED**.
- Calibration attestation / AI leverage authorization: **NOT ISSUED**.
- Runtime integration: **NOT IMPLEMENTED**.
- `AI_EXECUTION_ENABLED=false`; no T0/T1 DB/feeder/exchange, paper or live runtime touched.

## Next step

Approve one of the two target semantics (regression-to-direction or direct directional classification) and define whether H1 is part of the AI feature matrix. Then implement a versioned label/decision contract and bind its hashes to the signed manifest with RED tests. No model training, OOS access, or runtime activation in this increment.
