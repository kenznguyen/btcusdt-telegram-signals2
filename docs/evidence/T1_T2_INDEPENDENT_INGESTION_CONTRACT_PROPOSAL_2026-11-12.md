# T1 → T2 Independent Ingestion Contract — Design Proposal

Updated: 2026-11-12 (UTC)

Status: **PROPOSAL ONLY — NOT OWNER-APPROVED, NOT IMPLEMENTED, NOT A FROZEN CONTRACT.**

## 1. Decision boundary

- T0 and T1 are independent data assets and independent producers.
- T1 does **not** feed T0. No T1 → T0 adapter, canonicalization, storage write, or dependency is part of this proposal.
- T2 consumes T0 and T1 through separate source adapters.
- T0 → T2 remains the existing read-only Candle Contract v1 path. This proposal does not change it.
- T1 remains inactive. No VPS, live Binance connection, runtime activation, or real trading is authorized.

## 2. Proposed topology

`T0 canonical candles → T0 adapter ─┐`
`                                 ├→ T2 source-aware integration / feature layer`
`T1 raw futures files → T1 adapter ┘`

T2 must retain source provenance through validation, feature generation, training, inference, and audit. Combining features must not erase which source and source interval produced each value.

## 3. T1 producer data currently documented

T1 CSV schema documents the common fields `exchange`, `market`, `datatype`, `timestamp_ms`, `datetime_utc`, and lowercase `symbol`. Timestamp semantics vary by datatype and must not be treated as interchangeable:

- Order-book depth diffs: event time; ordered by `last_update_id`, with `first_update_id` and `prev_update_id` continuity.
- Order-book snapshots: snapshot time and `last_update_id`; event type distinguishes initial, bridge, and periodic snapshots.
- Trades: trade time and `trade_id`.
- 1m klines and mark/index/premium klines: candle open time.
- Liquidations: event time.
- Funding and open interest: sample time.
- Long/short and taker ratios: period-bucket start time.

Price and quantity lexemes must remain exact decimal strings at ingestion boundaries. Do not convert them to binary floating point for identity, deduplication, storage, or order-book reconstruction.

## 4. Proposed T1 → T2 transport boundary

Preferred first implementation for a single-host deployment: a **read-only filesystem adapter** over explicitly shared T1 output paths. If T1 and T2 are on different hosts, use an explicit file-transfer/object handoff with the same manifest and digest contract; do not invent a second market-data schema or route through T0.

The adapter must not read or acknowledge a still-mutating CSV as a completed immutable batch. A producer-side sealed-segment/manifest publication mechanism is required before durable batch ingestion can be claimed. Current T1 CSV rotation alone is not evidence of a sealed, checksummed, acknowledged handoff.

Proposed batch envelope (manifest, not repeated on every row):

- `contractVersion`: `t1-ingest/1.0.0`
- `producer`: repository identity, exact source commit SHA, collector build identity
- `sessionId`: unique collector process/capture session
- `batchId`: unique immutable publication ID
- `exchange`, `market`, `symbol`, `datatype`
- `schemaVersion`: explicit version for the datatype row schema
- `timestampSemantics`: explicit enum per datatype (EVENT_TIME, BAR_OPEN_TIME, SAMPLE_TIME, BUCKET_START_TIME, SNAPSHOT_TIME)
- `filePath`, `byteLength`, `sha256`, `rowCount`
- `firstTimestampMs`, `lastTimestampMs` where meaningful
- `publishedAtMs`, `sealedThroughMs`
- `qualityEvidence`: datatype-specific checks and their status; unknown checks remain UNKNOWN, never inferred PASS
- `gaps`: explicit gap references or an explicit empty list only when the producer has evidence for that interval

The manifest must be published atomically after the data segment is closed and its byte length, row count and digest are fixed. Existing files are immutable after publication. No overwrite/reuse of batch IDs or paths.

## 5. Consumer validation requirements

T2 adapter must fail closed on:
- unknown contract/schema version, missing required identity, invalid symbol/market/datatype combination;
- digest, byte-length, row-count or manifest/file mismatch;
- malformed CSV/JSON, duplicate or invalid required fields, malformed decimal lexemes, invalid timestamps;
- timestamp ordering violations where ordering is required;
- duplicate batch identity with different content;
- unsupported or unknown timestamp semantics;
- incomplete required coverage or unclassified gaps.

T2 must distinguish:
- `transport_integrity` (file/manifest digest and length match),
- `schema_validity` (rows satisfy the declared datatype schema),
- `market_data_completeness` (datatype-specific coverage/continuity evidence),
- `consumer_persisted` (T2 durably stored the accepted batch and checkpoint).

These are separate states. A valid manifest or sidecar does not prove market-data completeness.

## 6. Durable acknowledgement and replay

Proposed consumer checkpoint key:
`(producer, sessionId, batchId, filePath, sha256)`.

T2 acknowledges only after:
1. immutable source segment and manifest validate;
2. rows pass datatype-specific validation;
3. accepted rows and provenance are durably committed to T2's own ingest store;
4. the checkpoint is durably committed atomically with the ingest result (or through an equivalent transactional inbox pattern).

Delivery semantics: **at-least-once with idempotent ingestion**, not an unsupported exactly-once claim. Same batch identity + same digest is a safe replay/no-op; same identity + different digest is a hard conflict. A producer-side acknowledgement ledger may record T2's response, but it must not mutate or delete the raw source segment.

No automatic deletion, retention expiry, compaction, or source cleanup is included. Raw T1 files remain producer-owned and independently recoverable.

## 7. Timestamp alignment and T0/T1 feature joins

- Preserve original source timestamps and timestamp semantics. Never replace event/sample/bar-open time with ingestion time.
- Record ingestion/observation time separately.
- For training and inference, use point-in-time/as-of joins: a feature is eligible only when it was available by the decision cutoff. Do not join on nearest timestamp without a defined tolerance and availability rule.
- T1 M1 candles may be aggregated into higher intervals only from complete, closed constituent bars; preserve the derivation lineage and gap state.
- T0 M15/H1 candles remain the canonical candle inputs under Candle Contract v1. T1 M1 and derivatives remain T1-origin features, not replacements for T0 candles.
- Order-book windows spanning a `prev_update_id` discontinuity must be marked invalid/untrusted until re-anchored by a valid snapshot and continuity checks.
- Late-arriving data must not silently rewrite historical training examples. Use explicit dataset revision/versioning and availability cutoffs.

## 8. Existing implementation gaps (source review at 2026-11-12)

- T1 `docs/SCHEMA.md` defines datatype-specific CSV fields and common timestamp columns, but the reviewed schema does not establish the proposed versioned immutable batch manifest/acknowledgement contract.
- T1 `docs/ARCHITECTURE.md` describes local CSV, gaps and stats output; no T1 → T2 adapter is established by the reviewed source.
- T1 connection-sidecar README states it is a portable offline reference implementation, not integrated into the upstream collector. It explicitly separates sidecar persistence, manifest consistency and market-data completeness. It cannot currently be used as proof of T1 market-data completeness.
- T1 Dashboard currently converts decimal strings to Python float and exposes numeric API values; this is a separate confirmed precision-loss finding. Do not use those dashboard endpoints as the exact-decimal ingestion path.
- T0 → T2 remains a separate read-only Candle Contract v1 HTTP path; no changes proposed.

## 9. Acceptance gates before implementation

1. Owner approves T0/T1 independence and the T1 → T2 boundary.
2. Freeze datatype schemas and timestamp-semantics mapping, including explicit schema versioning.
3. Approve immutable segment/manifest publication and crash-recovery behavior.
4. Approve the transport choice (shared read-only filesystem for same-host, or immutable file transfer for cross-host).
5. Approve T2 transactional/idempotent checkpoint and acknowledgement semantics.
6. Define per-datatype completeness rules, especially order-book continuity, trades, klines and sampled REST metrics.
7. Define point-in-time join and late-data revision policy for training/inference.
8. Only then implement contract tests (RED first), adapter and producer publication support on existing branches, with exact-source CI evidence.

## 10. Explicit non-goals and constraints

- No T1 → T0 path.
- No modification to T0 Candle Contract v1, T0 database, API, feeder, lease/fencing, or data.
- No modification to Strategy Core, AI strategy, ledgers, Shared Risk Engine or Kill Switch.
- No T1 source, dashboard, sidecar, or runtime implementation in this design-only increment.
- No VPS, live Binance connection, real orders, or trading.
- No raw-data deletion, retention policy, cleanup, or compaction.
- No branch creation, PR creation, merge, or branch divergence.
