# OKX Swap Shadow Data Source — Phase 1

## Scope

This phase adds a public, read-only adapter and isolated SQLite shadow store
for OKX BTC-USDT-SWAP, a linear USDT-settled perpetual swap. It captures only
confirmed closed M15 and H1 candles. No API key, account access, or order
submission is used.

The adapter validates the live SWAP instrument metadata: linear contract,
BTC base, USDT quote and settlement. It checks OKX server time and requires
the candle `confirm=1` flag before accepting a candle. Raw decimal strings
are validated without float conversion.

OKX SWAP candle fields distinguish `vol` (contract count), `volCcy`
(base-currency volume) and `volCcyQuote` (quote-currency turnover). The
shadow schema stores `volCcy` as BTC volume and `volCcyQuote` as USDT
turnover; it never mislabels contract count as BTC.

## Isolation

`OkxSwapSQLiteStore` writes only to `okx_swap_candles` in a dedicated
SQLite file. It rejects a path resolving to the Binance canonical database.
Primary keys make retries idempotent; existing candle values and first
observed availability timestamps are immutable. Conflicting history rolls
back the batch. This store is not registered with Binance canonical storage,
Strategy Core, AI strategy, Shared Risk Engine, paper execution or Binance
backtest. No fallback, merging, source migration or cutover is implemented.

## CI and capture boundary

GitHub Actions runs the offline adapter/store contract tests and compilation
on pull requests and pushes to the feature branch. The workflow does not
contact OKX, open the Binance canonical database, create a canonical file,
start the Feeder, or enable execution. It runs with database paths and
exchange credentials unset and `ai_execution_enabled=false`.

The optional public OKX snapshot capture remains a separate, not-yet-authorized
acceptance step. It must write only to the dedicated shadow artifact directory;
it must never create, open, or modify the Binance canonical database. No live
capture was performed as part of this PR validation.

A successful CI run alone is not source acceptance. Inspect exact source SHA,
test logs, instrument metadata, returned candles, coverage, gaps and hashes
before considering a separately approved shadow capture. This phase is not a
production source migration.

## Official API contract

- Instruments: https://www.okx.com/docs-v5/en/#public-data-rest-api-get-instruments
- Server time: https://www.okx.com/docs-v5/en/#public-data-rest-api-get-system-time
- Candles: https://www.okx.com/docs-v5/en/#market-data-rest-api-get-candlesticks
