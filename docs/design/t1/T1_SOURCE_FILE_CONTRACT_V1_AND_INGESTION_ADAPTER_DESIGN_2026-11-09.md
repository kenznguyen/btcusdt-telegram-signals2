# T1 Source-File Contract v1 and Ingestion Adapter Design — 2026-11-09

> [!IMPORTANT]
> **ARCHIVAL / NON-NORMATIVE — SUPERSEDED FOR PRODUCER SOURCE CONTRACT BY T1 SOURCE-FILE CONTRACT v1.1.**
>
> This document is retained as the historical adapter-design baseline. For the current Binance USD-M BTCUSDT 1m producer feed, the v1.1 document is the sole normative source-file/producer contract. If any statement here conflicts with v1.1, v1.1 controls. This document does not authorize implementation or runtime use.
>
> In particular, the per-row `is_closed` schema, the proposed v1 header, and the associated finality assumptions below are superseded by v1.1's versioned manifest declaration `output_mode=FINAL_ONLY` plus producer regression proof that provisional events are filtered before persistence. A per-row `is_closed` field is not required for this first mode. Legacy/unversioned files remain ineligible for canonical aggregation. The remaining adapter concepts below are historical design material only and require reconciliation with v1.1 before any implementation.

## Status and decision

**ARCHIVAL DESIGN BASELINE — NON-NORMATIVE FOR PRODUCER CONTRACT; v1.1 CONTROLS. NOT IMPLEMENTED / NOT APPROVED FOR RUNTIME.**

This document defines a bounded, fail-closed contract for a future T1 CSV reader and isolated canonicalization adapter. It does not change the T1 collector, T0, T2, VPS or runtime.

Reviewed T1 source:
- Repository: `kenznguyen/binance-futures-collector`
- PR #1: OPEN / DRAFT / not merged
- Exact source SHA: `6e20fe94f3ad64cc450e73def80a167fe371e49e`
- Relevant source files and blob SHAs are recorded in `T1_COLLECTOR_DATA_CONTRACT_COMPATIBILITY_REVIEW_2026-11-09.md`.

## 1. SUPERSEDED — historical per-row finality proposal (v1.1 controls)

At the reviewed source SHA:
- `KlineData` receives Binance field `x` as `is_closed: bool`.
- `KlineCsv` does not contain an `is_closed` field.
- `HEADER_KLINES` has no `is_closed` column.

Therefore the current persisted CSV cannot independently prove whether a row is a final candle or an interim WebSocket update. A consumer must not infer finality from file age, row order, elapsed wall-clock time, or the last row observed.

**Required source change before canonical candle ingestion:** persist `is_closed` explicitly in a versioned CSV schema, or publish a distinct final-candle-only file/stream with equivalent provenance. Interim rows must remain distinguishable from final rows. Existing schema files without this field are legacy/untrusted for canonical 1m→15m/1h aggregation and must be rejected by this adapter mode, not silently guessed.

No collector source change is included in this design task.

## 2. Scope boundary

Initial adapter scope is deliberately limited to:
- Exchange: Binance
- Market: USD-M / USDT-M perpetual (the T1 repository calls this `futures`; adapter must verify the exact market identity, not trust a directory name alone)
- Symbol: BTCUSDT only for the first fixture suite; symbol identity normalized to uppercase canonical form
- Source datatype: native `klines` only
- Native interval: 1m
- Candidate derived intervals: 15m and 1h
- Output: isolated staging/canonicalization result and validation report only

Out of scope until separately specified: trades, depth/orderbook, liquidations, funding, open interest, long/short ratios, mark/index/premium klines, and any use of sidecar manifests as proof of market-data completeness.

T1 is not the canonical data foundation. The adapter must not write to T0's SQLite database, modify T0's API, or replace the T0 Binance canonical ingestion path. T0 remains independently authoritative. A future promotion path requires its own review and approval.

## 3. Source file identity and schema contract

### 3.1 Accepted file layout

The existing documented layout is:

`<root>/klines/<symbol-lowercase>/<YYYY-MM-DD>/<symbol-lowercase>_klines_<YYYY-MM-DD>.csv`

The reader must:
- Resolve paths beneath one explicitly configured root; reject path traversal and symlinks escaping the root.
- Require `exchange=binance`, the explicitly allowed futures market, `datatype=klines`, and the symbol to agree across path and every row.
- Require date partition to agree with the UTC date of each candle open timestamp.
- Treat all timestamps as integer Unix milliseconds in UTC.
- Parse CSV using a real CSV parser; never split rows naively on commas.
- Require exact ordered header equality for the declared schema version. Unknown, missing, duplicate or reordered columns are rejected unless a future version explicitly defines compatibility.
- Reject malformed quoting, truncated rows, invalid UTF-8, non-finite numbers, negative volume/trade count, invalid OHLC relationships, and invalid timestamp ranges.
- Preserve the original source bytes and source-relative path as provenance; never rewrite T1 source files.

### 3.2 SUPERSEDED — historical proposed schema versions

- **Legacy v0:** existing header without `is_closed`. Read-only archival/diagnostic use only; NOT eligible for canonical candle aggregation.
- **Historical proposed v1 (SUPERSEDED; DO NOT IMPLEMENT):** existing columns plus a per-row `is_closed` column. The current v1.1 FINAL_ONLY manifest mode supersedes this proposal for the present scope; see v1.1 section 20.
- The schema version must be declared in a small sidecar manifest for each file or in a deterministic file-level metadata record. The adapter must not infer version from a permissive partial-header match.
- The manifest must include at minimum: `schema_version`, `collector_source_sha`, `exchange`, `market`, `datatype`, `symbol`, `partition_date_utc`, `file_relative_path`, `header_sha256`, and a monotonic file generation/identity.
- A manifest is descriptive provenance, not proof of completeness or durability. The adapter verifies the header and content independently.

### 3.3 Candle row semantics

- `timestamp_ms` is candle open time, not close time or event-arrival time.
- `datetime_utc` must encode the same instant as `timestamp_ms`, millisecond precision, UTC.
- `is_closed=false` rows are provisional and cannot contribute to canonical aggregates.
- `is_closed=true` rows are final source candidates. Multiple final rows for the same (exchange, market, symbol, interval, open_time) with identical normalized payload are idempotent duplicates. Conflicting final payloads are quarantined and fail the affected aggregate window; never pick the last row silently.
- A final row must have the exact 1m open-time alignment and OHLCV invariants. Decimal values must be parsed losslessly (decimal arithmetic; no binary-float rounding during aggregation).

## 4. File tailing and durable cursor semantics

T1 files are append-oriented and may still be active. The reader must:
1. Open files read-only and record a stable file identity (device/inode where available, relative path, header hash, and generation).
2. Read only complete newline-terminated CSV records. A partial final record is deferred; it is not an error and the cursor must not advance beyond the last complete record.
3. Maintain a byte-offset cursor per source file, plus source identity, schema version, last committed row key and content hash.
4. Detect truncation, replacement, header change, identity change or offset regression. Halt that file and require controlled replay/reconciliation; never continue from a stale offset.
5. Process at-least-once. Commit parsed rows, deduplication keys, derived staging records, and cursor advancement atomically in the adapter's own staging store.
6. Use stable row identity derived from source file identity + byte start/end offsets + canonical row hash. For candle semantic uniqueness also enforce (exchange, market, symbol, interval, open_time).
7. If a retry sees the same identity and same payload, treat it as duplicate. If the same semantic candle key has a different final payload, mark CONFLICT and block the affected window.
8. Never delete, rename, truncate, rotate, compact or otherwise mutate source files. No source retention/deletion policy is defined here.

The T1 writer's buffered `flush()` is not a durable-commit acknowledgement. Adapter cursor advancement proves only that the adapter durably committed the bytes it read to its own staging store; it does not prove that all source events reached the T1 file. Collector-side durability/sealing semantics remain a separate prerequisite and must be independently specified.

## 5. 1m → 15m / 1h aggregation contract

All windows are UTC-aligned and half-open:
- 15m: `[floor(open_time / 900000) * 900000, start + 900000)`
- 1h: `[floor(open_time / 3600000) * 3600000, start + 3600000)`

For a candidate aggregate, require exactly 15 or 60 distinct, non-conflicting, final 1m candles with open times at every expected minute in the interval. No missing-minute fill, interpolation, synthetic candle, carry-forward, or partial aggregate is permitted.

Aggregation:
- open = open of first minute
- high = maximum high
- low = minimum low
- close = close of last minute
- volume = exact sum of base volume
- quote_volume = exact sum of quote volume
- trade_count = integer sum
- taker_buy_base = exact sum
- taker_buy_quote = exact sum

Validation:
- Every constituent candle must be final, schema-valid, same symbol/market and exactly aligned.
- Require contiguous expected open times and exactly one accepted final payload per minute.
- Require `low <= min(open, close) <= max(open, close) <= high`, positive/valid price values, non-negative volumes and non-negative integer trade count.
- Verify deterministic output: same accepted input set produces byte-equivalent normalized aggregate values and identical constituent provenance.
- A late or corrected final minute invalidates/recomputes the derived staging window under a new revision; it must not silently mutate an already promoted canonical candle.
- A gap, conflicting duplicate, malformed row, unknown schema or unresolved correction marks the window INCOMPLETE/CONFLICT and blocks output promotion.

The aggregate's source provenance must include the full set or a deterministic digest of all constituent row identities and payload hashes, source file identities, collector source SHA, adapter version, aggregation contract version, and the time the adapter durably committed the result. Do not fabricate T0 `availableAtMs`, `quality`, `availabilityKind` or datasetVersion fields from a T1 CSV timestamp. Mapping into the T0 contract requires a separate approved promotion contract.

## 6. Isolated adapter boundary

Proposed logical stages:

1. **Discover:** enumerate eligible source files under the configured root; read-only.
2. **Validate source:** verify manifest, header, identity, path, row schema and timestamps.
3. **Tail/parse:** consume complete rows and persist adapter-owned source cursor.
4. **Normalize:** preserve raw decimal strings and derive validated typed values without mutating source bytes.
5. **Deduplicate:** enforce both source-row identity and semantic candle uniqueness.
6. **Aggregate:** produce 15m/1h candidate windows only when every expected final minute is present.
7. **Quarantine:** retain rejected row/window metadata and reason codes in staging; do not silently drop malformed or conflicting input.
8. **Report:** emit machine-readable coverage, gaps, conflict counts, lag, source provenance and deterministic dataset digest.
9. **Promotion gate:** disabled by default and absent from this implementation scope. No write path to T0.

The adapter should have read-only access to T1 source files and write access only to its own isolated staging/output directory or database. It must not have T0 DB credentials, T0 API write capability, exchange credentials, or trading permissions.

## 7. Stable error/status taxonomy

- `SOURCE_NOT_FOUND`: expected file/partition not present.
- `UNSUPPORTED_SCHEMA`: legacy v0 or unknown header/version.
- `SOURCE_IDENTITY_CHANGED`: replacement, truncation, generation mismatch or header drift.
- `PARTIAL_RECORD`: trailing incomplete bytes; defer without advancing cursor.
- `ROW_INVALID`: malformed CSV, timestamp, decimal or invariant.
- `DUPLICATE_IDENTICAL`: idempotent duplicate; informational.
- `CANDLE_CONFLICT`: same semantic key with different final payload.
- `WINDOW_GAP`: one or more expected 1m candles missing.
- `WINDOW_INCOMPLETE`: not all expected final minutes available.
- `WINDOW_VALIDATED`: complete and valid staging aggregate; not T0 promotion.
- `SOURCE_DURABILITY_UNPROVEN`: source collector durability/sealing contract not established.

Errors must fail closed for the affected symbol/window. No silent fallback to OKX, synthetic data, another exchange, or stale cached values.

## 8. Deterministic test matrix (required before implementation)

| ID | Fixture / scenario | Expected result |
|---|---|---|
| C01 | Valid v1 header and one final row | Parse PASS |
| C02 | Legacy v0 header without `is_closed` | UNSUPPORTED_SCHEMA |
| C03 | Interim row (`is_closed=false`) | Excluded from aggregates |
| C04 | One valid final 1m candle | Staging row PASS; no 15m/1h aggregate yet |
| C05 | Exactly 15 contiguous final 1m rows | One 15m WINDOW_VALIDATED |
| C06 | Exactly 60 contiguous final 1m rows | One 1h WINDOW_VALIDATED |
| C07 | Missing one minute in a 15m/1h bucket | WINDOW_GAP; no aggregate |
| C08 | Identical duplicate final row | DEDUPLICATED; same output |
| C09 | Conflicting duplicate final row | CANDLE_CONFLICT; window blocked |
| C10 | Partial final CSV line | PARTIAL_RECORD; cursor stays at prior complete offset |
| C11 | Restart after staging transaction before acknowledgement | Replay safe; no duplicate aggregate |
| C12 | Crash before transaction commit | Cursor and rows both remain uncommitted |
| C13 | File truncation/replacement/header change | SOURCE_IDENTITY_CHANGED; halt file |
| C14 | Wrong symbol/date/market/exchange in row | ROW_INVALID |
| C15 | UTC midnight/day partition boundary | Correct bucket and file selection |
| C16 | High/low/OHLC invariant violation | ROW_INVALID |
| C17 | Decimal precision stress | Exact deterministic sums; no float drift |
| C18 | Late final minute after prior incomplete window | Window can become validated only after all minutes present |
| C19 | Conflicting late correction after validation | New revision/conflict; no silent overwrite |
| C20 | Source file changes while being read | Only complete stable records consumed; retry/reconcile |
| C21 | Source manifest/header hash mismatch | UNSUPPORTED_SCHEMA or SOURCE_IDENTITY_CHANGED |
| C22 | T0 DB path accidentally supplied | Configuration rejected; no T0 write path exists |
| C23 | Missing data with OKX available | Fail closed; no venue fallback |
| C24 | 1m stream contains duplicate interim updates and one final update | Only one final semantic candle enters aggregation |

Test levels:
- Pure parser/normalizer unit fixtures first.
- Cursor/idempotency/restart tests against a temporary adapter-owned store.
- Aggregation/gap/conflict tests with deterministic generated fixtures.
- Read-only file integration test against copied fixture files.
- No VPS, T0 database, live Binance connection, T1 activation or real market-data ingestion in these tests.

## 9. Acceptance gates

The adapter implementation cannot start until:
1. T1 source owner approves adding a versioned explicit `is_closed` field or final-only output.
2. T1 source-file manifest and writer durability semantics are specified and reviewed.
3. Independent review accepts schema, cursor transaction model and aggregation semantics.
4. The deterministic fixture suite is implemented and passes.
5. The adapter is proven unable to write to T0 and cannot fall back to another venue.

The adapter cannot be connected to T0 or promoted to T2 without a separate owner approval, T0 contract mapping, and a separate end-to-end evidence gate.

## 10. Guardrails

- T0 remains independent and canonical.
- No direct T1 writes into T0 SQLite or T0 API.
- No T1 runtime activation or VPS command in this task.
- No T0/T2 source or runtime changes.
- No Strategy Core, AI strategy, ledger, Shared Risk Engine or Kill Switch changes.
- Paper-only; no live orders; `AI_EXECUTION_ENABLED=false`.
- No OKX replacement or fallback.
- No deletion, archive, cleanup, vacuum, compaction, backup expiry or destructive tests.
- T1 PR #1 remains OPEN/DRAFT; no review or merge action submitted.

## Final status

**DESIGN COMPLETE / IMPLEMENTATION BLOCKED ON T1 SOURCE CONTRACT CHANGE AND DURABILITY EVIDENCE.**

No tests executed; this is a design/evidence artifact. GitHub Actions was not dispatched. No artifact, runtime or VPS evidence is claimed.

Next step: independent review of this contract, then (only after explicit approval) implement the smallest source-schema change that preserves `is_closed` and produces versioned file metadata. Adapter implementation remains a later gate.
