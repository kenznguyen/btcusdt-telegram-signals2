# T1 Order Book V1 — Source Gap Assessment

Date: 2026-11-13
Status: **BLOCKED — T1 source does not satisfy T1_T2_ORDERBOOK_V1**
Review type: read-only source review; no T1 files changed and no runtime was started.

## 1. Reviewed source identity

- T1 repository: `kenznguyen/binance-futures-collector`
- Reviewed PR: [#1](https://github.com/kenznguyen/binance-futures-collector/pull/1), OPEN / DRAFT
- PR head branch: `feature/t1-connection-sidecar-integration-20261107`
- Exact reviewed T1 head SHA: `f64419dd3e4a9d64dbd4281f206f1a8b2c5637db`
- T1 main SHA at review: `45218c694af01602e39966d4668630323b4f8333`
- Frozen target: `T1_T2_ORDERBOOK_V1`, design evidence commit `522314bdd7aade63a86ec692ad22003e58fc9ff2`
- T2-side isolated contract tests: 32/32 PASS at T2 source SHA `09fc9b3125af2eb4dbb434e3c18faa05dd8c62ed`. This proves only the T2-side validator behavior.

### Exact T1 source blobs

| File | Blob SHA |
|---|---|
| `src/collectors/orderbook_manager.rs` | `7e6b0d04cd4098b7b4bab12eaa6f3b3ab92b70ca` |
| `src/models.rs` | `ca2e23cdede536b0dd004f36257e7974d5a8245f` |
| `src/websocket/connection_manager.rs` | `b048964fa38756e3bf5e755bd3c35fa2d7c57f15` |
| `src/utils/decimal.rs` | `22167a711524a14a9315a9ae2a1e384a688f6c7b` |
| `src/utils/csv_writer.rs` | `48ff1ae43d36a3c0877f063e552f2b52880257e3` |
| `dashboard/backend/server.py` | `1bfc322d9868f5eda7a2d9152575fb22b547093d` |
| `dashboard/backend/tests/test_orderbook.py` | `6dc9fef489c0f4f0d6cd75cf80a25ef36e3daf6d` |
| `docs/ORDERBOOK.md` | `d3e8f446258675cc5fb92751db220c9ae19a7b69` |
| `docs/SCHEMA.md` | `895f87a8281a3f9b6d37d96b5f68568e4285bee6` |

## 2. Required findings

### T1-OB-01 — CRITICAL: live reconnect path accepts sequence gaps without invalidating the book

Evidence:
- `src/collectors/orderbook_manager.rs:1143-1191`; especially 1174-1189.
- `docs/ORDERBOOK.md`, section 3 explicitly says reconnect does not trigger resync and live loop does not check `pu`.
- Regression-style test `reconnect_pu_break_leaves_untouched_levels_stale_in_live_book` at orderbook_manager.rs:1448-1468 explicitly asserts the quiet level remains stale after a reconnect gap.

Observed behavior: the live loop drains diffs and calls `apply_diff` without checking `update.prev_update_id == book.last_update_id`. It applies absolute quantities only to touched price levels. A price level changed during the outage but not present in the reconnect diff remains stale. The implementation and its own test/documentation acknowledge this state.

V1 requirement: invalidate the old generation on reconnect/gap; do not publish or consume the book until a fresh REST anchor and contiguous diff chain have been verified.

Disposition: **BLOCKER**. Remove the live gap-acceptance path from any trusted T2 source; reconnect must make the book BROKEN/unavailable and enter bounded re-anchor.

### T1-OB-02 — CRITICAL: non-contract bridge rule can accept a missing update range

Evidence:
- `src/collectors/orderbook_manager.rs:42-58` (`BridgeRule::PuAttach` and `find_bridge`).
- `src/collectors/orderbook_manager.rs:631-655`.
- `docs/ORDERBOOK.md`, section 1, Rule 2.
- Unit test `bridge_rule2_pu_attach` at orderbook_manager.rs:1332-1338.

Observed behavior: besides the valid first-event bridge `U <= snapshotLastUpdateId + 1 <= u`, `find_bridge` accepts `pu <= snapshotLastUpdateId < U`. This second rule can accept a first diff whose U starts after snapshotLastUpdateId+1, leaving update IDs between the snapshot and U unaccounted for. The V1 contract intentionally specifies only the first-event bridge condition and then requires every subsequent `pu == previous u`.

Disposition: **BLOCKER**. Delete the alternate `PuAttach` acceptance rule and its positive test. Add negative tests where the snapshot lies below `U-1`; the attach must fail closed and re-anchor.

### T1-OB-03 — CRITICAL: no generation fencing or immutable snapshot identity

Evidence:
- `OrderbookState` at orderbook_manager.rs:25-31 has only Initializing/FetchingSnapshot/Syncing/Live.
- `Orderbook` at orderbook_manager.rs:75-85 has symbol, last_update_id, maps and an in-memory Instant; no generation, snapshotId, contractVersion, decision watermark or continuity status.
- `DepthSnapshotCsv` at models.rs:51-64 has only row-level fields and last_update_id.
- `connect_and_run` at connection_manager.rs:337-445 creates/reconnects socket state but no order-book generation identity is propagated into snapshots.

Observed behavior: no monotonically increasing generation exists to fence old data or distinguish snapshots before/after reconnect. A consumer cannot prove that the book and the sequence watermark belong to the same connection/re-anchor epoch.

Disposition: **BLOCKER**. Add explicit per-symbol generation and immutable snapshot identity; stale generation reads must be rejected by T2. Generation changes on every reconnect/re-anchor trigger, before any replacement snapshot can become available.

### T1-OB-04 — CRITICAL: snapshot rows are not atomically published as a complete object

Evidence:
- `write_current_orderbook_snapshot` at orderbook_manager.rs:940-1006 copies the current maps and writes one CSV row per level.
- `CsvWriter::write_depth_snapshot` at csv_writer.rs:497-541 iterates rows and calls `write_row` individually; no snapshot transaction, temporary object, atomic rename, commit marker or manifest is present in this path.
- The snapshot schema at models.rs:51-64 has no `complete`, row count, snapshotId or manifest checksum.

Observed behavior: a reader can encounter a partially appended snapshot and has no protocol-level way to distinguish incomplete from complete. A common timestamp and last_update_id on each row are not an atomic publication guarantee.

Disposition: **BLOCKER**. Publish an immutable complete snapshot object plus manifest/commit marker only after all levels and metadata are durable; expose it to T2 atomically. T2 must reject absent/incomplete manifests.

### T1-OB-05 — HIGH: freshness cannot be proven against the V1 decision-time limits

Evidence:
- `DepthSnapshotRest` at models.rs:42-49 has lastUpdateId/bids/asks only.
- `Orderbook.last_processed_time` at orderbook_manager.rs:75-85 is process-local `Instant`, not a serializable source timestamp.
- `write_current_orderbook_snapshot` and `write_snapshot_csv` assign `chrono::Utc::now().timestamp_millis()` at serialization time (orderbook_manager.rs:962 and 1017); this is an observation/write timestamp, not the exchange event/source timestamp.
- No source timestamp, observedAtMs pair, age calculation or future-skew gate is present in the snapshot contract.

Observed behavior: T2 cannot verify both source age and observation age <= 2,000 ms, or future skew <= 250 ms, at decision time from the current snapshot rows.

Disposition: **BLOCKER for T2 acceptance**. Record source and observed timestamps separately, preserve their provenance, and enforce the V1 age/skew thresholds at the consumer boundary. Do not relabel write time as source time.

### T1-OB-06 — HIGH: decimal lexemes are preserved, but order-book domain constraints are not enforced

Evidence:
- `src/utils/decimal.rs`: `normalize_plain_decimal` preserves exact string values but accepts optional '+'/'-' and does not enforce positive prices or non-negative quantities.
- `apply_update_to_book` at orderbook_manager.rs:789-819 normalizes and inserts values without checking price > 0, quantity >= 0 (except treating zero as deletion), or finite/domain invariants.
- Snapshot seed ingestion at orderbook_manager.rs:568-599 follows the same normalization path.
- No best-bid < best-ask validation is performed before the live state is marked trusted.

Observed behavior: exact decimal representation is a useful foundation, but malformed domain values can enter the in-memory book. Map insertion also collapses equivalent normalized price keys instead of explicitly rejecting duplicate/conflicting levels.

Disposition: **REQUIRED**. Keep exact strings; add strict positive-price / non-negative-quantity checks, duplicate/conflict detection, and best bid < best ask validation before publication. Zero quantity remains a deletion instruction, not a stored level.

### T1-OB-07 — HIGH: depth completeness is not enforced

Evidence:
- REST snapshot is converted into maps at orderbook_manager.rs:568-599 and the configured depth is later used for trimming.
- No acceptance check requires at least 20 valid bid and 20 valid ask levels before a book becomes Live or a snapshot is written.
- `DepthSnapshotCsv` has no actual per-side depth or completeness field.

Observed behavior: configured `depth_limit` is a memory cap/request parameter, not proof that the published snapshot contains the required minimum depth.

Disposition: **REQUIRED**. Count validated levels per side and reject incomplete books below the V1 minimum 20/20. Publish actual depth and complete=true only after successful validation.

## 3. Secondary findings

### T1-OB-08 — duplicate sequence records are silently resolved by event timestamp

Evidence: `normalize_messages_for_attach` at orderbook_manager.rs:717-743 sorts by IDs and deduplicates equal `u`, keeping the record with the later event time.

Risk: conflicting payloads with the same final update ID are silently collapsed rather than rejected. This weakens forensic provenance and can hide malformed input.

Recommendation: detect exact duplicates separately from conflicting duplicates. Permit only an explicitly defined idempotent duplicate policy; fail closed on different payloads for the same sequence identity.

### T1-OB-09 — current dashboard API is unsuitable as the Core/T2 source

Evidence:
- `dashboard/backend/server.py:1537-1565` returns float-derived price/qty/cumulative values.
- Endpoint omits contractVersion, source/observation timestamps, U/u/pu watermark, continuity, generation, snapshotId, completeness and freshness.
- `dashboard/backend/tests/test_orderbook.py` tests dashboard reconstruction/reporting, not the V1 source publication contract.

Disposition: **DO NOT USE** `GET /api/orderbook/{symbol}` for Core decisions. Dashboard/replay is a presentation surface only.

## 4. Positive findings

- Raw WebSocket model fields retain Binance `U/u/pu` as integer sequence values and bid/ask values as strings (`models.rs:4-25`).
- REST snapshot bid/ask values are decoded as strings (`models.rs:42-49`).
- Exact decimal normalization/comparison avoids binary floating-point conversion for the computational price keys.
- Initial bridge code has a strict subsequent `pu == last_u` check inside `apply_attach_updates_to_book` (orderbook_manager.rs:762-786), but the invalid alternate first-bridge rule and the live reconnect path still violate V1.

## 5. Five-axis review

| Axis | Verdict | Reason |
|---|---|---|
| Correctness | **BLOCKED** | Reconnect gaps can leave stale levels; alternate bridge can accept a hole; no source freshness/complete-snapshot proof. |
| Readability | **PASS WITH NOTES** | Lifecycle is documented, but docs intentionally describe behavior that conflicts with V1. |
| Architecture | **BLOCKED** | In-memory operational book, raw audit tape, periodic snapshots and dashboard reconstruction are not separated by a V1 publication boundary. |
| Security / data integrity | **BLOCKED** | No generation fencing, complete manifest, strict domain validation or trusted snapshot identity. |
| Performance | **NOT VERIFIED FOR V1** | Existing rate-limit rationale explains avoiding resnapshot storms, but no bounded batch re-anchor coordinator exists to preserve correctness without a burst. |

## 6. Minimal implementation sequence — plan only, not authorized execution

1. Introduce a per-symbol state machine with explicit BROKEN/REANCHORING/READY states and monotonically increasing generation fencing.
2. On reconnect, sequence gap, malformed diff or failed snapshot validation: invalidate current generation immediately; never keep it available as trusted.
3. Remove `PuAttach`; enforce first-event bridge `U <= snapshotLastUpdateId+1 <= u`; require subsequent `pu == previous u`.
4. Re-anchor using fresh REST snapshot + buffered diff chain. Coordinate requests with a bounded queue/rate budget so correctness does not create a REST storm; if capacity is unavailable, remain BROKEN.
5. Validate Decimal domain, duplicate/conflicting levels, crossed/locked book, 20/20 depth, source/observed freshness and timestamp skew.
6. Build immutable snapshot plus manifest containing V1 fields; publish atomically only after full verification. Include contractVersion, symbol/market, generation, snapshotId, anchor, first/last applied IDs, decision watermark, sourceTimestampMs, observedAtMs, per-side depth, continuity=VERIFIED and complete=true.
7. Add source-side tests for every V1 rejection path and fault-injection tests for partial write/crash/reconnect races. Then run T1 CI at an exact SHA and publish artifact/evidence.
8. Only after T1 source CI passes, build a read-only T2 adapter that independently validates the manifest and rejects stale generation/snapshot IDs.

No T1 code change, runtime activation, VPS access, T0 change, Core runner implementation, AI execution or live trading is authorized by this review.

## 7. Disposition

- T1 source compatibility with V1: **BLOCKED**.
- Exact Decimal preservation: **PARTIAL PASS** (representation preserved; domain validation missing).
- Sequence continuity: **PARTIAL PASS** (initial attach after selected bridge checks pu; alternate bridge and live reconnect violate V1).
- Reconnect/re-anchor/generation fencing: **FAIL / NOT IMPLEMENTED** for V1.
- Freshness/depth/atomic publication: **FAIL / NOT IMPLEMENTED** for V1.
- Dashboard API as decision source: **PROHIBITED**.
- T1 runtime trust: **NOT VERIFIED**.
- T2 actual T1 integration: **BLOCKED**.
