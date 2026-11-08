# T1 Collector-Side Rust Connection Sidecar Writer — 2026-11-07

## Verdict

**PASS — portable Rust writer reference implementation and offline CI. NOT INTEGRATED into the upstream collector. NOT OPERATIONAL.**

This increment implements a standalone Rust crate inside the Quant System repository. It does not modify the third-party collector repository, start a collector, contact Binance, open a database, or change the CSV importer.

## Source and CI evidence

- Quant System repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Tested source SHA: `0c8b0121e894c0de566a2ddea1a96b1f64488ad0`
- GitHub Actions run: [42342147186](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42342147186)
- Overall workflow: **SUCCESS**, 6/6 jobs SUCCESS.
- Dedicated job: `128312193339`, T1 collector sidecar writer · Rust offline tests — **SUCCESS**.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test --all-targets`: **9/9 PASS**, 0 failed.
- Existing T1 Python importer/sidecar suite: **24/24 PASS**.
- Artifact: [13561009846](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42342147186/artifacts/13561009846)
  - Name: `t1-sidecar-rust-evidence-0c8b0121e894c0de566a2ddea1a96b1f64488ad0`
  - Size: 2,190 bytes
  - GitHub upload digest: `sha256:409dec36ec4f52f2f41976e824920f08100bc2d78c6a1dfbda08bb2c4c5d26a5`
  - Artifact ZIP was not downloaded and independently re-hashed; payload checksum recomputation remains NOT VERIFIED.

## Files added

- `futures_intelligence/collector_sidecar_writer/Cargo.toml`
- `futures_intelligence/collector_sidecar_writer/src/lib.rs`
- `futures_intelligence/collector_sidecar_writer/tests/sidecar_writer.rs`
- `futures_intelligence/collector_sidecar_writer/README.md`
- `futures_intelligence/README.md` links the writer and documents the integration boundary.
- Existing GitHub Actions workflow `.github/workflows/t0-single-writer-gateway-red.yml` adds job `t1-collector-sidecar-rust`.

## Implementation

The crate exposes `SidecarWriter::create`, `connected`, `ping_sent`, `pong_received`, `disconnected`, `reconnect_scheduled`, and `finalize`.

- Creates the sidecar using exclusive create + append; never truncates an existing path.
- Writes JSONL v1 events with unique session-scoped event IDs and the contract fields required by the Python validator.
- Calls `flush()` and `sync_data()` before returning from each event append.
- Requires globally non-decreasing UTC epoch milliseconds, bounded event/file sizes, unique connection IDs, and valid lifecycle transitions.
- Pairs each Pong with the exact outstanding Ping heartbeat ID; rejects duplicate IDs and unmatched Pong.
- Stores exact subscription names in the manifest and records a deterministic subscription-set SHA-256/count on CONNECTED.
- Finalization requires all sockets disconnected, a completeness watermark covering the last event, and a finalization timestamp at or beyond the watermark.
- Computes SHA-256 from the actual sidecar bytes. Publishes the manifest through a synced temporary file and no-overwrite hard link; syncs the parent directory on Unix.

Resource bounds: 16 KiB/event line, 64 MiB/sidecar, 100,000 events, 10,000 subscriptions/socket, 2 MiB total subscription-name bytes/socket, reconnect attempt 1..1,000,000, reconnect delay 1..60,000 ms.

## Offline test coverage (9/9)

1. JSONL schema compatibility, per-event visibility after sync, and reopen/readback.
2. Connection lifecycle and exact Ping/Pong pairing.
3. Global timestamp ordering rejects a late event without appending.
4. Manifest file size, SHA-256, finalization watermark, event count, and subscription list.
5. Incomplete watermark cannot produce a finalized manifest.
6. Open socket cannot be finalized.
7. Empty and duplicate subscription sets are rejected.
8. Existing sidecar path cannot be overwritten.
9. Invalid source identity and reconnect attempt/delay bounds are rejected.

All tests use temporary local files. No network, database, collector process, or exchange connection is used.

## Upstream source review and integration blockers

Reviewed upstream `waynemason1/binance-futures-collector@bc4f0ef633fbeee4a49defd72827f17162693805`. Its README says it is published as-is and not actively maintained; it invites forks. No files in that upstream repository were changed.

Static source findings requiring explicit integration work:

1. `conn_id(batch_id, route)` is stable for a logical batch/route and is reused across reconnects. Sidecar `connectionId` must instead be unique for every socket lifetime.
2. Client Ping currently uses an empty payload (`Message::Ping(Bytes::new())`); incoming `Message::Pong(_)` discards its payload. A unique `heartbeatId` must be carried in the Ping payload and correlated against the actual matching Pong.
3. The `Message::Ping` branch responds to a server Ping with a Pong and also updates `last_pong`. That server-initiated ping/pong exchange must not be recorded as a Pong response to the collector's own Ping.
4. Connection lifecycle is currently represented by logs and in-memory `WebSocketMessage::Connected/Disconnected/Error`; no durable JSONL event sidecar is written.
5. Reconnect attempt/backoff is computed in `run_connection`; it must be emitted with the actual scheduled delay before the sleep/retry.
6. The writer is synchronous. Integration must use a dedicated blocking writer worker and bounded queue, waiting for durable acknowledgement so filesystem sync does not block Tokio's async runtime.

## Limitations and status

| Item | Status |
|---|---|
| Portable Rust sidecar writer | PASS |
| Rust format + Clippy | PASS |
| Rust offline tests | PASS (9/9) |
| Existing Python importer/sidecar regressions | PASS (24/24) |
| Exact-source GitHub Actions workflow | PASS (6/6 jobs) |
| Exact process session ID generation in collector | NOT IMPLEMENTED |
| Per-socket connection ID integration | NOT IMPLEMENTED |
| Heartbeat payload correlation in collector | NOT IMPLEMENTED |
| Collector-side lifecycle/reconnect event integration | NOT IMPLEMENTED |
| Live writer durability under process kill/power loss | NOT VERIFIED |
| Live reconnect/heartbeat behavior | NOT RUN |
| T1 transport continuity | NOT VERIFIED |
| T1 operational readiness | NOT CERTIFIED |

The manifest SHA-256 is not a digital signature. The expected digest and manifest must be stored/protected through a trusted capture path. On non-Unix targets, std does not provide the same parent-directory fsync guarantee; intended collector runtime remains a Linux integration target.

## Next bounded task

Create a user-owned fork of `waynemason1/binance-futures-collector` pinned from `bc4f0ef633fbeee4a49defd72827f17162693805`, then integrate this writer with:
- fresh process `sessionId` and per-socket `connectionId`;
- exact route subscription set;
- non-empty, unique client Ping payload and matching Pong payload;
- explicit disconnect reason and reconnect attempt/effective delay;
- a dedicated blocking writer worker with durable acknowledgements;
- shutdown disconnect records and finalized manifest.

The available GitHub connection can read and write files/branches in existing repositories but does not expose a fork/create-repository operation. Therefore the upstream repository was left untouched; a user-owned fork must exist before integration can continue.

## Safety boundaries retained

- Existing CSV importer remains unchanged and keeps `connectionStatus=UNVERIFIABLE`.
- Sidecar validator is not wired into feed quality or decision gating.
- Canonical SQLite NOT CREATED; Controlled First Run NOT AUTHORIZED; Feeder STOPPED.
- No exchange contacted, no market data captured, no database opened.
- T2 OKX source unchanged; no live orders; `ai_execution_enabled=false`.
- No PR opened or merged; no branch merged.


## 2026-11-08 — Sidecar validator semantic schema + manifest identity regression closeout

- T1 source repository: `kenznguyen/binance-futures-collector`; branch `feature/t1-connection-sidecar-integration-20261107`; final source SHA `6c7e29489128d0c3f1cfff30b0434b8ac6f306ec`.
- Validator implementation source SHA: `b4d6e34eeaaa557e98cdad9ec5a32ad9330c144c`. It now deserializes required v1 event identity fields, checks schema version, bounded identity values, route/event-type allowlists and timestamp bounds, enforces consistent sourceCommit/sessionId across events, and compares those identities with the manifest.
- TDD RED: Push CI #219 `42451614036`; the two new regressions failed as intended (missing eventType accepted as SealedConsistent; manifest sourceCommit mismatch accepted as SealedConsistent). Other collector and dashboard checks passed in that RED run.
- Fixture compatibility correction: commit `6c7e29489128d0c3f1cfff30b0434b8ac6f306ec` updated only the shared publication-failure test fixture to use a schema-valid JSONL event and manifest. It did not change validator logic.
- Push CI #223: [42452189107](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42452189107), SUCCESS 5/5 at exact source SHA `6c7e29489128d0c3f1cfff30b0434b8ac6f306ec`.
- PR CI #224: [42452192126](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42452192126), SUCCESS 5/5 at the same PR head SHA; PR #1 base `bc4f0ef633fbeee4a49defd72827f17162693805`.
- Collector checks: Format, Clippy, Build PASS; collector library 43/43 and binary 1/1; Sidecar writer format/Clippy PASS; Sidecar offline unit tests 11/11 and integration tests 27/27 PASS. Dashboard frontend/backend, Docker build and Security audit PASS in both workflows.
- Push artifact metadata: ID `13605344125`, name `t1-collector-linux-x86_64-6c7e29489128d0c3f1cfff30b0434b8ac6f306ec`, size 4,186,964 bytes, GitHub-reported SHA-256 `58a379be44fda51c806af9264b9f7b3cfc595dbc722d10e428948425228c58c4`. Metadata only; artifact payload was not independently downloaded/rehashed. PR workflow did not publish an artifact.
- Verdict: **PASS** for the two validator regression cases and complete Push/PR CI at exact SHA `6c7e29489128d0c3f1cfff30b0434b8ac6f306ec`.
- Remaining limitation: validator still does not semantically compare manifest `connectionSubscriptions` against the JSONL-derived connection/batch/route/subscription inventory. Full manifest inventory integrity is therefore **NOT VERIFIED** and must not be claimed PASS.
- Safety boundaries: PR #1 remains OPEN / DRAFT / NOT MERGED. No T0 runtime, VPS deployment, collector runtime, Binance connection, live execution, or trading action was performed. Sidecar validation remains offline/read-only and is not connected to feed-quality or strategy gating.
