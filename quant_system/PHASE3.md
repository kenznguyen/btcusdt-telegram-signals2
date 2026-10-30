# Phase 3 — Dual-Strategy paper intent, Freqtrade/FreqAI runtime and historical gates

## Source and safety boundary

Phase 3 extends `feature/dual-strategy-phase2-20261030`. It does not change
`freqtrade_parity/rules.py`, any Kotlin StrategyEngine parameter, or the
FreqAI strategy's native entry controls. **No live exchange orders.**
Never merge into `main` or certify `full_core_parity_certified=true` on
the strength of these checks alone.

## 1. Atomic paper order handoff

Modules: `quant_system/paper_bridge.py`,
`paper_execution/ledger.py`, `quant_system/dual_strategy.py`.

- Use the **same durable SQLite file** for `ReservationLedger` and `PaperLedger`.
  This is a persistent volume, **not** Codemagic's temporary checkout.
- `PaperSignalCoordinator.evaluate(...)` emits a `PAPER_RESERVED` signal
  only after CORE/AI conflict arbitration and risk admission.
- `DualPaperBridge.execute(route, closed_m15, canonical_window, prediction,
  risk, hummingbot_book, now_ms)` revalidates candle, model provenance,
  strategy source, margin, no pending paper order, no open paper position,
  budget, and the observed order book before attempting submission.
- Account equity for this isolated paper engine is initial paper capital +
  realized paper PnL - booked paper fees, **not** mark-to-market equity;
  open positions and unverified balances block new entries. The paper
  capital is immutable for a given database.
- The old CORE margin policy is preserved: 50% of equity at 13x (subject to
  the existing paper maximum-position limit). RSI/ADX/DCA/TP/SL thresholds
  are unchanged. Model forecast magnitude is NOT passed off as probability.
- **Transaction A:** store a durable one-way attempt marker. If interrupted
  later, nobody can automatically retry that reservation.
- **Transaction B:** bind the exact paper intent ID **and** simulate/persist the
  paper order with one caller-owned SQLite `BEGIN IMMEDIATE` transaction.
  Either both commit, or neither does. This is possible only because the
  two ledgers share one database.
- A restart or duplicate callback sees the existing attempt marker / BOUND
  reservation and does not issue a second paper order.
- `recover(signal_id)` is read-only; `operator_cancel_unfilled` requires
  explicit evidence and refuses cancellation when any paper fill exists or
  an order remains active. Operator actions after a crash require independent
  inspection of the paper ledger.
- Paper fills are visible-depth **simulations**, not exchange fills.
  Native Freqtrade entries remain zero and `confirm_trade_entry=False`.

Important: the old `ReservationLedger.resolve()` method remains available
as a research primitive for Phase 2 unit tests. Production-facing workflows
should expose only the stricter Phase 3 reconciliation API. The Phase 3
bridge is **not yet** wired into a continuously running paper service, and
paper TP/SL/DCA lifecycle wiring is a remaining task.

## 2. One dataset for Freqtrade + FreqAI + Kotlin comparison

Codemagic `dual-strategy-phase3-native-research` is **manual only**.

The research workflow (with no exchange API credentials):

1. Installs pinned Freqtrade/FreqAI 2026.9.
2. Downloads public **OKX USDT perpetual futures** history using an isolated
   `freqai_bridge/config.okx-research.json`, including native mark/funding
   candles when the exchange offers them. For a 180-day initial research
   window, request 220 days (180 days + 35-day warmup + buffer); 360-day
   windows need at least 395 days. No georestriction bypass of Binance.
3. Loads the **native OKX Freqtrade OHLCV file** and exports identical observed
   closed 15m, 1h and 5m (or 1m) candle sets to CSV.
4. Checks a continuous 180- or 360-day window, closed H1 alignment, OHLCV
   aggregation, native dataset checksum, detailed candle checksum and at
   least 35 days of preceding model-training history. The manifest includes
   `exchange=okx`, `marketType=USDT_PERPETUAL`, pair, and a venue-bound
   provenance SHA; each native backtest verifies those fields before running.
   Gaps, mismatched venue, or source restrictions fail closed.
5. Loads both guarded native strategies, then executes Freqtrade CORE and
   FreqAI LightGBM research backtests with `--timeframe-detail 5m` or
   `--timeframe-detail 1m`, passing the **same native data directory**.
   The CORE and FreqAI native order signals are **disabled**. Zero native
   trades cannot prove strategy performance, or entry/DCA/exit parity.
6. Outputs JSON and logs with `full_core_parity_certified=false`.
   Model research success does NOT certify predictive ability; independent
   FreqAI prediction provenance, OOS testing and exchange-independent
   trade traces are still required.

Binance access was blocked with HTTP 451 in Codemagic on 2026-10-30,
so this *separate research workflow* uses OKX; the existing Binance
paper-trading and model-admission paths are not relabeled as OKX. Freqtrade
warns that OKX only exposes about three months of historical MARK candles,
so **180/360-day funding/mark coverage is NOT verified**. The native data
manifest and research report must keep `funding_mark_full_coverage_verified`
false until independent complete proof exists. If the necessary 1m/5m
OHLCV, funding or mark data is absent, never fabricate it or declare
trading-profit / funding / liquidation parity. Any OKX access restriction
also fails closed.
Do not change RSI/ADX/DCA/stop thresholds merely to create an Emergency SL.

For a separately acquired canonical dataset, the offline command is:

```bash
python3 -m quant_system.intrabar_audit \
  --m15 parity-input/m15.csv --h1 parity-input/h1.csv \
  --detail parity-input/5m.csv --detail-minutes 5 \
  --days 360 --output artifacts/phase3/history-audit-360.json
```

The CSV must have
`open_time,open,high,low,close,volume,closed` with timestamps in
UTC **milliseconds** and `closed=1` for every row. The 1m/5m data must
aggregate to the corresponding M15 candle, and M15 to H1. The audit detects
first-detail-candle Emergency SL touches and gap-aware synthetic estimates
but never invents `actual_fill_price` or claims a fill from OHLC alone.

## 3. How to launch Codemagic on Android

Open the existing Codemagic application for `btcusdt-telegram-signals2`.

- Branch: `feature/dual-strategy-phase3-paper-audit-20261030`
- First workflow: `dual-strategy-phase3-unit`. This should run Python
  unit tests for atomic rollback, restart dedup, source conflict,
  DCA/SL parameter preservation and data audits.
- Expensive, optional manual workflow:
  `dual-strategy-phase3-native-research`.
  Set `PHASE3_DAYS=180` for the first run and `PHASE3_DAYS=360` for
  the second run. Keep `PHASE3_DETAIL_MINUTES=5` initially; a separate
  run with `1` is useful if data limits permit. Default download is
  `PHASE3_DOWNLOAD_DAYS=220` for 180-day research; set this to `400`
  for 360-day research. Both use OKX-only exchange provenance.

Artifacts (if the native workflow reaches them):
`artifacts/phase3/canonical/native-export-report.json`,
`history-audit-180.json` or `history-audit-360.json`,
`native-research-180.json` or `native-research-360.json`,
`core-native-*.log`, `freqai-native-*.log`.

## 4. Unfinished validation required for real trade parity

- Kotlin and Freqtrade must independently export same-candle event traces
  for LONG/SHORT ENTRY, one-shot DCA, TP, Soft SL and Emergency SL.
- Both runtime traces must be tied to the same canonical OHLCV V2 SHA,
  include actual native fill provenance, gap/slippage/funding/liquidation
  records, and pass strict event-by-event reconciliation.
- FreqAI must produce authenticated model/prediction artifacts with
  chronological training/test boundaries, no lookahead and walk-forward OOS.
- Backtests must be **native trade-bearing backtests** on the audited common
  data, not prediction-only no-trade research. Stop prices must be reconciled
  with 1m/5m detail; unknown exchange fills remain unknown.
- Review Android build/feature preservation and release signing separately.
- Until these gates are independently demonstrated, keep
  `full_core_parity_certified=false` and keep live trading disabled.
