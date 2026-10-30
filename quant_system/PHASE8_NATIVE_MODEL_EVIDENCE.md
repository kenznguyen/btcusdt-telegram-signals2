# Phase 8 — Native LightGBM fingerprints (experimental paper research)

Phase 7 used one constant FreqAI config identifier. Phase 8 captures a model-specific
SHA-256 fingerprint from the fitted LightGBM Booster inside the real native
predict() call, with timestamps and the observed available-label cutoff.

## Components

- freqai_bridge/ChartProAuditLightGBMRegressor.py subclasses pinned
  Freqtrade 2026.9 LightGBMRegressor; super().train and super().predict
  remain responsible for actual fitting and forecasting.
- The subclass records fold_model_name, in-memory Booster SHA, training window
  end, last available labeled feature candle, last observable forward label
  end, actual prediction open timestamp, configured horizon (4 M15 candles),
  and acceptance flag into native/freqai-native-model-lineage.csv.
- quant_system/phase8_model_evidence.py requires Phase 7 consistency and
  SHA-256 matching of the native prediction CSV. Every accepted forecast
  must have a same-timestamp FreqAI model lineage row; duplicate timestamps,
  missing model lineage, invalid SHA and noncausal label cutoffs fail closed.
- The model training boundary records an upper bound from the available
  labeled input. It does NOT attest exact fitted feature rows after NaN
  filtering, train/test splitting, or additional purge operations.

## Codemagic operator steps

Branch: feature/dual-strategy-phase8-native-model-fingerprints-20261031

Run dual-strategy-phase3-unit first. Then manually run
dual-strategy-phase3-native-research with PHASE3_DAYS=180,
PHASE3_DETAIL_MINUTES=5 and PHASE3_DOWNLOAD_DAYS=220.

Inspect native/freqai-native-model-lineage.csv and
paper/phase8-native-model-evidence.json within artifacts/phase3.
Failure of the bridge or a missing lineage is a FAIL, not certification.
Actual pinned FreqAI runtime compatibility has not yet been tested on
Codemagic for this new branch.

## Safety constraints

Native strategy places no orders. Do not change CORE RSI/ADX/Smart DCA,
Shared Risk, existing stop thresholds, Android APK or keystore.
Always keep OOS, purge verification, native trade parity, live and 360-day
certification false. No main merge and no APK release for this phase.

Next: independently check actual train/validation indices and label
horizon after feature filtering; then chronological model OOS,
Kotlin/Freqtrade trade parity, funding/mark/liquidation audits.
