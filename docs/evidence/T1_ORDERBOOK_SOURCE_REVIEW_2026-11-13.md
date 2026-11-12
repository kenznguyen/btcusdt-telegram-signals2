# T1 Order Book Source Review — 2026-11-13

- Scope: read-only repository inspection of T1 Order Book storage, reconstruction, dashboard endpoint, and current integration status.
- No T1 code, T0, VPS, runtime, service, database, provider, exchange or trading action was performed.
- Hummingbot remains paused and is removed from the proposed Core decision-cycle source path.
- Proposed target: T1 BTCUSDT Order Book, subject to a source-contract gate. T1 is preferred in principle, **not yet accepted as a trusted live decision input**.

## Repository and exact source evidence

T1 repository: `kenznguyen/binance-futures-collector`.

- T1 `main` HEAD inspected: `45218c694af01602e39966d4668630323b4f8333`.
- `docs/SCHEMA.md` blob: `895f87a8281a3f9b6d37d96b5f68568e4285bee6`.
- `docs/ORDERBOOK.md` blob: `d3e8f446258675cc5fb92751db220c9ae19a7b69`.
- `src/models.rs` blob: `993419725268d1308645e3a37c15e9779a9e92cc`.
- `src/collectors/orderbook_manager.rs` blob: `d18d047c1f7cdddd03cea60b02de54b656ad4edf`.
- `dashboard/backend/server.py` blob: `1bfc322d9868f5eda7a2d9152575fb22b547093d`.
- `dashboard/backend/tests/test_orderbook.py` blob: `6dc9fef489c0f4f0d6cd75cf80a25ef36e3daf6d`.

T1 PR #1 is still **OPEN / DRAFT**, head `f64419dd3e4a9d64dbd4281f206f1a8b2c5637db`; one review finding remains marked required before merge in the connection-sidecar manifest-publication error path. This PR state is recorded as a separate integration blocker, not as proof that the Order Book itself is ready.

## What T1 currently provides

1. `DepthUpdateWs` receives Binance `b`/`a` levels as `Vec<[String; 2]>`; `DepthUpdateCsv::to_csv()` serializes these string pairs into `bids_json` and `asks_json`. Raw `depth_updates` therefore retain decimal text and the `U/u/pu` update identifiers.
2. Initial REST snapshot data also arrives as string pairs. `write_snapshot_csv()` serializes those initial snapshot values through `format_decimal_str`.
3. Periodic `depth_snapshot` rows are different: they are re-serialized from the in-memory `Orderbook`, whose price keys and quantities are stored as `f64`, then formatted back to decimal text. These periodic snapshots are not a guaranteed exact-decimal source.
4. T1's documented raw storage is append-only CSV under `data/futures/orderbooks/btcusdt/<UTC-date>/`; depth-diff files rotate hourly. Snapshot rows are one row per price level.
5. T1's order-book cadence is configured separately from its periodic snapshot interval. A snapshot row timestamp is when it was written; it is not itself proof that the book was reconstructed from a fully contiguous stream.

## Blocking findings for direct T2 consumption

### T1-OB-01 — dashboard endpoint is not a trusted T2 contract

The existing `GET /api/orderbook/{symbol}?levels=20` endpoint is a dashboard endpoint, not a frozen machine-to-machine source contract:

- It returns price/quantity as JSON numbers after conversion through Python `float`; cumulative quantities are also float-derived.
- It does not return the source timestamp, exchange update ID, snapshot anchor ID, dataset/version identity, continuity status, or a freshness attestation.
- The backing `_current_book()` selects the latest snapshot by update ID, reads only the last two update files, and applies diffs without validating the `pu == previous u` chain.
- The dashboard is documented as optional and unauthenticated; it binds to loopback by default. Its API must not be treated as an externally stable/authenticated T2 service.

Disposition: **BLOCKED**. Do not connect T2 to this endpoint.

### T1-OB-02 — periodic snapshots are float-derived

The live in-memory order book stores `f64` price/quantity values. Periodic snapshots are written from those float values. This breaks the frozen Bundle v1 requirement that the T2 Order Book payload contain exact decimal strings with no JSON floats.

Disposition: **BLOCKED**. Do not use periodic snapshots as the authoritative exact-decimal seed.

### T1-OB-03 — reconnect gaps are detectable but not automatically re-anchored

T1's current live loop deliberately does not enforce `pu == last_update_id` or trigger a fresh REST snapshot on every WebSocket reconnect. The documented strategy avoids a snapshot storm across hundreds of symbols; raw `depth_updates` retains the gap for offline detection, while the in-memory book is described as self-healing for levels that update again.

Consequences for T2:
- A detected continuity break means the reconstructed book cannot be assumed complete.
- A later periodic snapshot is re-serialized from the in-memory float book; it does not prove that every quiet/deep level was corrected after the gap.
- The current dashboard endpoint does not expose the continuity result alongside the returned book.

Disposition: **BLOCKED** until T1 exposes a verified re-anchor or T2 can prove a contiguous chain from a trusted exact-decimal seed to the chosen decision watermark. Any gap, missing file, partial row, stale source or ambiguous anchor must fail closed.

### T1-OB-04 — no stable read-only T2 interface is frozen

The repository contains raw CSV capture and dashboard-specific read/reconstruction functions, but no approved, versioned, read-only T2 interface that atomically returns:
- BTCUSDT, Binance USD-M perpetual identity;
- exact decimal-string bids/asks and bounded depth;
- source timestamp and local receive/observation timestamp semantics;
- snapshot/update anchor and last applied update ID;
- continuity/gap status over the exact consumed range;
- source generation/file watermark or equivalent consistency token;
- explicit freshness and completeness verdict.

Disposition: **NOT IMPLEMENTED / BLOCKED**.

## Required target contract before implementation

Preferred direction is a T1-owned, read-only Order Book snapshot contract for BTCUSDT. The implementation mechanism remains undecided; do not assume the dashboard API is that contract.

The contract must guarantee:
1. Exact decimal strings end-to-end; no float conversion in the T2 path.
2. A trusted exact-decimal anchor plus every required diff through a single declared watermark.
3. Verified update continuity (`U/u/pu`) across the consumed range.
4. Explicit reconnect/resync generation and gap state; no silent reuse of a partially self-healed book.
5. Source and observation timestamps, freshness bound, depth bound and symbol/market identity.
6. Atomic/consistent read semantics while CSV files are appended/rotated, or an equivalent immutable snapshot response.
7. Fail-closed behavior for missing/stale/partial/corrupt files, gaps, crossed book, invalid decimals, insufficient depth or unavailable T1.

A targeted BTCUSDT resync/re-anchor policy may be evaluated separately because the current collector intentionally avoids mass resnapshotting after reconnect. No T1 behavior change is authorized by this review.

## Revised Core one-shot design disposition

- C1 (T0 datasetVersion preservation): unchanged, BLOCKER.
- C2 (Order Book): Hummingbot float-normalization finding is retired from the selected path. Replaced by T1 findings T1-OB-01 through T1-OB-04; C2 remains **BLOCKER**.
- Core should target T1 as the preferred Order Book source, but must not consume the current dashboard endpoint or trust periodic float-derived snapshots.
- Hummingbot remains **PAUSED / OUT OF SCOPE**.
- T1 remains **NOT ACTIVATED**; no collector runtime, VPS, service or data access was performed.
- Core runner remains **NOT IMPLEMENTED**. No code implementation authorization is inferred from this source review.
- Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.

## Next bounded step

Freeze the T1 → T2 read-only Order Book contract and decide the smallest source-side requirement needed for exact Decimal reconstruction and post-reconnect trust. This is a design/evidence step only. Any T1 source code change, T1 activation, VPS access, or Core runner implementation requires its own explicit bounded authorization.
