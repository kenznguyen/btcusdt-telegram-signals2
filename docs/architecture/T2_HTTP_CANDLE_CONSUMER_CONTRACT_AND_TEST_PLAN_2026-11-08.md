# T2 HTTP Candle Consumer — Contract and RED Test Plan

- Date: 2026-11-08 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Baseline API source: `e317b7dc02363db0600737a89442dd918af3c`
- Related design: `docs/architecture/T0_READ_ONLY_CANDLE_CONTRACT_V1_2026-11-08.md`
- Related review: `docs/evidence/t0/T0_CANDLE_CONTRACT_V1_INDEPENDENT_REVIEW_2026-11-08.md`
- Status: DESIGN + HTTP CONSUMER MIGRATION IMPLEMENTATION/ACCEPTANCE RECORD. T2 runtime activation remains NOT AUTHORIZED.

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

The RED test seam fixes the adapter module and public interface as `freqai_bridge.http_candles`:

- `CandleHttpConfig(base_url, token, max_lag_ms, ...)` validates required values and approved transport limits.
- `CandleHttpClient(config, session=..., sleep=..., clock_ms=...)` provides deterministic transport/time injection for tests.
- `CandleHttpClient.fetch(start_ms, end_ms, as_of_ms)` issues the request and returns the complete validated Contract v1 envelope as an in-memory dictionary.
- `CandleHttpError` exposes a stable `.reason` category; its string representation must not contain the token, response body, or internal host details.
- The injected session uses a Requests-compatible `get(url, params=..., headers=..., timeout=(3,5), stream=True, allow_redirects=False, verify=True)` interface. Response bodies are consumed incrementally and bounded before JSON decode.

The adapter has two responsibilities:

1. **Transport:** issue GET to configured base URL plus `/v1/candles`, send Bearer token only in the Authorization header, send `Cache-Control: no-store`, use HTTPS for cross-host requests, and enforce approved timeout/retry/body-size policy.
2. **Validation:** treat the response as untrusted external input; parse and validate the entire envelope and every candle before returning a typed/normalized in-memory context.

The adapter must not import `market_data.store`, open files/SQLite, write to T0, initialize schemas, or contact an exchange directly.

Configuration contract:
- Required: API base URL, token, connect timeout, read timeout, maximum response bytes, and M15 `max_lag_ms`.
- Missing/blank values, non-HTTPS cross-host URL, invalid thresholds, or invalid bounds => unavailable/fail closed.
- Never log or include the token in exception text, URLs, artifacts, or diagnostics.
- No token query parameter.
- Loopback HTTP may be allowed only for an explicitly configured same-host deployment; remote HTTP is forbidden.
- Approved transport defaults: connect timeout 3 s; read timeout 5 s; at most 3 total attempts; fixed backoff 250 ms then 500 ms; maximum response body 256 KiB.
- Send `Accept-Encoding: identity`; do not automatically follow redirects; stream and enforce the body cap before full JSON decoding.
- TLS certificate verification is mandatory for cross-host HTTPS. These limits govern the client only; they do not authorize runtime deployment or changes to the T0 server.

## 4. Request semantics

Phase 1 consumer supports the existing FreqAI bridge use case only:
- `symbol=BTCUSDT`
- `timeframe=15m`
- `startMs` and `endMs` aligned to 15-minute boundaries, half-open `[startMs,endMs)`
- 1–32 requested bars; never exceed API's 2,000-slot ceiling
- `asOfMs` set to the consumer observation cutoff so candles first observed after the cutoff are excluded.

The client must preserve the current window semantics and validate that the response echoes the exact request identity/range/as-of value.

### Approved freshness / request-window rule

**APPROVED by user on 2026-11-08.**

- Evaluate whether the requested window is complete against its own expected slots; for M15, the latest required candle is exactly `openTimeMs = endMs - 900000`.
- Do not require the server-global `freshness.latestExpectedOpenTimeMs` to lie inside the consumer's requested window. It is diagnostic server-clock metadata, not the request-window membership criterion.
- Continue validating `generatedAtMs` and each `availableAtMs` for integer/type validity and the separately approved time/freshness policy.
- Require an explicitly configured M15 freshness threshold; missing or invalid threshold fails closed.
- Do not automatically shift/retry the request window and do not fall back to cache, SQLite, synthetic candles, or another venue.
- Add deterministic tests with client/server clocks on opposite sides of an M15 boundary, proving that a complete requested window is evaluated by its own end slot and stale data still fails the configured threshold.

This approval resolves the boundary comparison only. It does not approve numeric timeout/retry/body-size limits or implementation/runtime activity.

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
- Explicit M15 `max_lag_ms` is mandatory; approved value is `120000` ms (120 seconds). Missing or invalid configuration => unavailable.
- **Meaning of this threshold:** ingestion/first-observation delay for the latest required candle, calculated as `latestAvailableAtMs - latestCloseTimeMs`. This is also `closeLagMs - observationAgeMs` using the API's documented fields. It is NOT the raw `closeLagMs` (`generatedAtMs - latestCloseTimeMs`) and NOT `observationAgeMs` (`generatedAtMs - latestAvailableAtMs`); those grow naturally during an M15 interval and a 120-second cap on either would reject otherwise-current data for much of every 15-minute cycle.
- Require `latestAvailableAtMs >= latestCloseTimeMs`; negative or uncomputable ingestion delay fails closed. Accept delay exactly 120000 ms; reject any value greater than 120000 ms.
- Continue validating the API's `generatedAtMs`, `availableAtMs`, `observationAgeMs`, `closeLagMs`, and `evaluable` arithmetic. The latest required candle must also be present at `openTimeMs = endMs - 900000`.
- An HTTP 200 response with incomplete coverage, ingestion delay above threshold, or `evaluable=false` is a rejection, not a successful empty/partial context.

### Transport and errors
- TLS certificate verification enabled for cross-host HTTPS; no insecure bypass.
- Connect/read timeouts always bounded.
- Retry only transient connection/transport errors, connect/read timeouts, and HTTP 503; maximum 3 total attempts with fixed 250 ms then 500 ms backoff. HTTP 400/401/404/405 and all contract/data validation failures are not retried. Other HTTP statuses fail closed without retry.
- Do not automatically follow redirects. No retry may silently switch endpoint, source, DB, or cache.
- Send `Accept-Encoding: identity`; require the expected JSON content type. Stream the response and abort as soon as the body exceeds 256 KiB, before full JSON decode. Reject oversized, truncated, malformed, non-JSON, or unexpected content types.
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
27. Accept ingestion delay exactly 120000 ms and reject 120001 ms; verify the calculation `availableAtMs - closeTimeMs = closeLagMs - observationAgeMs`.
28. Prove a normal M15 interval does not fail merely because raw `closeLagMs` or `observationAgeMs` exceeds 120000 ms.
29. Reject latest required candle missing from the requested window.
30. Test client/server clocks immediately before and after a 15m boundary.
31. Test `asOfMs` filtering at exact equality and one millisecond after/before.

### F. HTTP and resource safety
32. 401 stops retries and returns AUTH_REJECTED.
33. 400/404/405 and non-retryable statuses do not retry.
34. 503/transient transport failures obey the 3-attempt limit and 250/500 ms backoff.
35. Connect/read timeout uses 3 s/5 s bounds and returns unavailable after the bounded attempts.
36. Invalid TLS certificate fails closed; redirects are not followed.
37. `Accept-Encoding: identity` is sent; response body above 256 KiB is rejected before JSON decode.
38. Truncated/non-JSON/wrong content-type response is rejected.
39. Error body and token are not leaked to logs/artifacts.

### G. No fallback / integration
40. No code path imports `market_data.store` from the T2 HTTP adapter.
41. No T2 runtime path accepts `canonical_db_path`.
42. HTTP unavailable never triggers SQLite/cache/venue fallback.
43. Prediction artifact is unavailable on any rejected response.
44. Native entry/exit signals remain zero; trade-entry confirmation remains false.

### H. Regression
45. Existing FreqAI exporter/provenance tests remain unchanged and pass.
46. Existing T2 paper/research regression remains pass.
47. Full repository test suite passes after implementation.
48. GitHub Actions evidence identifies exact source SHA, run/event, checked-out SHA, job conclusions and artifact identity.

RED must be observed against the pre-implementation source. Do not label a test RED solely because it was authored; execute it and record exact source SHA and failure reason.

## 8. Implementation sequence and current boundary

1. Freshness boundary and transport/resource policies: APPROVED.
2. RED architecture baseline and executable behavior specification: completed and recorded in the RED evidence reports.
3. Isolated HTTP adapter GREEN implementation: completed; 45/45 focused tests PASS at exact SHA; see the GREEN evidence report.
4. Pinned Freqtrade 2026.9 strategy-load smoke: PASS at the same checked-out source SHA, without exchange sync or database access.
5. T2 consumer migration is a separate next increment: migrate canonical_context to the validated HTTP response, remove direct Store import/read_window, remove canonical_db_path from T2 config, and prove no SQLite/cache/venue fallback. This step requires separate explicit authorization.
6. Add consumer-level HTTP integration tests and run focused, T2 regression and full repository tests for that migration.
7. Independent review must assess the integrated consumer migration before merge.
8. Runtime promotion/deployment remains a separate approval; this adapter-only increment does not authorize runtime use.

## 9. Approval gates and status

| Gate | Status |
|---|---|
| Contract design / source review | CONDITIONAL PASS |
| Freshness vs request-window boundary clarification | APPROVED — request-window latest slot = endMs - 900000 |
| HTTP transport/resource limits | APPROVED — 3 s connect, 5 s read, 3 attempts, 250/500 ms backoff, 256 KiB body cap, identity encoding, no redirects |
| M15 freshness threshold | APPROVED — 120000 ms, using first-observation ingestion delay formula below |
| T2 HTTP client implementation | PASS — isolated adapter implemented; 45/45 focused tests PASS |
| Architecture RED baseline | CONFIRMED — 6 expected architecture failures; run 42468167014 at exact SHA 3222c1bd56ccc089d84f2744f4bafede4747ce50 |
| HTTP behavior test specification | GREEN — 45/45 adapter behavior and policy tests PASS at exact SHA 6b55f6f02f7e2bcceb4b38a7944e9f9b42bbe64d |
| GitHub Actions exact-SHA | PASS — adapter run 42469402438; Freqtrade smoke run 42469402445; same checked-out SHA |
| Pinned Freqtrade 2026.9 strategy-load smoke | PASS — run 42469402445; no exchange sync/database access |
| T2 direct SQLite removal / consumer wiring | NOT STARTED — separate authorization required |
| No-fallback consumer migration acceptance | NOT RUN |
| Independent second-reviewer sign-off | NOT VERIFIED |
| T2 runtime activation/deployment | NOT AUTHORIZED |

The original design-only disclaimer is superseded only for the isolated HTTP adapter GREEN increment explicitly approved by the user on 2026-11-08. The separate T2 consumer migration and all runtime activity remain gated.


## Approval record — freshness boundary rule

- User approval received 2026-11-08.
- Approved rule: request-window completeness and latest M15 candle are evaluated against the request's own end boundary; latest required candle is `endMs - 900000`. Server-global `latestExpectedOpenTimeMs` remains diagnostic and is not required to fall inside the requested range.
- Continue validating server generation and availability timestamps; configured M15 max-lag remains mandatory and fail-closed.
- No automatic window shift/re-request or fallback to SQLite/cache/synthetic/alternate venue.
- Scope of this earlier approval: freshness boundary design only. The transport limits were approved later in the subsequent policy record. No RED tests have been added or run; no implementation or runtime activity is authorized by either policy approval.


## Approval record — T2 HTTP transport and freshness policy

- User approval received 2026-11-08.
- Transport/resource limits approved: connect timeout 3 seconds; read timeout 5 seconds; maximum 3 attempts total; fixed backoff 250 ms then 500 ms; maximum response body 256 KiB; send `Accept-Encoding: identity`; do not follow redirects; verify TLS certificates for cross-host HTTPS; enforce the response cap while streaming and before full JSON decode.
- Retry only transient connection/transport errors, connect/read timeouts, and HTTP 503. Do not retry 400/401/404/405, other HTTP statuses, or contract/data validation failures. Never switch endpoint/source/cache/DB.
- M15 `max_lag_ms=120000` is approved subject to the verified interpretation: ingestion delay = `latestAvailableAtMs - latestCloseTimeMs`, equivalently `closeLagMs - observationAgeMs`. It is not raw `closeLagMs` or `observationAgeMs`, since those naturally increase during an M15 interval and a 120-second cap on either would reject valid current data during much of the interval.
- Require `availableAtMs >= closeTimeMs`; accept exactly 120000 ms and reject values greater than 120000 ms. Continue validating all server-generated freshness fields and their arithmetic.
- Add deterministic tests for the formula, exact threshold boundary (120000 accepted / 120001 rejected), and proof that normal M15 interval age does not trigger false stale rejection.
- Scope: documentation/policy approval only. This does not authorize RED test implementation/execution, T2 HTTP client implementation, T2 direct SQLite removal, T0/VPS/runtime changes, deployment, or trading activation. A separate explicit authorization is required before code/test work.


## RED-only execution record — 2026-11-08

- Test file: `freqai_bridge/test_http_candles.py`.
- Workflow: `.github/workflows/t2-http-consumer-red.yml`.
- Evidence report: `docs/evidence/t2/T2_HTTP_CONSUMER_RED_BASELINE_2026-11-08.md`.
- Exact source/checkout SHA: `d8ba2e1cf7e7e23977dc5eb0bd6484ed1d1d4745`.
- GitHub Actions run `42467842637`, event `push`, job `128691379082`, conclusion `success` because the expected RED was validated.
- Observed test result: 7 tests; 5 intentional architecture-gap failures (missing HTTP adapter, direct Store import/read, legacy DB path/call) and 2 policy assertions PASS; zero unexpected errors. Test compile PASS.
- Artifact ID `13612118332`; SHA-256 `39140a7a10cf3c723c67cab728784f836a6e89446cbf0c8c2e27618704d35de8`.
- This is an architecture-gap baseline only. The detailed HTTP behavior cases in section 7 (auth, TLS, retry, timeout, body cap, response schema, identity, coverage, decimal/candle integrity, freshness boundaries, secret redaction and no-fallback) are not yet implemented as executable tests and remain NOT VERIFIED.
- No production code, direct SQLite path, config, T0, Feeder, VPS or runtime changed. GREEN implementation remains NOT AUTHORIZED.


## Expanded RED test specification — 2026-11-08

- Test interface is now fixed for the RED/GREEN boundary: module `freqai_bridge.http_candles`; public types `CandleHttpConfig`, `CandleHttpClient`, `CandleHttpError`; client call `fetch(start_ms, end_ms, as_of_ms)`. Deterministic injection points are `session`, `sleep`, and `clock_ms`.
- Test file expanded to 37 tests. Exact-SHA workflow run `42468065621`, checked-out SHA `8bfc920a949c817fb6065657dda6663373bc2f25`.
- Observed: 37 tests, 6 architecture-gap assertion failures, 28 behavior tests blocked by missing adapter import, 3 assertions PASS, zero unexpected error types. The blocked tests are authored acceptance specifications; none of their client behaviors is yet verified.
- Evidence report: `docs/evidence/t2/T2_HTTP_CONSUMER_RED_EXPANDED_2026-11-08.md`; artifact ID `13612630819`; SHA-256 `f0912b735532640803fff56374dffe0e24b48c15411f37828c9142eefdcc9dd1`.
- Workflow conclusion PASS means the expected RED shape was validated. It does not mean the T2 HTTP client or its behavior passed.
- Next RED-only task is to resolve any test-interface ambiguity and extend/run behavior-specific checks when a test-only seam is available. No production code or GREEN implementation is authorized by this approval.


## Final RED fixture correction and rerun — 2026-11-08

- Test file SHA: `3222c1bd56ccc089d84f2744f4bafede4747ce50`.
- Corrected freshness fixtures so as-of cutoffs include the availability timestamps under test and server-global expected-slot metadata is consistent with server generation time.
- GitHub Actions run `42468167014`, job `128692428965`, conclusion PASS for the expected-RED harness.
- Result: 37 tests; 6 expected architecture assertion failures; 28 adapter-dependent behavior tests blocked by missing adapter import; 3 assertions PASS; no unexpected error types. Compile and preflight PASS.
- Artifact ID `13611894815`; SHA-256 `27d2f20452c19b50a9d02d0a61935e2b77071b895fa47375469d5fcc022b57ad`.
- Evidence report: `docs/evidence/t2/T2_HTTP_CONSUMER_RED_EXPANDED_2026-11-08.md`.
- The behavior tests remain NOT VERIFIED; expected RED harness PASS is not product/HTTP client PASS. No GREEN code or runtime authorization.


## GREEN implementation record — 2026-11-08

- User explicitly approved isolated HTTP client implementation after the RED baseline.
- Implementation: freqai_bridge/http_candles.py; public API CandleHttpConfig, CandleHttpClient, CandleHttpError; request method fetch(start_ms, end_ms, as_of_ms).
- Implementation commit: 3223fb5746841bfd537258f27c14d2a5d8f57039.
- Final test/workflow checked-out SHA: 6b55f6f02f7e2bcceb4b38a7944e9f9b42bbe64d.
- Focused workflow run 42469402438, job 128696421586: SUCCESS; 45 tests in 0.076s; 0 failures/errors; compile and paper-only preflight PASS.
- Focused artifact ID 13613080643; SHA-256 9f36fe04efe744f4a5cf1741919aa6dddffad0f60170719e003eed2c94c09497.
- Pinned Freqtrade 2026.9 strategy-load run 42469402445, job 128696421737: SUCCESS at the same checked-out SHA; no exchange sync/database access.
- Freqtrade smoke artifact ID 13613106308; SHA-256 69be478af85484583543a8ad92efcf3254fbbfb3886cfd69e2ded27fa43d6ca3.
- Final boundary test simulates asOfMs captured before the next M15 boundary and API response generated after it, while preserving the original requested endMs/window.
- Detailed evidence: docs/evidence/t2/T2_HTTP_CANDLE_CLIENT_GREEN_2026-11-08.md.
- The five direct-SQLite migration acceptance checks are separated in freqai_bridge/t2_http_migration_acceptance.py and were compile-checked only; not executed.
- T2 context.py still imports market_data.store/read_window and ChartProFreqaiResearch.py still uses canonical_db_path. The HTTP adapter is not wired into the strategy. Consumer migration remains NOT STARTED and requires separate approval.
- No T0 API/store/DB, Feeder, VPS, exchange, runtime config, model, paper order routing, deployment, or trading state changed. Keep ai_execution_enabled=false.


## Same-SHA T0/T1 regression — 2026-11-08

- Existing workflow run 42469402459 at exact SHA 6b55f6f02f7e2bcceb4b38a7944e9f9b42bbe64d concluded SUCCESS across all six jobs.
- Static Gateway job ran the complete market_data package: 280 tests, 42 skipped because no dedicated TimescaleDB DSN was supplied to that static job; result OK.
- Separate disposable TimescaleDB integration job, provider bootstrap, paper consumer fixtures, T1 importer and Rust sidecar offline tests all concluded SUCCESS.
- This is same-SHA regression evidence only; no canonical T0 DB, Feeder, VPS or exchange runtime was activated. Full repository-wide unittest discovery was not run.
- Details and artifact metadata: docs/evidence/t2/T2_HTTP_CANDLE_CLIENT_GREEN_2026-11-08.md.


## 9. T2 HTTP consumer migration — implementation and acceptance — 2026-11-08

### Scope and source identity

- User explicitly approved the T2 consumer migration after the isolated HTTP adapter passed.
- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Final branch HEAD for the migration verification: `65fe065ccdc197a51b969da37ce99d5414201a92`.
- The migration changes only the T2 consumer bridge, its research config, tests, workflow and documentation. No T0 API/store/DB, Feeder, VPS, exchange, model, or runtime process was changed.

### Implemented behavior

- `freqai_bridge/context.py` no longer imports `market_data.store`, calls `read_window`, accepts a database path, or opens local storage.
- `canonical_context(now_ms, bars, client=None)` computes the latest aligned M15 half-open window `[end - bars*900000, end)`, enforces 1–32 bars, and requests it through `CandleHttpClient.fetch(start_ms, end_ms, as_of_ms)`.
- `asOfMs` is the consumer observation cutoff. The API response is validated by the adapter before context is returned; its dataset hash is bound to the exact request cutoff.
- Production client configuration is read only from process environment:
  - `T0_CANDLE_API_BASE_URL`
  - `T0_CANDLE_API_TOKEN`
  - `T0_CANDLE_MAX_LAG_MS` (explicit integer; approved deployment value 120000)
- Missing or invalid configuration raises a safe `CandleHttpError`; no local database/cache/source fallback is attempted.
- `ChartProFreqaiResearch.py` no longer reads or passes `canonical_db_path`; it uses the HTTP context and emits a prediction-unavailable artifact when the HTTP contract is unavailable or invalid.
- `freqai_bridge/config.research.json` no longer contains `canonical_db_path`.
- Exporter tests now use contract-shaped fixtures rather than a local SQLite store.
- Entry/exit flags remain zero and `confirm_trade_entry()` remains false. Paper-only guards remain in place.

### Exact-SHA GitHub Actions evidence

1. HTTP adapter + consumer migration + exporter:
   - Run: `42470569288`
   - URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42470569288
   - Event: push; checked-out SHA: `65fe065ccdc197a51b969da37ce99d5414201a92`.
   - Job: `Verify T2 HTTP candle adapter`; job ID: `128700143303`; conclusion: SUCCESS.
   - Adapter: 45 tests; context + migration acceptance: 11 tests; exporter: 6 tests. All three suites reported OK.
   - Compile and isolated paper-only preflight PASS.
   - Artifact ID: `13612932409`.
   - Artifact name: `t2-http-adapter-65fe065ccdc197a51b969da37ce99d5414201a92`.
   - Artifact SHA-256: `2d93c86d272c13894e4662aef32229373a138701e0100dd6c02ad8f38b4d3f0f`.

2. Pinned Freqtrade 2026.9 strategy-load + consumer regression:
   - Run: `42470559497`
   - URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42470559497
   - Checked-out SHA: `f016e82434609d77eb17a10eb48207933dd4040c`.
   - Job ID: `128700074546`; conclusion: SUCCESS.
   - Exact Freqtrade version 2026.9 verified; paper-only preflight PASS; strategy loaded without exchange sync or database access.
   - Consumer/exporter/pipeline regression: 31 tests; result OK.
   - Artifact ID: `13613257638`.
   - Artifact SHA-256: `fef2b839a84a5c25fa0e090e2356542736932f9669bf61e34541271786bcdcbc`.
   - Comparison `f016e824...` to final branch HEAD `65fe065...` shows only the adapter workflow file changed; all T2 production/test source files were unchanged between those SHAs.

3. Existing T0/T1 regression:
   - Run: `42470342807`
   - URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42470342807
   - Checked-out SHA: `720bdf77106a58dfcd4e537d67cd329806ca2243`.
   - All six jobs SUCCESS: T1 importer offline tests, Rust sidecar offline tests, disposable provider bootstrap, paper consumer fixtures, static Gateway contracts and isolated TimescaleDB read-only integration.
   - This is regression evidence only. No canonical T0 DB or VPS runtime was used or activated.

### Verification boundaries and remaining limits

- **PASS:** isolated adapter behavior; HTTP context request construction; loopback HTTP end-to-end path through the real Requests adapter; migration AST acceptance; exporter/pipeline regressions; Freqtrade 2026.9 strategy-load smoke.
- **NOT VERIFIED:** live connection to the actual T0 endpoint; remote TLS certificate and deployed Bearer-token configuration; remote service availability/latency; runtime environment injection; 24/7 behavior.
- **NOT VERIFIED:** full repository-wide unittest discovery after this increment; independent second-reviewer sign-off.
- The loopback integration test is not evidence that the canonical T0 service is deployed or reachable.
- No runtime activation, systemd/service changes, VPS changes, T0 DB/Feeder changes, model training, paper order routing, deployment, or live execution were performed.
- Keep `ai_execution_enabled=false`; native Freqtrade order signals remain disabled.

### Final migration status

| Item | Status |
|---|---|
| T0 Candle Contract v1 isolated HTTP adapter | PASS |
| T2 context HTTP wiring | PASS |
| T2 direct T0 SQLite dependency removal | PASS |
| T2 `canonical_db_path` removal | PASS |
| No-fallback migration acceptance | PASS |
| Loopback HTTP integration | PASS |
| Freqtrade 2026.9 strategy-load smoke | PASS |
| Live T0 endpoint / remote TLS / credentials | NOT VERIFIED |
| Independent second-reviewer sign-off | NOT VERIFIED |
| Full repository-wide test discovery | NOT VERIFIED |
| T2 runtime activation/deployment | NOT AUTHORIZED |

### Next step

The next permitted technical increment is a separately reviewed deployment-configuration and live read-only connectivity verification plan for T0 HTTP, without activating T2 runtime. Do not create runtime services, start prediction collection, or enable any trading path without separate approval.
