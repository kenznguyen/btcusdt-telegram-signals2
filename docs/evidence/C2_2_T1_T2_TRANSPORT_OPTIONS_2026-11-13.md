# C2.2 — T1 → T2 Order Book Transport Options

Date: 2026-11-13
Status: **DESIGN REVIEW COMPLETE — RECOMMENDATION ONLY; TRANSPORT NOT FROZEN**
Scope: read-only repository/source inspection and transport architecture comparison. No source, runtime, VPS, T0, or trading changes.

## 1. Exact source baseline inspected

- T2 repository: `kenznguyen/btcusdt-telegram-signals2`
- T2 branch: `feature/core-operational-proof-20261112`
- T2 branch HEAD at review: `6032f77e681ce8e4b4147a5ab0e12da3ea00453e`
- T2 frozen validator: `core_runtime/orderbook_contract.py`, blob `1620c9f21b1f3df3c2fb65833f2afd80374bf6a5`
- T2 validator tests: `core_runtime/test_orderbook_contract.py`, blob `935a3f2c8467e4f56cc683a7c0afcaba8fbeee00`
- T1 repository: `kenznguyen/binance-futures-collector`
- T1 branch: `feature/t1-connection-sidecar-integration-20261107`
- T1 branch HEAD at review: `6c688878fe8bf40fb8581a1d23693490fe9df8ef`
- T1 publisher: `src/orderbook_v1.rs`, blob `a1711d2949fb6c9e807b385a4c9c9b811781141c`
- T1 PR #1 remains OPEN / DRAFT / NOT MERGED.

The T1 publisher currently exposes immutable in-process snapshots through `SnapshotPublisher::read_fresh()`. It does not provide an inter-process transport. T2's `SnapshotSlot` is also an in-process atomic pointer-swap model, not a transport implementation.

## 2. Important existing API distinction

T1's existing Dashboard FastAPI backend reads `stats.json` and captured CSV files. Its existing `/api/orderbook/{symbol}` path reconstructs a historical/display book from CSV and uses numeric values. It is not connected to the live `SnapshotPublisher` and must not be reused as the trusted V1 T1→T2 feed.

Any V1 feed must carry the exact immutable object produced by the live publisher, preserve price/quantity strings without float conversion, and expose no dashboard-derived fallback.

## 3. Transport comparison

| Option | Advantages | Risks / costs | Assessment |
|---|---|---|---|
| Dedicated read-only HTTP endpoint in the T1 collector process, bound to loopback | Natural process boundary; one complete JSON response; T1 can serialize one immutable `Arc<OrderbookSnapshotV1>`; T2 validates with the existing strict parser; easy deterministic API tests; no shared database or file lifecycle | Requires a small HTTP listener/route, bounded timeout, service authentication and explicit no-cache behavior; an extra request can fail or time out | **Preferred for design**, provided it reads directly from the live publisher and does not proxy the Dashboard CSV API |
| Atomic JSON file on a private shared local directory | No network listener; low overhead; same-host handoff; temp-write + fsync + atomic rename can prevent torn reads | Requires writer/reader filesystem ownership, atomic invalidation on reconnect/BROKEN, stale-file handling, directory durability, permissions and same-filesystem guarantees; file may outlive a crashed publisher | Viable fallback only if HTTP is unavailable or dependency cost is unacceptable |
| Shared SQLite table/database | Transactional row replacement and familiar tooling | Couples T1/T2 to database locks/schema/ownership; unnecessary for one latest snapshot; risks confusion with T0 canonical storage and its independent custody boundary | **Reject for V1**; do not use T0 SQLite or add a T0 table |

## 4. Recommended HTTP boundary (not yet frozen)

- Add a dedicated internal read-only resource, conceptually `GET /internal/v1/orderbook/BTCUSDT`, served by the same T1 process that owns `SnapshotPublisher`.
- Bind only to `127.0.0.1` (or a private Unix socket if implementation constraints make that simpler); do not expose it to the public interface or React browser.
- The handler obtains one `Arc` through `read_fresh(now_ms)`, serializes that immutable snapshot once, and returns it as one response. Never read bids and asks separately.
- Return `200` only when a currently fresh, complete, verified snapshot exists. If publisher is unavailable, BROKEN, stale, or stopped, return a structured non-2xx unavailable response. Do not return the previous snapshot as a fallback.
- Use `Cache-Control: no-store`; no pagination, partial-book response, stream cache, or stale-while-revalidate behavior.
- T2 performs one bounded GET per decision cycle, validates the entire body with `validate_snapshot(..., decision_at_ms=...)`, and fails closed on timeout, non-2xx, malformed body, unknown version, or validation failure. No retry within the same decision cycle; a later cycle may make a new read.
- Use a service-only authentication header if the endpoint is reachable beyond a strictly private local socket. Never put credentials in the URL or logs. Exact auth mechanism and timeout budget remain to be selected and tested.
- Keep the transport envelope (availability/error metadata) separate from the frozen `T1_T2_ORDERBOOK_V1` snapshot payload so the strict validator receives exactly the frozen snapshot schema.

This is a service-to-service path. It does not change the separate dashboard rule that browser traffic should use the Nginx gateway rather than calling multiple bot ports directly.

## 5. Required transport acceptance tests before implementation can be called complete

1. READY response contains one complete V1 snapshot; exact decimal strings and all watermark/generation fields survive round-trip unchanged.
2. Concurrent publication during serialization returns either the previous complete immutable snapshot or the next complete immutable snapshot, never mixed fields/sides.
3. Reconnect, sequence gap, publisher invalidation, STOPPED state and stale timestamps produce unavailable/non-2xx; T2 never reuses a prior response.
4. Timeout, connection refusal, malformed JSON, oversized response, wrong symbol/version and unknown fields all fail closed.
5. T2 invokes no Core producer, PaperLedger or Shared Risk Engine admission callback when transport or validation fails.
6. HTTP cache/proxy behavior cannot serve an older response; the endpoint is private and read-only.
7. Test exact one-request-per-decision behavior and bounded response size/time without weakening the existing 2,000 ms age or 250 ms future-skew contract.

## 6. Decision and limits

- Transport recommendation: **dedicated loopback HTTP endpoint in the T1 collector process**.
- Owner transport selection: **PENDING**.
- Contract V1 fields/thresholds: unchanged.
- T1 source changes, endpoint implementation, T2 live reader, runtime activation, deployment, VPS access and CI changes: **NOT AUTHORIZED by this design review**.
- T0 remains independent and untouched. Do not use T0's canonical SQLite database for this handoff.
- Existing Dashboard order-book reconstruction is not a trusted V1 source.
- No live trading, real orders, ledger or Shared Risk Engine changes. `AI_EXECUTION_ENABLED=false`.

## 7. Next step

Owner decision required: approve or reject the dedicated loopback HTTP transport recommendation. If approved, create a separate bounded implementation scope and TDD plan for the T1 endpoint and T2 one-shot read-only adapter. Do not implement either side or activate runtime before that approval.
