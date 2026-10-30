# Phase 6 — evidence readiness / 30-day research cohorts (paper-only)

This is NOT a new trading strategy, FreqAI training run, OOS certificate,
360-day backtest, or permission to execute orders.

The input is the completed Phase 4 and Phase 5 180-day OKX research dataset
and actual FreqAI native log. Strategy Core (RSI + ADX + Smart DCA) remains
unchanged; AI independently emits LONG/SHORT candidates in the paper replay
and all paper entries still pass the shared risk admission checks.

## What the audit checks

- Requires Phase 4's independently verified SHA-256 of the paper summary,
  three trade files and three event files; requires successful Phase 5 report.
- Requires native CORE/FreqAI *runtime* success but no native trade parity claims.
- Reads 26 observed 30-day rolling FreqAI training windows from the native
  log (retrained approximately every 7 days in the October 30 evidence).
  Rejects missing, out-of-order, future or incomplete log windows.
- Splits **closed paper trades** into six calendar-aligned 30-day research
  cohorts, based on each trade's entry timestamp, for CORE_ONLY, AI_ONLY,
  and DUAL. These are **descriptive entry cohorts**, NOT independent
  model walk-forward folds, because no individual prediction is linked to
  its exact trained model and label boundary.
- Verifies closed trade net PnL, immediately charged entry fees on still-open
  positions, and strategy-level realized net PnL. The report reconciles
  fees of open positions separately instead of treating them as losses.
- Surfaces negative AI_ONLY / DUAL paper PnL and displacement of CORE entries.

## State that must remain locked

`research_report_verified=true` only means audited files are internally
consistent. Always emit `oos_certified=false`,
`ai_promotion_eligible=false`, `ready_for_360=false`,
`full_core_parity_certified=false`, and `live_orders_enabled=false`.

Required *future* evidence before any promotion:
1. Exact prediction timestamp -> model build ID -> feature cutoff and
   purged label horizon, with disjoint train/test boundaries.
2. Strictly chronological, leakage-resistant independent model OOS
   performance with fees/funding and untouched held-out data.
3. Independent Kotlin / native Freqtrade trade-bearing parity for entries,
   DCA, TP, Soft SL, Emergency SL and detailed fill assumptions.
4. Complete funding, mark-price / maintenance margin / liquidation
   analysis and explicit operator approval.

## Codemagic execution

Branch: `feature/dual-strategy-phase6-oos-readiness-20261030`.

Run `dual-strategy-phase3-unit` first. Then manually run
`dual-strategy-phase3-native-research` with:
- `PHASE3_DAYS=180`
- `PHASE3_DETAIL_MINUTES=5`
- `PHASE3_DOWNLOAD_DAYS=220`

The manual research workflow still runs Phase 4 and Phase 5 first, then
writes `artifacts/phase3/paper/phase6-research-readiness.json`.

To audit an existing matching artifacts directory without downloading again:

```bash
python3 -m quant_system.phase6_readiness \
  --artifacts-root artifacts/phase3 \
  --out artifacts/phase3/paper/phase6-research-readiness.json
```

**Earlier uploaded 180-day evidence (not a new Codemagic execution):**
CORE_ONLY +147.19 USDT, AI_ONLY -95.10 USDT, DUAL -95.04 USDT realized
ex funding; 26 training windows observed; 21 CORE_ONLY decisions coincided
with an already occupied AI position in DUAL. Native Freqtrade strategies
executed zero orders by design. Do not use these numbers as an exchange
fill or predictive accuracy claim.

Never merge a draft PR or release an APK without separate verification.
