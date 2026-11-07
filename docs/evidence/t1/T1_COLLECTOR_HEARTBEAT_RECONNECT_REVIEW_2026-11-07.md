# T1 Collector Heartbeat and Reconnect Contract Review — 2026-11-07

## Scope and verdict

Read-only review of the pinned upstream collector source and the local T1 CSV importer. No collector was built or started; no exchange endpoint was contacted; no capture or database was accessed; no application or runtime configuration was changed.

**Verdict: PARTIAL SOURCE-LEVEL PASS / DURABLE CONNECTION EVIDENCE GAP.** The pinned collector contains WebSocket ping/pong monitoring and automatic reconnect behavior. However, connection lifecycle events are not persisted in the CSV capture schema. The local importer therefore correctly cannot certify connection continuity and reports `connectionStatus=UNVERIFIABLE`.

## Exact source identities

- Five-layer repository branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Five-layer repository HEAD at review: `2103efaa5b5ec2faa4182c7af25764b3924b30fe`.
- Local importer: `futures_intelligence/import_collector.py`, blob `5effe6540b86edcb190456c95b6bb11456aec099`.
- Local importer tests: `futures_intelligence/test_import_collector.py`, blob `19fd6f813d98ca199747d74929f967988bcdde0b`.
- Local T1 README: `futures_intelligence/README.md`, blob `8f475d7ef66b1e0adcb6132ccf57803bee7011c1`.
- Upstream collector pinned by the importer: `waynemason1/binance-futures-collector@bc4f0ef633fbeee4a49defd72827f17162693805`.

## Findings

### 1. Heartbeat and reconnect behavior exists in upstream source

Reviewed:
- [connection_manager.rs](https://github.com/waynemason1/binance-futures-collector/blob/bc4f0ef633fbeee4a49defd72827f17162693805/src/websocket/connection_manager.rs)
- [config.rs](https://github.com/waynemason1/binance-futures-collector/blob/bc4f0ef633fbeee4a49defd72827f17162693805/src/config.rs)
- [config.example.toml](https://github.com/waynemason1/binance-futures-collector/blob/bc4f0ef633fbeee4a49defd72827f17162693805/config.example.toml)
- [message_handler.rs](https://github.com/waynemason1/binance-futures-collector/blob/bc4f0ef633fbeee4a49defd72827f17162693805/src/websocket/message_handler.rs)

Observed source behavior:
- Each symbol batch starts separate WebSocket connections for the `/public` depth route and `/market` trade/kline/liquidation route.
- Client ping interval defaults to 20 seconds. The heartbeat monitor triggers reconnect after `ping_interval_seconds × heartbeat_miss_reconnect`; example config sets the miss multiplier to 3 (60 seconds).
- Server Ping frames receive an explicit Pong response and flush. Client Ping responses (Pong frames) update the in-memory `last_pong` timestamp.
- The message loop also treats more than 30 seconds without any received WebSocket frame as a connection timeout.
- Connection failures reconnect indefinitely with exponential backoff and jitter. Example configuration uses 2,000 ms and 60,000 ms bounds; `max_reconnect_attempts=10` escalates logging but does not stop retries.
- A connection lasting at least 60 seconds resets the retry counter before a later failure.
- Connection state, last-pong time, and reconnect counters are in memory.

These are source-code findings only. They do not prove that this collector version was deployed or that any live connection remained healthy.

### 2. Connection lifecycle is not durably captured

- The upstream message enum has `Connected`, `Disconnected`, and `Error` events.
- The message handler only writes these lifecycle events to application logs. It does not write them into the feed CSVs or a dedicated connection-event dataset.
- The pinned CSV schema contains market observations but no heartbeat, pong, disconnect, reconnect, connection-session, or reconnect-attempt event records.
- The local importer only reads those feed CSVs. It cannot reconstruct exact disconnect intervals from market rows, particularly for quiet feeds or liquidation events.
- The importer deliberately fixes `connectionStatus` to `UNVERIFIABLE`; trade aggregate-ID gaps can be detected, but absence of observed gaps is not proof of continuous transport.

### 3. Existing test coverage boundary

- The local T1 importer fixture suite passed 10/10 in GitHub Actions run `42339519835` at exact SHA `dbe05a406131659d83b22e2b27646cab49a98631`.
- That suite validates CSV parsing, feed semantics, freshness, provenance, trade-ID gaps, and fail-closed snapshot validation.
- It does not compile, run, or test the upstream Rust collector.
- The reviewed upstream connection manager contains unit tests for exponential backoff calculation (including cap/high-attempt behavior), but the inspected tests do not establish simulated pong loss, disconnect-event persistence, reconnect recovery, or durable continuity evidence.

## Required contract before continuity can be certified

Do not infer a continuous connection from event density, last trade time, a successful handshake, or the absence of aggregate-trade ID gaps.

A future, separately scoped upstream change should provide a dedicated append-only connection-event record (not overload trade/funding/OI/liquidation CSV rows). At minimum, the record should identify:
- collector source commit and collector process/session ID;
- connection ID, batch ID, route, and subscribed stream/symbol set;
- event type and UTC event timestamp;
- heartbeat Ping sent / matching Pong received, or an explicit heartbeat result;
- disconnect reason and reconnect attempt/backoff;
- successful reconnect/handshake time.

The importer/quality gate should then validate event ordering and identity, associate each feed with the correct market route and session, and derive connection coverage for the requested half-open window. Missing lifecycle evidence, malformed ordering, unclosed intervals, heartbeat expiry, or unexplained gaps must remain UNKNOWN/UNVERIFIABLE or fail closed; they must never be promoted to CONNECTED by inference.

Before accepting the upstream change, add deterministic offline tests for: ping/pong success, missed-pong timeout, remote close, transport error, retry/backoff progression, successful recovery, process restart/session boundary, event ordering/duplication, and event-file tampering/checksum provenance. No live exchange test is required for this contract stage.

## Status and next step

| Item | Status |
|---|---|
| Pinned source has heartbeat/reconnect implementation | PASS (static source review only) |
| Automatic retry continues beyond configured log threshold | PASS (static source review only) |
| Lifecycle events emitted internally | PASS (in-memory message enum) |
| Lifecycle events persisted in capture | NOT IMPLEMENTED in pinned schema |
| Local importer can prove connection continuity | NOT POSSIBLE with current inputs |
| Live collector behavior / reconnect under outage | NOT VERIFIED; NOT RUN |
| T1 operational readiness | NOT CERTIFIED |

**Recommended next bounded task:** prepare a schema proposal and offline acceptance tests for a dedicated connection-event sidecar, keeping the current CSV importer backward compatible and preserving `connectionStatus=UNVERIFIABLE` until the new evidence is present.

No collector activation, exchange capture, database access, Canonical SQLite creation, Feeder startup, T2 source switch, merge, VPS provisioning, or live execution is authorized by this review. `ai_execution_enabled=false`.


## 2026-11-07 Addendum — Exact-version security graph and CI results

- Fork source SHA `22900b860426a5c19622ec6b5ea3673646df2229`; PR #1 remains OPEN / DRAFT / NOT MERGED.
- PR run 42350687437 checked out synthetic merge SHA `ac53d7b672e91590f16e555f2ef0ffd232ab905c`; push run 42350684200 checked out source SHA `22900b860426a5c19622ec6b5ea3673646df2229`.
- Both runs passed collector library 40/40, binary 1/1, sidecar writer 11/11, Rust format/Clippy/build, dashboard backend/frontend and Docker. Security failed at cargo-audit (12 vulnerabilities + 2 warnings); npm audit steps skipped. No artifacts.
- Exact-version all-target graph confirms reverse paths for rustls 0.23.43, rustls-webpki 0.103.14, webpki-root-certs 1.0.9, webpki-roots 1.0.9, tokio 1.53.1 and chacha20 0.10.1. Key paths are recorded in `T1_COLLECTOR_CARGO_AUDIT_EXACT_EVIDENCE_2026-11-07.md`.
- `quinn-proto@0.11.16` remains NOT VERIFIED: cargo tree returned "nothing to print" with exit 0. The diagnostic script's PRESENT marker is a false-positive condition and must not be treated as reachability evidence.
- No dependency or runtime changes. Sidecar remains an offline reference implementation; no collector was started and no exchange/data/database operation was performed. T1 continuity remains NOT CERTIFIED; security BLOCKED.
