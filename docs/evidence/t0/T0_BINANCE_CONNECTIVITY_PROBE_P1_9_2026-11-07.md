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


## 2026-11-07 — PC rerun and WebSocket timeout-stage observability

### PC run on implementation SHA ab564ecc

User ran:
- Source folder: `btcusdt-telegram-signals2-ab564eccbb9c0484fdd30b694f5b052bc4a2c991`.
- Probe time: `2026-11-07T01:57:09Z`.
- REST: **5/5 PASS**; ping 211.28 ms, time 117.62 ms, exchangeInfo 216.14 ms, M15 114.80 ms, H1 135.95 ms. Every endpoint HTTP 200 and schema_valid true.
- WebSocket: `TIMEOUT`, `TimeoutError`, 20,440.33 ms, `status:null`, event_valid false.
- No credentials, proxy, DB, Feeder, persistence, or execution.
- Because the old probe discarded HTTP Upgrade status when a later read timed out, this output alone does not distinguish timeout during handshake from timeout waiting for the first event. The earlier independent PowerShell HTTP 101 observation is not evidence that this particular probe run completed the upgrade.

### Timeout-stage diagnostic change

- Added `stage` to WebSocket probe outcomes:
  - `TCP_CONNECT`
  - `TLS_HANDSHAKE`
  - `HTTP_UPGRADE`
  - `WAITING_FOR_KLINE_EVENT`
  - `KLINE_EVENT_RECEIVED`
- Preserve HTTP status 101 after a successful Upgrade, even if receiving the first Kline frame times out.
- A timeout after a validated 101 Upgrade is now classified `EVENT_TIMEOUT`; timeouts before that stage retain their appropriate network timeout classification.
- Bounded error detail is retained.
- TDD RED for the isolated timeout-stage contract: commit `01bfdb9bd9aa9b21d42f4f505b37634548e2aee5`, workflow [42326976887](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42326976887), expected import failure because `_websocket_failure_result` had not yet been implemented.
- GREEN implementation SHA: `f61deca1cd7874e61851ca52ad4857bd0ff4535c`.
- Dedicated offline workflow [42327017054](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42327017054): **16 tests PASS**, including `test_timeout_after_upgrade_is_classified_as_event_timeout`.
- Artifact ID `13555462335`; name `t0-binance-probe-contracts-f61deca1cd7874e61851ca52ad4857bd0ff4535c`; size 938 bytes; GitHub upload digest `sha256:dde5bbb0f6b76903c62566cd238a9297292857533b8ea6e47f33f183ddbb2402`.
- The implementation request retains proper HTTP CRLF framing; the final test run verifies syntax and offline contracts. The previous intermediate mock-based integration fixture attempts failed and were replaced with a focused deterministic classification contract; those intermediate failures are not represented as PASS.

### Current gate status

| Gate | Status |
|---|---|
| Latest PC REST sample | PASS 5/5 |
| Latest PC WebSocket first event | NOT VERIFIED |
| WebSocket stage diagnostics | PASS on dedicated CI |
| Offline probe contracts | PASS 16/16 on SHA `f61deca1cd7874e61851ca52ad4857bd0ff4535c` |
| Controlled First Run / canonical ingestion / Feeder | NOT AUTHORIZED / NOT RUN |

Next: update PC source from exact SHA `f61deca1cd7874e61851ca52ad4857bd0ff4535c` and rerun only the read-only probe. Interpret `status=101` + `stage=WAITING_FOR_KLINE_EVENT` + `classification=EVENT_TIMEOUT` as successful Upgrade but no first Kline event observed within the timeout; it is not full WebSocket data-plane acceptance.


### Follow-up PC observation — 2026-11-07T02:05:21Z

- User reran the read-only probe on the updated diagnostic implementation (source SHA expected from the supplied run context: `f61deca1cd7874e61851ca52ad4857bd0ff4535c`; the JSON itself does not embed a source SHA, so exact runtime provenance remains user-folder/context reported, not independently attested).
- REST: **5/5 PASS**; all five endpoints returned HTTP 200 and valid schemas. Latencies: ping 190.69 ms; time 127.13 ms; exchangeInfo 250.60 ms; closed M15 143.63 ms; closed H1 142.83 ms.
- WebSocket: **TIMEOUT at HTTP_UPGRADE**, `status=null`, `TimeoutError: The read operation timed out`, 20,433.86 ms. The probe did not receive/validate HTTP 101. This is before the first-event wait stage; do not classify it as an event timeout.
- This repeat confirms the same broad split as the prior run: REST is reachable in the sampled interval, while the official WebSocket handshake remains blocked/unverified from this PC/network path. It does not establish the cause (firewall, ISP/network policy, endpoint path, or other handshake-path issue).
- Safety fields confirm no credentials, proxy, DB, Feeder, persistence, or AI execution were used.

### Updated gate verdict

| Gate | Status |
|---|---|
| PC REST reachability | CONDITIONAL PASS — 5/5 on two recent samples; not yet a durable availability/SLA claim |
| Official WebSocket HTTP Upgrade | BLOCKED — timeout at `HTTP_UPGRADE`, no HTTP 101 |
| Official WebSocket Kline event | NOT RUN — handshake did not complete |
| P1.9 overall | BLOCKED — REST passes but required WebSocket gate does not |
| Canonical ingestion / Controlled First Run / Feeder | NOT AUTHORIZED / NOT RUN |

Next diagnostic step: compare the probe's exact HTTP Upgrade request/response path with a fresh direct PowerShell handshake test from the same PC and network, recording timestamp, target host/path, HTTP status and response headers (never include secrets). A successful independent handshake would narrow the issue to differences in the probe's request/socket handling; a timeout there would point to the PC/network path or endpoint reachability. Do not add alternate domains, VPN/proxy, retries that bypass policy, or modify the probe until this comparison is available.



### Follow-up — PowerShell handshake comparison and HTTP header terminator fix (2026-11-07)

#### Independent PC handshake observation

- User ran a direct PowerShell 5.1.19041.4291 handshake at 2026-11-07T02:10:07Z.
- Target: fstream.binance.com:443/ws/btcusdt@kline_1m.
- TCP: PASS; TLS 1.2: PASS.
- Server returned HTTP/1.1 101 Switching Protocols; Sec-WebSocket-Accept validation: VALID.
- Measured elapsed time: 413.58 ms.
- This verifies an independent handshake for the 1m stream at that timestamp. It does not verify the probe's 15m stream or receipt of a Kline event.

#### Source-level root cause

- Compared the exact probe source at f61deca1cd7874e61851ca52ad4857bd0ff4535c with the successful PowerShell handshake.
- The probe passed a double-escaped CRLF marker to _recv_until, representing literal backslash characters rather than the HTTP header terminator bytes CRLF CRLF.
- As a result, the probe kept reading after receiving a valid HTTP 101 header block and timed out at HTTP_UPGRADE.
- Corrected by adding _recv_http_upgrade_response() using the actual byte marker b"\r\n\r\n" and routing the probe through that helper.

#### TDD and GitHub Actions evidence

- RED test commit: 8a7ab00f6f6a39c3ad63079298c9f6e0b397e2f9.
- RED workflow: [42327787488](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42327787488), failed as expected because _recv_http_upgrade_response was not yet implemented (ImportError). This confirms the new regression contract could not pass against the pre-fix implementation.
- Final tested source SHA: 54f9344e42baa2bd92a45fd6d96eae35c2b49148.
- Dedicated offline workflow: [42327833404](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42327833404), SUCCESS; exact checked-out SHA confirmed in logs; syntax compilation PASS; 17/17 probe contract tests PASS, including test_reads_headers_until_real_crlf_terminator.
- Artifact: [13556555458](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42327833404/artifacts/13556555458); name t0-binance-probe-contracts-54f9344e42baa2bd92a45fd6d96eae35c2b49148; size 983 bytes; GitHub upload digest sha256:9de24a8856c23cd402772c6577fbd543cd75441d6aefe2418713926cdaf6baee. Payload bytes have not been independently downloaded and re-hashed.

#### Updated verdict and boundary

| Gate | Status |
|---|---|
| PC direct PowerShell HTTP Upgrade (1m stream) | PASS — HTTP 101 and accept digest valid |
| Probe HTTP response terminator handling | PASS — regression fixed and 17/17 offline contracts pass |
| Probe WebSocket HTTP Upgrade (15m stream) | NOT YET RE-RUN ON PC |
| WebSocket 15m Kline event | NOT VERIFIED |
| REST reachability | CONDITIONAL PASS — recent 5/5 samples, not a durability/SLA claim |
| P1.9 overall | BLOCKED / NOT VERIFIED pending fresh PC probe |
| Canonical ingestion / DB / Feeder / Controlled First Run | NOT AUTHORIZED / NOT RUN |
| AI execution | DISABLED |

Next: download source snapshot from exact SHA 54f9344e42baa2bd92a45fd6d96eae35c2b49148, run the existing offline tests locally, then run only the read-only probe with explicit network confirmation. Record the resulting JSON and verify its source SHA separately. No credentials, proxy/VPN, alternate endpoint, DB writes, persistence, Feeder, or execution.


### P1.9 PC rerun — Upgrade succeeds, first 15m Kline event times out (2026-11-07)

- User-provided probe observation: `2026-11-07T02:15:07Z`.
- REST: **5/5 PASS**; all endpoints returned HTTP 200 and valid schemas. Latencies: ping 208.05 ms; time 134.20 ms; exchangeInfo 723.02 ms; closed M15 136.84 ms; closed H1 125.60 ms.
- WebSocket: `status=101`, `stage=WAITING_FOR_KLINE_EVENT`, `classification=EVENT_TIMEOUT`, `TimeoutError`, 20,430.78 ms; `event_valid=false`. This proves the probe completed and validated the HTTP Upgrade for its configured `/ws/btcusdt@kline_15m` stream, but no first WebSocket event was received before timeout.
- This is progress from the prior `HTTP_UPGRADE/status=null` result. The CRLF response-header reader is no longer the observed blocker. It does **not** prove the Binance server failed to publish data; possible causes remain unisolated (15m stream/path behavior, network middlebox/data-frame delivery, or client frame reception).
- Binance USDⓈ-M official market-stream documentation describes Kline updates for an existing current candle at 250 ms intervals. A 20.43-second first-event timeout is therefore anomalous and requires a controlled comparison; it is not explained by the 15-minute candle duration. Reference: https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Kline-Candlestick-Streams
- The supplied JSON does not include a source SHA. The intended PC snapshot was the archive pinned to source SHA `54f9344e42baa2bd92a45fd6d96eae35c2b49148`; runtime provenance remains contextual, not independently attested by the JSON.
- Safety fields: no credentials, proxy, DB, Feeder, market-data persistence, or AI execution.
  
#### Updated gate verdict

| Gate | Status |
|---|---|
| PC REST | CONDITIONAL PASS — 5/5 in this sample; not an SLA claim |
| Probe HTTP Upgrade for 15m | PASS — validated HTTP 101 |
| First 15m Kline event | NOT VERIFIED — 20.43s event timeout |
| P1.9 overall | BLOCKED / NOT VERIFIED |
| Canonical ingestion / DB / Feeder / Controlled First Run | NOT AUTHORIZED / NOT RUN |
| AI execution | DISABLED |

Next diagnostic: from the same PC/network, compare first-frame receipt for `btcusdt@kline_15m` and `btcusdt@kline_1m` using a direct WebSocket client, recording only endpoint interval, HTTP status, first frame opcode/length, and elapsed time. Do not change the canonical probe interval or accept a non-15m stream as satisfying P1.9. Keep the test read-only; no alternate host, VPN/proxy, credentials, DB, Feeder, or persistence.


### Same-PC direct .NET WebSocket comparison — both streams receive no first frame (2026-11-07)

- User ran the direct PowerShell `ClientWebSocket` comparison against `wss://fstream.binance.com/ws/btcusdt@kline_15m` and `...@kline_1m`.
- Both `ConnectAsync` operations completed and reported `WebSocketState.Open`.
- Both first `ReceiveAsync` operations were canceled at the 20-second timeout:
  - 15m: 20,008 ms; no frame received.
  - 1m: 20,006 ms; no frame received.
- The displayed `System.Threading.Tasks.VoidTaskResult` is incidental PowerShell output from the async connect invocation; the relevant observations are successful `Open` state followed by receive cancellation.
- This independent .NET client reproduces the same handshake-success / first-frame-timeout symptom as the Python probe on both intervals. This reduces the likelihood that the issue is limited to Python's WebSocket frame parser/receiver. It does not identify whether the cause is Binance edge/stream delivery, local network/intermediary handling after Upgrade, or another transport behavior.
- No frame opcode or payload was observed. No credentials, proxy/VPN, DB, Feeder, persistence, or AI execution were used.

#### Updated verdict

| Gate | Status |
|---|---|
| REST | CONDITIONAL PASS — recent 5/5 sample |
| Python probe HTTP Upgrade | PASS — HTTP 101 |
| .NET WebSocket Upgrade | PASS — both sockets Open |
| First frame on 15m | NOT RECEIVED — 20.008s timeout |
| First frame on 1m | NOT RECEIVED — 20.006s timeout |
| Python-only receiver defect hypothesis | DOWNGRADED — independent .NET client shows same symptom |
| Root cause | NOT DETERMINED |
| P1.9 overall | BLOCKED / NOT VERIFIED |

Next diagnostic should capture WebSocket control-frame behavior and compare the same PC/network against a separately documented Binance public WebSocket endpoint only if needed to isolate host/path policy; do not accept a different endpoint or interval as T0 Binance USD-M acceptance. Do not add proxy/VPN, credentials, persistence, DB, Feeder, or live execution.


### P1.9 endpoint route correction — current USD-M market WebSocket path (2026-11-07)

#### Root cause identified from current Binance documentation

- The probe source before this increment used `WS_PATH = "/ws/btcusdt@kline_15m"`.
- Current official Binance USDⓈ-M WebSocket Market Streams documentation specifies the raw Kline route as `wss://fstream.binance.com/market/ws/{symbol}@kline_{interval}`, with combined route `/market/stream?streams=...`. It documents current Kline updates every 250 ms when an existing candle is available. Source: https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/ws-streams/market#kline-candlestick-streams
- Therefore, the earlier Python and PowerShell tests were both testing the legacy `/ws` route. The .NET comparison was not independent evidence for the current documented route. Its Open state only proved the old route's Upgrade, not that the current USD-M Kline subscription was correctly addressed.
- This is the concrete configuration defect to correct; no network policy, proxy, or parser workaround is justified by the previous evidence.

#### TDD and GitHub Actions

- RED test commit: `14e744e8ff124aa478aa8c82a9bfb579b2521a89`; added `test_usdm_kline_stream_uses_current_market_ws_route` asserting `/market/ws/btcusdt@kline_15m`.
- Dedicated offline workflow [42328640533](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42328640533) failed at the new route assertion on the old `/ws` constant (expected RED).
- Implementation source SHA: `2b4cc1cd0f7c3e55e6de27388df6c4e87de811e3`; changed only `WS_PATH` to `/market/ws/btcusdt@kline_15m`.
- Dedicated offline workflow [42328662902](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42328662902): exact SHA checkout confirmed; py_compile PASS; **18/18 probe contract tests PASS**; offline scope guard PASS; no external network, credentials, DB, Feeder, persistence, or AI execution.
- Artifact [13556750284](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42328662902/artifacts/13556750284), name `t0-binance-probe-contracts-2b4cc1cd0f7c3e55e6de27388df6c4e87de811e3`, size 1,010 bytes, upload digest `sha256:9640bb7daebd67b4330663a07ee8f92372bf013d6a8f6007000f8dab016432c1`. Payload has not been independently downloaded/re-hashed.

#### Updated gate verdict

| Gate | Status |
|---|---|
| Route matches current official USDⓈ-M Kline docs | PASS in source and offline test |
| Probe contracts | PASS 18/18 on exact SHA `2b4cc1cd0f7c3e55e6de27388df6c4e87de811e3` |
| PC handshake on corrected `/market/ws` route | NOT YET TESTED |
| First 15m Kline event on corrected route | NOT VERIFIED |
| P1.9 overall | BLOCKED / NOT VERIFIED pending PC rerun |

Next: user downloads the exact source snapshot at `2b4cc1cd0f7c3e55e6de27388df6c4e87de811e3`, runs the offline contract tests, then runs only the read-only network probe. The old PowerShell `.NET ClientWebSocket` test must be updated to the documented `/market/ws/...` path if independently repeated. Do not use the old `/ws` result as current endpoint evidence. No DB writes, canonical ingestion, Feeder, Controlled First Run, VPS, proxy/VPN, or AI execution.
