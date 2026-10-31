# Phase16: all 26 historical fitting-time folds & fixed prospective OOS

This is a research-only, no-order, manual Codemagic workflow. GitHub stores
source and historical evidence. Codemagic performs native FreqAI checks.

## Original evidence — exact immutable 26-fold dataset

Upload the file `phase16-all-26-original-fit-evidence.zip` unchanged to
`research_evidence/phase16-all-26-original-fit-evidence.zip` on the Phase16 branch.
SHA256 MUST equal:

`0e76c0851ba3ffeac2706d681efee4ea034998d70eb8e183ede11e01306e8bc7`

The ZIP is 12,641,658 bytes and contains exactly 52 original
FIT_TRAIN/FIT_TEST NPZ archives out of the historic 78-event ledger.
All 52 per-archive SHA-256 values match the original Phase13B event ledger.
It also preserves source model commit, original 15m closed candles,
59,696 TRAIN + 14,825 VALIDATION source sample rows, original fitted
candidate, candidate metadata, native-research report and Phase13B audit.
The 26 PREDICT NPZ archives were deliberately excluded as unrelated
to FIT-time X/y/w; their existing SHA metadata remains in the ledger.

Run the manual Codemagic workflow:
`dual-strategy-phase16-all-26-original-fit`.

The gate checks each fold's identity, chronological/label-horizon purge,
source raw OHLCV, fresh FreqAI DataSieve + label scaler fit ONLY to
historical TRAIN samples, exact original native LightGBM FIT_TRAIN and
FIT_TEST X/y/weights including row order, future-only raw market OHLCV
intervention and positive controls that mutate actual eligible TRAIN
volume and label. No LightGBM retraining or replacement model.
Any missing fold or X/y/weight mismatch fails closed and reports its name.

Success is **not yet observed**; do not mark a PASS until the real
Codemagic report contains 26 folds, 59,696 TRAIN and 14,825 VALIDATION
rows and has `all_26_folds_fitting_time_verified=true`, `errors=[]`.

## Immutable OOS protocol — UNCHANGED

- Venue: OKX BTC/USDT:USDT USDT perpetual, paper-only.
- Start: **2026-11-04 00:00:00 UTC**.
- End: **2026-12-04 00:00:00 UTC**.
- Exact 2,880 closed M15, 720 H1, 8,640 5m holdout candles.
- Additional immediately preceding, strictly closed feature-only prehistory:
  exactly 128 M15 candles and 100 H1 candles.
- The original joblib SHA-256 remains
  `918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f`.
- Source Git commit remains
  `082edc082996425f61f48c952be41fb037564103`.
- Protocol and metadata hashes remain in the original pre-holdout
  Git SHA seal commit `888efb11b613b42a2badb3bc8adfa19ff090f2bb`.
- **Never call FreqAI train/fit** on the holdout. Fixed model and
  fitted DataSieve/label scaler are applied once per CLOSED candle,
  using only the prefix ending at that candle.
- The original CORE RSI+ADX+Smart DCA and Shared Risk admission stay
  unchanged. `CORE_ONLY`, `AI_ONLY` and `DUAL` are simulated on the
  same 5m/15m/1h data, leverage 13x, entry margin 10% equity,
  margin cap 60%, at most 3 positions, at most 2 AI slots in DUAL,
  DCA once, fees 0.05% per side, no live orders.
- Existing `paper_portfolio.replay_portfolio` is used with an
  explicitly allowed `freqai-frozen-oos` source tag; existing native
  backtests still default to `freqai-native-backtest`.

## Deliberately locked OOS manual workflow

Workflow name: `dual-strategy-frozen-30d-oos`.

It MUST refuse to run until **after 2026-12-04 00:00 UTC**, and unless
an independent review registers a separate SHA-pinned, pre-holdout Git
approval commit for the exact 26-fold report:

`research_seals/phase13b-20261104/phase16-all26-original-fit-audit.json`
and `research_seals/phase13b-20261104/phase16-oos-release-gate.json`.

The review was successfully recorded on 2026-10-31 UTC. The
independent SHA summary of the original Codemagic 26/26 native report was
committed as `0978727223c528d941bf3005362c4e494df89d2d`.
The pre-holdout **research-only** approval gate was committed as
`409d446bb186a8e2ea0189df26057a9df7e839de`.
GitHub server timestamps are 2026-10-31T02:09:59Z and
2026-10-31T02:10:30Z, both before OOS start.

The workflow's `PHASE16_APPROVAL_COMMIT` is pinned to exactly
`409d446bb186a8e2ea0189df26057a9df7e839de` and rejects any
replacement. Approval is only for the **future manual frozen paper replay**.
It is NOT OOS certification, AI promotion or authorization to place trades.
The external SHA review and original ZIP stay frozen; do not change model
hyperparameters, strategy or Shared Risk using holdout data.

After the full 30 days have elapsed, populate in repository:
`research_evidence/frozen-oos-20261104/holdout/{15m,1h,5m}.csv`,
`research_evidence/frozen-oos-20261104/prehistory/{15m,1h}.csv`.
All must be genuine OKX closed candles, with exact contiguous UTC
timestamps. Missing, duplicated, out-of-order or inconsistent cross-
timeframe prices cause failure. No interpolation/backfilling.

OOS output includes frozen forecast trace and paper trade/event/equity
CSV for all three strategy modes, plus SHA-linked reports.
**Funding/mark/liquidation and venue execution are NOT certified** by
OHLCV alone. The report deliberately keeps
`independent_oos_verified=false`, `oos_certified=false`,
`ai_promotion_eligible=false`, `ready_for_360=false`,
`live_orders_enabled=false` pending separate independent validation.
This is not a trading-profitability guarantee.
