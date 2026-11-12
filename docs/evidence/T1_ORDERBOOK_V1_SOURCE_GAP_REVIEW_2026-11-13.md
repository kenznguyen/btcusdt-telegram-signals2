# T1 Order Book V1 — Source Gap Review

Date: 2026-11-13
Status: **BLOCKED — T1 source is not compatible with the frozen V1 acceptance contract**
Review-only. No T1 repository file, PR, collector runtime, T0, VPS or exchange endpoint was modified or accessed.

## 1. Reviewed source identity

- T1 repository: `kenznguyen/binance-futures-collector`
- PR: [#1](https://github.com/kenznguyen/binance-futures-collector/pull/1), OPEN / DRAFT
- PR head reviewed: `f64419dd3e4a9d64dbd4281f206f1a8b2c5637db`
- T1 main at review: `45218c694af01602e39966d4668630323b4f8333`
- Compare main...PR: `ahead_by=230`, `behind_by=1`, merge base `bc4f0ef633fbeee4a49defd72827f17162693805`; branch is diverged and requires reconciliation before any merge assessment.
- Exact reviewed blobs:
  - `src/collectors/orderbook_manager.rs`: `7e6b0d04cd4098b7b4bab12eaa6f3b3ab92b70ca`
  - `src/models.rs`: `ca2e23cdede536b0dd004f36257e7974d5a8245f`
  - `src/utils/decimal.rs`: `22167a711524a14a9315a9ae2a1e384a688f6c7b`
  - `src/utils/csv_writer.rs`: `48ff1ae43d36a3c0877f063e552f2b52880257e3`
  - `src/websocket/connection_manager.rs`: `b048964fa38756e3bf5e755bd3c35fa2d7c57f15`
  - `src/websocket/message_handler.rs`: `378975ada26366796fbf4af7bc3cdc3295929c79`
  - `dashboard/backend/server.py`: `1bfc322d9868f5eda7a2d9152575fb22b547093d`

## 2. Findings against T1_T2_ORDERBOOK_V1

### F1 — Critical: reconnect does not invalidate the live book or force re-anchor

- `src/collectors/orderbook_manager.rs:1143-1190` deliberately applies live updates without checking `pu == last_update_id` and without resnapshotting.
- `src/websocket/connection_manager.rs:621` emits only `Disconnected(batch_id)`; `src/websocket/message_handler.rs:188` only logs that event. It does not invalidate per-symbol order-book state or notify the OrderbookManager to fence the current book.
- Existing test `reconnect_pu_break_leaves_untouched_levels_stale_in_live_book` at `orderbook_manager.rs:1449-1467` explicitly asserts that a quiet level remains stale after reconnect while the book advances its update ID.
- V1 requires the current snapshot to become BROKEN immediately on reconnect/gap, with no trusted publication until a fresh REST anchor and contiguous diff chain are verified.
- Disposition: **BLOCKER**.

### F2 — Required: attach accepts a second bridge rule that is outside the frozen V1 rule

- `orderbook_manager.rs:54-90` accepts both `U <= snapshot_u + 1` and a separate `pu <= snapshot_u < U` rule (`PuAttach`).
- The test `bridge_rule2_pu_attach` explicitly endorses the second rule (around lines 1340-1355).
- Frozen V1 requires the first accepted event to satisfy the single bridge predicate `U <= snapshotLastUpdateId + 1 <= u`. The additional `PuAttach` route must not be treated as a valid V1 anchor unless the contract owner changes the contract.
- Disposition: **BLOCKER**; align implementation and tests to the frozen V1 predicate.

### F3 — Required: generation fencing and snapshot identity are absent

- `OrderbookState` is only `Initializing / FetchingSnapshot / Syncing / Live` (`orderbook_manager.rs:47-52`).
- `Orderbook` contains symbol, update ID, level maps and an `Instant`, but no generation, snapshotId, immutable watermark identity or contract version (`orderbook_manager.rs:95-104`).
- Connection reconnect events carry a batch ID, not a per-symbol generation token.
- V1 requires monotonically increasing generation and identity fencing so updates from an old connection/session cannot mutate or republish a newer snapshot.
- Disposition: **BLOCKER**.

### F4 — Required: source freshness and observation freshness cannot be proven

- `Orderbook` has only `last_processed_time: Instant` (`orderbook_manager.rs:103`); it is updated when a diff is applied (`orderbook_manager.rs:818`).
- Snapshot CSV timestamps are assigned using local `Utc::now()` (`orderbook_manager.rs:963-964, 1022-1023`), not the exchange snapshot source timestamp.
- There is no sourceTimestampMs + observedAtMs pair or decision-time age rejection at the book publication boundary.
- V1 requires both source and observation age <= 2,000 ms and future skew <= 250 ms.
- Disposition: **BLOCKER**.

### F5 — Required: Decimal lexemes are improved, but semantic price/quantity validation is incomplete

- Positive progress: PR head adds exact decimal strings and normalized keys in `orderbook_manager.rs:95-102, 790-818`; REST and WS wire fields remain strings in `models.rs:1-42`; CSV persistence validates lexical decimal syntax.
- However, `normalize_plain_decimal` accepts a leading negative sign (`decimal.rs:6-37`), and `validate_decimal_string` accepts optional positive/negative signs (`csv_writer.rs:20-68`). `apply_update_to_book` normalizes values but does not enforce price > 0 and quantity >= 0 (`orderbook_manager.rs:790-816`).
- A negative price or negative nonzero quantity can therefore enter the in-memory order book; zero quantity is the valid delete operation.
- V1 requires strictly positive finite price and non-negative finite quantity before mutation/publication.
- Disposition: **BLOCKER** for the V1 trust boundary. Preserve the exact-string work; add semantic checks rather than reverting to floats.

### F6 — Required: per-level CSV writes are not an atomic snapshot publication

- `csv_writer.rs:497-534` builds rows and then calls `write_row` separately for each level. The underlying writer appends rows to a buffered file; there is no atomic snapshot envelope, complete marker, generation or publication manifest tied to the book.
- `orderbook_manager.rs:940-1002` exports current in-memory levels as a set of rows. A concurrent reader can observe an incomplete set while rows are being appended; same `last_update_id` alone does not prove the complete set has been published.
- V1 requires an immutable/atomic snapshot that is visible only after full validation and complete publication.
- Disposition: **BLOCKER**. Do not treat current CSV snapshots or dashboard reconstruction as a V1 atomic read interface.

### F7 — Required: minimum depth and book-shape acceptance are not enforced before LIVE

- Initial snapshot fetch uses configured `depth_limit` (`orderbook_manager.rs:553-566`), and later trimming caps levels (`orderbook_manager.rs:830-850`); neither proves at least 20 valid bid and ask levels before transition to LIVE.
- No source-side gate is visible for positive price, non-negative quantity, duplicate/conflicting levels, best bid < best ask, source/observation freshness and completeness as one acceptance operation.
- V1 requires at least 20 levels each side plus all shape/freshness checks before publication.
- Disposition: **BLOCKER**.

## 3. Five-axis review

- Correctness: **BLOCKED** by F1/F2/F4/F5/F6/F7.
- Readability: order-book state and CSV responsibilities are understandable, but the trust state does not model BROKEN/REANCHORING/READY.
- Architecture: connection lifecycle events are not coupled to per-symbol book invalidation; persistence format is being used as a potential read interface without a snapshot commit protocol.
- Security/data integrity: exact string preservation is a positive change, but semantic validation and generation fencing remain missing.
- Performance: reconnect-wide re-anchor could cause REST request-weight bursts. V1 implementation should use bounded concurrency/rate limiting and fail closed; this operational concern must not be solved by accepting a known-stale live book.

## 4. Contract matrix

| V1 requirement | T1 PR head |
|---|---|
| Exact decimal strings | PARTIAL PASS — exact in-memory/raw strings, but semantic sign/range checks missing |
| Strict REST bridge predicate | FAIL — extra PuAttach rule |
| Subsequent pu continuity | PARTIAL — attach path checks later updates; live path skips it |
| Reconnect invalidation/re-anchor | FAIL |
| Generation fencing | FAIL |
| Source + observation freshness | FAIL |
| Min 20 levels per side | NOT ENFORCED |
| Crossed/locked book rejection | NOT ENFORCED at publication gate |
| Immutable/atomic snapshot | FAIL |
| Complete snapshot identity/watermark | FAIL |
| Fail closed when any validation fails | FAIL for reconnect/live path |

## 5. Review conclusion and safe next step

- T1 PR #1 is **NOT READY** to act as the trusted V1 Order Book source.
- The exact-decimal changes in the PR are useful and should be retained, but they do not close the reconnect, continuity, generation, freshness, depth or atomic-publication blockers.
- The PR branch is 230 commits ahead and 1 behind main. Do not merge or extend this diverged branch without first reconciling the exact intended source history and reviewing the resulting diff.
- Next safe engineering increment: produce a small T1-owned implementation specification and test plan for (a) per-symbol BROKEN/re-anchor lifecycle, (b) exact bridge + contiguous pu sequence, (c) generation-fenced immutable snapshot publication, and (d) semantic decimal/freshness/depth acceptance. Prefer a dedicated BTCUSDT V1 path or isolated adapter; do not alter unrelated all-symbol collection behavior until the owner approves the scope.
- This review did not modify T1, merge PR #1, run T1 CI, activate collector, access T0/VPS, use exchange credentials or send orders. No T1 runtime claim is made.
