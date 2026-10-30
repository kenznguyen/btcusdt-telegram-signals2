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

## 2026-10-31 — native FreqAI 0 accepted forecast diagnosis

The first Phase12 Codemagic native research run returned **exit 0 for both
CORE and FreqAI**, but `prediction_capture_verified=false` with
`NO_ACCEPTED_NATIVE_FREQAI_FORECASTS`. The 180-day OKX input had a different
checksum from the previous Phase11 run. This alone neither establishes a
label purge failure nor permits acceptance of neutral forecasts.

Pinned upstream FreqAI 2026.9 can **catch train() exceptions**, append
synthetic *neutral* backtest rows with `do_predict=0`, and still return
native exit code 0. In the original Phase12 code, an exception during
postfit observational row matching could discard an otherwise trained
model in that upstream exception handler.

Phase12 now isolates the observation AFTER the actual LightGBM `fit()`.
When observation fails it records one row in
`native/phase12-fit-observer-errors.jsonl` per affected fold, including
exception type and code, but returns the exact already-fitted booster to
FreqAI. This is NOT a downgrade of the verification gates:
- `native-research-180.json` always records native `do_predict` counts
  and the observer-error count/examples; native still fails when accepted
  forecasts are zero, and includes native log tail.
- `phase12-native-fit-label-audit.json` **rejects every nonzero observer
  failure count** with `PHASE12_FIT_OBSERVER_REPORTED_ERROR` and still
  requires row SHA, exact labels and purged boundaries.
- Neutral `do_predict=0` rows cannot become entries. No metadata-only
  approval or synthetic predictions are permitted.
- The original FreqAI and CORE strategy rules and risk policy are unchanged.

If the next Codemagic build still produces zero accepted forecasts,
inspect `prediction_do_predict_distribution`,
`phase12_observer_failure_examples` and `freqai_training_log_tail` in
`native-research-180.json`, plus the original full
`native/freqai-native-180.log`; do not change `DI_threshold` or any
signals to force acceptance. If FreqAI restores real predictions but
the postfit mapping fails, the Phase12 audit correctly blocks and the
row-index linkage must be repaired using the native observed evidence.

## Root cause found from native Codemagic ZIP (Phase12 26/26 observer failures)

An uploaded 180-day OKX Codemagic research archive (source SHA
`d6f176e436cc4ddd5aa8f3faff63a897e69ba6ce`) contained:
- `phase12_observer_failure_count=26`, unique 26 folds, all
  `PHASE12_FIT_INDEX_IDENTITY_UNVERIFIED`.
- 17,103 real accepted forecasts (`do_predict=1`), 3,122 neutral;
  successful native FreqAI/CORE and passed Phase8–11 audits.
- An otherwise empty `freqai-native-training-samples.csv` did not exist.
- Observer errors, prediction CSV and booster lineage all matched SHA-256
  checksums inside the same native report.

Confirmed mechanical cause: pinned FreqAI 2026.9 `dk.filter_features()`
retains original source row indices in `dk.train_dates`. The DataSieve
`Pipeline._convert_back_to_df()` reconstructs the transformed model X/y
as fresh pandas DataFrames with `RangeIndex(0..N-1)`. The former Phase12
observer incorrectly demanded that post-transform fit X/y indices matched
the original `dk.train_dates` indices. They are not the same provenance
domain. This is a **bug in research instrumentation**, not proof of
label leakage, not a change in live order risk, and not grounds for
manually promoting `ready_for_360`.

Patch: `phase12_sample_identity.resolve_fit_row_ids` reconstructs the
**approved, chronological** 20% test split from the filtered FreqAI
`train_dates`; checks that actual post-fit TRAIN rows preserve full length;
derives TEST selection from the real fitted DissimilarityIndex validation
mask; rejects extra or missing rows and unknown feature pipelines. For
every real TRAIN/TEST label delivered to LightGBM, it inverse-transforms
the model's actual scaled y and checks 1:1 against the original raw label,
in order. This allows DataSieve's reset index without ignoring lost,
reordered, or unaccounted-for rows. Raw labels are independently
reconstructed from canonical BTCUSDT OKX `close[t+4]/close[t]-1` in the
separate Phase12 audit.

Unit regressions cover reset-index mapping, genuine DI filtering,
scaled-label inversion, shuffled fit labels, DI-mask tamper, changed
feature preprocessing, sample-count mismatch and unapproved split.
Full Codemagic unit/native validation remains pending. The native
research input's OHLCV may differ between runs; compare exact dataset
hashes in every artifact before claiming parity.

### Next failure to assess independently

Once each original fit row is correctly traced, Phase12 may reveal that
the current FreqAI 20% validation split does **not** purge four M15 candles
at the train/test boundary. If `TRAIN_TEST_LABEL_HORIZON_NOT_PURGED`
occurs, keep that as a legitimate failed independent audit and implement
a separate chronological label-horizon purge under new tests **without
changing strategy thresholds, paper risk sizing or live enablement**.
