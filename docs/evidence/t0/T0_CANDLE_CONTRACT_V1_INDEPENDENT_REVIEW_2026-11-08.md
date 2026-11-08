# T0 Read-only Candle Contract v1 — Independent Code Review

- Date: 2026-11-08 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Review branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Reviewed implementation SHA: `e317b7dc02363db0600737a89442dd918559af3c`
- Reviewed API blob: `81733c9b6de811cbebb2f5d472d41f37f337990c`
- Scope: source and test review only. No code, runtime, DB, Feeder, exchange, or consumer changes.

## Verdict

**CONDITIONAL PASS — API implementation is a sound read-only diagnostic foundation; Contract v1 is not yet certified for T2 consumption.**

No confirmed critical defect was found in the reviewed API path. Local tests are PASS (focused 13/13 and repository-wide 404/404 at the exact reviewed SHA, based on user-provided terminal output). GitHub Actions exact-SHA evidence remains NOT VERIFIED. Consumer conformance and transport/deployment controls remain outstanding.

## Findings

### Required before T2 HTTP client can be accepted

1. **T2 remains architecturally non-conformant.** `freqai_bridge/context.py` imports `market_data.store.read_window` and reads a configured SQLite path; `ChartProFreqaiResearch.py` passes `canonical_db_path`. This bypasses the approved T0 service boundary. The HTTP migration must remove this runtime path rather than add an HTTP option with a silent SQLite fallback. Until then, T2 HTTP conformance is BLOCKED.

2. **Consumer-side fail-closed validation is not implemented or reviewed yet.** The API intentionally returns HTTP 200 with explicit `coverage.complete=false` and gaps for diagnostic use, and `freshness.evaluable` means timestamps can be calculated—not that data is fresh or strategy-eligible. The T2 client must independently validate exact identity/range/version, all candle timestamps and decimal/OHLC constraints, strict ordering/uniqueness, full coverage/no gaps, latest-returned equals latest-expected, and configured per-timeframe freshness limits. Missing/invalid thresholds must reject the window. No fallback to SQLite, cache, synthetic candles, or another venue.

3. **Transport and response-bound policy need explicit client/deployment proof.** The API code does not itself provide TLS; the design requires HTTPS across host boundaries. The HTTP client must use certificate verification, bounded connect/read timeouts, bounded retries, and a documented maximum response-body size. The 2,000-slot and bounded decimal-field constraints limit normal payload growth, but there is no explicit byte-size contract in the current API. Verify TLS termination and network exposure separately before any remote consumer use.

### Review notes / no defect confirmed

- **Freshness calculation:** `latestExpectedOpenTimeMs = floor(generatedAtMs / interval) * interval - interval` correctly derives the latest expected closed candle from the server generation clock, including exact interval boundaries. Observation age and close lag use `generatedAtMs - availableAtMs` and `generatedAtMs - closeTimeMs`; empty windows return null observations and `evaluable=false`. This is a computability indicator, not a freshness pass.
- **Timestamp/data validation:** query timestamps are ASCII nonnegative integers, bounded to signed 64-bit range and aligned; start/end form a nonempty half-open window. Store candle construction validates aligned opens, closed-before-observation, decimal values and OHLC bounds. SQL orders by open time and primary-key uniqueness prevents duplicate candle identity.
- **Coverage/gaps:** Store computes leading, internal and trailing gaps without filling them. API exposes incomplete coverage rather than silently dropping or synthesizing candles. This is correct diagnostic behavior; consumer rejection remains mandatory.
- **Identity/version/provenance:** response includes exchange, market type, symbol, timeframe, volume unit, source, contract/schema versions, query bounds and dataset hash. Candle records carry source, quality, availability kind/time and exclusive close boundary. Dataset hash is a deterministic hash of query identity and selected candle content; it is not an authenticity proof, consistent with the design.
- **Authentication:** protected candle route requires a configured Bearer token and uses constant-time comparison. Missing token fails closed. Token is not accepted in query parameters. `/health` is intentionally unauthenticated liveness only and must not be treated as readiness or data health.
- **Read-only behavior:** route accepts GET only; SQLite reads use `mode=ro`; PostgreSQL reads use a read-only transaction; storage constructors do not initialize/migrate schema. API does not expose write/order routes.
- **Bounds:** API limits query length, parameter count, duplicate/unknown fields, and the requested window to 2,000 aligned slots. The cap is separate from storage write/sync limits.

## Test coverage gaps to close in the client/API contract suite

- Add explicit tests for freshness at an exact timeframe boundary, future `availableAtMs`, negative/future timestamps, malformed candle timestamp relationships, and a stale latest candle. Assert the distinction between API `evaluable` and consumer eligibility.
- Add consumer tests for every fail-closed rule, unsupported contract/schema versions, mismatched response range/identity, malformed digest, incomplete/gapped windows, duplicate/out-of-order candles, missing threshold, and no fallback path.
- Add HTTP-client tests for invalid/expired credentials, TLS verification, timeout, bounded retry, oversized/truncated/non-JSON response, and safe error redaction.
- Add an explicit maximum response-body size to the consumer contract and test it.

## Verification record

| Item | Result |
|---|---|
| Focused API tests | PASS — 13/13 at reviewed SHA (user-provided) |
| Repository unittest suite | PASS — 404 tests, `OK`, exit 0 at reviewed SHA (user-provided) |
| GitHub Actions exact-SHA run/artifact | NOT VERIFIED |
| Source-level API review | CONDITIONAL PASS |
| T2 HTTP consumer | NOT IMPLEMENTED / BLOCKED |
| T2 direct SQLite removal | NOT DONE |
| TLS/deployment posture | NOT VERIFIED |
| Runtime / canonical DB / Feeder | NOT TOUCHED |
| Live execution | DISABLED; `ai_execution_enabled=false` |

## Next permitted step

Prepare a separately scoped T2 HTTP-client contract/test plan. Implement only after separate authorization. Keep it fixture/local-server-only; do not connect to the canonical T0 database, activate T2 runtime, run Data Quality Gate, deploy, or enable live execution.
