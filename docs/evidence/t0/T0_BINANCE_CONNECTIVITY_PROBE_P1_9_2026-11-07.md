# T0 P1.9 — Binance USD-M Public Connectivity Probe

Date: 2026-11-07 (UTC)

## Scope and authorization

P1.9 was approved to implement a read-only connectivity probe for the target PC/network. This work is limited to public Binance USD-M REST and WebSocket reachability. It does not authorize production ingestion or runtime activation.

Safety invariants:
- No API key or secret is used.
- REST requests do not inherit HTTP proxy environment settings; WebSocket connects directly over verified TLS.
- No SQLite/PostgreSQL database is opened or created.
- No Feeder, scheduler, recovery coordinator, or `sync_window()` is started.
- No market data is persisted.
- `ai_execution_enabled=false`; no orders or execution are possible.
- GitHub Actions runs offline contract tests only. It does not contact Binance.

## Implementation

Files:
- `market_data/binance_connectivity_probe.py`
- `market_data/test_binance_connectivity_probe.py`
- `.github/workflows/t0-binance-connectivity-probe.yml`
- `market_data/README.md`

Direct PC command:

```bash
python3 -m market_data.binance_connectivity_probe --confirm-network
```

Optional timeout:

```bash
python3 -m market_data.binance_connectivity_probe --confirm-network --timeout 10
```

REST checks:
- `GET /fapi/v1/ping`
- `GET /fapi/v1/time`
- `GET /fapi/v1/exchangeInfo` and validate BTCUSDT TRADING / PERPETUAL / BTC-USDT settlement metadata
- `GET /fapi/v1/klines?symbol=BTCUSDT&interval=15m&limit=2` and validate a closed candle
- `GET /fapi/v1/klines?symbol=BTCUSDT&interval=1h&limit=2` and validate a closed candle

WebSocket check:
- Direct TLS connection to `fstream.binance.com:443`
- RFC6455 upgrade validation
- Subscribe to `/ws/btcusdt@kline_15m`
- Require a valid BTCUSDT 15m kline event

HTTP 451, 429, 401/403, 5xx, DNS, TLS, timeout and generic connection errors are reported separately. The probe does not try alternative domains, VPNs, proxies, or other network circumvention.

Scope exclusion: T1 funding rate, open interest, taker flow, large trades and liquidation endpoints are not part of this T0 M15/H1 acceptance.

## Test evidence

TDD progression:
- RED: workflow run [42323474586](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42323474586), source SHA `0b68f0469676eb4c4cd8d988b0590456a97c3ff2`; tests could not compile because the implementation module had not yet been added.
- Subsequent fixture failures exposed an unaligned M15 timestamp and incorrectly escaped CRLF in the test handshake fixture. Both were corrected in later commits.
- GREEN: workflow run [42323874872](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42323874872), source SHA `688e108ba84b1de526d32cc03a9129e0ae952e9c`.
- Job `128254520505`: SUCCESS.
- Offline probe contract tests: **11/11 PASS**.
- Artifact ID `13553953410`; name `t0-binance-probe-contracts-688e108ba84b1de526d32cc03a9129e0ae952e9c`; GitHub upload ZIP SHA-256 `0564a3fc7a9889adcc9c99237f555f3dacb3530874a1bec83cdbd8332503ad82`.
- Artifact URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42323874872/artifacts/13553953410

The green run checked out exactly the source SHA recorded above. Its environment had empty DB and exchange credential variables and `AI_EXECUTION_ENABLED=false`.

## Additional regression evidence

The existing T0 Single Writer Gateway workflow also ran on the same implementation SHA:
- Workflow run [42323874886](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42323874886), exact checkout SHA `688e108ba84b1de526d32cc03a9129e0ae952e9c`.
- Static Gateway job `128254667811`: SUCCESS. Complete `market_data` discovery: **251 tests, 42 skipped, OK**.
- Paper consumer job `128254668064`: SUCCESS.
- Fresh-cluster provider bootstrap job `128254668032`: FAILED at the known migration-role guard: `t0_migrator may only be granted to the ephemeral t0_migrator_login role`. No guard was weakened; this is a separate PostgreSQL 16 provider-bootstrap blocker, not a Binance probe failure.
- Isolated TimescaleDB job `128254761702`: FAILED only in the concurrently added PG-LC-07 test `test_interrupted_migration_rolls_back_and_retry_applies_cleanly`; psycopg raised `ProgrammingError: only '%s', '%b', '%t' are allowed as placeholders, got '%p'`. Other TimescaleDB integration assertions in that job were executed, but the job conclusion is FAILURE. This is a separate PG-LC-07 test defect, not a Binance probe failure.
- Static artifact ID `13553339580`; GitHub digest `sha256:3fd69246338950f5d2588238fa649331e0da8faf43a5ac3f3fe0c41c2c5808be`. Paper artifact ID `13554027300`; digest `sha256:e76bc0af0261f6088f727c2104cba92a26d177705fc848e2d33fb3a672dab83a`. These are GitHub upload metadata digests, not independently recomputed payload hashes.

## Verdict

| Gate | Status | Evidence |
|---|---|---|
| Probe implementation and syntax | PASS | Exact-SHA workflow run 42323874872 |
| Offline REST/WS contract tests | PASS (11/11) | Artifact 13553953410 |
| GitHub Actions workflow isolation | PASS | Empty DB/credential env; offline tests only |
| PC DNS/TLS/REST reachability | NOT VERIFIED | Must run the command on the target PC |
| PC WebSocket reachability | NOT VERIFIED | Must run the command on the target PC |
| Binance M15/H1 live response acceptance | NOT VERIFIED | No live Binance request was made by CI |
| Canonical T0 ingestion / Feeder activation | NOT RUN / NOT AUTHORIZED | Explicitly outside P1.9 |

A successful 11/11 GitHub Actions run proves only that the probe contracts pass. It is not evidence that Binance is reachable from the user's PC or that historical coverage is complete.

## Next gate

Run the command on the target PC and save the JSON report. Review the exact endpoint classifications and response validation. If REST and WebSocket are reachable, proceed to a separately authorized Controlled First Run using an isolated temporary destination; do not write to the canonical T0 database until the acceptance and authorization gates are met.

Current branch: `feature/t0-centralized-data-feeder-p1-20261101`.
Implementation GREEN source SHA: `688e108ba84b1de526d32cc03a9129e0ae952e9c`.
Documentation update commit: `d612774c9e5fd056a311d572f754065599f73f81`.
