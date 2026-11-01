# Isolated Kraken Spot SQLite persistence

## Scope

`market_data.kraken_spot_store.KrakenSpotSQLiteStore` persists only validated
`SourceCandle` values emitted by the Kraken Spot adapter. It uses a dedicated
SQLite file and a separate `kraken_spot_candles` table.

The store is intentionally not registered in `market_data.storage`, the
canonical Binance USD-M `CandleStore`, the read API, or any Futures strategy,
backtest, paper-execution, or risk-control component.

## Construction

Pass both the Kraken Spot database path and the Binance canonical database path:

```python
from market_data.kraken_spot_store import KrakenSpotSQLiteStore

store = KrakenSpotSQLiteStore(
    "/data/kraken-spot.sqlite3",
    canonical_db_path="/data/binance-canonical.sqlite3",
)
```

If `canonical_db_path` is omitted, the store requires
`MARKET_DATA_DB` to be set. Construction fails closed if the resolved paths
refer to the same file. The database must be an on-disk SQLite file; in-memory
storage is rejected so that persistence cannot silently become ephemeral.

## Contract

- Accepts only `SourceCandle` values with identity
  `exchange=kraken`, `marketType=SPOT`, `symbol=BTC/USDT`, and a non-empty
  native Kraken market ID.
- Persists M15/H1 candles with decimal strings and first-observed availability.
- Uses a source-qualified primary key including exchange, market type, native
  market ID, symbol, timeframe, and candle open time.
- Exact retries are idempotent and preserve the original availability time.
- A conflicting closed candle raises an error and rolls back the entire batch.
- Readback is read-only, supports an `as_of_ms` cutoff, reports gaps, and
  returns a deterministic SHA-256 dataset version.
- No automatic fallback, blending, stitching, or copying into Binance storage.

## Verification boundary

The manual Codemagic workflow `market-data-kraken-spot-sqlite-tests` runs unit
and temporary-file SQLite integration tests. It does not call Kraken or Binance
network APIs, migrate production databases, expose a public API, or connect this
dataset to Futures consumers. Passing it validates isolated persistence only;
the separate live Kraken Spot acceptance and Binance USD-M collector acceptance
retain their independent scopes.
