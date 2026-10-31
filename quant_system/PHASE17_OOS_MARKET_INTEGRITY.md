# Phase 17 — pre-holdout OHLCV integrity, PAPER ONLY

This change is stacked on Phase16 Draft PR #86. It does not modify the
pre-registered November 4–December 4, 2026 UTC OOS window, original model
candidate SHA, DataSieve or label scaler, CORE thresholds, AI thresholds,
Shared Risk limits, Android APK or any release signing asset.

## Finding / fix

The original Phase16 runner validated complete closed-candle timebases and
OHLC aggregation across the *holdout*, but not aggregate **volume**, and
did not reconcile the overlapping prehistory H1/M15 candles. That allows
individually valid historical CSVs to contain different market observations
while continuing to paper replay. Phase17 fails closed before the frozen
model loads or a portfolio receives any candles.

The new pure function
`quant_system.phase17_oos_ohlcv.verify_oos_ohlcv_integrity`
checks:

1. 5m -> M15 OPEN/HIGH/LOW/CLOSE/**summed volume**, with exact timestamps.
2. M15 -> H1 OPEN/HIGH/LOW/CLOSE/**summed volume**, with exact timestamps.
3. Exactly the overlapping final **32 H1 historical warmup bars** against
   all **128 M15 historical warmup bars**, before the OOS boundary.

The pre-registered 100-bar H1 warmup intentionally contains 68 earlier H1
bars not covered by the 128 M15 historical candles; this fix does not
pretend to independently verify their OHLCV provenance. Both entire
prehistory series still must pass the existing contiguous, closed UTC
checks. The floating-point comparison tolerance matches the existing
Phase16 OHLC comparator; no interpolation or imputed volume is allowed.

A mismatch sets a descriptive `OOSContractError`, prevents FreqAI
inference and all three paper portfolios, and leaves OOS certification and
real trading disabled.

## TDD evidence

A first RED run of 7 tests failed because the new guard did not exist.
After implementing it, all 7 focused tests passed locally with Python
stdlib unittest. This does not establish a native Codemagic build success,
real OKX holdout availability, frozen model prediction parity, funding,
mark price, liquidation, exchange fills or independent OOS certification.

## Codemagic manual-only verification

Branch:
`feature/dual-strategy-phase17-oos-ohlcv-integrity-20261031`

Run **only** `dual-strategy-phase17-preholdout-ohlcv` now. It executes
`python3 -m unittest quant_system.test_phase17_oos_ohlcv -v`, then
compiles the standalone verifier and exports a test log. It has no
auto-trigger, market download, AI training, model loads or order actions.

After **2026-12-04 00:00 UTC**, the existing separate
`dual-strategy-frozen-30d-oos` workflow may be considered only with
pre-registered research-only approval commit
`409d446bb186a8e2ea0189df26057a9df7e839de`, exact SHA-sealed
model/protocol, and authentic completed prehistory + holdout. Its test
suite now includes the Phase17 regressions. If genuine multi-timeframe
records disagree, fail closed and investigate source provenance; **do not**
silently alter this fixed holdout or strategy parameters to force a pass.

All existing OOS / 360-day / promotion / real-orders certification flags
remain false pending separate independent evidence.
