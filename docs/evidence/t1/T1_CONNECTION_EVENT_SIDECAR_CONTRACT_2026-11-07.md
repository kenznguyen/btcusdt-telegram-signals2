# T1 Connection Event Sidecar Contract — 2026-11-07

## Verdict and scope

**PASS for offline contract validator and fixture tests only. NOT IMPLEMENTED in the upstream collector. NOT OPERATIONAL.**

This increment adds a separate JSONL connection-event validator. It does not change the existing CSV importer, start or modify the Rust collector, contact an exchange, open a database, or capture live data. The legacy importer continues to return `connectionStatus=UNVERIFIABLE`.

## Source and CI identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- CI source SHA: `8ef12c8839ab15cf2e60c6d06e4386250c0621d6`
- Workflow run: [42340838793](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42340838793)
- Dedicated job: `128308192940`, T1 Futures Intelligence importer offline tests.
- Dedicated job conclusion: **SUCCESS**; checked-out SHA in job logs exactly matches the workflow head SHA above.
- Overall workflow conclusion: **SUCCESS**, all 5/5 jobs completed successfully (Static Gateway, Paper consumer, T1 offline tests, restricted provider bootstrap, isolated TimescaleDB integration).
- Python compile: PASS for importer, importer tests, sidecar validator, sidecar tests, and shared values module.
- Combined suite: **24/24 tests PASS** — 10 legacy importer regression tests and 14 connection-event sidecar tests.
- T1 evidence artifact: [13561403522](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42340838793/artifacts/13561403522)
  - Name: `t1-importer-offline-evidence-8ef12c8839ab15cf2e60c6d06e4386250c0621d6`
  - Size: 1,775 bytes
  - GitHub upload digest: `sha256:62de84e2ffd59808661e512be8c827ea9b117eadf6888f468be779d3cc9620c8`
- The artifact digest is GitHub's upload digest; ZIP payload bytes were not downloaded and independently re-hashed.
- A prior exact-source attempt at SHA `15f917bec81d7e2999976302fe152ef5f31207fc` failed one fixture because a reconnect event occurred beyond its declared capture watermark. The fixture was corrected to declare a watermark covering that event; final SHA `8ef12c8...` passes all 24 tests.

## Files

- `futures_intelligence/connection_events.py`: offline parser, integrity checks, lifecycle state validation, and conservative window verdict.
- `futures_intelligence/test_connection_events.py`: deterministic temporary-file fixtures.
- `.github/workflows/t0-single-writer-gateway-red.yml`: T1 offline job now compiles and runs both importer and sidecar test suites.
- `futures_intelligence/import_collector.py`: unchanged.
- `futures_intelligence/test_import_collector.py`: unchanged.

## JSONL event contract v1

One UTF-8 JSON object per line, appended in non-decreasing `eventAtMs` order. Common fields:

| Field | Requirement |
|---|---|
| `schemaVersion` | Integer `1` |
| `eventId` | Unique event identifier |
| `sourceCommit` | Exact 40-character collector source SHA |
| `sessionId` | Collector process/session identity; changes after process restart |
| `connectionId` | Unique identity for one WebSocket socket lifetime |
| `batchId` | Non-negative collector batch identity |
| `route` | `public` or `market` |
| `eventType` | One of the event types below |
| `eventAtMs` | UTC Unix epoch milliseconds |

Event types:
- `CONNECTED`: WebSocket connection established.
- `PING_SENT`: requires unique `heartbeatId`.
- `PONG_RECEIVED`: requires the matching outstanding `heartbeatId`.
- `DISCONNECTED`: requires reason: `REMOTE_CLOSE`, `TRANSPORT_ERROR`, `HEARTBEAT_TIMEOUT`, `SHUTDOWN`, or `UNKNOWN`.
- `RECONNECT_SCHEDULED`: requires positive `attempt` and `delayMs` in [1, 60000].

Producer requirements for a future collector implementation:
1. Use one append-only event stream per collector process/session; do not merge process restarts under one `sessionId`.
2. Assign a new `connectionId` for each socket lifetime. Keep `batchId` and `route` stable for that connection.
3. Persist each lifecycle/heartbeat event with its UTC timestamp; do not synthesize Pong events from successful market messages.
4. Pair each Pong to the exact client Ping using `heartbeatId`.
5. Persist the disconnect reason and reconnect attempt/delay before starting the next socket.
6. Seal each captured sidecar segment and finalize a trusted manifest with byte size, SHA-256, and `captureCompleteThroughMs` watermark. The watermark must cover the requested window end; do not treat an unsealed/truncated tail as evidence of no disconnect.
7. Keep event output independent of trades/funding/OI/liquidation CSV schemas.

## Validator rules

`load_and_validate_connection_events(...)` requires the expected file SHA-256, collector source SHA, session ID, half-open window `[startMs,endMs)`, heartbeat gap policy, `capture_finalized=True`, a trusted `capture_complete_through_ms >= windowEndMs`, and optionally expected (batchId, route) pairs. Events later than the trusted watermark are rejected. The result exposes the finalized flag and watermark. A sealed capture segment does not require stopping the collector process.

Resource bounds: 64 MiB sidecar, 16 KiB per event line, 100,000 events.

- Reject malformed JSON, unsupported schema, wrong source/session, checksum mismatch, duplicate event IDs, unordered records, connection identity reuse across batch/route, invalid lifecycle transitions, duplicate heartbeat IDs, unmatched Pong, invalid disconnect reason, and invalid reconnect delay/attempt.
- A connection is `VERIFIED_CONNECTED` only if it was opened at/before window start, has paired Pong evidence spanning the window boundaries with no excessive heartbeat gap or expired unanswered Ping, and has no disconnect inside the half-open window.
- A disconnect inside the window yields `DISCONNECTED`.
- Missing/excessive heartbeat evidence yields `HEARTBEAT_GAP`.
- Connections wholly outside the requested window are `OUTSIDE_WINDOW` and do not poison a later recovered connection's window result.
- Missing expected batch/route evidence or partial-window connection yields `UNVERIFIABLE`.
- Overall result fails closed; no rows, market message volume, or lack of trade-ID gaps can substitute for heartbeat evidence.

The SHA-256 comparison detects changes relative to a trusted expected digest. It is not a digital signature and does not prove who produced the file.

## Offline acceptance coverage

The 14 sidecar tests cover:
1. paired Pong evidence across a healthy window;
2. missing expected route remains UNVERIFIABLE;
3. missing Pong/excessive heartbeat gap;
4. disconnect inside the half-open window;
5. transport-error disconnect reason;
6. reconnect attempt and bounded delay;
7. distinct connection identity after reconnect;
8. recovered connection after an older connection closed before the window;
9. session restart cannot be spliced into one session;
10. out-of-order events and duplicate event IDs;
11. unmatched Pong and reused heartbeat identity;
12. sidecar checksum tampering;
13. unfinalized capture and insufficient completeness watermark;
14. event timestamp beyond the trusted capture watermark.

All tests use synthetic JSONL files in temporary directories. They make no network or database calls.

## Explicit limitations

- The pinned upstream collector `waynemason1/binance-futures-collector@bc4f0ef633fbeee4a49defd72827f17162693805` does **not** write this sidecar. Its `Connected`, `Disconnected`, and `Error` lifecycle events are currently handled as logs.
- No Rust collector code or schema was changed in this increment.
- No live Ping/Pong, disconnect, reconnect, process restart, or outage recovery was exercised.
- No collector-side durability/fsync guarantee, event writer atomicity, or trusted manifest/signature mechanism has been implemented or proven.
- The validator is not yet integrated into `import_collector.py`, feed quality, or decision gating. Existing CSV snapshots must remain `connectionStatus=UNVERIFIABLE`.
- T1 live capture, transport continuity, and operational readiness remain **NOT VERIFIED / NOT CERTIFIED**.

## Next bounded task

Review and implement the collector-side append-only writer in a separately pinned upstream source revision, with deterministic offline Rust tests for writer durability/order, Ping/Pong pairing, remote close, transport error, heartbeat timeout, retry/backoff, process restart/session identity, and manifest checksum. Only after that should a separate importer integration be designed. No live collector run is implied.
