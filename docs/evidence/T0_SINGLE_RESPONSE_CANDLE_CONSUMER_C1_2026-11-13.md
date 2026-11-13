# T0 Single-Response Candle Consumer — C1 Evidence

- Date: 2026-11-13 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- Scope: T2 HTTP consumer only; add a public one-response read path for T0 Candle Contract v1 while preserving the legacy paginated `fetch()` behavior.
- Runtime posture: PAPER; `AI_EXECUTION_ENABLED=false`; no live orders.

## Source changes

- RED test commit: `7f6f89528d6beb1a9a8bec19e8546d65b146215b`.
- GREEN implementation commit: `6fc860d7f696b3faacdb87b69a9017909e6f92d9`.
- Changed files:
  - `.github/workflows/t2-http-consumer-red.yml`: enable this existing branch in the existing HTTP-consumer workflow; update exact test count from 45 to 48.
  - `freqai_bridge/test_http_candles.py`: add 3 tests covering exact 100-candle M15, exact 100-candle H1, and rejection above the T0 2,000-candle API limit before network access.
  - `freqai_bridge/http_candles.py`: add `CandleHttpClient.fetch_one_page()`.
- New method validates aligned timestamps/timeframe/range (1–2,000 candles), performs one bounded T0 request through the existing secure transport/retry path, applies the existing full envelope validator, and returns the original decoded envelope unchanged. It does not recompute, normalize or synthesize `datasetVersion`.
- Existing `fetch()` pagination behavior remains unchanged. No T0 API/server change.

## TDD and CI evidence

### RED

- Workflow run: `43346208499`
- Source SHA: `7f6f89528d6beb1a9a8bec19e8546d65b146215b`
- Result: expected failure. Compile passed; 48 tests ran; the two new 100-candle cases failed because `fetch_one_page` did not yet exist. The API-limit rejection test passed.
- Job: `131626080248`.

### GREEN

- Workflow: [run 43346301451](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43346301451)
- Exact source SHA: `6fc860d7f696b3faacdb87b69a9017909e6f92d9`
- Job: `131626382017`, conclusion **SUCCESS**.
- Compile: PASS.
- HTTP adapter tests: **48/48 PASS**.
- HTTP context + migration acceptance tests: **11/11 PASS**.
- HTTP-backed exporter regressions: **6/6 PASS**.
- Isolated paper-only preflight: PASS; no DB paths, exchange credentials or AI execution enabled.
- Artifact: `t2-http-adapter-6fc860d7f696b3faacdb87b69a9017909e6f92d9`
- Artifact ID: `14001207782`
- ZIP SHA-256: `0a0073b97c7428f1dbc0aa6862f36b5a0627bdcb33de5db169ce2664f7d56f82`
- Artifact expires: 2026-11-20T01:37:34Z.

## Disposition

- C1 single-response consumer method: **PASS — IMPLEMENTED AND EXACT-SHA CI VERIFIED**.
- Preservation of source `datasetVersion`: **PASS — exact envelope equality asserted for both M15 and H1 fixtures**.
- Legacy pagination regression: included in the 48-test suite; **PASS**.
- Runtime/T0 connectivity: **NOT VERIFIED**; tests use deterministic local fixtures only.
- Core runner integration/call-site use: **NOT IMPLEMENTED**.
- C2 T1 Order Book source contract/implementation: **BLOCKED / OUTSTANDING**.
- One-shot Core runner: **NOT IMPLEMENTED**.
- No T0 API/database, T1, VPS, persistent service, ledger, strategy, Shared Risk Engine, AI execution or live-trading changes.

## Next step

Review/close C1 at the architecture level, then address C2 under its separate source-side implementation authorization. Do not infer that the new client method is already used by a production or runtime decision cycle.
