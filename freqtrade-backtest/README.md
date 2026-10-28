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
