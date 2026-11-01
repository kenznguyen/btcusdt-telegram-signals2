# Bybit Linear Shadow Data Source — Phase 1

## Scope

This phase adds a read-only adapter and isolated SQLite shadow store for the
Bybit V5 **BTCUSDT USDT linear perpetual** instrument. It supports closed M15
and H1 candles. Public endpoints only; no API key, account access, or order
submission is used.

The adapter validates the instrument as active `LinearPerpetual`, category
`linear`, base BTC and quote USDT. It uses Bybit server time and the local
observation clock conservatively to exclude unclosed candles. V5 kline rows
are returned newest-first, so the adapter orders them chronologically and
rejects duplicates, malformed rows, unaligned timestamps and invalid OHLC.

Bybit's linear USDT contract kline `volume` is recorded as BTC base volume;
`turnover` is recorded separately as USDT quote turnover. Raw decimal strings
are preserved and validated without float conversion.

## Storage isolation

`BybitLinearSQLiteStore` writes only to `bybit_linear_candles` in a dedicated
SQLite file. It rejects a path resolving to the Binance canonical database.
The schema fixes exchange, market type, category and symbol; primary keys make
retries idempotent. Existing candle values and first-observed availability
timestamps are immutable; conflicting history aborts the full transaction.

The Bybit store is deliberately not registered in the canonical Binance
storage factory, Binance API, Strategy Core, AI strategy, Shared Risk Engine,
paper execution, or Binance backtest. No source fallback or data merging is
implemented.

## Manual Codemagic shadow capture

Run `market-data-bybit-shadow` manually in Codemagic. It runs unit tests,
then fetches a bounded last-24-hour closed M15/H1 snapshot from Bybit and
writes the isolated SQLite database and JSON coverage/hash report as artifacts.
The workflow has no push trigger and uses public market data only.

Artifacts:
- `ci-source-sha.txt`
- `bybit-shadow-artifacts/bybit-shadow.sqlite3`
- `bybit-shadow-artifacts/bybit-shadow-report.json`

This is a phase-1 shadow snapshot, not a continuously scheduled collector.
No Research/Backtest, signal generation, Strategy Core changes, source
migration, Binance canonical writes, or production cutover are part of this PR.

## Upstream contract

- Kline: https://bybit-exchange.github.io/docs/v5/market/kline
- Instrument metadata: https://bybit-exchange.github.io/docs/v5/market/instrument
- Server time: https://bybit-exchange.github.io/docs/v5/market/time
