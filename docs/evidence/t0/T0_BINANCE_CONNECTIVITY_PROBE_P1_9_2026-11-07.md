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


## 2026-11-07 — PC observation and WebSocket receiver diagnostics

### Target-PC observations (user-provided)

- First official probe:
  - REST 5/5: HTTP 200; schemas valid.
  - WebSocket: TIMEOUT at approximately 10.45 seconds.
- Second official probe:
  - Ping, server time, M15 and H1: HTTP 200; schemas valid.
  - Exchange Info: `URLError` / `CONNECTION_ERROR` after 29.71 ms; original reason was not retained by the probe.
  - WebSocket: TIMEOUT at approximately 20.33 seconds.
- Independent PowerShell checks:
  - DNS resolution succeeded (8 IPv4 answers were observed; answer sets can rotate).
  - TCP port 443: `TcpTestSucceeded=True`.
  - TLS authentication: `True`, protocol TLS 1.2, AES-128.
  - Manual RFC6455 handshake: HTTP 101 Switching Protocols, Upgrade and Connection headers accepted.
  - The PowerShell `Find-NetIPsecRule` command-not-found diagnostic did not invalidate the reported TCP success.
- Boundary: the manual handshake did not read/validate a Kline event. Therefore it does not upgrade WebSocket event delivery to PASS.

### TDD receiver and diagnostics correction

- Test-first commit: `16ca2f0896cccbbf0273e669f9feefc9874f9014`.
- RED workflow: [42326134473](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42326134473), exact source SHA `16ca2f0896cccbbf0273e669f9feefc9874f9014`; failed as expected because `_receive_kline_event` had not yet been implemented/imported.
- RED artifact ID `13554977848`; name `t0-binance-probe-contracts-16ca2f0896cccbbf0273e669f9feefc9874f9014`; upload digest `sha256:46136092c8f2a6ea23e97f85f63301a194fc3e18e0edcc56b667fc44c37c50e9`.
- Implementation commit / exact source SHA: `ab564eccbb9c0484fdd30b694f5b052bc4a2c991`.
- Changes:
  - Read WebSocket frames until a text event arrives.
  - Reply to server Ping with a masked client Pong carrying the same payload.
  - Ignore Pong frames; classify Close before first event as a connection closure.
  - Enforce the RFC6455 125-byte control-frame limit.
  - Preserve bounded `URLError.reason` type and detail in REST diagnostics.
- GREEN workflow: [42326194320](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42326194320), exact source SHA `ab564eccbb9c0484fdd30b694f5b052bc4a2c991`; dedicated offline contracts **15/15 PASS**.
- GREEN artifact ID `13554799956`; name `t0-binance-probe-contracts-ab564eccbb9c0484fdd30b694f5b052bc4a2c991`; GitHub upload digest `sha256:41b66386edded07ad4a98f89dfa0ec4fbbb3805dc9f446849640b614d1d322af`.

### Full T0 regression on the implementation SHA

- Workflow: [42326194295](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42326194295), push event, branch `feature/t0-centralized-data-feeder-p1-20261101`, exact head/checkout SHA `ab564eccbb9c0484fdd30b694f5b052bc4a2c991`.
- Static Gateway job `128262017337`: SUCCESS. Complete `market_data` suite **255 tests, 42 skipped, OK**; static Gateway, behavioral/Feeder, Health/Readiness, and process SIGKILL steps also completed successfully.
- Paper consumer job `128262017581`: SUCCESS.
- Static artifact ID `13555675449`; name `t0-swg-contract-evidence-ab564eccbb9c0484fdd30b694f5b052bc4a2c991`; size 11,285 bytes; GitHub upload digest `sha256:0cdd64351806dc64ead10583cdfc8dc2b9efa4942e4a1ffec886fc2c40cbd5bb`.
- Paper artifact ID `13555535334`; name `t0-paper-consumer-tests-ab564eccbb9c0484fdd30b694f5b052bc4a2c991`; size 1,694 bytes; GitHub upload digest `sha256:7863f192dbdfeeb957eb439d59ae462fa4e7c6406863f5922a966c56a7300c44`.
- Fresh-cluster restricted provider bootstrap and isolated TimescaleDB integration jobs were still running at the time of this evidence update. Their conclusions are deliberately NOT RECORDED until the jobs complete. Existing provider-bootstrap role guard and PG-LC-07 placeholder failure remain unrelated known blockers; do not weaken guards or bypass dependencies.
- GitHub upload digests above are workflow metadata; artifact payload ZIPs have not been independently downloaded and re-hashed in this increment.

### Updated verdict at this evidence point

| Gate | Status |
|---|---|
| PC REST reachability | CONDITIONAL / INTERMITTENT (two samples differ) |
| PC DNS / TCP 443 / TLS 1.2 | PASS for the observed independent checks |
| Manual WebSocket HTTP Upgrade | PASS |
| Official probe WebSocket Kline event | NOT VERIFIED (both attempts timed out) |
| TDD RED | PASS (expected failing test import) |
| Dedicated offline contracts | PASS (15/15) |
| Static T0 regression | PASS (255 tests, 42 skipped) |
| Paper consumer regression | PASS |
| Disposable PostgreSQL integration jobs | IN PROGRESS at evidence capture |
| Controlled First Run / canonical ingestion / Feeder | NOT AUTHORIZED / NOT RUN |

No network request was made by GitHub Actions. No API credentials, DB, canonical T0 store, Feeder, sync operation, proxy/VPN, or execution capability was used.


### Final exact-SHA regression reconciliation — run 42326194295

The run completed. All jobs checked out exact source SHA `ab564eccbb9c0484fdd30b694f5b052bc4a2c991`.

- Static Gateway job `128262017337`: **SUCCESS**; complete `market_data` suite 255 tests, 42 skipped, OK.
- Paper consumer job `128262017581`: **SUCCESS**.
- Fresh-cluster restricted provider bootstrap job `128262017655`: **FAILURE** at the existing strict role membership guard: `t0_migrator may only be granted to the ephemeral t0_migrator_login role`. This is unchanged from prior runs and unrelated to the probe.
- Isolated TimescaleDB job `128262082698`: **FAILURE** in the pre-existing PG-LC-07 test `test_interrupted_migration_rolls_back_and_retry_applies_cleanly`; psycopg raised `ProgrammingError: only '%s', '%b', '%t' are allowed as placeholders, got '%p'`. The job ran the PostgreSQL atomic writer suite (10 tests, one error) and then skipped the dependent FeederRuntime, lifecycle, role-privilege, and read-only TimescaleDB steps. Do not claim those skipped suites passed.
- TimescaleDB artifact `13555023203`; name `t0-timescale-read-only-evidence-ab564eccbb9c0484fdd30b694f5b052bc4a2c991`; size 1,181 bytes; GitHub upload digest `sha256:e76db931726ada7aa9e66c1d311f44a515f9b04e044ec1338415ede400500ef7`.
- Provider bootstrap artifact `13555685559`; digest `sha256:43a34c348822115e02bb5f177421d2d6511ddfaa4fc99f5eaf8a241e65b68612`.
- Overall workflow [42326194295](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42326194295): **FAILURE due to the two pre-existing independent blockers above**. Probe-specific offline contracts and the static market_data/paper regressions remain PASS.
- No PG-LC-07 fix was attempted in this work. No role guard was weakened. Artifact digests remain GitHub upload metadata and have not been independently recomputed from downloaded ZIP payloads.

Final code verdict remains: probe receiver/diagnostic change **PASS on dedicated CI**; broader static regression **PASS**; provider/bootstrap and PG-LC-07 integration blockers **BLOCKED**; target-PC WebSocket Kline event **NOT VERIFIED**.
