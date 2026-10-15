# 180-day BTCUSDT strategy comparison plan

This branch isolates the A/B comparison from the live Telegram bot.

## Strategies

### A — BTCUSDT M15/H1 RSI + ADX + Smart DCA
Use the project's current strategy rules as the source of truth. Before reporting results, reconcile exact entry trigger (cross vs threshold), H1 filter, DCA eligibility, ROE denominator, and the order of DCA / Soft SL / Emergency SL with the currently deployed bot/Pine version. Do not silently substitute another variant.

### B — RSI %b Signal [H1 Backtesting] (user-provided Pine v5 source)
- RSI(14) on close, then EMA(28) smoothing.
- Bollinger Bands(80, 3) applied to smoothed RSI.
- %b = (oscillator - lower band) / (upper band - lower band).
- Long entry: previous %b < 0.2 and current %b > 0.2.
- Short entry: previous %b > 0.8 and current %b < 0.8.
- Both positions close when %b crosses down through 0.2 or crosses up through 0.8.
- No DCA, explicit stop loss, ADX filter, or position sizing is present in the supplied Pine source.
- Pine's RSI/EMA/standard-deviation calculations and strategy fill semantics must be matched or discrepancies documented.

## Shared test protocol
- Market: BTCUSDT perpetual futures.
- Window: same 180-day UTC interval for both strategies, using only fully closed candles.
- Data: one consistent exchange source and candle series; use M15 as the master timeline, and H1 bars only after their close.
- Starting balance: 200 USDT.
- Fees: 0.04% per fill side for both strategies.
- Leverage reference: 13x, but strategy B's original source does not define leverage/margin. Therefore report (1) native/original sizing interpretation if determinable and (2) a clearly labelled standardized sizing run. Never claim the two sizing models are identical without stating the rule.
- Slippage: configure one shared assumption and include it in the report; report the exact tick-size and ticks-per-side used.
- Funding: if not simulated, explicitly mark results as excluding funding.
- Open positions: mark to market at the end of the test window; show realized PnL and unrealized PnL separately.
- No lookahead: do not use an H1 candle until its close.

## Required outputs
- `comparison_summary.csv` and `comparison_summary.json`
- `trades_A.csv`, `trades_B.csv`
- `equity_curve_m15.csv` with marked-to-market equity and drawdown
- `README_RESULTS.md` containing the data source, exact UTC dates, assumptions, validation notes, and limitations

## Required metrics
Net profit (realized and marked-to-market), return %, max drawdown in USDT and %, profit factor, win rate, completed trade count, average trade PnL, total fees, slippage estimate, funding (or explicit not-modeled flag), max margin used, DCA count, Soft SL count, Emergency SL count, and ending open-position exposure.

## Acceptance checks
1. Both strategies use identical start/end timestamps and candle source.
2. No results are published if candle coverage has gaps or indicators have insufficient warm-up.
3. Fees are applied on entry and exit fills.
4. Mark-to-market equity includes unrealized PnL and estimated exit fee.
5. Open positions at the end are reported rather than silently discarded.
6. CSV summary totals reconcile with trade ledger and equity curve.
7. Unit tests cover all B entry/exit crossings and A's risk-priority edge cases.
8. This branch must not change the live bot or default Telegram backtest outputs.

## Status
Plan only until the comparison engine, tests, and a successful 180-day run are present. Do not publish estimated or invented performance numbers.
