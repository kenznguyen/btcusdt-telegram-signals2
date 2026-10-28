# Android / Python Replay / Actual Freqtrade Runtime

Three distinct execution paths exist and must never be misrepresented:

1. **Android StrategyEngine** is the phone-native paper backtest using Binance
   Futures closed M15/H1 candles. No trading orders are sent.
2. **Python offline replay** models StrategyEngine conditions and is compared
   event-by-event to Android JVM tests by `parity_suite.py`. This is **not**
   the Freqtrade backtesting runtime. Currently ENTRY and Emergency SL consume
   shared JSON fixture files; DCA and TP still use mirrored deterministic OHLC
   generators.
3. **Freqtrade runtime** is a separate tool. The Codemagic
   `freqtrade_runtime_probe` workflow tries to start a real Freqtrade Docker
   image, reads its version, and discovers the adapter strategy. The workflow
   does NOT run a real strategy backtest or certify parity. It requires Docker
   access on the selected Codemagic worker and may fail if Docker is unavailable.

## Current hard blocker to actual Android ↔ Freqtrade backtest parity

`strategies/BtcM15H1ParityGate.py` intentionally sets
`enter_long`, `enter_short`, `exit_long`, `exit_short` to 0.
A successful Freqtrade CLI invocation with this strategy would test runtime
availability only, **not** StrategyEngine's entry/DCA/exit logic. Never turn
its results into profitability evidence or mark `verified=true`.

## Proper future implementation sequence

- Port closed-candle M15/H1 entry + indicator warm-up with previous **closed**
  H1 alignment to the Freqtrade strategy; compare bar-by-bar entry predicates.
- Port 13x exposure, initial margin, DCA entry eligibility, partial fills and
  weighted average cost accounting using relevant Freqtrade callbacks,
  keeping the strategy paper/backtest-only.
- Implement TP and both stops, including the Android intrabar emergency/soft
  stop precedence. Investigate limitations of standard Freqtrade backtesting
  with same-candle multi-events, gaps and detail timeframe.
- Export independent Freqtrade runtime trade/ledger results from the actual
  backtesting command and Android StrategyEngine traces on **the same**
  historical OHLCV dataset, with identical fees, slippage, timestamps,
  warm-up and end-of-run open-position valuation.
- Compare event order, quantity, margin, entry/exit price, fees, net PnL,
  equity and max drawdown. Investigate discrepancies before considering any
  parity certification. Keep `verified=false` until manually reviewed.

## Codemagic

`android_freqtrade_debug` runs Kotlin/Python unit tests and the current
offline replay parity suite, then builds a Debug APK. The optional
`freqtrade_runtime_probe` is isolated so Docker/image availability cannot
break normal Android builds.

No Release signing, exchange API keys, or real trade execution is required.

## ENTRY DataFrame parity progress

`entry_frame.py` now computes RSI(14), Wilder DMI/ADX(14), and LONG/SHORT
entry *diagnostic columns* from M15 OHLCV plus closed H1 OHLCV. It uses
`android_indicators.indicator_series` and the already audited
`android_signal_predicates.entry_side`, both independent of the Freqtrade
package. H1 open-time rows become visible only at open time + one hour,
preventing same-hour lookahead.

`tests/test_entry_frame.py` compares the initial LONG ENTRY timestamp to
the Python state replay on the **same**
`fixtures/android_python_entry_ohlc_v1.json` used by the Android JVM test.
It also checks H1 close timing and missing/duplicate candle rejection. The
tests require pandas, and skip when pandas is not installed; such a skip
must not be treated as verified parity.

**Limitations:** this is diagnostic ENTRY logic, not the live Freqtrade
strategy adapter; Freqtrade-specific data-provider integration, exchange
data import, position-state handling, DCA/TP/stops, trade ledger and
runtime backtest are still unimplemented. Existing
`BtcM15H1ParityGate` deliberately continues to suppress all entries
and exits. No trading functionality is enabled.

## Actual Freqtrade backtesting command (diagnostic-only MVP)

Codemagic now defines `freqtrade_runtime_backtest`. Unlike
`freqtrade_runtime_probe`, this workflow executes actual
`freqtrade download-data` and `freqtrade backtesting` commands in the
`freqtradeorg/freqtrade:stable` Docker image. It downloads 45 days of
Binance **SPOT** BTC/USDT 15m/1h candles, invokes
`BtcM15H1EntryRuntime`, and archives the resulting Freqtrade result ZIP
and logs. It does not use live trading API credentials.

The adapter is deliberately a **backtest-only, LONG-only ENTRY diagnostic**.
Its exit rules are temporary spot ROI 5% and spot stoploss -20%, which
are NOT equivalent to Android TP +5% ROE at 13x, Soft SL -35% ROE, or
Emergency SL -90% ROE. It does not reproduce Android DCA, SHORT,
isolated futures margin, fees/slippage or intrabar priority. Its profit,
win rate and drawdown **must not** be compared as equivalent to Android.
No reported numbers are invented; read the real exported Freqtrade ZIP.

The workflow requires Docker access and Binance public historical
downloads from the Codemagic worker. If unavailable, it must fail and
the run cannot be represented as successful. On completion, its manifest
still states Android–Freqtrade parity is **not verified**. The Docker
`stable` tag is mutable, so the workflow records `freqtrade --version`
but reproducible comparisons will require pinning an image digest.

To reach actual 13x Android parity, implement a separate futures strategy
with matching leverage callbacks, position adjustments, exact TP/SL
conditions and ledger export, then use **the same** time-aligned
OHLCV and fee assumptions for both engines.

## Futures 13x candidate (NEW, not parity-certified)

`strategies/BtcM15H1FuturesRuntime.py` is a separate experimental
**BACKTEST-ONLY** Freqtrade strategy, with `config.runtime-futures.json`
and the `freqtrade_futures_backtest` Codemagic workflow.

- OKX **BTC/USDT:USDT perpetual**, isolated margin, 100 USDT starting wallet.
- `leverage()` demands 13x instead of silently reducing it.
- Both LONG/SHORT entries from the Android RSI cross + prior closed H1.
- Initial stake target 50 USDT; `adjust_trade_position()` can add one
  DCA stake, gated by Android ROE/ADX/RSI and wallet limits.
- `custom_exit()` evaluates **EMERGENCY_SL -> SOFT_SL -> TP** in this
  priority order, using candle OHLC and prior closed H1.
- Static ROI/stoploss are disabled as performance targets; Freqtrade
  nevertheless maintains an emergency -99% safety bound as required by
  the framework.

**Known discrepancies that MUST be resolved before parity certification:**
1. Freqtrade callbacks may run after the Android closed-bar event timestamp
   and the exit fill may not equal Android `stopFillPrice`; a high/low
   threshold crossed within a candle does not imply the same fill.
2. Intra-candle exit-versus-DCA ordering, short liquidation/funding and fees
   are controlled by Freqtrade's execution simulation, not Kotlin accounting.
3. Initial stake currently references a configured 100-USDT starting wallet,
   not Android's **dynamic balance * 50%** across sequential trades.
4. Freqtrade backtesting may use different candle availability in callbacks;
   bar-by-bar, common-dataset trace comparison is mandatory.
5. Full equity and fee reconciliation, including open positions at final bar,
   has not been implemented. No win-rate/profit assertions are made.

A complete Codemagic run only proves the **Freqtrade runtime** processed
futures backtesting with this candidate strategy. It does not prove parity.
The existing Spot workflow stays available as the verified runtime baseline.

## Extended 90 / 180 / 360-day futures backtesting

Codemagic workflow `freqtrade_futures_backtest` defaults to **180 days**
and accepts the `BACKTEST_DAYS` environment variable: `90`, `180`,
or `360`. The download requests an additional **7 days** to warm up
RSI/ADX indicators and H1 filters. The backtest command includes an
explicit UTC `--timerange`; it does not assume all downloaded bars form
the performance measurement window.

The `backtest_window.py` helper writes `window.json` and
`validate_futures_history.py` reads the actual 15m and 1h futures
Feather files to reject missing/duplicate candles, insufficient
warm-up/start coverage, or stale end-of-period data. The coverage
report `history-coverage.json` is a workflow artifact. If the exchange
cannot provide 180/360 days, the workflow deliberately fails instead
of silently reporting a shorter backtest.

**Practical note:** Longer runs increase OKX download requests, time
and free CI resource consumption. Start with 90 days if the 180-day
download is rate-limited, then check the full coverage report before
evaluating performance. DCA and exit callback diagnostic logs remain
enabled. No automatic tuning, real orders, or Android strategy changes.

## Detailed stop-fill validation and historical walk-forward (October 2026)

The futures adapter now uses Freqtrade's **native -90% stoploss on leveraged
stake** for the emergency protection threshold. This is the exchange/engine
risk cap for backtesting, not a claim of identical Android intrabar fills.
The custom Android emergency predicate is still evaluated for diagnostics,
but no competing `custom_exit` is submitted for emergency breaches.
Soft SL retains its H1 reversal + two-candle confirmation and a
`custom_exit` request after confirmation; the resulting simulated fill
will not necessarily equal the Android theoretical stop price.

`freqtrade_futures_backtest` downloads 5m/15m/1h OKX Futures OHLCV and
uses `--timeframe-detail 5m` in its full-period backtest (180 days by
default, `BACKTEST_DAYS=360` for the longer run). The history
validator fails on gaps or incomplete timeframes.

New exported artifacts:
- `freqtrade-futures-results/fill-reconciliation.csv` and `.json`:
  `expected_fill_price` from an actually matched Android-model stop
  trace, `actual_fill_price` from the Freqtrade trade, signed
  `fill_difference = actual - expected`. Unmatched emergency stops,
  missing traces and ordinary TP fills remain **null**, never guessed.
- `freqtrade-futures-results/common-ohlcv/*.csv.gz` plus
  `shared-ohlcv-manifest.json`: common UTC timestamp OHLCV and SHA256
  checksums for future Kotlin/Python input comparison.
- With `BACKTEST_DAYS=360`: three **120-day, non-overlapping,
  chronological** validation reports under
  `freqtrade-futures-data/walkforward/window-{1,2,3}`.
  These are fixed-parameter sequential evaluation windows,
  **not** model re-training/optimization.

**Not yet verified:** The Kotlin Android engine has not been executed
against this exported OKX dataset. Stop fills and accounting do not have
bar-for-bar parity certificates. Native stoploss may be affected by
market gaps, leverage funding, order simulation, and data granularity.
All backtests remain paper/historical only, and every real-trading
mode is rejected by the strategy.

## 360-day default and 5m open-position equity audit

The `freqtrade_futures_backtest` Codemagic workflow now defaults to
`BACKTEST_DAYS=360`. It performs a complete 360-day futures backtest
with 5m intra-candle simulation followed by three independent
120-day chronological windows. It **does not run real orders**.
The historical exchange coverage check fails rather than inventing
missing data.

`equity_reconstruction.py` exports
`freqtrade-futures-results/equity-5m.csv.gz` and
`equity-5m-summary.json`. It reconstructs mark-to-market unrealized PnL
at each 5m closing price from actual entry fills (including DCA), deducts
entry fees while positions are open, and settles Freqtrade's reported
`profit_abs` at the exit. Settlement includes Freqtrade's exit
fees and funding. The script **fails the build** if final equity does
not reconcile with Freqtrade's final account balance.

**Disclosure:** The 5m OHLCV close is not the exchange's mark price.
Per-funding-event timestamps are not available in standard Freqtrade
trade exports, so accumulated funding is recognized only on exit;
the resulting intermediate equity/drawdown is an audit estimate.
The report separately labels the largest absolute drawdown and
the largest percentage drawdown; they need not coincide.
No Android parity or liquidation parity is claimed.
Per user preference, no separate Emergency SL stress-test workflow
was added.

## Post-360d risk-engine audit (no StrategyEngine tuning)

This phase adds only auditing, tests, and CI artifacts. Android Kotlin
StrategyEngine, its 13x leverage, RSI/ADX thresholds, DCA, TP, Soft SL,
and Emergency SL are **unchanged**.

- `market_risk_audit.py` reports actual Freqtrade liquidation fills,
  the protective stop price, the recorded fee/funding totals, and the
  presence and date coverage of raw OKX funding-rate and mark candles.
- `funding_timeline_audit.py` independently estimates funding
  observations at historical UTC candle timestamps using the open
  position quantity (including additional DCA fills) and the last
  available mark price. The output explicitly provides per-trade
  differences versus actual Freqtrade funding totals. These
  observations are **not verified exchange settlement timestamps** and
  must not replace Freqtrade accounting.
- `common_dataset_parity.py` checks SHA256 of the shared 5m/M15/H1
  OHLCV files. It can compare independently supplied Kotlin and
  Freqtrade event traces using timestamp/side/event type/price, but
  without those actual traces it returns `parity_verified: false`.
  Shared-source files alone do not prove identical event processing.

### Liquidation caveat

In the 360-day result the SHORT opened 2026-02-24 15:45 UTC
at 63716.10 closed as `liquidation` on 2026-02-25 16:45 UTC at
68080.30, before its recorded stop-loss price 68127.20. Per the
Freqtrade 2026.9 documentation, `liquidation_buffer` defaults to
0.05 and the engine computes a buffer-adjusted liquidation threshold.
Liquidation fees are *not* modelled by Freqtrade. The original
backtest config did not specify a different buffer. This finding
shows a gap versus an ideal emergency SL fill; it does not prove
the exact exchange maintenance margin or independent mark-price
liquidation trigger.

Codemagic now exports
`liquidation-funding-input-audit.json`,
`funding-timeline-estimate.json`, and
`common-dataset-parity-status.json`. Review the contents before any
claims about 360-day funding accuracy or Android parity.
