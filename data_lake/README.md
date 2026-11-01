# Central BTCUSDT data lake

Layer 0 now supports PostgreSQL for shared storage and SQLite for local development.
The public candle shape, exact decimal strings, immutable closed-bar identity,
first-observed availability and dataset hashes are the same on both backends.
Scope is Binance **USDT perpetual BTCUSDT**, **15m and 1h**. Markets are not mixed.

Readers never call an exchange. A designated collector owns rate-limited CCXT
requests; FastAPI, FreqAI research exports and Hummingbot research clients read
the stored data. Live order books and funding collection remain separate feeds.
Internal requests still use bounded windows and server concurrency limits.

## Server setup

For a local computer trial with Docker Compose, private generated credentials,
separate reader/writer roles and optional collection, use the
[local quickstart](../deploy/data-lake/README.md). It binds only to loopback and
keeps database state in a persistent Docker volume.

Install into a server virtual environment with Python 3.10+:

```bash
python -m pip install -r requirements-data-lake.txt -r requirements-market-data.txt
```

Set `DATA_LAKE_DATABASE_URL` to a private PostgreSQL URI through your server's
secret/environment configuration, and set `MARKET_DATA_TOKEN` to a dedicated read
token. Do not put either secret in source, command arguments, screenshots or CI
artifacts. For local development, `MARKET_DATA_DB=.data/lake.sqlite3` is supported.
Initialize with a database account allowed to create/write these tables:

```bash
python -m data_lake init
```

The PostgreSQL tables are `candles` and `intelligence_snapshots`. Prices and
volumes use unconstrained `NUMERIC`; timestamps use `BIGINT`. Indexed market/time
keys select candle windows; the archive has an availability index. Conflicting
closed candles reject the transaction instead of silently changing history.

Run API processes with a separate PostgreSQL account granted only `CONNECT`,
schema `USAGE` and `SELECT` on those two tables. API reads also use read-only,
repeatable-read transactions with connection/statement/lock timeouts. GET never
creates schema or synchronizes the exchange.

```bash
uvicorn data_lake.api:app --host 127.0.0.1 --port 8788 --workers 2 --limit-concurrency 16
```

Use HTTPS through your existing reverse proxy for remote consumers. `localhost`
refers to the process's own host/container; an APK or a separate container must
use the reachable gateway address. API tokens and PostgreSQL credentials are
different credentials; database credentials never belong in the APK.

## Collection and retention

Backfill an explicit aligned window, at most 100,000 bars per command. This example
requests January 2026 M15 history, using pages of at most 2,000 closed bars:

```bash
python -m data_lake backfill --timeframe 15m --start-ms 1767225600000 --end-ms 1769904000000
```

Run one collector pass for the most recent 2,000 slots in both supported frames:

```bash
python -m data_lake.refresh --bars 2000
```

It checks stored gaps before fetching, combines missing slots into one bounded
span, and preserves earlier observations when reimporting identical bars. A
PostgreSQL transaction advisory lock or SQLite file lock serializes backfill and
refresh producers. Failed pages do not invent data; previously committed pages
remain available for a later retry. Gaps older than the rolling lookback require
an explicit backfill. No retention deletion is performed automatically.

For unattended collection, schedule the refresh command on the persistent server,
for example with a systemd oneshot service and a 60-second timer. Point
`EnvironmentFile` to a private environment file and use your actual installation
paths/account:

```ini
# chart-lake-refresh.service
[Service]
Type=oneshot
User=chartlake
WorkingDirectory=/opt/chart
EnvironmentFile=/etc/chart-lake.env
ExecStart=/opt/chart/venv/bin/python -m data_lake.refresh --bars 2000

# chart-lake-refresh.timer
[Timer]
OnBootSec=30s
OnUnitActiveSec=60s
Unit=chart-lake-refresh.service
[Install]
WantedBy=timers.target
```

After the T1 importer has produced a real snapshot, archive each version before
overwriting its output file:

```bash
python -m data_lake archive-intelligence --input .data/intelligence.json
```

The archive validates the pinned collector schema and content hash, preserves
publication time, and deduplicates by snapshot ID. Each document is limited to
64 KiB; a query rejects more than 10,000 documents or 8 MiB instead of truncating.
No historical T1 tape or macro-event calendar is bundled or manufactured.

## Read API

`GET /health` reports process health only. All three data endpoints require
`Authorization: Bearer <MARKET_DATA_TOKEN>`. Docs/OpenAPI and HTTP writes are
disabled. Responses use `Cache-Control: no-store` and fixed error codes.

| Endpoint | Result |
| --- | --- |
| `/v1/candles` | Exact canonical OHLCV, coverage/gaps, query-bound `datasetVersion` |
| `/v1/features` | Causal `causal-v2` feature rows, provenance and unavailable reasons |
| `/v1/cross-analysis` | Publication-time flow alignment, sample counts and descriptive correlations |

All use `symbol=BTCUSDT&timeframe=15m&startMs=...&endMs=...`, with optional
`asOfMs`. Windows are aligned, half-open and limited to 2,000 slots. Duplicate or
unknown parameters, unsupported markets, future endpoints and future `asOfMs`
are rejected. Missing bars remain gaps. `generatedAtMs` is response time; it does
not replace source publication time.

Features are `return1`, `sma20`, population `volatility20` of returns, Wilder
`rsi14`, `plusDi14`, `minusDi14`, and `adx14`. They use present/past candles only,
reset after gaps, retain actual source availability, and return null with reasons
for warmup or undefined calculations. These definitions are versioned; no TA-Lib
parity is assumed. They are computed by this service on demand, not yet stored as
materialized feature tables or automatically injected into the existing FreqAI
strategy.

Cross-analysis fixes `analysisAtMs` to **candle close +60 seconds**. Every candle
feature and matched T1 publication must be available by that time; future rows
stay pending. Reports published later are excluded even if their event timestamps
are older. Late historical backfills cannot pretend to have been known then.
Matched trade observations must have zero detected ID gaps and be at most 60
seconds old. Missing feeds stay null. Returns/net taker flow, returns/funding and
ADX/funding correlations require at least three usable samples and nonzero
variance; outputs are descriptive associations, not forecasts or causation.

## Freqtrade/FreqAI and Hummingbot consumers

The stdlib `DataLakeClient` reads validated canonical windows without CCXT:

```python
import os
from data_lake.client import DataLakeClient

client = DataLakeClient("http://127.0.0.1:8788", os.environ["MARKET_DATA_TOKEN"])
window = client.read_candles("15m", 1767225600000, 1767312000000)
```

Hummingbot strategy/research code can use this client for past candles. This is a
consumer interface; it does not replace Hummingbot's live order-book connector.

For native Freqtrade OHLCV files, install the optional export dependencies and
export to a **new** directory:

```bash
python -m pip install -r requirements-data-lake-export.txt
python -m data_lake.export --base-url http://127.0.0.1:8788 --timeframe 15m \
  --start-ms 1767225600000 --end-ms 1769904000000 --output-dir .data/research-jan-2026
```

The exporter freezes one `sourceAsOfMs`, reads complete pages through the API,
keeps exact `canonical.json`, and writes
`futures/BTC_USDT_USDT-15m-futures.feather` using the official Freqtrade 2026.9
schema. Feather's float64 conversion can lose precision; canonical JSON remains
exact. `manifest.json`, with file/page/content hashes, is published last and is
the completion marker. Missing pages or an existing output directory fail.
Only completed directories are consumable. This is an OHLCV export; futures
mark-price/funding histories and actual model training remain separate inputs.

For the common paper API and prediction producer, `DATA_LAKE_DATABASE_URL` takes
precedence for candles. Keep `MARKET_DATA_DB` as a local SQLite path for the paper
ledger/write budget. Both inference consumers still query the same two M15
candles with `asOfMs=None`, preserving their existing dataset-identity contract.
The API's 20-bar/2,000-bar previews are separate query identities.

## Validation and operations

GitHub stores source. Codemagic workflow `data-lake-postgres` on
`feature/data-lake-api` starts a disposable PostgreSQL 17 server, requires actual
psycopg/pyarrow imports, runs the PostgreSQL/ASGI/export tests and cleans up. The
`canonical-market-data` workflow retains the existing five-layer regressions.
Codemagic does not host the API, run the long-lived collector or train a model.

Local tests use real SQLite and ASGI requests. Without the optional server/engine,
PostgreSQL and real Feather round-trip checks explicitly skip locally; the new
Codemagic job requires those dependencies and a real database. Production
deployment, backup/restore and live exchange operation require the target server
and operational configuration; source tests do not establish those outcomes.
