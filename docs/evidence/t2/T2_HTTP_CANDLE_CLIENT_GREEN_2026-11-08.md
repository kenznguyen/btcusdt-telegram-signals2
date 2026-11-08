# T2 HTTP Candle Client — GREEN Implementation Evidence

- Date: 2026-11-08 (UTC)
- Repository: kenznguyen/btcusdt-telegram-signals2
- Branch: feature/t0-centralized-data-feeder-p1-20261101
- Exact checked-out source SHA for final test and smoke runs: 6b55f6f02f7e2bcceb4b38a7944e9f9b42bbe64d
- HTTP client implementation commit: 3223fb5746841bfd537258f27c14d2a5d8f57039
- HTTP client path: freqai_bridge/http_candles.py
- Test path: freqai_bridge/test_http_candles.py
- Separate migration acceptance tests: freqai_bridge/t2_http_migration_acceptance.py
- Workflow: .github/workflows/t2-http-consumer-red.yml

## Scope approved and implemented

User explicitly approved Phase GREEN for the isolated T2 HTTP client. Implemented only the freqai_bridge.http_candles adapter and its focused tests/workflow/evidence.

Public interface:
- CandleHttpConfig(base_url, token, max_lag_ms)
- CandleHttpClient(config, session=None, sleep=None, clock_ms=None)
- CandleHttpClient.fetch(start_ms, end_ms, as_of_ms)
- CandleHttpError.reason stable safe category.

Behavior implemented:
- BTCUSDT / Binance USDT perpetual / M15 only; aligned half-open window; 1–32 bars.
- Bearer token only in Authorization header; config repr and errors do not expose token.
- HTTPS for remote endpoints; loopback HTTP only when explicitly configured as loopback; TLS verification always enabled.
- Fixed connect/read timeout 3s/5s; maximum 3 attempts; 250ms/500ms backoff; retries only transient transport/timeouts and HTTP 503.
- No automatic redirects; no-store and identity-encoding request headers; reject non-identity response encoding.
- Incremental response streaming with 256 KiB cap before JSON decode; strict UTF-8 JSON; duplicate JSON keys and malformed/deeply nested JSON rejected.
- Strict envelope/schema/identity/request echo/dataset-version/coverage/candle field/timestamp/decimal/OHLCV validation.
- Strict freshness arithmetic, client/server future-time rejection, and request-window completeness.
- max_lag_ms is explicit and capped at the approved 120000 ms; ingestion delay is availableAtMs - closeTimeMs; exactly 120000 accepted, greater rejected.
- No SQLite, cache, synthetic candle, or alternate venue fallback inside the adapter.

## Focused GitHub Actions evidence

- Run: 42469402438
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42469402438
- Event: push
- Checked-out SHA: 6b55f6f02f7e2bcceb4b38a7944e9f9b42bbe64d
- Job: Verify T2 HTTP candle adapter
- Job ID: 128696421586
- Conclusion: SUCCESS
- Exact log summary:
  - isolated paper-only preflight PASS;
  - Python compile PASS;
  - Ran 45 tests in 0.076s;
  - OK;
  - T2_HTTP_GREEN=PASS;
  - T2_HTTP_GREEN_TESTS=45.
- Artifact name: t2-http-adapter-6b55f6f02f7e2bcceb4b38a7944e9f9b42bbe64d
- Artifact ID: 13613080643
- Artifact SHA-256: 9f36fe04efe744f4a5cf1741919aa6dddffad0f60170719e003eed2c94c09497

## Pinned Freqtrade 2026.9 compatibility smoke

- Run: 42469402445
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42469402445
- Event: push
- Checked-out SHA: 6b55f6f02f7e2bcceb4b38a7944e9f9b42bbe64d
- Job: Pinned Freqtrade 2026.9 FreqAI strategy load
- Job ID: 128696421737
- Conclusion: SUCCESS
- Steps verified: paper-only/source guards; pinned Freqtrade 2026.9 image; exact framework version; existing strategy load without exchange sync or database access.
- Artifact name: t2-freqtrade-2026-9-strategy-smoke-6b55f6f02f7e2bcceb4b38a7944e9f9b42bbe64d
- Artifact ID: 13613106308
- Artifact SHA-256: 69be478af85484583543a8ad92efcf3254fbbfb3886cfd69e2ded27fa43d6ca3

## Test coverage

45 focused tests cover:
- endpoint/token/freshness configuration and token redaction;
- exact request parameters, Bearer header, timeout/TLS/redirect/encoding/cache policy;
- valid response and dataset provenance;
- contract/schema/identity/range and dataset hash;
- coverage, timestamps, exclusive close boundary, availability cutoffs;
- decimal-string syntax, precision, OHLCV constraints;
- exact 120000 / 120001 ms ingestion-delay boundary;
- normal M15 interval age and server-global expected-slot behavior, including a response generated after the next M15 boundary while retaining the original request asOfMs;
- freshness arithmetic, missing/evaluable-false freshness, future timestamps;
- 400/401/404/405/429/500 no-retry, HTTP 503 bounded retry, transient timeout retry;
- TLS certificate failure, malformed/duplicate/deep JSON, content-type/encoding and 256 KiB limits;
- secret redaction and existing native order signals disabled.

## Review and limitations

- Self-review completed across correctness, readability, architecture, security and resource bounds; no confirmed critical defect found in the isolated adapter implementation.
- Independent second-reviewer sign-off: NOT VERIFIED.
- The 5 separately gated direct-SQLite migration acceptance checks in freqai_bridge/t2_http_migration_acceptance.py were compiled but intentionally not executed; they are expected to remain blocked until the migration is separately authorized.
- freqai_bridge/context.py still imports market_data.store and calls read_window(); ChartProFreqaiResearch.py still uses canonical_db_path. The new HTTP client is not wired into the strategy yet.
- No live T0 HTTP endpoint, TLS certificate, canonical DB, exchange, cache, or runtime was contacted. No T0 API/store/DB, Feeder, VPS, T2 runtime config, model, paper order routing, deployment, or trading state changed.
- The successful Freqtrade smoke loads the existing strategy without exchange sync/database access; it does not prove HTTP client integration into the strategy.
- ai_execution_enabled=false remains enforced.

## Verdict

**ISOLATED HTTP CLIENT: PASS (45/45 focused tests; Freqtrade 2026.9 strategy-load smoke PASS).**

**T2 HTTP CONSUMER MIGRATION: NOT STARTED.** Direct SQLite removal, context/strategy wiring, and no-fallback migration acceptance remain separately gated. Runtime activation/deployment and any trading execution remain NOT AUTHORIZED.


## Final request-boundary rerun — 2026-11-08

- Strengthened the boundary case to simulate the consumer capturing asOfMs before the next M15 boundary while the T0 API generates the response after that boundary. The response remains evaluated against the original requested half-open window; server-global latestExpectedOpenTimeMs is diagnostic only.
- Final checked-out source SHA: 6b55f6f02f7e2bcceb4b38a7944e9f9b42bbe64d.
- Focused HTTP adapter run 42469402438, job 128696421586: SUCCESS; 45 tests in 0.076s; compile/preflight PASS.
- Focused artifact ID 13613080643; SHA-256 9f36fe04efe744f4a5cf1741919aa6dddffad0f60170719e003eed2c94c09497.
- Pinned Freqtrade 2026.9 smoke run 42469402445, job 128696421737: SUCCESS at the same exact SHA; no exchange sync or DB access.
- Freqtrade smoke artifact ID 13613106308; SHA-256 69be478af85484583543a8ad92efcf3254fbbfb3886cfd69e2ded27fa43d6ca3.


## Existing T0/T1 regression workflow at the same source SHA

- Run: 42469402459
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42469402459
- Checked-out SHA: 6b55f6f02f7e2bcceb4b38a7944e9f9b42bbe64d
- All six existing jobs concluded SUCCESS, including paper-consumer fixtures, Gateway/Feeder regressions, the market_data suite, isolated TimescaleDB integration, T1 importer and Rust sidecar offline tests.
- Static Gateway job 128696421966 ran the complete market_data test package: 280 tests, 42 skipped because the dedicated TimescaleDB DSN was not supplied to that job; result OK.
- Separate isolated TimescaleDB integration job 128696468092 concluded SUCCESS. This used disposable CI containers, not the canonical T0 DB or VPS.
- This is regression evidence for the unchanged T0/T1 code at the same checkout SHA; it does not certify or activate canonical T0 runtime.
- Artifact IDs include 13613170916 (Gateway), 13613190837 (provider bootstrap), 13612911518 (Timescale read-only), 13612946066 (paper consumers), 13613160296 (T1 importer), and 13612966914 (T1 Rust sidecar). Their GitHub artifact digests are recorded in run metadata; payload bytes were not independently downloaded and re-hashed in this increment.
