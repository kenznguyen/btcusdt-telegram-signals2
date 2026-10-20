# BTCUSDT strategy/backtest audit (evidence-first)

## Scope
Audit-only branch. Strategy thresholds, sizing parameters, and production behavior are not changed in this pass. No live orders are placed.

## Source snapshot inspected
- Python bot: `bot.py` on `main`, base strategy settings: leverage 13x; RSI 30/70 entry cross; closed-H1 directional filter and ADX > 20; DCA ROE <= -20%, M15 ADX > 45 and RSI direction; TP RSI 76/24 and ROE >= 5%; Soft SL ROE -35%, reversal H1 ADX > 35 plus two-candle confirmation; emergency stop ROE -90%.
- Python backtest: `backtest.py` on `main`.
- Android engine and existing unit tests: `feature/android-btcusdt-live-alerts`.
- Python defaults currently specify fee 0.05% per side (0.0005) and slippage 5 bps. This is recorded as an implementation fact, not a recommendation to change a parameter.

## Confirmed discrepancies / risks
1. **Entry fill model differs.** Android applies adverse slippage to entry via `executionFillPrice`. Python bot signal-state and Python backtest entry use raw candle close for average entry and quantity sizing. This changes quantity, entry notional, fees and all later ROE/exit calculations.
2. **DCA fill model differs.** Android applies adverse slippage to the DCA fill. Python backtest and Python bot use raw close for DCA quantity and average entry.
3. **End-of-test liquidation is optimistic vs the configured execution model.** Backtest closes a remaining position at the final raw close without the adverse slippage used by TP/SL fills.
4. **H1 filter may be one hour stale at quarter-hour boundary.** Both Python and Android select H1 data using `h1.open_time < floor(m15.open_time, 1h)`. At M15 open 00:45, the M15 close is 01:00; the 00:00 H1 candle has also closed at that time, but the current selector still uses the prior H1 candle. This should be checked against the exact Pine/TradingView bar-timing contract before changing it.
5. **Parameter-source discrepancy to reconcile, not change now.** Current Python/Android engine default fee is 0.05% per side. Earlier supplied Pine configuration used 0.04% commission. Do not compare performance numbers until the intended commission assumption is documented and identical across platforms.

## Already aligned in inspected source
- Entry RSI cross inequalities and H1 DI/ADX thresholds are consistent between Python rule helpers and Android pure-rule functions.
- DCA threshold is inclusive at ROE <= -20%; ADX threshold is strict > 45; RSI direction conditions match.
- TP requires both RSI threshold and ROE >= 5%.
- Emergency SL precedes Soft SL, which precedes TP in the Python and Android engines.
- Both Python and Android use stop-gap logic plus adverse slippage for stop fills.

## Tests
`tests/test_strategy_backtest_audit.py` covers boundary behavior and records four known execution/timing gaps as expected failures. Expected failures are not passes of the underlying behavior; they are tracked gaps that should turn into ordinary passing regression tests after a separately reviewed implementation fix.

## Not claimed
No fresh historical backtest metrics are claimed by this audit. No market data was downloaded or replayed in this commit. Do not treat historical profitability as verified until execution parity is resolved and a deterministic fixture plus a fresh backtest report have been reviewed.
