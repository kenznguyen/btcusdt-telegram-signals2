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
