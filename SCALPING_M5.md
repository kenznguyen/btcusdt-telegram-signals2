# BTCUSDT M5 Scalping — isolated prototype

This branch adds a **signal-only** M5 scalping engine. It does not alter `bot.py`, Telegram command handling, dashboard behavior, or the existing M15/H1 strategy.

## Architecture

- `scalping_bot.py`: independent M5 signal and simulated-position state machine.
- `.github/workflows/m5-scalping-scan.yml`: separate scheduled/manual scanner.
- `scalping_state.json`: separate state file; no sharing with the main strategy state.
- Market candles come from OKX `BTC-USDT-SWAP`. Only confirmed candles whose close time has passed are used.
- Telegram notifications explicitly say that no exchange order was placed.

## Prototype entry rules

**M15 trend filter (latest closed M15 candle):**
- LONG allowed when ADX > 20, +DI > -DI, and RSI > 50.
- SHORT allowed when ADX > 20, -DI > +DI, and RSI < 50.
- Otherwise, no new entry.

**M5 trigger (latest closed M5 candle):**
- M5 ADX > 18.
- LONG: previous M5 RSI in 40–50, current RSI crosses above 50, +DI > -DI, and close exceeds the previous candle high; M15 must allow LONG.
- SHORT: previous M5 RSI in 50–60, current RSI crosses below 50, -DI > +DI, and close falls below the previous candle low; M15 must allow SHORT.
- No DCA. A cooldown candle is required after closing a position.

## Prototype exits and defaults

- TP: estimated gross ROE >= 3% **and** M5 RSI >= 70 for LONG / <= 30 for SHORT.
- ATR stop reference: 1.5 × M5 ATR from entry. Stop touches are checked against completed candle low/high; gap-through fills are approximated using candle open.
- Soft SL: closed M15 trend is confirmed in the opposite direction and M5 confirms an opposite break.
- Emergency SL: estimated gross ROE <= -35%.
- Default leverage for ROE estimates: 13x.

These are **test parameters, not validated profitable settings**. ROE is a simplified price-move × leverage estimate; reported values do not fully model fees, funding, liquidation, queue position, or live slippage. Candle OHLC cannot reconstruct exact intrabar order. Do not use this prototype as an execution or emergency risk-control system.

## Run manually

GitHub → Actions → **BTCUSDT M5 Scalping Scanner** → Run workflow. Confirm the workflow log and Telegram output. The scanner only processes a newly closed M5 candle; running it twice against the same candle should skip the second run.

## QA checklist

- [ ] Scanner imports/compiles and workflow installs dependencies.
- [ ] No signal on an unconfirmed/current M5 or M15 candle.
- [ ] Same closed M5 candle is not processed twice.
- [ ] LONG and SHORT are never open simultaneously.
- [ ] M15 trend filter is respected for entries.
- [ ] ATR stop checks candle low/high, including a gap-through approximation.
- [ ] State and metrics are isolated from the existing strategy.
- [ ] Verify Telegram messages in paper/signal mode before considering any live integration.
- [ ] Backtest 90/180/360 days where data is available, including fees/slippage, before evaluating performance.
