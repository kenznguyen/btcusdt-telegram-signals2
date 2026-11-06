# Kraken Spot read-only API

## Isolation

The WSGI application in `market_data.kraken_spot_api` is a separate service
from `market_data.api`. It reads only the dedicated Kraken Spot SQLite file
through `KrakenSpotSQLiteStore(initialize=False)`.

It does not import or call the Binance canonical API, canonical storage factory,
Futures strategy, backtest, paper execution, or risk-control modules. Its route
table contains no `/v1/candles` endpoint.

## Configuration

Set these environment variables in the service runtime:

- `KRAKEN_SPOT_DB`: path to the existing Kraken Spot SQLite database.
- `KRAKEN_SPOT_CANONICAL_DB`: path identifying the Binance canonical SQLite
  database. The service fails closed if either path is missing or both paths
  resolve to the same file.
- `KRAKEN_SPOT_API_TOKEN`: non-empty bearer token used for read access.
- `PORT`: optional listen port; defaults to `8790`.

The API opens the Spot database in SQLite read-only mode, verifies the expected
table/schema without creating or migrating anything, and never initializes a
missing database. A missing or invalid database returns
`503 STORE_UNAVAILABLE`.

## Endpoints

### `GET /health`

Returns service identity only:

```json
{"ok": true, "service": "kraken-spot-market-data"}
```

### `GET /v1/kraken-spot/candles`

Requires `Authorization: Bearer <KRAKEN_SPOT_API_TOKEN>`.

Required query parameters:

- `symbol=BTC%2FUSDT`
- `timeframe=15m` or `timeframe=1h`
- `startMs=<aligned Unix milliseconds>`
- `endMs=<aligned Unix milliseconds>`

Optional: `asOfMs=<Unix milliseconds>`, which excludes rows first observed
after the requested point in time.

The window must be aligned, nonempty, and no larger than 2,000 candles. The
response includes source identity/provenance, closed-candle data, coverage and
gaps, dataset SHA-256, and generation time. Responses use
`Cache-Control: no-store`.

## HTTP behavior

- `200`: health or candle read succeeded.
- `400`: malformed, duplicate, unsupported, or oversized query.
- `401`: missing or invalid bearer token.
- `404`: route is not part of this service, including `/v1/candles`.
- `405`: methods other than GET.
- `503`: missing configuration or unavailable/invalid read-only store.

## Verification

Run the manual Codemagic workflow
`market-data-kraken-spot-read-api`. It runs the Kraken adapter, SQLite store,
and API contract tests against temporary files and prints
`KRAKEN_SPOT_READ_API_COMPILEALL=PASS` when compilation succeeds.

This workflow does not contact Kraken/Binance, run a production server, migrate
any database, or validate Futures integration. It validates the isolated
read-only HTTP boundary only.
