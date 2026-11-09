# T1 Source-File Contract v1.1 — Producer Completeness and Durable Publication

Date: 2026-11-09
Status: REVISION DRAFT — DESIGN ONLY — NOT APPROVED FOR IMPLEMENTATION

This revision addresses R1–R7 in the adversarial pre-review. It tightens the v1 proposal without changing the original review record. The target remains Binance USD-M BTCUSDT 1m klines, isolated staging/report only. This document does not claim that the current collector implements any requirement below.

## 1. Non-goals and authorization boundary

No T1 source modification, adapter implementation, collector activation, VPS command, T0/T2 change, T0 write path, strategy/AI/ledger/risk change, live order, OKX replacement/fallback, deletion, archive, cleanup, vacuum, compaction, backup expiry or destructive test is authorized. No promotion to T0/T2 is in scope.

## 2. Producer product identity (R1)

The generic persisted value market=futures does not prove the product contract. A v1 manifest must declare:
- exchange_id=binance;
- market_scope=BINANCE_USDM;
- contract_type=PERPETUAL;
- symbol=BTCUSDT, base_asset=BTC, quote_asset=USDT;
- margin_asset=USDT only where authoritative metadata provides it;
- datatype=klines, interval=1m;
- source_endpoint_family identifying the configured USD-M stream;
- exchange_info_snapshot_sha256 and the exact symbol metadata record used for eligibility;
- schema_version, collector_source_sha and file_generation.

The producer must derive identity and symbol eligibility from the actual USD-M stream configuration and authoritative exchange metadata. Directory names, the generic futures label, symbol spelling or operator assertion alone are insufficient. The adapter independently checks the manifest against a pinned reviewable allowlist/fixture and embedded exchange metadata. Missing or contradictory evidence yields SOURCE_IDENTITY_UNPROVEN.

Exact field availability must be checked against the pinned Binance exchange metadata model before implementation. Do not invent margin_asset if unavailable; leave it unavailable and require an approved derivation or fail closed.

## 3. Explicit interval and row schema (R6)

The first source contract is klines/1m. Manifest interval must equal 1m; missing, unknown or mismatched values are rejected. Never infer interval from a path or filename.

Version 1 adds is_closed as a literal boolean copied from Binance WebSocket k.x. Legacy files without it are v0 and cannot feed canonical aggregation. Interim updates may be retained as raw observations but cannot contribute to an aggregate. Conflicting final payloads for the same semantic candle key quarantine the affected window.

## 4. Producer-owned watermark and completeness (R2)

### 4.1 Meaning

A missing row is not a confirmed gap until the producer publishes a valid completeness watermark covering the window. Before that point, the adapter reports PENDING / INCOMPLETE_UNSEALED.

The watermark is an exclusive event-time boundary with this producer-owned meaning:

For the declared stream identity and file generation, every eligible kline update received and accepted by the collector with candle open time strictly less than watermark_open_time_exclusive_ms has been serialized into the source file, and all bytes through committed_offset_bytes have crossed the declared durability boundary before the watermark manifest is published.

This statement covers events actually received and accepted by the collector. It does not prove Binance emitted no event that the collector failed to receive. If reconnects, transport gaps or receive continuity are unknown, source_health must be GAP_DETECTED or UNKNOWN and the affected windows cannot be sealed. No wall-clock delay, file mtime, consumer-calculated watermark, connection sidecar or caller assertion can authorize completeness.

### 4.2 Required manifest fields

Each file generation has a manifest containing:
- manifest_version, schema_version, file_generation;
- exchange_id, market_scope, contract_type, symbol, base_asset, quote_asset;
- datatype, interval, source_endpoint_family;
- exchange_info_snapshot_sha256 and symbol metadata record;
- collector_source_sha, collector_instance_id;
- state=ACTIVE | SEALED | QUARANTINED;
- committed_offset_bytes and committed_record_count;
- watermark_open_time_exclusive_ms;
- source_health=CONTIGUOUS | GAP_DETECTED | UNKNOWN;
- source_gap_ranges or a digest linked to an immutable gap record;
- header_sha256 and data_prefix_sha256 for bytes [0, committed_offset_bytes);
- updated_at_utc.

Watermark may advance only for a contiguous source-health interval. Detected or unknown transport continuity holds the watermark. A detected gap is reported; it is never permission to synthesize data.

### 4.3 Seal rule

For a UTC half-open window [start_ms,end_ms), the adapter may classify the source as sealed only when:
1. identity, schema and generation validate;
2. state is ACTIVE or SEALED, never QUARANTINED;
3. source_health is CONTIGUOUS across the whole window;
4. watermark_open_time_exclusive_ms >= end_ms;
5. committed_offset_bytes and prefix digest validate;
6. candidate rows are complete, final, schema-valid and within the committed prefix;
7. no unresolved receive gap or generation discontinuity overlaps the window.

Only then may missing minute rows be classified as WINDOW_GAP. The adapter still emits no aggregate for a gap. If any precondition is absent, status remains pending/unsealed.

## 5. Manifest lifecycle and durable publication (R4, R5)

### 5.1 Single writer and generations

Exactly one writer owns an active file generation. A producer-side exclusive ownership mechanism prevents concurrent writers. Each process lifecycle durably allocates a monotonically increasing generation before append. If ownership or generation continuity is uncertain, quarantine the file; do not continue a stale cursor. Replacement, truncation, header rewrite or uncertain restart creates a new generation and explicit discontinuity evidence.

### 5.2 Ordered publication protocol

For every publication batch, the producer must:
1. Serialize complete CSV records, each ending in one newline.
2. Flush the userspace buffer.
3. Invoke the platform durable file synchronization primitive (fdatasync or a verified equivalent); any error blocks progress.
4. Capture exact durable end offset, record count and committed-prefix digest.
5. Write a complete new manifest to a temporary file in the same directory.
6. Flush and durably synchronize the temporary manifest.
7. Atomically rename the temporary manifest over the published manifest.
8. Durably synchronize the containing directory where required for rename durability.
9. Only then expose the new committed offset and watermark to readers.

This is a proposed POSIX-style protocol, not evidence of current durability. Filesystem, mount, device and provider behavior must be verified on the target environment. If a required primitive fails or is unavailable, watermark must not advance.

### 5.3 Active and sealed states

ACTIVE files are append-only and may publish successive committed prefixes. SEALED means the writer has stopped, the file has been durably synchronized, the final offset/digest has been published, and no future append is allowed. QUARANTINED means identity, health, writer ownership, integrity or durability is uncertain.

Daily rotation alone does not prove sealing. The old partition becomes SEALED only after the full seal protocol. A new partition has a distinct generation and manifest.

### 5.4 Crash recovery

On restart, compare the published manifest with actual file identity, size and committed-prefix digest. Bytes beyond the last published committed offset are uncommitted and cannot be consumed. Preserve such tail bytes for diagnosis/quarantine; this contract does not authorize truncation or deletion. Recovery may validate and republish under a documented recovery procedure, or create a new generation and record the unresolved tail.

The producer must never publish an offset or watermark for bytes not durably synchronized before manifest publication. Consumer cursor transactions prove only consumer replay safety, not producer event completeness.

## 6. Decimal preservation (R3)

String-typed model fields alone do not prove lossless persistence. The complete WebSocket → deserialization → kline conversion → CSV serialization path must be traced at the exact source revision before implementation approval.

Requirements:
- Preserve original Binance decimal strings for OHLC, base volume, quote volume and taker volumes byte-for-byte in CSV.
- No f64/f32 conversion, fixed-precision formatter or arithmetic before raw source serialization.
- Aggregation uses exact decimal arithmetic with explicit precision/scale bounds; overflow or unsupported scale fails closed.
- Parser retains raw field text alongside exact parsed values.
- Golden fixtures cover leading/trailing zeros, tiny and large values, maximum documented precision, exponent notation if accepted, and malformed/non-finite values.
- Verify JSON source string equality with decoded CSV field and deterministic exact aggregate sums.

Status: NOT VERIFIED. The prior inspection confirmed String-typed model fields but did not trace the complete producer call path. Do not claim lossless persistence until trace and tests pass.

## 7. Bounded file snapshot and cursor commit (R7)

For each scan:
1. Open source read-only; capture file identity, generation, manifest version, committed offset and current size.
2. Fix scan_end=min(current_size, manifest.committed_offset_bytes).
3. Read only from the prior committed cursor through scan_end.
4. Parse only complete newline-terminated records wholly within that fixed range.
5. Validate manifest and committed-prefix digest.
6. Before atomic staging rows+cursor commit, re-stat file and re-read manifest identity/version. If identity, generation, committed prefix or manifest changed incompatibly, abort and retry/reconcile.
7. Never advance beyond the last complete record covered by the committed offset.

Appends after scan_end are deferred to the next poll. Truncation, replacement, manifest rollback or prefix mismatch causes quarantine, not best-effort continuation.

## 8. Additional status taxonomy

- SOURCE_IDENTITY_UNPROVEN: product, market or symbol identity cannot be verified.
- SOURCE_WATERMARK_UNTRUSTED: watermark is absent, caller-created or not durably bound to source generation.
- SOURCE_HEALTH_UNKNOWN: receive/transport continuity is unknown.
- SOURCE_NOT_SEALED: valid watermark does not yet cover the window.
- SOURCE_DURABILITY_UNPROVEN: producer sync/publication ordering or target storage semantics are unproven.
- SOURCE_MANIFEST_ROLLBACK: manifest generation/version/offset regressed.
- SOURCE_PREFIX_MISMATCH: committed-prefix digest differs from file bytes.
- SOURCE_IDENTITY_CHANGED: file or generation changed during scan.

Missing rows before a valid seal are PENDING, not a confirmed gap. Missing rows after a valid seal and contiguous health proof are WINDOW_GAP. Both block aggregation.

## 9. Additional deterministic acceptance tests

Retain C01–C24 from v1 and add:
- C25 wrong market scope → SOURCE_IDENTITY_UNPROVEN.
- C26 BTCUSDT spelling without trusted product metadata → SOURCE_IDENTITY_UNPROVEN.
- C27 missing/non-1m interval → UNSUPPORTED_SCHEMA.
- C28 missing minute before watermark reaches window end → PENDING / SOURCE_NOT_SEALED.
- C29 missing minute after valid watermark and contiguous health → WINDOW_GAP, no aggregate.
- C30 watermark with UNKNOWN/GAP_DETECTED health → no seal.
- C31 caller-created watermark → SOURCE_WATERMARK_UNTRUSTED.
- C32 manifest published before data sync → producer protocol failure.
- C33 data sync succeeds but manifest rename fails → old manifest authoritative.
- C34 crash after data sync before manifest publication → uncommitted tail not consumed.
- C35 crash before manifest rename → old manifest authoritative.
- C36 crash after rename before directory sync → target-filesystem recovery test required; no durability claim until verified.
- C37 producer restart with generation mismatch → quarantine.
- C38 decimal strings preserved JSON-to-CSV byte-for-byte → golden fixture PASS.
- C39 float conversion/rounding in path → fixture FAIL and contract blocked.
- C40 append after captured scan end → bounded current scan; later bytes next scan.
- C41 truncate/replace during scan → abort cursor transaction.
- C42 bytes beyond committed offset → ignored.
- C43 prefix digest mismatch → SOURCE_PREFIX_MISMATCH.
- C44 append to SEALED generation → producer invariant violation.
- C45 second writer claims same generation → fail closed.

Unit fixtures cannot prove power-loss/storage durability. Any D2–D4 or provider-specific test needs a separate authorized environment gate.

## 10. Finding disposition and remaining evidence

| Finding | Contract revision | Evidence still required |
|---|---|---|
| R1 | Product identity fields and validation defined | Confirm exact exchange metadata model and producer source |
| R2 | Producer watermark and health semantics defined | Implement/prove receive continuity and health behavior |
| R3 | Byte-preservation requirements defined | Trace full call path and golden tests |
| R4 | Generation, active/sealed lifecycle and publication order defined | Producer implementation and filesystem tests |
| R5 | Sync-before-manifest protocol defined | Target filesystem/provider crash-restart evidence |
| R6 | Explicit interval=1m required | Producer declaration and mismatch tests |
| R7 | Bounded scan and pre-commit revalidation defined | Adapter concurrency tests |

This is design-level disposition only. None of R1–R7 is implementation-resolved.

## 11. Approval gates

Before any producer code change:
1. T1 owner approves product identity fields and trusted symbol eligibility source.
2. T1 owner approves is_closed and interval=1m schema.
3. Producer watermark semantics and transport-gap behavior are accepted.
4. Manifest generation, active/sealed lifecycle, publication order and recovery semantics are accepted.
5. Exact kline conversion/writer path is traced and decimal golden tests are prepared.
6. A separate reviewer/model or designated human reviews and accepts this revised contract.
7. A separate explicit approval is obtained for the smallest producer-only implementation.

Before adapter implementation, producer implementation and crash/restart durability tests must exist and pass; adapter bounded-read/cursor/idempotency tests must pass; staging must have no T0 write path or credentials. T0/T2 promotion remains a separate approval gate.

## 12. Guardrails and status

T0 remains independent and canonical. No T1 writes to T0. No T1 activation/VPS command. No T0/T2/strategy/AI/ledger/risk changes. Paper-only; no live orders; AI_EXECUTION_ENABLED=false. No OKX replacement/fallback. No destructive data operations. No PR review submission or merge.

**P1.1 DESIGN REVISION DRAFTED / IMPLEMENTATION BLOCKED / INDEPENDENT REVIEW REQUIRED.**

No code changed, tests run, workflow dispatched or runtime/filesystem property verified.
