# C2.2 Implementation Scope — T1 Loopback HTTP Snapshot + T2 One-shot Reader

Date: 2026-11-13
Decision: **OWNER APPROVED** dedicated read-only loopback HTTP transport.
Status: **SCOPE FROZEN FOR IMPLEMENTATION PLANNING; CODE NOT YET CHANGED**
Related design: `docs/evidence/C2_2_T1_T2_TRANSPORT_OPTIONS_2026-11-13.md`

## 1. Authorization boundary

Approved:
- A dedicated read-only HTTP resource in the T1 collector process, bound to loopback only.
- T1 serves the current immutable `OrderbookSnapshotV1` from its live `SnapshotPublisher`.
- T2 obtains one complete response per decision cycle and validates the existing frozen V1 contract.

Not approved:
- Public network exposure, browser/React access, Nginx public routing, or reuse of the Dashboard CSV reconstruction endpoint.
- T0 changes, shared T0 SQLite, shared database, VPS/runtime activation, systemd/autostart, deployment, or production operation.
- Core strategy changes, ledger writes, Shared Risk Engine admission changes, AI execution, or real orders.
- Any relaxation of freshness, future-skew, depth, sequence, or strict-schema validation.

## 2. Repositories and existing branches

- T1: `kenznguyen/binance-futures-collector`, existing branch `feature/t1-connection-sidecar-integration-20261107`.
- T2: `kenznguyen/btcusdt-telegram-signals2`, existing branch `feature/core-operational-proof-20261112`.
- Do not create replacement branches or PRs without separate approval.
- Before implementation, re-check branch heads and working-tree-equivalent remote state. T2 branch was observed as heavily diverged from main (3,664 ahead / 82 behind) at approval time. Do not merge, rebase, force-push, or synchronize automatically. If the target branch cannot safely accept a fast-forward commit, stop and report BLOCKED rather than rewriting history.

## 3. T1 endpoint scope

Implement a dedicated internal route in the T1 process that owns `SnapshotPublisher`.

Conceptual route: `GET /internal/v1/orderbook/{symbol}`.

Requirements:
1. Bind only to `127.0.0.1`; no `0.0.0.0`, public listener, or Dashboard proxy.
2. Read exactly one immutable snapshot using the publisher's freshness-aware read path.
3. Serialize one complete object; never combine bids/asks or metadata from separate reads.
4. Return HTTP 200 only for a current, complete, verified, fresh snapshot.
5. Return a structured non-2xx response when unavailable, stale, broken, disconnected, or stopped; never serve a cached last-good snapshot.
6. Preserve V1 contract version `T1_T2_ORDERBOOK_V1`, decimal price/quantity strings, IDs, timestamps, generation and depth shape without numeric conversion or renaming.
7. Set `Cache-Control: no-store`; bound request/response sizes and handler work.
8. Keep route read-only; no control endpoint, mutation, subscription or persistence.
9. Local authentication decision must be explicit: if loopback binding alone is not accepted by the implementation security model, use a service-only header secret supplied outside source control and never log it. No credential in URL.

Exact server framework integration, error JSON shape, maximum response bytes and timeout values are implementation details to settle from repository conventions and measured bounded behavior; do not invent a new V1 snapshot schema.

## 4. T2 one-shot reader scope

Implement a small read-only adapter for the endpoint.

Requirements:
1. One bounded GET per decision cycle; no same-cycle retry.
2. Reject timeout, connection refusal, any non-2xx, malformed JSON, oversized body, unknown/missing/invalid contract fields, wrong symbol, stale/future timestamps and all existing validator failures.
3. Pass the full parsed snapshot through the existing strict `validate_snapshot(..., decision_at_ms=...)` contract before exposing it to the caller.
4. Return a typed unavailable/invalid result or existing repository-standard error; do not return an old snapshot.
5. No fallback to CSV, Dashboard API, T0 database, synthetic book, exchange REST, or in-memory last-good value.
6. No direct call to Core producer, PaperLedger, Shared Risk Engine admission, or execution code in this adapter.
7. Keep `AI_EXECUTION_ENABLED=false`; no execution pathways added.

## 5. TDD plan and required evidence

### T1 RED tests first
- READY snapshot is returned as exact V1 JSON with decimal strings preserved.
- Concurrent publisher update during serialization yields one complete old or new snapshot, never mixed state.
- stale, BROKEN, invalidated, stopped and missing snapshot states return non-2xx.
- route is loopback-only by configuration/testable listener construction; no public bind.
- no-store header and bounded body behavior are verified.
- no stale response is served after reconnect/generation change.

### T1 GREEN
- Minimal route/handler attached to the live publisher.
- Run focused endpoint tests, then all repository CI-required Rust tests, format, Clippy, build and architecture checks.

### T2 RED tests first
- Valid response passes strict V1 validation and preserves source fields.
- timeout, refusal, non-2xx, malformed JSON, oversize, wrong version/symbol, unknown fields and timestamp violations fail closed.
- Exactly one request per decision invocation.
- Failure result cannot be mistaken for a valid book and does not invoke Core/Risk/Ledger/Execution.

### T2 GREEN
- Minimal HTTP client adapter using repository-standard HTTP client and configured bounded timeout.
- Run focused adapter/contract tests, existing T0 HTTP consumer regressions, paper-only preflight and all repository CI-required checks.

### Integration evidence (still non-runtime)
- In-process test server + T2 client round-trip with real serialized T1 snapshot.
- Fault injection for disconnect, stale state, malformed/oversize response and concurrent publication.
- No Binance connection or VPS is required for this phase.

## 6. Sequencing and gates

1. Revalidate both branch heads and inspect existing T1 server/bootstrap conventions.
2. T1 RED → T1 GREEN → focused/full CI; record exact tested source SHA and workflow/artifacts.
3. T2 RED → T2 GREEN → focused/full CI; record exact tested source SHA and workflow/artifacts.
4. Add a deterministic cross-repository integration fixture/test if repository structure permits without creating a runtime dependency.
5. Update each repository's evidence and T2 `docs/PROJECT_SESSION_HANDOFF.md`; commit on existing branches only when fast-forward-safe.
6. Report PASS/BLOCKED/NOT VERIFIED and preserve exact SHA, workflow run IDs, artifact IDs/hashes, test counts and expiry.

No end-to-end live T1→T2 soak, runtime activation, VPS changes, or Core Runner implementation is included in this authorization.

## 7. Exit criteria

C2.2 implementation can be marked PASS only when:
- T1 endpoint tests and T2 adapter tests pass on exact source SHAs;
- all required CI jobs succeed;
- cross-boundary integration tests prove complete immutable snapshot delivery and fail-closed behavior;
- evidence and handoff records contain source SHAs, workflow runs, artifact metadata and remaining limits.

Until then: transport implementation status is NOT VERIFIED; runtime delivery is NOT VERIFIED.
