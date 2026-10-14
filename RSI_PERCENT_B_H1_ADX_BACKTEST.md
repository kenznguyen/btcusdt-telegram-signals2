# RSI %b M15 Entry + H1 ADX Backtest

This feature is isolated from the live Telegram bot and existing backtest engine.

## Strategy rules

- Market/data: Binance USDⓈ-M Futures klines for `BTCUSDT`.
- Entry timeframe: M15, using RSI(14), EMA(28) smoothing, Bollinger Bands(80, 3) applied to the smoothed RSI, then %b.
- LONG: M15 %b crosses above 0.2 and the latest fully closed H1 candle has ADX(14) >= 20 and +DI > -DI.
- SHORT: M15 %b crosses below 0.8 and the latest fully closed H1 candle has ADX(14) >= 20 and -DI > +DI.
- LONG exit: %b crosses above 0.8. SHORT exit: %b crosses below 0.2.
- One position at a time. No DCA, funding payment, or liquidation simulation in this first baseline.

## Run from GitHub Actions

1. Open the repository and select branch `feature/rsi-percent-b-h1-adx-backtest`.
2. Open **Actions** → **RSI %b H1 ADX Backtest**.
3. Click **Run workflow**, set branch to this feature branch, and keep `180` days or change the period.
4. Download the artifact `rsi-percent-b-h1-adx-180d`. It contains:
   - `summary.json`: headline metrics and assumptions
   - `trades.csv`: per-trade entries/exits, fees, PnL and margin
   - `equity_curve_m15.csv`: equity and drawdown at each M15 candle

## Assumptions / limitations

- Defaults: starting capital 1000 USDT, 10% of current balance as margin per trade, 1x leverage, 0.05% taker fee per side, 2 ticks of slippage per side. These are test inputs, not claims about your account's actual fee schedule.
- Tick size defaults to 0.1; override `TICK_SIZE` if needed for the symbol's current contract specification.
- Entry and exit signals are evaluated on candle close; fills include configured slippage.
- H1 filtering uses only fully closed H1 candles to avoid lookahead.
- Funding payments, liquidation/margin-call rules, exchange-specific fills, and live execution delays are not modeled.
- Results are historical simulation only and are not a profit guarantee.
