# Phase 12 — observed LightGBM fit rows, 4-candle labels and purge audit

**Research only; no order execution and no model OOS certification.**

## Why Phase 8/11 were insufficient

Phase 8 linked 26 in-memory booster fingerprints to 17,103 accepted native
FreqAI forecasts on the uploaded 180-day OKX run. That verified the model
identity at prediction time, but not which feature rows or future-return labels
the model used. Phase 11 verified one genuine CORE SHORT versus FreqAI LONG
same-candle source conflict; that did not test the training sample selection.

This phase intercepts the **actual 2026.9 LightGBMRegressor.fit() call** after
FreqAI's `filter_features`, `train_test_split`, feature pipeline and label
pipeline have selected the final data dictionaries. It records final
`train_features` and `test_features` row indices, joins them to
`dk.train_dates` and the original filtered candle/target, checks that the
fitted model hash matches the Phase 8 prediction trace and emits the following
per sample:

- `fold_model_name`, `model_identifier`, `model_sha256`
- `row_kind`: TRAIN or TEST (FreqAI validation set used in LightGBM eval)
- `feature_open_ms`, `label_end_ms`, training fold end and 4-candle horizon
- `observed_raw_label`, `expected_recomputed_label`, feature/future close

The native run stores `phase12_training_samples_sha256` in
`native-research-180.json`; the independent audit re-reads the exact sample
CSV, Phase 8 model trace, canonical OKX M15 closes and previously passed
Phase 8 and 11 reports. Every raw label must equal the independently
reconstructed `close[t+4*15m]/close[t] - 1`. All label end timestamps must
precede the model train cutoff and its first prediction.

**Crucial chronological boundary:** latest TRAIN sample's `t+4` label
candle must be **strictly earlier** than the earliest TEST feature candle.
The existing pinned FreqAI configuration has chronological
`test_size=0.2, shuffle=false` but no explicit 4-candle purge at that split.
A run may therefore correctly **FAIL** with
`TRAIN_TEST_LABEL_HORIZON_NOT_PURGED`. A failure is useful evidence and must
not be bypassed, reclassified as success or used to change trading thresholds.

## Artifacts and manual Codemagic

Branch: `feature/dual-strategy-phase12-actual-fit-label-purge-20261031`

Run `dual-strategy-phase3-unit` and then, only if it passes, the manual
`dual-strategy-phase3-native-research` with:
`PHASE3_DAYS=180`, `PHASE3_DETAIL_MINUTES=5`,
`PHASE3_DOWNLOAD_DAYS=220`.

Files under `artifacts/phase3`:
- `native/freqai-native-training-samples.csv`
- `native/native-research-180.json` (new training sample SHA)
- `paper/phase12-native-fit-label-audit.json`
- `paper/phase12-native-fit-label-audit.log`

The Codemagic Phase12 step exits nonzero for missing fit samples, model
hash/ID mismatches, duplicate/unmapped train/test indices, wrong labels,
noncausal label timestamps or unpurged label overlap. Preserve diagnostics.

## Explicit limitations

This does **not** independently prove that every feature is causal, that
the train/test partition is independent walk-forward OOS, that the LightGBM
model generalizes, that all 26 folds are independent or that a live exchange
can run three distinct positions on one BTCUSDT pair. A FreqAI validation
set passed as `eval_set` is not independent untouched OOS.

The fail-closed audit never sets `oos_certified`, `ai_promotion_eligible`,
`ready_for_360`, `full_core_parity_certified` or
`live_orders_enabled` to true.

Keep CORE RSI + ADX + Smart DCA unchanged, three virtual DUAL slots with
max two AI-origin positions, entry margin 10% current equity, max total
margin 60%, 13x leverage, one DCA per position, independent SL/TP, no
live order execution. Keep Android release, signing keys and main unchanged.
