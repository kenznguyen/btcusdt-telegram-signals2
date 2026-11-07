# Rust Collector Connection Sidecar Writer

**Status: portable offline reference implementation. Not integrated into the upstream collector.**

This crate writes a separate append-only JSONL event stream for WebSocket connection lifecycle evidence. It is deliberately independent of the CSV market-data importer.

## Contract

Each event contains the v1 identity fields:

- `schemaVersion`, `eventId`, `sourceCommit`, `sessionId`
- `connectionId` (unique for one socket lifetime), `batchId`, `route`
- `eventType`, `eventAtMs`

Supported event types:

- `CONNECTED`
- `PING_SENT` and `PONG_RECEIVED`, paired by a unique `heartbeatId`
- `DISCONNECTED`, with `REMOTE_CLOSE`, `TRANSPORT_ERROR`, `HEARTBEAT_TIMEOUT`, `SHUTDOWN`, or `UNKNOWN`
- `RECONNECT_SCHEDULED`, with bounded `attempt` and `delayMs`

The `CONNECTED` event stores the number of subscriptions and a deterministic SHA-256 of the sorted subscription set. The manifest stores the exact subscription names and their hash for audit/reconciliation.

## Basic use

```rust
use collector_connection_sidecar::{
    ConnectionIdentity, DisconnectReason, Route, SidecarWriter,
};

let mut writer = SidecarWriter::create(
    "capture/session-001/connection-events.jsonl",
    "bc4f0ef633fbeee4a49defd72827f17162693805",
    "process-session-uuid",
)?;

let socket = ConnectionIdentity {
    connection_id: "socket-uuid-for-this-one-socket".to_string(),
    batch_id: 0,
    route: Route::Public,
    subscriptions: vec!["btcusdt@depth@100ms".to_string()],
};

writer.connected(&socket, connected_at_ms)?;
writer.ping_sent(&socket, "heartbeat-0001", ping_sent_at_ms)?;
writer.pong_received(&socket, "heartbeat-0001", pong_received_at_ms)?;
writer.disconnected(&socket, DisconnectReason::Shutdown, disconnected_at_ms)?;

let manifest = writer.finalize(capture_complete_through_ms, finalized_at_ms)?;
# Ok::<(), std::io::Error>(())
```

The caller supplies UTC Unix epoch milliseconds. The caller must generate a fresh process `sessionId` for every collector process and a fresh `connectionId` for every WebSocket socket lifetime. Never reuse the upstream collector's current stable `(batch, route)` connection key as a socket ID.

## Durability and fail-closed rules

- The JSONL file is created with exclusive create + append; an existing path is never truncated or reused.
- Each event is serialized as one line, flushed, then `sync_data()` completes before the writer method returns.
- Initial file creation and manifest publication sync the parent directory on Unix.
- Event timestamps must be globally non-decreasing.
- Ping/Pong must pair exactly; duplicate heartbeat IDs, unmatched Pong, invalid lifecycle transitions, invalid reconnect bounds, and identity reuse are rejected.
- Limits: 16 KiB per event line, 64 MiB per sidecar, 100,000 events, 10,000 subscriptions per socket, 2 MiB total subscription-name bytes per socket.
- Finalization requires at least one event, all sockets disconnected, a completeness watermark at or beyond the final event, and a finalization timestamp at or beyond the watermark.
- The manifest is written to a temporary file, synced, linked into place without replacing an existing manifest, and followed by a parent-directory sync on Unix. It records sidecar byte size, SHA-256, event count, session/source identity, watermark, and exact subscription sets.

SHA-256 detects a sidecar mismatch only when compared with a separately protected expected digest. The manifest is not digitally signed and does not authenticate its own producer.

## Async collector integration constraints

The writer uses synchronous filesystem operations. Do not call it directly from a high-frequency Tokio task. A future collector integration should use one dedicated blocking writer worker with a bounded queue and wait for a durable acknowledgement for each lifecycle event before claiming it was recorded.

For heartbeat correlation, the collector must put the unique `heartbeatId` in the client Ping payload and read that same payload from the matching Pong frame. A server Ping followed by the collector's Pong response is not a `PONG_RECEIVED` event for the collector's own Ping.

## Offline checks

```bash
cargo fmt --manifest-path futures_intelligence/collector_sidecar_writer/Cargo.toml --all -- --check
cargo clippy --manifest-path futures_intelligence/collector_sidecar_writer/Cargo.toml --all-targets -- -D warnings
cargo test --manifest-path futures_intelligence/collector_sidecar_writer/Cargo.toml --all-targets
```

Tests use temporary local files only. They do not start a collector, open a database, or contact an exchange.
