# Phase19 — original sealed native prediction reconciliation (historical only)

## Evidence and reason for Phase19

Phase18 Codemagic result in user-uploaded
`btcusdt-telegram-signals2_1_artifacts (6).zip`:
10/10 regression tests, 24/24 historical shadow witnesses,
23 accepted and 1 rejected forecast,
`historical_frozen_prefix_invariance_verified=true`,
`errors=[]`. This is NOT original-native predictor parity or OOS certification.

The 12.6 MB Phase16 all-fold archive deliberately keeps ONLY
52 FIT_TRAIN/FIT_TEST NPZ matrices; it **cannot** certify native PREDICT
features. Phase19 therefore requires **the separately SHA-pinned ORIGINAL
Phase14 evidence archive**, already stored in the repository:

`research_evidence/phase14-frozen-original-evidence.zip`

Expected SHA256:
`b64f39bd70c27c8d6abed1795ee06504c108eed42ebdab98ce375a6449b5b035`.

This Phase14 archive was designed for the original final-fold PREDICT
NPZ, frozen-model and native forecast review. Never claim a missing
PREDICT witness was reconstructed from FIT matrices or invented data.

## Exact historical parity checks

The Phase19 read-only auditor verifies:

1. ZIP byte hash and Git original source `082edc082996425f61f48c952be41fb037564103`.
2. Original pre-holdout SHA seal commit
   `888efb11b613b42a2badb3bc8adfa19ff090f2bb`
   and research approval
   `409d446bb186a8e2ea0189df26057a9df7e839de`.
3. Full native matrix ledger, native FreqAI prediction CSV and sealed model
   identity, all checked against their original SHA fingerprints.
4. For **all rows of the last original PREDICT model fold**, exact candle
   identities and original native LightGBM X matrix from NPZ, FreqAI
   DataSieve acceptance flags, model prediction and inverse-scaled
   captured native forecast. All timestamp, field order, reject/accept and
   predicted-return mismatches fail closed, with the first failing timestamp.
5. Only original historical closed-candle M15 data; no holdout reads,
   online exchange access, retraining, self-updating model, trade orders
   or change in CORE/AI/risk thresholds.

The report is saved to
`artifacts/phase19/report/phase19-native-forecast-reconciliation.json`.
Accept a PASS **only** if
`native_last_fold_prediction_reconciled=true`,
`original_last_fold_native_predict_x_verified=true`,
`original_last_fold_native_forecasts_verified=true`,
`errors=[]` and all original last-fold PREDICT rows are present.
Do not set full pipeline/OOS certification flags based on last-fold parity.

## How to run

Repository: `kenznguyen/btcusdt-telegram-signals2`

Branch:
`feature/dual-strategy-phase19-native-forecast-reconciliation-20261031`

Manual Codemagic workflow:
`dual-strategy-phase19-native-forecast-reconciliation`.

This workflow preflights the archive and release SHA, executes isolated
contract regressions, installs pinned FreqAI CPU dependencies, then
replays the original *last fold* once. No GitHub Actions execution.

This investigation does **not** extend the observed 26-fold fit-time
audit to independently certified OOS, Kotlin parity, funding, mark,
liquidation, venue fills or 360d performance. Keep PR Draft, model
bytes/protocol/Shared Risk fixed and real orders disabled. The original
prospective OOS remains **2026-11-04T00:00:00Z through
2026-12-04T00:00:00Z** with no retraining, no holdout-driven tuning and
no evaluation prior to the complete end timestamp.
