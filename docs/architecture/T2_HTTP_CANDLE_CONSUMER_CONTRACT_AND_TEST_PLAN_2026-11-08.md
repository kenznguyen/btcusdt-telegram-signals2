# T2 HTTP Candle Consumer — Contract and RED Test Plan

- Date: 2026-11-08 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Baseline API source: `e317b7dc02363db0600737a89442dd918af3c`
- Related design: `docs/architecture/T0_READ_ONLY_CANDLE_CONTRACT_V1_2026-11-08.md`
- Related review: `docs/evidence/t0/T0_CANDLE_CONTRACT_V1_INDEPENDENT_REVIEW_2026-11-08.md`
- Status: DESIGN / TEST PLAN ONLY. No implementation or runtime approval is implied.

## 1. Objective and boundaries

Replace the T2 FreqAI bridge's direct T0 SQLite read with the existing versioned read-only HTTP contract. Preserve the current consumer behavior: BTCUSDT, 15m candles, bounded 1–32 bar inference window, closed candles only, availability cutoff, dataset-version provenance, and fail-closed prediction-unavailable behavior.

T0 remains the only canonical data owner and writer. T2 receives data only through `GET /v1/candles`. This work does not authorize:
- canonical DB creation/opening or schema changes;
- Feeder, VPS, exchange, Data Quality Gate, or T0 runtime operations;
- T1/T2 runtime activation, model training, deployment, paper order routing, or live execution;
- changing the official Freqtrade/OKX backtest or out-of-sample source;
- changing shared risk policy or AI execution settings.

Keep `ai_execution_enabled=false`.

## 2. Current T2 call path to remove

At the reviewed source:
- `freqai_bridge/context.py` imports `INTERVAL_MS` and `read_window` from `market_data.store`, then calls `read_window(database, ...)`.
- `freqai_bridge/ChartProFreqaiResearch.py` obtains `canonical_db_path` and passes it into `canonical_context()`.

The migration must remove this T0 Store import and the canonical DB path from the T2 runtime configuration. A read-only SQLite connection is still a direct database dependency and is not an acceptable fallback.

## 3. Proposed module boundary

Add a small T2-owned HTTP adapter (final module name to follow repository conventions) with two responsibilities:

1. **Transport:** issue GET to configured base URL plus `/v1/candles`, send Bearer token only in the Authorization header, send `Cache-Control: no-store`, use HTTPS for cross-host requests, and enforce bounded connect/read timeouts, bounded retry policy, and maximum response-body bytes.
2. **Validation:** treat the response as untrusted external input; parse and validate the entire envelope and every candle before returning a typed/normalized in-memory context.

The adapter must not import `market_data.store`, open files/SQLite, write to T0, initialize schemas, or contact an exchange directly.

Configuration contract:
- Required: API base URL, token, connect timeout, read timeout, max response bytes, and freshness threshold for 15m.
- Missing/blank values, non-HTTPS cross-host URL, invalid thresholds, or invalid bounds => unavailable/fail closed.
- Never log or include the token in exception text, URLs, artifacts, or diagnostics.
- No token query parameter.
- Loopback HTTP may be allowed only for an explicitly configured same-host deployment; remote HTTP is forbidden.
- Numeric timeout/retry/body-size defaults are NOT approved here; define and review them before implementation rather than silently inventing operational limits.

## 4. Request semantics

Phase 1 consumer supports the existing FreqAI bridge use case only:
- `symbol=BTCUSDT`
- `timeframe=15m`
- `startMs` and `endMs` aligned to 15-minute boundaries, half-open `[startMs,endMs)`
- 1–32 requested bars; never exceed API's 2,000-slot ceiling
- `asOfMs` set to the consumer observation cutoff so candles first observed after the cutoff are excluded.

The client must preserve the current window semantics and validate that the response echoes the exact request identity/range/as-of value.

### Contract clarification required before implementation

The API's `freshness.latestExpectedOpenTimeMs` is calculated from server `generatedAtMs`, while the T2 request range is currently calculated from the consumer clock. Near a 15-minute boundary, the server's latest expected candle may fall outside the requested `[startMs,endMs)` range. The design also says the latest returned candle must equal the latest expected candle for strategy use.

Before writing the client, resolve this clock/range relationship in the contract:
- define whether T2's freshness comparison is against the latest expected slot inside the requested range (`endMs - interval`) or the server-global `latestExpectedOpenTimeMs`;
- define behavior when client/server clocks straddle a timeframe boundary;
- define maximum permitted clock skew, if any, and whether a single bounded re-request is permitted;
- ensure `asOfMs` and `generatedAtMs` semantics cannot make a valid current window look stale or let a stale window pass.

Do not code around this ambiguity with a permissive exception. Add deterministic tests for both sides of a timeframe boundary.

## 5. Fail-closed response validation

Reject the complete response (do not partially salvage candles) unless all checks pass:

### Envelope and identity
- HTTP 200; valid UTF-8 JSON object; no duplicate JSON keys if parser support is available.
- Exact supported `contractVersion=1.0.0` and `schemaVersion=1` for phase 1.
- Exact `exchange=binance`, `marketType=USDT_PERPETUAL`, `symbol=BTCUSDT`, `timeframe=15m`, `volumeUnit=BTC_BASE_ASSET`, `source=ccxt.binanceusdm`.
- Exact echoed `startMs`, `endMs`, and `asOfMs`.
- `generatedAtMs` is an integer, nonnegative, and not unreasonably in the future under the approved clock-skew policy.
- `datasetVersion` matches `sha256:[0-9a-f]{64}`; retain it with each prediction artifact. This format check is not a cryptographic authenticity check.

### Coverage and candles
- `coverage.expected` equals requested slots; `returned` equals candle count and expected; `complete is true`; `gaps=[]`.
- Candle array length is within requested 1–32 bars.
- Every candle has exact required fields and types; no bool-as-int acceptance.
- `openTimeMs` values are aligned, strictly increasing, unique, and inside the half-open request range.
- Exact expected timestamp sequence is present; no gaps, duplicates, reordering, or extras.
- `closeTimeMs = openTimeMs + 900000`; `isClosed is true`; `availabilityKind=FIRST_OBSERVED`; `quality=VALIDATED`; candle source matches dataset source.
- Decimal fields are strings only, parse as finite decimals, and satisfy `low <= min(open,close) <= max(open,close) <= high`; volume is nonnegative. Do not pass through binary float during validation/normalization.
- `availableAtMs` is an integer, not after the approved observation cutoff, and not invalid/future relative to the clock policy.
- Freshness fields are internally consistent: age and close lag equal their documented differences, nullability is consistent, and `evaluable` has the documented meaning.

### Strategy freshness
- Explicit 15m max-lag threshold is mandatory and must be a positive bounded integer.
- No threshold or invalid threshold => unavailable.
- Latest required candle and freshness policy must pass according to the clock/range rule resolved in section 4.
- An HTTP 200 response with incomplete coverage, stale candles, or `evaluable=false` is a rejection, not a successful empty/partial context.

### Transport and errors
- TLS certificate verification enabled for cross-host HTTPS; no insecure bypass.
- Connect/read timeouts always bounded.
- Retry only transient transport errors and selected 503 responses; bounded attempts/backoff; never retry 400/401/404/405.
- No retry may silently switch endpoint, source, DB, or cache.
- Enforce maximum response bytes before full JSON decode; reject oversized, truncated, malformed, non-JSON, or unexpected content types.
- Redact credentials and internal endpoint details from logs/errors/artifacts.

## 6. Error contract returned to FreqAI bridge

Adapter returns either a fully validated context or a typed unavailable result with a stable reason category, for example:
- `CONFIG_INVALID`
- `AUTH_REJECTED`
- `CONTRACT_UNSUPPORTED`
- `IDENTITY_MISMATCH`
- `RANGE_MISMATCH`
- `COVERAGE_INCOMPLETE`
- `CANDLE_INVALID`
- `FRESHNESS_UNAVAILABLE`
- `FRESHNESS_EXCEEDED`
- `RESPONSE_TOO_LARGE`
- `HTTP_UNAVAILABLE`
- `HTTP_TIMEOUT`

No exception should expose token, DB path, SQL, response body, or internal host details. FreqAI prediction publication retains the existing unavailable artifact behavior; no candle response means no prediction. The strategy continues to set native entry/exit signals to zero and rejects trade entry.

## 7. RED test plan

Tests must be deterministic, local-only, and written before implementation. Use a local HTTP test server or controlled transport fake; no external network, canonical DB, exchange, model training, or runtime.

### A. Request and configuration
1. Missing base URL fails closed.
2. Missing/blank token fails closed.
3. Missing/invalid freshness threshold fails closed.
4. Remote non-HTTPS endpoint is rejected.
5. Request sends Bearer header and no token query parameter.
6. Request uses exact BTCUSDT/15m/range/as-of parameters.
7. Requested bars outside 1–32 are rejected before network I/O.
8. Secret never appears in logs, exception text, or artifacts.

### B. Valid response
9. Accept a complete, exact 1–32 candle response with valid provenance.
10. Preserve decimal strings without float conversion.
11. Preserve datasetVersion and request identity in the returned context.
12. Accept exact expected timestamp sequence only.

### C. Contract/identity/range
13. Reject unsupported contract major/schema version.
14. Reject exchange/market/symbol/timeframe/volumeUnit/source mismatch.
15. Reject echoed start/end/asOf mismatch.
16. Reject malformed datasetVersion.
17. Reject missing/extra/wrong-type envelope fields where required.

### D. Coverage and candle integrity
18. Reject `complete=false`, nonempty gaps, expected/returned mismatch.
19. Reject missing, duplicate, out-of-order, off-grid, out-of-range timestamps.
20. Reject open candle, incorrect exclusive close boundary, invalid availability kind/quality/source.
21. Reject non-string, NaN/infinite, malformed, negative-volume or invalid-OHLC decimals.
22. Reject future availability timestamp and invalid timestamp relationships.
23. Reject malformed empty response for a nonempty requested window.

### E. Freshness and time boundary
24. Reject missing/null freshness for a nonempty response.
25. Reject inconsistent age/close-lag arithmetic.
26. Reject `evaluable=false`.
27. Reject stale response above configured max lag.
28. Reject latest expected candle missing from the requested current window.
29. Test client/server clocks immediately before and after a 15m boundary.
30. Test `asOfMs` filtering at exact equality and one millisecond after/before.

### F. HTTP and resource safety
31. 401 stops retries and returns AUTH_REJECTED.
32. 400/404/405 do not retry.
33. 503/transient transport failures obey bounded retry count.
34. Connect/read timeout returns unavailable.
35. Invalid TLS certificate fails closed.
36. Oversized body is rejected before JSON decode.
37. Truncated/non-JSON/wrong content-type response is rejected.
38. Error body and token are not leaked to logs/artifacts.

### G. No fallback / integration
39. No code path imports `market_data.store` from the T2 HTTP adapter.
40. No T2 runtime path accepts `canonical_db_path`.
41. HTTP unavailable never triggers SQLite/cache/venue fallback.
42. Prediction artifact is unavailable on any rejected response.
43. Native entry/exit signals remain zero; trade-entry confirmation remains false.

### H. Regression
44. Existing FreqAI exporter/provenance tests remain unchanged and pass.
45. Existing T2 paper/research regression remains pass.
46. Full repository test suite passes after implementation.
47. GitHub Actions evidence identifies exact source SHA, run/event, checked-out SHA, job conclusions and artifact identity.

RED must be observed against the pre-implementation source. Do not label a test RED solely because it was authored; execute it and record exact source SHA and failure reason.

## 8. Implementation sequence after approval

1. Resolve section 4 freshness/range ambiguity and approve numeric timeout/retry/body limits.
2. Add RED tests only; run focused tests and capture actual RED at exact SHA.
3. Implement the HTTP adapter only; no T0 API/store/DB changes.
4. Migrate `canonical_context` to consume validated HTTP response and remove direct Store import.
5. Remove `canonical_db_path` from T2 runtime configuration and update README/config docs.
6. Add local-server integration tests, secret-redaction checks, and no-fallback tests.
7. Run focused tests, relevant T2 regression, and full repository suite.
8. Independent review confirms no direct T0 DB dependency remains in T2 runtime.
9. Run GitHub Actions on the same branch and record exact source/checkout SHA and artifacts.
10. Record PASS/BLOCKED/NOT VERIFIED. Runtime promotion remains a separate approval.

## 9. Approval gates and status

| Gate | Status |
|---|---|
| Contract design / source review | CONDITIONAL PASS |
| Freshness vs request-window boundary clarification | BLOCKED — decision required |
| Timeout/retry/body-size numeric policy | NOT APPROVED |
| T2 HTTP client implementation | NOT AUTHORIZED |
| T2 direct SQLite removal | NOT STARTED |
| Local fixture/HTTP tests | NOT RUN |
| GitHub Actions exact-SHA | NOT VERIFIED |
| T2 runtime activation/deployment | NOT AUTHORIZED |

This plan defines the proposed implementation and acceptance criteria only. It does not authorize source changes or runtime activity.
