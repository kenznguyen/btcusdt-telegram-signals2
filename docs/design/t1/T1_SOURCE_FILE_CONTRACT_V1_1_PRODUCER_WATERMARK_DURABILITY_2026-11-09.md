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

The producer must derive identity and symbol eligibility from the actual configured Binance USD-M endpoint/stream and the exact authoritative ExchangeInfo symbol record captured for this generation. The manifest must bind the endpoint family/configuration digest, ExchangeInfo snapshot digest, exact symbol record and collector source SHA. The adapter independently validates these values; a static symbol allowlist or symbol spelling is not a substitute for the bound exchange record.

A symbol-discovery exception or hardcoded allowlist MUST NOT bypass checks for status=TRADING, contract_type=PERPETUAL, quote_asset=USDT and the expected BTCUSDT/base_asset=BTC identity. Revalidate the exact record after any exception path and before opening a generation. A record that is absent, ambiguous, stale under the accepted snapshot policy, or contradictory yields SOURCE_IDENTITY_UNPROVEN. The pinned producer's BTCUSDT exception path is not accepted as proof because it does not recheck all eligibility fields.

Exact field availability must be checked against the pinned Binance exchange metadata model before implementation. Do not invent margin_asset if unavailable; leave it unavailable and require an approved derivation or fail closed.

## 3. Explicit interval and row schema (R6)

The first source contract is klines/1m. Manifest interval MUST equal 1m; missing, unknown or mismatched values are rejected. Never infer interval from a path or filename. The configured WebSocket subscription identity and every incoming kline event interval must both be validated as 1m before the event reaches the persistence writer. An unexpected interval, stream name, symbol or endpoint family is rejected and invalidates/quarantines the affected generation; do not silently filter it and continue claiming a homogeneous feed.

For the first adapter, the only accepted producer mode is output_mode=FINAL_ONLY. The producer filters every is_closed=false event before persistence. The versioned manifest must declare output_mode=FINAL_ONLY, and producer regression tests must prove both that provisional events never reach the writer and that only 1m events from the exact declared subscription reach it. The row schema does not need an is_closed column in this mode because every persisted row is contractually final. If a future producer persists interim updates, that is a different schema/output mode and must include a per-row finality flag; it cannot be silently interpreted as this FINAL_ONLY feed. Legacy files without a versioned manifest remain v0 and are ineligible. Conflicting final payloads for the same semantic candle key quarantine the affected window. Close-time semantics must be validated against the 1m interval boundary according to the exchange's documented event schema; where that mapping is not proven, reject rather than infer finality from local wall-clock time.

## 4. Producer-owned watermark and completeness (R2)

### 4.1 Meaning

A missing row is not a confirmed gap until the producer publishes a valid completeness watermark covering the window. Before that point, the adapter reports PENDING / INCOMPLETE_UNSEALED.

The watermark is an exclusive event-time boundary with this producer-owned meaning:

For the declared stream identity and file generation in `output_mode=FINAL_ONLY`, every eligible final 1m kline event received and accepted by the collector with candle open time strictly less than `watermark_open_time_exclusive_ms` has been serialized into the source file, and all bytes through `committed_offset_bytes` have crossed the declared durability boundary before the watermark manifest is published. Interim updates are outside this persisted feed and must never advance the final-candle watermark.

This statement covers final events actually received and accepted by the collector. It does not prove Binance emitted no final event that the collector failed to receive. A healthy WebSocket connection or absence of a locally observed disconnect is not, by itself, proof that no event was missed. Until the producer has a separately validated reconciliation mechanism against an authoritative Binance USD-M kline source for every interval potentially affected by disconnect, reconnect, overload or uncertain delivery, `source_health` must be `UNKNOWN` for those intervals and the watermark must not seal them. No wall-clock delay, file mtime, consumer-calculated watermark, connection sidecar or caller assertion can authorize completeness.

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
- source_health=RECONCILED_COMPLETE | UNKNOWN | INVALIDATED;
- optional reconciliation_evidence_ref bound to an immutable evidence record;
- header_sha256 and data_prefix_sha256 for bytes [0, committed_offset_bytes);
- updated_at_utc.

Watermark may advance only for an interval whose final-candle completeness has been reconciled by an explicitly defined and independently testable producer mechanism. A healthy socket alone is insufficient. Detected or unknown delivery continuity holds the watermark. A detected gap is reported; it is never permission to synthesize data.

### 4.3 Seal rule

For a UTC half-open window [start_ms,end_ms), the adapter may classify the source as sealed only when:
1. identity, schema and generation validate;
2. state is ACTIVE or SEALED, never QUARANTINED;
3. source_health is RECONCILED_COMPLETE across the whole window;
4. watermark_open_time_exclusive_ms >= end_ms;
5. committed_offset_bytes and prefix digest validate;
6. candidate rows are complete, final, schema-valid and within the committed prefix;
7. no unresolved receive gap or generation discontinuity overlaps the window.

Under the current v1.1 evidence profile, WINDOW_GAP is RESERVED AND NOT ASSIGNABLE, just like GAP_DETECTED. The current REST candidate does not establish complete coverage/no-trade semantics, and source asymmetry remains UNKNOWN/DIVERGENCE. A missing row therefore cannot be promoted to WINDOW_GAP by any current fixture or consumer. It remains SOURCE_HEALTH_UNKNOWN, SOURCE_HEALTH_INVALIDATED, RECONCILIATION_SOURCE_DIVERGENCE or SOURCE_NOT_SEALED as applicable. A future WINDOW_GAP state requires a separately versioned authoritative evidence profile, exact source/time-range binding, independent review and explicit approval. Even then it never authorizes synthetic data or aggregation across the gap.

## 5. Manifest lifecycle and durable publication (R4, R5)

### 5.1 Single writer and generations

Exactly one cooperative writer may own the source root at a time. The v1.1 reference ownership primitive is an OS kernel advisory exclusive lock on a pre-created, stable lock file in the source root; every writer MUST acquire it before generation allocation or any source mutation, and every reader MUST acquire the corresponding shared lock before reading the manifest, commit receipt or committed prefix. The lock file must never be unlinked, replaced or rotated. PID files, timestamps and lease expiry are not fencing primitives.

The exclusive lock is held across generation allocation, append, data synchronization, manifest publication and commit-receipt publication. A paused former owner retains the kernel lock and blocks takeover; a crashed process releases the kernel lock. No operator may steal a lock based on age or PID. If the filesystem/provider does not provide the required cross-process lock semantics, or any process cannot acquire/verify the lock, fail closed and quarantine/stop. The lock protects only cooperating processes; source-root permissions and process identity remain part of the trust boundary.

While holding the exclusive lock, allocate a monotonically increasing generation sequence using a durable counter transaction: write a complete temporary counter, fsync it, atomically rename it, fsync the parent directory, then and only then create/open the generation and append. A crash before the durable counter transaction completes must not have written source rows for that reserved sequence. If the counter, lock inode or generation history is missing, regressed or ambiguous, do not reuse a possibly published generation; quarantine and require an explicit recovery epoch/new root. Generation IDs also include a cryptographically random instance identifier so accidental sequence reuse is detectable.

### 5.2 Ordered publication protocol

For every publication batch, the producer must perform the following while holding the exclusive writer lock:
1. Serialize complete CSV records, each ending in one newline; flush the userspace buffer.
2. fdatasync/fsync the data file. Any error blocks progress and invalidates the generation.
3. Capture exact file identity, durable end offset, record count and committed-prefix digest.
4. Write a complete canonical manifest to a temporary file in the same directory; fsync the temporary manifest.
5. Atomically rename the temporary manifest over the fixed manifest path.
6. fsync the containing directory. Until this call succeeds, the new manifest is NOT COMMITTED and MUST NOT be accepted by readers.
7. Only after step 6 succeeds, create an immutable commit-receipt file for this publication sequence. The receipt binds generation ID/sequence, manifest SHA-256, file identity, committed offset, record count, prefix digest and watermark. Write and fsync the receipt temporary file, then atomically rename it to its unique final receipt name.
8. Readers accept a publication only when they hold the shared lock and find exactly one valid receipt that matches the exact manifest bytes and all bound fields. A visible manifest without a matching receipt is PREPARED/UNCOMMITTED and must be rejected. A receipt that mismatches, regresses or is ambiguous causes quarantine.
9. The writer may release the exclusive lock only after the receipt is visible. A receipt may become visible before its own directory entry is durable; this is safe for acceptance because the receipt is created only after the manifest rename's directory fsync has succeeded. If the receipt entry is lost after a crash, the result is a false-negative (no matching receipt, fail closed), never acceptance of a manifest whose directory durability barrier did not complete.

The reader MUST hold the shared lock while opening and validating the manifest, receipt and bounded data prefix, preventing observation of an in-progress publication by a cooperating writer. If a writer crashes before the receipt is published, its lock is released but the new manifest has no matching receipt and is rejected. If the previous receipt no longer matches the visible manifest, the reader quarantines rather than guessing which version is authoritative. No reader may fall back to a watermark copied from a filename, cache, previous process memory or an unmatched receipt.

This protocol is a contract proposal, not evidence of current durability. The exact lock, atomic rename, file-sync and directory-sync semantics must be verified on the target filesystem, mount, device and provider. If any required primitive or lock behavior is unavailable or ambiguous, the source remains SOURCE_DURABILITY_UNPROVEN and no watermark advances.

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

Status: CONFIRMED PRODUCER DEFECT. The read-only trace at `docs/reviews/t1/T1_KLINE_PRODUCER_CALL_PATH_TRACE_2026-11-09.md` proves the current writer parses decimal strings as `f64`, formats to 12 fractional digits and substitutes `0.0` on parse failure. The lossless requirement is not met. Do not claim lossless persistence until a producer correction and golden tests pass.

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
- RECONCILIATION_SOURCE_DIVERGENCE: REST contains a candle key absent from the WebSocket-derived generation; no implicit agreement or row insertion.
- SOURCE_HEALTH_INVALIDATED: a durable or inferred continuity failure invalidates the affected range/generation; watermark remains withheld until an accepted recovery procedure resolves it.


Missing rows before a valid seal are PENDING, not a confirmed gap. Under the current v1.1 evidence profile, missing rows after a nominal watermark are still UNKNOWN/DIVERGENCE unless an independently accepted profile proves completeness. WINDOW_GAP is reserved and unassignable in the current profile. Both missing-row states block aggregation.

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
- C46 full REST coverage and matching WS values → only eligible for further review; commit is forbidden unless every identity, exact request-boundary, pagination, finality/correction, source-health, no-conflict, generation-binding, durable-publication and receipt-verification gate passes. This fixture must fail if any prerequisite is absent.
- C82 reader sees a renamed manifest before the parent-directory fsync has completed → no matching commit receipt exists; reject as PREPARED/UNCOMMITTED.
- C83 manifest directory fsync completed but process crashes before commit receipt publication → reject/quarantine (safe false-negative); do not infer commit from manifest visibility.
- C84 matching receipt is atomically visible after the manifest directory fsync, but receipt directory fsync has not completed → accept only if receipt file content validates and all bound manifest/data checks pass; after crash, missing receipt is a safe false-negative.
- C85 receipt digest/generation/offset/prefix does not match manifest → reject and quarantine.
- C86 two writer processes contend for stable lock → exactly one acquires exclusive ownership; the other cannot allocate generation or append.
- C87 former writer is paused while holding lock; takeover attempt → blocked; no PID/age-based lock stealing.
- C88 target filesystem lock semantics cannot be established or lock file identity changes → SOURCE_DURABILITY_UNPROVEN; no write or watermark.
- C89 crash during generation-counter transaction before directory fsync → no source append was permitted; recovery may reuse only if no generation/file/receipt for that sequence exists and the counter state is unambiguous, otherwise quarantine.
- C90 reader races with writer publication → shared lock blocks until writer completes or crashes; reader accepts only a manifest+receipt pair matching exact bytes.
- C91 incoming kline event interval or configured subscription differs from 1m → reject event and invalidate/quarantine generation.
- C92 hardcoded symbol exception attempts to bypass PERPETUAL/USDT quote-asset checks → SOURCE_IDENTITY_UNPROVEN.
- C93 duplicate manifest keys, unknown v1.1 fields, invalid types, non-canonical bytes or invalid digest input → reject manifest.
- C94 symlinked source root, manifest, receipt or data file; non-regular file; unexpected hard-link identity → reject/quarantine.
- C95 multiple manifests or receipts claim the same generation/publication sequence → ambiguous state; quarantine.
- C96 attempt to assign WINDOW_GAP from current REST/WS silence, absent row or unaccepted completeness evidence → reject; remain UNKNOWN/DIVERGENCE/NOT_SEALED.
- C97 FINAL_ONLY producer receives provisional event → it never reaches persistence; test fails if writer is invoked.
- C98 unexpected close-time/interval boundary semantics → reject; do not infer finality from local time.
- C99 manifest field-to-file binding or generation/source SHA mismatch → SOURCE_IDENTITY_UNPROVEN or SOURCE_PREFIX_MISMATCH; quarantine.

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


## 13. Source-trace amendment — confirmed producer behavior

A read-only trace of T1 source SHA `6e20fe94f3ad64cc450e73def80a167fe371e49e` is recorded in `docs/reviews/t1/T1_KLINE_PRODUCER_CALL_PATH_TRACE_2026-11-09.md` (trace commit `df4406d08fb16010f78a2bef3f9748582cca82be`).

The trace confirms a critical producer defect: `src/utils/csv_writer.rs::write_kline` parses each kline decimal field as `f64`, formats to 12 fractional digits, and substitutes `0.0` when parsing fails. The current CSV path therefore does not preserve raw source decimals and can silently serialize invalid numeric input as zero. R3 is a confirmed blocker, not merely an unverified risk.

The contract remains strict: producer serialization must preserve original decimal strings byte-for-byte and reject malformed numeric values; it must not weaken acceptance to match current lossy output. The producer correction requires separate explicit approval and regression tests.

The trace also confirms `message_handler.rs::process_kline` drops `is_closed=false` messages before CSV writing. The selected v1 contract is therefore `output_mode=FINAL_ONLY` plus `interval=1m`, explicitly declared in the versioned manifest and proven by producer regression tests. Persisting `is_closed=true` per row is not part of this first v1 mode; any change to mixed/provisional persistence requires a separate schema version.

The inspected ExchangeInfoSymbol model exposes symbol, status, base_asset, quote_asset, underlying_type and contract_type. Symbol discovery checks TRADING, PERPETUAL, excludes PREMARKET and requires quote_asset=USDT. The inspected model does not expose margin_asset; it must remain optional/unavailable unless another authoritative source is verified.

This amendment does not resolve R3. No code change, tests, workflow dispatch or runtime evidence exists. Implementation remains blocked and not authorized.


## 14. Producer-owned reconciliation protocol — candidate, not yet accepted (P12-03)

### 14.1 Source identified from pinned repository and official API contract

The pinned T1 source SHA `6e20fe94f3ad64cc450e73def80a167fe371e49e` contains REST methods for mark-price, index-price and premium-index klines, but the inspected `src/rest/client.rs` does not expose the standard trade-kline endpoint. The collector therefore does not currently implement the reconciliation path required by this contract.

Candidate authoritative recovery source: Binance USDⓈ-M Futures REST `GET /fapi/v1/klines`, with `symbol=BTCUSDT` and `interval=1m`. Binance documents Klines as uniquely identified by open time; the response contains open time, OHLC, base volume, close time, quote volume, trade count and taker-buy volumes as decimal strings/integers. Request limit is capped by the documented API maximum. Official documentation: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data . The documentation catalog also lists the endpoint under USDⓈ-M market data: https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data .

This endpoint is a candidate, not yet approved as a completeness oracle. The existing T1 REST client does not call it, and the contract must not imply that it already does.

### 14.2 Required reconciliation transaction

For every affected symbol and UTC interval `[start_ms,end_ms)`, after startup/restart, WebSocket reconnect, queue overflow, writer error, process crash, unknown receive continuity or manifest-generation discontinuity:

1. Freeze the affected interval as `RECONCILIATION_PENDING`; do not advance the source watermark.
2. Query the USDⓈ-M standard trade-kline REST endpoint for `BTCUSDT`, `1m`, covering the exact affected range. Pagination must be deterministic, bounded by the documented endpoint limit and preserve the requested half-open interval after local filtering by open time.
3. Retain the raw response bytes, request parameters, response status, retrieval time, endpoint identity, response digest and the trusted exchange-time observation used to establish that returned candles are closed.
4. Validate schema, symbol, interval, UTC alignment, open-time uniqueness, close-time boundary, decimal strings, OHLC invariants and expected time coverage.
5. Compare each REST final candle against the WebSocket-derived candidate. Identical values may be reconciled; any mismatch is `RECONCILIATION_CONFLICT` and quarantines the affected interval. No silent overwrite or source preference is allowed by this draft.
6. Persist reconciliation evidence and resulting accepted final-candle records durably before publishing a manifest that advances `watermark_open_time_exclusive_ms`.
7. Bind the evidence to the file generation and manifest using a reconciliation record ID, exact `[start_ms,end_ms)` range, endpoint/parameters, retrieval timestamp, server-time observation, response digest, validated candle count, gap/conflict result and the resulting committed prefix digest.

If the REST source is unavailable, rate-limited, incomplete, delayed or cannot prove the queried candles are final, keep the affected interval pending and do not advance the watermark. Retries must be bounded and observable; exhaustion is a blocked interval, never a successful seal.

### 14.3 Critical unresolved API semantics

Before `RECONCILED_COMPLETE` may be emitted, verify from authoritative Binance documentation and deterministic observations:
- exact `startTime` / `endTime` inclusion semantics and safe mapping to the half-open interval;
- whether standard 1m klines are returned for every minute with no trades, or whether no-trade intervals can be omitted;
- when a returned candle is guaranteed final and whether historical candles can be revised;
- behavior during symbol status transitions, maintenance, API partial failure and delayed publication;
- whether response pagination can be proven gap-free for the requested range.

If the endpoint omits no-trade intervals, an absent REST row cannot be interpreted as a missing candle or a no-trade minute without an additional authoritative rule. The producer must either obtain a documented exchange guarantee plus a deterministic fixture for this behavior, or design a separate trade-level reconciliation protocol. It must not infer no-trade intervals from silence.

If the endpoint's semantics do not establish completeness, this REST endpoint cannot authorize `RECONCILED_COMPLETE`; retain `UNKNOWN` and block the watermark. No synthetic candles, interpolation, carry-forward or fabricated zero-volume records are permitted.

### 14.4 Late corrections and sealed history

A later REST response that differs from an already sealed record must not rewrite the original file or silently mutate a sealed generation. Record an immutable correction event referencing the original candle key, prior payload digest, corrected payload digest, REST evidence and observation time. The correction path, downstream invalidation and re-aggregation semantics require a separately approved versioned contract. Until then, any post-seal discrepancy quarantines the affected interval and blocks downstream promotion.

### 14.5 Additional deterministic fixtures

Add:
- C46 REST reconciliation returns exact full expected 1m coverage and values match WS → reconciled evidence may be committed.
- C47 REST response omits a minute; no-trade semantics not proven → SOURCE_HEALTH_UNKNOWN, no watermark.
- C48 REST response is delayed/partial/rate-limited → RECONCILIATION_PENDING, no watermark.
- C49 REST and WS final candle differ → RECONCILIATION_CONFLICT, quarantine.
- C50 REST pagination repeats or skips an open time → reconciliation fails closed.
- C51 REST response contains a candle not yet proven closed by exchange-time boundary → pending, no watermark.
- C52 REST evidence digest or request-range binding mismatch → reject reconciliation evidence.
- C53 later REST correction to a sealed candle → immutable correction event or quarantine; never rewrite sealed source.
- C54 restart/reconnect with overlapping REST reconciliation → idempotent evidence and candle keys, no duplicate accepted record.

### 14.6 Status

This section identifies a concrete candidate endpoint from the official API documentation and confirms that the pinned T1 code does not yet implement it. It does not prove the endpoint's no-trade, finality, correction or pagination semantics. `RECONCILED_COMPLETE` remains unavailable until those questions are answered, the producer contract is implemented and tested, and an independent review accepts the evidence model.


## 15. P1.3 conservative REST reconciliation acceptance profile

### 15.1 Documentation evidence boundary

The official USDⓈ-M REST market-data catalog documents `GET /fapi/v1/klines`, `symbol`, `interval`, optional `startTime`/`endTime`, `limit` (maximum 1500), and that klines are uniquely identified by open time. It documents the response tuple and close-time field. The documentation reviewed for this revision does not establish all of the following: whether every no-trade minute is emitted, exact inclusive/exclusive semantics for both time parameters, a formal finality guarantee, historical immutability/correction policy, or a complete pagination proof under all boundary conditions.

Sources reviewed:
- https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data
- https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data

Therefore the endpoint remains a **candidate recovery/reconciliation source**, not an accepted completeness oracle. A 200 response, a non-empty array, a close-time field, or an apparent sequential result is not by itself proof that the requested interval is complete.

### 15.2 Fail-closed acceptance rule

For a requested UTC half-open interval `[start_ms,end_ms)` aligned to 1m, define the expected open-time set as every UTC minute boundary in that interval. The producer may mark the interval `RECONCILED_COMPLETE` only if all of the following are independently established:

1. The authoritative request-boundary semantics are verified, and the retrieval strategy proves that the complete requested range was queried without silently excluding either boundary.
2. Every expected minute has exactly one valid REST kline with that exact open time; duplicate, missing, out-of-range or non-aligned open times fail reconciliation.
3. Every returned candle is proven final under an authoritative rule, not merely inferred from local wall-clock time or the presence of a close-time field.
4. All pages are proven complete, ordered, non-overlapping after deduplication, and bound to the exact requested range and source identity.
5. REST and any existing WebSocket candidate agree field-for-field after exact decimal normalization. Any disagreement quarantines the interval; this draft does not authorize silently choosing one source.
6. Raw responses, request parameters, retrieval/server-time evidence, response digests, validation result, expected/observed open-time sets and generation/manifest binding are durably committed before watermark publication.

**A missing REST minute is always `SOURCE_HEALTH_UNKNOWN` under this version.** It is not classified as a no-trade minute and is not classified as a confirmed market-data gap. It blocks `RECONCILED_COMPLETE`, watermark advancement and aggregation. The producer must not synthesize a zero-volume candle, interpolate, carry forward, or infer no trades from an empty response.

This conservative rule may leave legitimate no-trade intervals permanently unsealable. That is an accepted reliability trade-off until a separate, authoritative no-trade proof is designed and approved. Do not relax this rule to improve availability.

### 15.3 Boundary and pagination handling

Because the reviewed documentation does not fully specify time-boundary inclusion, the producer must not assume `startTime` or `endTime` is inclusive or exclusive. A future implementation proposal must supply authoritative contract evidence for the exact semantics. Until then, a local filter cannot repair a server-side boundary omission that was never returned.

The documented maximum `limit=1500` is a page-size ceiling, not proof of pagination completeness. A future implementation must define deterministic page advancement, overlap/replay handling, duplicate detection, exact expected-open-time verification, response truncation detection, rate-limit/error handling and a hard bounded retry policy. If any page cannot be proven complete, the whole affected interval remains pending/unknown.

### 15.4 Finality and correction boundary

A candle's documented `close time` field describes its interval boundary; it does not, by itself, prove the API response is immutable or that no later correction can occur. Finality must be established using an authoritative exchange guarantee or another independently accepted proof. Local `now > close_time`, a delay buffer, or repeated identical polls are not sufficient proof of immutability.

If the exchange does not provide a documented no-revision guarantee, the design must explicitly limit its claim to a point-in-time reconciliation observation and retain a correction-detection/quarantine mechanism. It must not claim permanent finality. Any later mismatch against a previously sealed candle creates an immutable correction event and quarantine; sealed bytes are never rewritten.

### 15.5 New deterministic fixtures

- C55 one REST kline for each expected minute, exact range and verified boundary semantics → eligible for further finality/identity checks; not an unconditional pass.
- C56 missing REST open time → SOURCE_HEALTH_UNKNOWN; no no-trade inference, no watermark.
- C57 duplicate open time across overlapping pages → reject/quarantine; no watermark.
- C58 first or last expected minute absent due uncertain request-boundary semantics → SOURCE_WATERMARK_UNTRUSTED; no watermark.
- C59 page reaches documented limit and continuation cannot prove next expected open time → RECONCILIATION_PENDING; no watermark.
- C60 candle close time has passed locally but no authoritative finality guarantee → pending; no watermark.
- C61 later REST response differs from a previously reconciled candle → immutable correction event plus quarantine; never rewrite sealed bytes.
- C62 endpoint returns an empty array for a requested interval → SOURCE_HEALTH_UNKNOWN; not proof of no trades or full coverage.

### 15.6 P1.3 disposition

The conservative acceptance profile is now explicit. It resolves the unsafe ambiguity in how missing REST rows are interpreted, but it does **not** resolve the external API-contract gaps. The endpoint remains a candidate only. `RECONCILED_COMPLETE` remains disabled until boundary semantics, no-trade behavior, finality/correction guarantees and pagination completeness are independently evidenced and accepted. No implementation or runtime action is authorized by this design update.


## 16. P1.5 clarification — REST-only rows and source provenance (F02)

### 16.1 No implicit agreement when the WebSocket row is absent

For a candle key expected in the affected reconciliation interval:

- REST row present + matching WebSocket row present: compare every required field using exact decimal semantics. Equality is necessary but does not, by itself, prove completeness, finality or immutability.
- REST row present + WebSocket row absent: classify as `RECONCILIATION_SOURCE_DIVERGENCE`, not as agreement. The absence may represent a missed WebSocket event, a producer drop, a source publication difference or an unresolved exchange semantic.
- WebSocket row present + REST row absent: retain `SOURCE_HEALTH_UNKNOWN`; do not infer no-trade or a confirmed market gap.
- Both present but any field differs: `RECONCILIATION_CONFLICT`; quarantine the interval. Do not choose a preferred source or overwrite either payload.

Under the current contract revision, a REST-only row MUST NOT be inserted into a WebSocket-derived generation and MUST NOT advance its watermark. It is retained only as separately identified reconciliation evidence in isolated staging/quarantine. This conservative rule avoids silently changing the source composition of an existing generation.

### 16.2 Future mixed-source mode requires a new explicit contract

A future design may propose REST-supplied rows, but only as a separately versioned source mode. At minimum it must define:
- per-row source provenance (`WS_FINAL` or `REST_RECONCILED`) and immutable source-record identity;
- raw response/request evidence digest and exact interval binding for each REST-supplied row;
- deterministic precedence/conflict policy that never silently overwrites an accepted record;
- generation-level source composition and reconciliation transaction identity;
- replay/idempotency and correction/quarantine behavior;
- independent review and a separate explicit approval.

Until that contract is accepted, the adapter must not merge REST-only rows into the canonical candidate file. The current REST endpoint remains an unaccepted completeness oracle (F01).

## 17. P1.5 clarification — durable producer health and watermark invalidation (F03)

### 17.1 Fail-closed health events

The producer contract must expose explicit, monotonic health evidence for at least:
- WebSocket disconnect, reconnect and subscription/session replacement;
- inbound queue capacity exhaustion, dropped/rejected event, or inability to prove queue continuity;
- parser/deserialization failure for a kline event;
- writer task failure, buffer flush failure, short/failed write, fdatasync/fsync failure;
- process shutdown, unexpected termination, restart and generation change;
- reconciliation request failure, partial/ambiguous response, retry exhaustion or conflicting source result.

Each detectable event must carry event type, collector instance, generation, symbol/interval scope, observation time, affected event-time range when known, sequence/counter where available, and durable record identity. Health evidence must be committed before any later manifest publication can claim the affected range complete.

### 17.2 Sticky invalidation and recovery

- Queue overflow/drop, unknown queue continuity, parse failure affecting a potentially eligible event, writer error, uncertain process termination or generation discontinuity invalidates the affected completeness claim.
- Invalidation is sticky for the affected range and generation. A later healthy socket, successful write, or restarted process does not clear it.
- If the exact affected range cannot be bounded, invalidate from the last independently proven checkpoint through the next independently reconciled boundary; if no trustworthy checkpoint exists, hold the generation watermark and quarantine the uncertain range.
- No watermark may advance across an unresolved health event.
- Recovery requires the separately accepted reconciliation protocol, durable evidence and a new validated publication transaction. Under current P1.3, unresolved or missing REST minutes remain `SOURCE_HEALTH_UNKNOWN`; therefore recovery may remain blocked.
- On startup, absence of a clean durable shutdown/continuity record is itself uncertainty. Do not infer continuity from process uptime, file length, timestamps or a healthy current socket.

### 17.3 Crash limitation and negative acceptance cases

A process cannot guarantee that it writes a final health marker after abrupt power loss or forced termination. Therefore the design must not depend on a last-second shutdown callback. Generation allocation, durable checkpoints and restart reconciliation must make an unclean termination detectable from previously committed state; if it cannot be detected or bounded, quarantine and withhold the watermark.

Add required negative fixtures (planned, not executed):
- C63 queue full with explicit drop/reject → sticky invalidation; no watermark.
- C64 queue continuity cannot be established → SOURCE_HEALTH_UNKNOWN; no watermark.
- C65 parser rejects an eligible-event payload → affected range invalidated; no watermark.
- C66 flush/write/sync error → no committed offset or watermark advance.
- C67 process terminates without clean-shutdown record → restart generation marked uncertain; no continuity assumed.
- C68 health event is recorded after a candidate manifest publication → reject ordering; no watermark.
- C69 healthy reconnect after an unresolved gap → invalidation remains sticky.
- C70 affected range cannot be bounded → quarantine from last trusted checkpoint or entire generation if none exists.
- C71 repeated/overlapping reconciliation evidence → idempotent event identity; no duplicate acceptance and no bypass of unresolved gaps.

These are contract acceptance requirements only. They do not assert that the current producer emits such events or that a tested implementation exists.

## 18. P1.5 clarification — manifest integrity threat model (F04)

### 18.1 Current protection claim

The current adjacent manifest, header digest and committed-prefix digest are intended to detect accidental corruption, truncation, inconsistent publication and certain crash/recovery mismatches. A digest stored beside the data that it hashes is not, by itself, an authenticity mechanism.

**Current contract scope is accidental failure/corruption detection only. It does not claim protection against a local attacker who can replace both data and manifest, roll both back, alter the host clock, or modify the collector and its credentials.**

No security claim may describe the current SHA-256 prefix digest as tamper-proof, authenticated, anti-rollback or independently anchored.

### 18.2 If adversarial local modification is in scope

Before claiming protection against malicious local modification or rollback, a separately reviewed design must specify:
- manifest authentication (for example, a keyed MAC or digital signature) with key custody separated from the data-writer's ordinary file permissions;
- key rotation, revocation, recovery and compromise response;
- monotonic generation/checkpoint anchoring outside the mutable data+manifest directory or another independently controlled trust boundary;
- verification behavior when the anchor is unavailable, stale, rolled back or inconsistent;
- threat coverage for host root compromise, credential compromise, backup restoration and clock manipulation.

A MAC whose key is available to the same compromised writer/host does not protect against full host compromise. An external anchor and key separation must be described honestly; no mechanism is presumed available or implemented by this document.

### 18.3 Fail-closed rollback handling

Even within the current accidental-failure scope:
- manifest version, generation, committed offset and durable checkpoint must never regress relative to the last trusted state available to the consumer;
- missing, stale, conflicting or unverifiable prior state yields `SOURCE_MANIFEST_ROLLBACK` or `SOURCE_DURABILITY_UNPROVEN`, then quarantine;
- restoration of an older backup is not silently accepted as a continuation of the current generation. It requires a separately recorded restore epoch/reconciliation decision and a new generation;
- if no independent prior checkpoint exists, the consumer cannot claim adversarial rollback detection. It must state that limitation rather than infer trust from a self-consistent file/manifest pair.

Add required negative fixtures (planned, not executed):
- C72 data and adjacent manifest replaced together with a self-consistent older pair → not claimed detectable under current threat scope; adversarial rollback protection remains NOT PROVIDED.
- C73 manifest generation/offset regresses against a trusted external checkpoint → reject and quarantine.
- C74 manifest authentication fails or key is unavailable under an authenticated future profile → fail closed; no watermark.
- C75 external monotonic anchor is stale/unavailable → no anti-rollback claim; hold promotion/watermark according to the approved profile.
- C76 backup restore presents an older generation → require restore epoch and new generation; never append as if continuity were proven.

These fixtures are design requirements only; none has been executed.

## 19. P1.5 disposition and unchanged blockers

- F02: clarified conservatively. REST-only rows are divergence evidence and cannot be inserted into the current WS-derived generation. A future mixed-source mode requires a new versioned contract.
- F03: clarified at contract level with sticky invalidation, durable health-event ordering, unclean-shutdown uncertainty and negative fixtures. Actual producer instrumentation and failure semantics remain unimplemented and unverified.
- F04: threat scope is explicitly limited to accidental failure/corruption detection. Adversarial local tampering/rollback protection is NOT PROVIDED unless a separately reviewed authenticated-manifest and independent-anchor design is approved.
- F01 remains CRITICAL: Binance REST is not an accepted completeness oracle; no-trade, boundary, finality/correction and pagination semantics remain unresolved.
- F05 remains HIGH: pinned producer decimal serialization defect is confirmed; no source correction is authorized or evidenced.
- F07 remains MEDIUM/HIGH operational blocker: target filesystem/provider durability and crash-recovery behavior are unverified.

This P1.5 update is documentation-only. It does not make the contract implementation-ready, does not authorize source changes, tests, Actions, VPS/runtime, T1 activation, T0/T2 changes, promotion, or destructive data operations.


## 20. P1.7 clarification — normative contract precedence, GAP_DETECTED and health-evidence failure

### 20.1 Normative precedence and FINAL_ONLY

For the current Binance USD-M BTCUSDT 1m producer-feed scope, this v1.1 document is the sole normative source-file and producer contract. The earlier `T1_SOURCE_FILE_CONTRACT_V1_AND_INGESTION_ADAPTER_DESIGN_2026-11-09.md` is archival/non-normative wherever it conflicts with this revision. Its proposed per-row `is_closed` field and related finality/schema requirements are superseded for this first mode.

The current mode is exclusively `output_mode=FINAL_ONLY` with `interval=1m` declared in the versioned manifest. The producer must filter every `is_closed=false` event before persistence, and producer regression tests must prove that behavior. The absence of a per-row flag is acceptable only when the versioned manifest and producer implementation/test evidence jointly establish this exact mode. Legacy or unversioned files, missing manifests, unknown schema versions, and files without a verifiable FINAL_ONLY declaration are ineligible for canonical aggregation. This clarification does not make the current producer compliant; its decimal serialization defect and missing manifest/durability implementation remain blockers.

### 20.2 Exact meaning and availability of GAP_DETECTED

Under the current contract, `GAP_DETECTED` is a reserved state and is **not currently assignable**. No current producer or consumer may set it merely because an expected row is absent.

It may be enabled only by a separately approved, versioned evidence profile that proves a specific missing source event over an exact symbol/interval/event-time range, identifies the authoritative source and completeness semantics, binds the evidence to the generation, and passes independent review. No such profile is accepted today.

The following must never set `GAP_DETECTED`:
- a missing or empty Binance REST response, uncertain REST boundary, incomplete pagination, rate limit, or unavailable reconciliation;
- an absent WebSocket row, silence, no-trade inference, or REST/WS divergence;
- queue overflow, disconnect, parser/writer/sync failure, process crash, or unknown receive continuity;
- a missing row in an unsealed or otherwise unproven window.

Those cases remain `SOURCE_HEALTH_UNKNOWN`, `SOURCE_HEALTH_INVALIDATED`, `RECONCILIATION_SOURCE_DIVERGENCE`, or another precise quarantine/pending state as applicable. A transport/collector continuity failure is health invalidation, not proof of a market-data gap. `WINDOW_GAP` remains a consumer classification available only after a valid seal and complete health proof establish that a source row is absent; it does not authorize aggregation or synthesis. Under P1.3, the REST endpoint cannot currently provide that proof, so missing REST minutes remain UNKNOWN.

### 20.3 Failure to durably persist health evidence

If the producer detects a health failure but cannot durably persist its health event or invalidation record (including disk full, write/flush/fsync/fdatasync failure, health-journal corruption, or unavailable storage):

1. Immediately set a sticky in-process invalidation for the affected range/generation; if the range cannot be bounded, invalidate from the last independently trusted checkpoint, or the entire generation if no such checkpoint exists.
2. Stop all committed-offset, manifest-state, watermark and seal advancement for that generation. Do not attempt to publish a success/healthy manifest through the failed persistence path. The implementation may stop the writer entirely; no further bytes from the uncertain generation are eligible for consumption.
3. Treat the generation as uncertain/quarantined. A later successful write, healthy reconnect or process restart cannot clear this state.
4. On restart, require a verifiable durable clean-close/seal record and matching generation/checkpoint/prefix state. If the prior generation was still ACTIVE, its close marker is absent, the health journal is missing/corrupt, or any checkpoint cannot be verified, quarantine the affected range/generation. Absence of a health event is never evidence that no failure occurred.
5. Recovery requires a new generation and a separately accepted reconciliation/recovery procedure. Because the current REST profile does not establish completeness, recovery may remain blocked indefinitely.

No independent durable health-event channel is currently specified or assumed. The present guarantee is deliberately limited: detect uncertainty through previously durable generation/checkpoint/clean-close state and fail closed; it does not guarantee that every last-moment failure event can itself be recorded. Any future independent journal/channel requires a separate design, failure-domain analysis, independent review and approval. If prior durable state cannot distinguish clean closure from interruption, the source cannot be trusted and remains quarantined.

### 20.4 Additional negative acceptance fixtures (planned, not executed)

- C77 health-event write fails due disk full or fsync/fdatasync error → immediate sticky in-process invalidation; no offset/manifest/watermark advance; generation quarantined.
- C78 health journal missing, corrupt or unverifiable on restart → quarantine; absence of event is not interpreted as healthy continuity.
- C79 restart finds prior generation ACTIVE or no verifiable durable clean-close marker → generation uncertain/quarantined; no watermark or aggregation.
- C80 attempted transition from UNKNOWN/INVALIDATED to GAP_DETECTED based only on REST absence, WS absence, transport loss or no-trade inference → reject; state remains UNKNOWN/INVALIDATED.
- C81 producer manifest omits `output_mode=FINAL_ONLY`, declares another mode, or producer regression evidence is absent → reject source for canonical aggregation.

These fixtures are contract requirements only. They have not been implemented or executed. No current implementation is claimed.

### 20.5 P1.7 disposition

P1.6-F01 is resolved at documentation level by making v1 archival/non-normative and v1.1 the sole normative producer contract for this scope. P1.6-F02 is resolved conservatively by reserving `GAP_DETECTED` until a separately accepted authoritative evidence profile exists. P1.6-F03 is resolved at design level by defining immediate sticky invalidation, publication stop, restart quarantine and the absence of an assumed independent health channel.

These clarifications do not resolve the pre-existing blockers: no accepted REST completeness oracle (F01), confirmed producer decimal-loss defect (F05), and unverified target filesystem/provider durability (F07). Independent review remains required. Design readiness and implementation authorization are not granted.


## 21. P1.9 contract correction — publication receipts, writer fencing and gap-state availability

This section is normative and supersedes any conflicting wording in §§2–5, 8–9 and 20. The exact behavior below is a design contract only; no implementation or filesystem claim is made.

### 21.1 Publication commit point and reader visibility

A manifest rename is not itself a commit point. The commit point for a publication is the visibility of a valid immutable commit receipt whose contents bind the exact manifest and data-prefix state, and which can only be created after the manifest's containing-directory fsync has returned successfully.

The writer sequence and reader acceptance rules are specified in §5.2. In particular:
- The manifest is PREPARED until the directory fsync after its rename succeeds.
- The commit receipt is written only after that durability barrier; its unique filename and contents bind the manifest SHA-256, generation, publication sequence, file identity, offset, record count, prefix digest and watermark.
- A reader requires a shared lock and an exact matching receipt. Manifest visibility without a matching receipt is never sufficient.
- If the writer dies before receipt publication, readers reject the candidate manifest. If the receipt is lost after a crash, readers fail closed. This intentionally prefers false-negative availability over false-positive completeness.
- Receipt visibility cannot certify a manifest that skipped the prior directory fsync, because the producer cannot enter the receipt-publication step until that fsync succeeds. This ordering must be proven by deterministic process-crash tests and then by an authorized target-filesystem crash/recovery test.

### 21.2 Writer lock and generation fencing

The stable lock-file protocol in §5.1 is mandatory for all writers and readers. The lock file is created once during controlled initialization, never replaced/unlinked, and all cooperating processes use the same filesystem object. The writer holds exclusive ownership from before generation allocation through publication-receipt visibility. Readers hold shared ownership across manifest/receipt/prefix validation. A paused process cannot be displaced by timeout or PID heuristics; it continues to hold the kernel lock. A crashed process loses the lock, but its incomplete publication is rejected because it has no matching receipt.

Generation allocation is durable before any append is permitted. The counter update must complete file sync, atomic rename and parent-directory sync while holding the exclusive lock. An ambiguous counter or lock identity blocks reuse. Random generation-instance identity supplements but does not replace the monotonic sequence. If the target filesystem does not reliably implement the required locking and sync semantics, the contract is unsupported on that filesystem and remains blocked.

### 21.3 WINDOW_GAP is reserved under the current profile

The current v1.1 profile cannot assign WINDOW_GAP. P1.3 does not accept the REST endpoint as a completeness oracle; missing REST rows remain SOURCE_HEALTH_UNKNOWN, and REST/WS asymmetry remains divergence/unknown. A nominal watermark or local socket health cannot convert absence into a confirmed source gap. Therefore no current fixture, manifest writer or adapter may set WINDOW_GAP. A future profile must be separately versioned, authoritative for exact interval completeness (including no-trade semantics), independently reviewed and explicitly approved. Even under such a future profile, a gap blocks aggregation and never authorizes synthetic candles.

### 21.4 Producer interval and product identity checks

The producer must validate the configured USD-M endpoint/stream family and each incoming event's exact symbol and interval before persistence. Only BTCUSDT 1m final kline events from the declared USD-M perpetual stream are eligible. The producer must filter provisional events, reject mismatched intervals, and bind the exact ExchangeInfo snapshot/record to the generation. A hardcoded symbol exception is never sufficient and may not bypass status, contract type or quote-asset validation. The adapter repeats manifest checks independently. margin_asset remains optional/unavailable unless authoritative evidence supplies it.

### 21.5 Strict v1.1 manifest serialization and file binding

The v1.1 manifest is UTF-8 JSON using RFC 8785 JSON Canonicalization Scheme (JCS) for the digest input. The parser must reject duplicate keys, invalid UTF-8, non-canonical serialization, invalid types, missing required fields, null where not allowed, and unknown fields in schema v1.1. Numeric fields are integers only where specified; floating-point JSON numbers are prohibited. Decimal market values remain raw strings in CSV and are not placed in manifest floating-point fields.

Required manifest fields and types:
- manifest_version: exact string 1.1;
- schema_version: exact supported schema identifier;
- generation_sequence: unsigned integer, strictly increasing within the source root;
- generation_id: unique random identifier;
- publication_sequence: unsigned integer, strictly increasing within the generation;
- exchange_id, market_scope, contract_type, symbol, base_asset, quote_asset, datatype, interval, source_endpoint_family, output_mode: non-empty strings constrained to the approved values;
- endpoint_config_sha256, exchange_info_snapshot_sha256, symbol_record_sha256, collector_source_sha256, header_sha256, data_prefix_sha256: lowercase 64-character SHA-256 hex strings;
- collector_instance_id, data_file_relative_path, data_file_identity: non-empty strings; file identity includes the platform identity tuple captured by the producer and revalidated by the reader;
- state: one of ACTIVE, SEALED, QUARANTINED;
- committed_offset_bytes, committed_record_count, watermark_open_time_exclusive_ms: non-negative integers;
- source_health: one of RECONCILED_COMPLETE, UNKNOWN, INVALIDATED;
- reconciliation_evidence_ref: required non-empty immutable evidence identifier whenever RECONCILED_COMPLETE is claimed; absent otherwise;
- created_at_utc, updated_at_utc: RFC 3339 UTC strings for audit only, never used as completeness or fencing evidence.

The fixed manifest path is manifest.json within the generation directory. The generation directory name must contain and match the generation ID and sequence. The manifest binds exactly one relative data-file path; the file must be a regular file and its identity, header, committed size and prefix digest must match. The commit receipt is stored under a fixed commits/ subdirectory with a unique generation/publication-sequence filename and contains the manifest digest plus the exact bound commit fields. Duplicate receipts for a sequence, multiple candidate manifests, or any path ambiguity causes quarantine.

The configured source root and all descendants must be opened without following symlinks (for example, directory-relative no-follow opens where supported). Symlinked root/components, manifest, receipt or data files are rejected. Unexpected hard links, non-regular files, path traversal, absolute paths, alternate encodings and file replacement during validation are rejected. If the platform cannot enforce these checks, source eligibility is NOT VERIFIED and the adapter must fail closed. The schema is closed-world for v1.1; extensions require a new schema version, not ignored fields.

### 21.6 Fixture acceptance rule

C01–C99 are contract scenarios, not executed tests. A fixture PASS proves only its deterministic software property; it cannot prove Binance completeness or target-filesystem D2–D4 durability. C46 is explicitly conditional on every P1.3 prerequisite. C82–C90 cover publication/locking/generation; C91–C92 cover interval and product identity; C93–C95 cover manifest parsing/binding/path safety; C96 covers unavailable WINDOW_GAP; C97–C99 cover FINAL_ONLY/finality/manifest binding. The test suite must assert both expected rejection and absence of committed watermark/receipt where applicable.

### 21.7 Remaining blockers and disposition

- Publication protocol: DESIGN CLARIFIED; implementation and target-filesystem proof NOT VERIFIED.
- Writer fencing/generation: DESIGN CLARIFIED; lock semantics and crash behavior NOT VERIFIED on target storage.
- WINDOW_GAP: RESERVED / NOT ASSIGNABLE under current profile.
- FINAL_ONLY/interval/product identity: CONTRACT REQUIREMENTS CLARIFIED; producer implementation/tests NOT VERIFIED; pinned source remains non-compliant until corrected.
- Manifest schema/fixture catalog: DESIGN SPECIFIED; parser and fixtures NOT IMPLEMENTED/EXECUTED.
- REST completeness oracle: BLOCKED; no-trade, boundary, pagination, finality/correction unresolved.
- Decimal preservation: BLOCKED; pinned writer f64/12-decimal/parse-to-zero defect remains.
- Filesystem durability: NOT VERIFIED; no target crash/recovery test authorized or executed.

This section does not authorize producer or adapter code changes, test execution, GitHub Actions dispatch, REST requests, VPS/runtime, T1 activation, T0/T2 changes or destructive data operations.
