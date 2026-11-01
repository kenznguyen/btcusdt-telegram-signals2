# Alternative-source market-data acceptance (Kraken spot)

This acceptance is intentionally isolated from the Binance USD-M collector acceptance.

## Source and isolation

- Exchange: Kraken public spot market.
- Market: BTC/USDT spot (not a perpetual/futures contract).
- Timeframes: 15m and 1h; a 24-hour closed-candle window.
- Storage: a workflow-local SQLite database artifact named `alternative-source-acceptance.sqlite3`.
- No credentials, trading endpoints, production database, or canonical Binance tables are used.

The workflow validates the Kraken market identity, retrieves closed OHLCV candles, persists them, repeats ingestion, verifies zero additional inserts, reads the stored window back, and checks the dataset hash and coverage.

## Explicit evidence boundary

A PASS proves only that the alternative Kraken spot path worked for the reported window and source SHA. It does **not** prove:
- Binance USD-M API reachability or Binance collector correctness;
- Binance futures market identity or futures data semantics;
- PostgreSQL/TimescaleDB canonical persistence;
- the canonical `/v1/candles` API.

Do not reuse this report as Binance collector acceptance evidence. Binance collector acceptance remains blocked until a permitted Codemagic execution environment can reach Binance USD-M and the original Binance acceptance passes independently.
