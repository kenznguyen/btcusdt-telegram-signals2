# Phase 13 — Independent OOS & Feature Causality Audit (PAPER ONLY)

Branch: `feature/dual-strategy-phase13-oos-feature-causality-20261031`,
stacked on Phase 12 PR #81. **No main merge, no native entry, no Android changes.**

## Already established by 180d Phase12 artifacts

- 26 native LightGBM model folds, 4-closed-M15-bar label horizon, no
  TRAIN/validation label overlap after the Phase12 prefit purge.
- Real 180d CORE/AI/DUAL paper signals and 5m modeled fills are historical
  DEVELOPMENT RESEARCH. The historic dataset and its reported results were
  already inspected. It **cannot be rebranded an untouched independent holdout**.
- AI-only and DUAL equity paths show marked 30d regime instability.
- Funding/mark coverage, liquidation, exchange execution and native/Kotlin
  trade parity are NOT certified.

## Three explicit Phase13 evidence tracks

1. **Source-level future-candle perturbation**:
   `python -m quant_system.phase13_feature_causality`.
   Load real SHA-bound, closed OKX 15m candles. Use the **actual strategy's**
   `feature_engineering_expand_all` at periods 14/28,
   `feature_engineering_expand_basic`, and
   `feature_engineering_standard`, plus positive lag 1/2.
   Require all **20 supported feature columns**, finite values, strict
   timestamp continuity, and unchanged values on the last known closed
   candle across many prefix-vs-full recomputations. A future `shift(-1)`,
   centered rolling calculation, back-fill or unexpected new feature must
   be rejected. This check deliberately does NOT certify the fitted model's
   exact full DataSieve feature matrix, scalers or any outside source.
   TARGET `close.shift(-4)/close-1` is a FUTURE LABEL, never a feature.
2. **Model-SHA-linked native forecast quality**:
   `python -m quant_system.phase13_forecast_quality`.
   Match every accepted native prediction to its actual Phase8 model SHA,
   model training timestamp and latest observed label end. Recompute
   realized forward 4-M15 return from canonical `close[t+4]/close[t]-1`.
   Output 6 consecutive 30d directional accuracy, MAE, RMSE and Pearson
   correlation. Last history-edge forecasts with no outcome are **excluded
   with an explicit count**, not fabricated.
3. **6 x 30d retrospective risk stability**:
   `python -m quant_system.phase13_oos_stability`.
   SHA-bind canonical source, Phase12 evidence, native dataset and all
   three modelled equity curves to their run reports. Recompute complete
   (including open position MTM) equity period returns, max drawdown,
   negative-window counts and whole-span max drawdown.

Codemagic test order: `dual-strategy-phase3-unit`, then manual
`dual-strategy-phase3-native-research` with
`PHASE3_DAYS=180`, `PHASE3_DETAIL_MINUTES=5`,
`PHASE3_DOWNLOAD_DAYS=220`. New Phase13 diagnostic artifacts:
`paper/phase13-feature-causality.json`,
`paper/phase13-native-forecast-quality.json`,
`paper/phase13-retrospective-stability.json`.
A successful diagnostic command does NOT mean independent OOS certified.
If any input SHA, feature prefix, model lineage or equity trace fails, the
specific command returns a nonzero exit and keeps gates false.

## Formal independent OOS promotion gate (NOT yet implemented or satisfied)

A separate pre-registered, **previously untouched** 30-day chronological
holdout must be acquired **after** the known development artifact's end
(2026-10-30 20:15 UTC). The holdout must be disjoint from ALL model/feature
selection and parameter tuning. Before its first candle:

- Freeze the strategy + feature-source SHA, training code/runtime versions,
  label horizon, fees, slippage, risk limits, AI decision thresholds, data
  venue, candidate selection and evaluation criteria in a signed/hashed
  manifest. Record its timestamp before holdout data collection.
- Freeze a genuinely trained model artifact at or before the boundary
  (or predeclare walk-forward retraining explicitly as a different protocol).
  Every train label end and every preprocessing/scaler fit data timestamp
  must be earlier than the allowable training cutoff; holdout rows cannot
  be used to learn model parameters if claiming a frozen-model holdout.
- Capture **actual fitted/predicted feature matrices**, component-wise
  preprocessing provenance, and all outlier/normalization transforms;
  independently replay prefix-changed future candles and verify the
  already-issued inference features/predictions are invariant.
- Re-run CORE_ONLY, AI_ONLY, DUAL under identical new venue candles, a
  common paper fill model, costs, funding assumptions and Shared Risk.
  Reconcile every position and measure path-dependent equity, drawdown,
  exposure, liquidation and regime stability. No parameter changes after
  looking at holdout performance; any changes restart the protocol.
- Require independent review and explicit acceptance; Phase12 label purge
  alone is insufficient. **Current flags remain**:
  `independent_oos_verified=false`, `oos_certified=false`,
  `ai_promotion_eligible=false`, `ready_for_360=false`,
  `full_core_parity_certified=false`, `live_orders_enabled=false`.

No real trading or 360-day certification is authorized by Phase13 diagnostics.
