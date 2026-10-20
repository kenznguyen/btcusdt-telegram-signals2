# BTCUSDT strategy/backtest audit (evidence-first)

## Scope
Audit-only branch. Strategy thresholds, sizing parameters, and production behavior are not changed in this pass. No live orders are placed.

## Source snapshot inspected
- Python bot: `bot.py` on `main`, base strategy settings: leverage 13x; RSI 30/70 entry cross; closed-H1 directional filter and ADX > 20; DCA ROE <= -20%, M15 ADX > 45 and RSI direction; TP RSI 76/24 and ROE >= 5%; Soft SL ROE -35%, reversal H1 ADX > 35 plus two-candle confirmation; emergency stop ROE -90%.
- Python backtest: `backtest.py` on `main`.
- Android engine and existing unit tests: `feature/android-btcusdt-live-alerts`.
- Python defaults currently specify fee 0.05% per side (0.0005) and slippage 5 bps. This is recorded as an implementation fact, not a recommendation to change a parameter.

## Findings and fixes on this branch
1. **Entry/DCA fill parity:** fixed Python bot and backtest to apply the existing adverse-slippage model to entry and DCA, and to derive quantity, average entry and notional from fill price.
2. **End-of-test liquidation:** fixed backtest to apply the configured adverse slippage to final liquidation.
3. **H1 close-time selection:** fixed Python bot, backtest and Android engine to use the latest H1 candle whose close time is no later than the closed M15 candle close time. At M15 open 00:45 (close 01:00), the H1 candle opened 00:00 is now eligible. Only closed H1 candles are selected.
4. **Protective exits with NaN indicators:** removed early indicator guards from Python bot/backtest. RSI/ADX-dependent entry, TP and Soft SL conditions evaluate false for NaN, while price-based Emergency SL still executes. Android already allows Emergency SL evaluation while RSI is warming up when a position exists.
5. **DCA margin guard:** added the same available-margin check to the Python signal bot that already existed in backtest and Android. A DCA add is skipped when its reserved margin would exceed simulated account balance.
6. **Fee source discrepancy remains unresolved:** Python/backtest/Android default is 0.05% per side; an earlier supplied Pine configuration used 0.04%. The intended Pine commission assumption must be explicitly confirmed before changing this parameter. No fee or strategy threshold was changed.

## Already aligned in inspected source
- Entry RSI cross inequalities and H1 DI/ADX thresholds are consistent between Python rule helpers and Android pure-rule functions.
- DCA threshold is inclusive at ROE <= -20%; ADX threshold is strict > 45; RSI direction conditions match.
- TP requires both RSI threshold and ROE >= 5%.
- Emergency SL precedes Soft SL, which precedes TP in the Python and Android engines.
- Both Python and Android use stop-gap logic plus adverse slippage for stop fills.

## Tests
`tests/test_strategy_backtest_audit.py` now contains ordinary regression assertions for adverse Entry/DCA/end-exit fills, closed-H1 timing in Python and Android, protective-stop evaluation with missing indicators, core strategy conditions, and unchanged fee/slippage defaults. CI must pass before this branch is considered validated.

## Not claimed
No fresh historical backtest metrics are claimed by this audit. No market data was downloaded or replayed in this commit. Do not treat historical profitability as verified until execution parity is resolved and a deterministic fixture plus a fresh backtest report have been reviewed.


## State and notification recovery hardening

- Python state and Telegram outbox/ledger JSON writes are atomic (fsync + os.replace). A corrupt state file now fails closed rather than silently resetting an open paper position.
- BOT_STATE_DIR controls the directory for state.json, telegram_outbox.json, telegram_sent_event_ids.json, and Telegram webhook update IDs. On Render, point this to a mounted persistent disk path if restart/deploy durability is required. Without persistent storage, local files may be lost on instance replacement.
- Telegram signal events are queued durably before delivery, retried on later runs, and deduplicated by event type/side/closed-candle timestamp. Telegram Bot API does not provide an idempotency key for sendMessage; a crash after Telegram accepts a message but before the sent ledger is written leaves a narrow duplicate-delivery window.
- Telegram webhook updates are persisted to telegram_seen_updates.json; failed GitHub workflow dispatches return HTTP 503 without marking the update handled, allowing Telegram to retry. Configure the same BOT_STATE_DIR on a persistent Render disk to preserve this ledger across restarts.
- Android validates OHLCV, timestamps and conflicting duplicate candles; corrupt persisted strategy state now fails closed. Strategy alerts are persisted to a SharedPreferences outbox before state/cursor commit. Chart/strategy notifications denied by Android notification permission are queued and retried when permission is restored.
- Android stable notification IDs update the same system notification on retry, but OS delivery cannot be transactionally coupled to SharedPreferences. Device-level validation still requires testing on the target phone with notifications enabled, battery restrictions reviewed, and the app allowed to run in the background.
- GitHub Actions cache is best-effort recovery, not a transactional database or guarantee of permanent storage. For the scheduled scanner, state/outbox/ledger files are included in the cache path; a persistent service volume or external database is stronger if strict durability is required.
