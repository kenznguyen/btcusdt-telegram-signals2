# Phase 18 — historical-only fixed FreqAI inference shadow (no holdout)

This stacked **Draft** development phase follows Phase17 and the original
Phase16 26/26 fitting-time PASS. It exercises the exact SHA-pinned original
candidate and fitted DataSieve/label scaler on *already-known historical*
OKX M15 candles, not the 2026-11-04 to 2026-12-04 prospective holdout.

## Historical shadow specification

- Load the original Phase16 evidence ZIP unchanged. Require its exact SHA256:
  `0e76c0851ba3ffeac2706d681efee4ea034998d70eb8e183ede11e01306e8bc7`.
- Import the model **only after** checking its exact byte hash, the original
  independent Git seal `888efb11b613b42a2badb3bc8adfa19ff090f2bb`,
  source commit and original model identity.
- Never read a market candle whose open falls inside or after the
  2026-11-04 00:00 UTC holdout start, and verify all source candles are
  contiguous closed M15 with an aligned UTC timestamp.
- Select 24 distinct post-training timestamps on historical candles only,
  with adequate past warmup and at least three future historical candles
  available *solely* for negative leak interventions.
- For each witness, reconstruct the 20 pre-registered source features with
  the same `rebuilt_features()` source as Phase16, using (1) 160 historical
  candles, (2) 320 historical candles, (3) all historical candles up to
  three after the prediction timestamp, and (4) those same rows with the
  later three OHLCV candles deliberately perturbed. Verify raw features,
  ordered post-fitted DataSieve X, do_predict flag and reverse-scaled frozen
  forecast are unchanged for all four.
- Positive control: disturb volume of the *current* candle and demand the
  extracted raw feature row changes. A no-op intervention fails.
- Do not fit/train, update any parameter, promote AI, issue orders, or
  compare future holdout returns.

This is a **historical self-consistency check**. It is NOT an independent
reconstruction of all original native model prediction callbacks. The report
always retains `native_last_fold_prediction_reconciled=false`,
`independent_oos_verified=false`, `oos_certified=false`,
`ready_for_360=false` and `live_orders_enabled=false`.
In particular, the 26-fold training matrix audit does not imply future
inference parity or profitability.

## Manual Codemagic workflow

Branch: `feature/dual-strategy-phase18-historical-frozen-shadow-20261031`

Workflow: `dual-strategy-phase18-historical-frozen-shadow`

The job first runs 10 focused historical-only contract regressions, verifies
the original source evidence ZIP and approval/seal branch, then installs
the original pinned CPU FreqAI dependencies and reruns tests. Only then
does it load the sealed model and perform historical shadow replay.
Output is `artifacts/phase18/report/phase18-historical-shadow-audit.json`.
Success requires:
`historical_frozen_prefix_invariance_verified=true`,
at least 16 distinct post-training historical witnesses, at least one
accepted frozen forecast, and `errors=[]`.

No native Codemagic report for this new phase has yet been observed.
If the report fails, investigate the model/pipeline/feature mismatch without
altering the sealed OOS model or using the future holdout for tuning.

The **OOS workflow remains locked until 2026-12-04 00:00 UTC**, with
research-only preholdout authorization commit
`409d446bb186a8e2ea0189df26057a9df7e839de`.
CORE RSI/ADX/Smart DCA, 13x paper risk, three-slot 10% entry and 60%
margin cap, separate AI LONG/SHORT, Android APK/keystore and no-live-orders
policy remain unchanged.
