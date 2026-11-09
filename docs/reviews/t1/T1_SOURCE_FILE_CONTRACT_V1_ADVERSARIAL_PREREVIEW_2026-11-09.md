# Adversarial Pre-Review — T1 Source-File Contract v1 (2026-11-09)

## Review type and independence

This is a second-pass technical pre-review of the proposed design against the reviewed T1 source at SHA `6e20fe94f3ad64cc450e73def80a167fe371e49e`. It is **not an independent reviewer sign-off**: it was prepared in the same assistant session/model that drafted the design. It must not be represented as independent approval.

Design under review:
`docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_AND_INGESTION_ADAPTER_DESIGN_2026-11-09.md`

## Verdict

**REQUEST CHANGES — DESIGN NOT READY FOR IMPLEMENTATION.**

The isolation and fail-closed direction is sound, but important producer-side evidence and completeness semantics are not yet sufficiently specified. The adapter must not be implemented or activated until the required findings below are addressed and a genuinely independent review is recorded.

## Findings

### R1 — Critical: market identity is underspecified by current persisted rows

The reviewed T1 constants persist `market=futures`. That label alone does not prove USD-M / USDT-M perpetual identity. README describes the collector as USDT-M, but the row-level persisted contract does not carry the full product identity. The design currently asks the adapter to verify exact market identity without defining a verifiable source of that identity.

**Required:** T1 v1 metadata must carry an explicit market scope (for example, Binance USD-M perpetual), quote asset, contract type and the collector's source of symbol eligibility. The adapter must validate those fields against an approved static allowlist/fixture or trusted collector metadata. A directory name or generic `futures` field is insufficient. No silent assumption based on BTCUSDT's spelling.

### R2 — Critical: source completeness/watermark protocol is missing

The design explains how to detect missing 1m rows inside a candidate bucket, but it does not define how the adapter knows whether a missing row is merely delayed/not yet flushed versus permanently absent. A complete-looking file or elapsed wall-clock delay is not proof that the collector has observed and persisted all source events up to a given time.

**Required:** define a producer-owned per-stream watermark/seal protocol with explicit semantics, source generation and durable publication. The watermark must mean that all eligible 1m kline events up to a stated event-time boundary have been processed and persisted. Until this exists and is validated, a bucket with missing rows must remain PENDING/INCOMPLETE; it cannot be declared a definitive source gap or promoted. A connection-sidecar manifest or caller-asserted watermark is not sufficient.

### R3 — High: lossless decimal persistence is not yet evidenced

The design requires exact decimal aggregation and says to preserve original decimal strings. The current `KlineCsv` model stores decimal fields as strings, but this review has not traced the complete producer call path that populates and serializes those fields. A string type alone does not prove that upstream conversion has not already rounded values.

**Required:** inspect the exact kline writer call path and prove no float conversion/rounding occurs before CSV serialization. Add golden fixtures with source decimal strings at maximum relevant precision and verify byte/value preservation. If any float conversion occurs, change the source producer contract before using these files for exact aggregation.

### R4 — High: file generation and manifest publication lifecycle is undefined

The design proposes `file_generation`, `collector_source_sha`, header hash and file manifest, but does not define when/how the producer creates, atomically publishes, updates or seals that manifest during an append-only file's lifecycle.

**Required:** define an atomic metadata publication protocol, including active versus sealed partitions, generation changes after restart/replacement, and the ordering between data flush and watermark/manifest update. A manifest must never claim bytes or a watermark that are not already durable under the stated durability contract.

### R5 — High: adapter cursor correctness depends on source durability not established by T1

T1 README describes buffered CSV writes and periodic flush; the reviewed writer uses `BufWriter::flush()`, not an explicit durable fsync acknowledgement. A consumer-side SQLite transaction can guarantee replay safety for bytes it has read, but cannot recover source events lost before they reach durable storage.

**Required:** keep the existing block, and add a producer crash/restart test proving the source durability contract, including forced termination around write/flush boundaries. Do not claim end-to-end no-loss from adapter cursor tests alone.

### R6 — Medium: fixed-source assumptions need to be encoded, not inferred

The proposed first adapter is 1m klines only, but the file header does not include interval. This is acceptable only if the v1 manifest explicitly declares `interval=1m`, the collector source is proven to emit that interval, and the reader rejects any mismatch. Do not infer interval from the datatype name or directory.

### R7 — Medium: active-file read race needs a precise snapshot rule

The design says to consume complete newline-terminated records, but does not state whether each polling pass snapshots the file length before reading. Without a bounded read end offset, concurrent appends can make cursor behavior and repeatability harder to reason about.

**Required:** at each scan, capture a file identity and byte length; read only up to that captured length; process only complete records ending at or before it; next poll starts from the committed cursor. Re-stat identity/size before cursor commit and retry if replacement/truncation is detected.

## Five-axis summary

| Axis | Assessment |
|---|---|
| Correctness | BLOCKED by R1–R3: market identity, completeness watermark and decimal provenance |
| Readability | PASS with clarifications to status names and manifest semantics |
| Architecture | PARTIAL: staging isolation is sound; producer/consumer contract boundary is incomplete |
| Security | PARTIAL: read-only/path containment is specified; producer metadata trust boundary needs definition |
| Performance | NOT VERIFIED: no implementation or representative file-volume benchmark |

## Required revision sequence

1. Extend the T1 v1 source contract with explicit product identity and interval metadata.
2. Specify producer-owned durable watermark/seal and manifest lifecycle; do not rely on sidecar assertions.
3. Trace and prove decimal preservation from WebSocket payload to CSV bytes.
4. Define bounded file snapshot reads and pre-commit identity revalidation.
5. Add fixture cases for market mismatch, missing/untrusted watermark, manifest publication ordering, decimal precision and concurrent append/truncation.
6. Obtain review from a separate reviewer/model or designated human. Record reviewer identity, reviewed design commit, findings and disposition.

## Guardrails

- No T1 source modification, adapter implementation, T1 activation or VPS command in this review.
- No T0/T2 changes and no T0 database/API write path.
- No live trading; `AI_EXECUTION_ENABLED=false`.
- No OKX replacement/fallback.
- No deletion, archive, cleanup, vacuum, compaction, backup expiry or destructive test.
- T1 PR #1 remains OPEN/DRAFT; no review or merge action submitted.

## Final status

**PRE-REVIEW COMPLETE / REQUEST CHANGES / INDEPENDENT REVIEW PENDING.**

This review is not an independent sign-off. No tests were run, no workflow was dispatched, and no runtime behavior was verified.
