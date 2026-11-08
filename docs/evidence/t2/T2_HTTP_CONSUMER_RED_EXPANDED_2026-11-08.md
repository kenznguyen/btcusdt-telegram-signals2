# T2 HTTP Consumer — Expanded RED Test Specification Evidence

- Date: 2026-11-08 (UTC)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact source / checked-out SHA: `3222c1bd56ccc089d84f2744f4bafede4747ce50`
- Test file: `freqai_bridge/test_http_candles.py`
- Workflow: `.github/workflows/t2-http-consumer-red.yml`
- Workflow run: `42468167014`
- Run URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42468065621
- Event: `push`
- Job: `Confirm T2 HTTP migration contract gaps`
- Job ID: `128692428965`
- Job conclusion: `success` because the workflow validated the explicitly expected RED state; this is not a GREEN implementation result.

## Exact-SHA execution

- Isolated preflight: PASS; DB paths and exchange credentials empty; `AI_EXECUTION_ENABLED=false`.
- HTTP test dependency install: PASS (`requests>=2.32.0,<3`).
- `python -m py_compile freqai_bridge/test_http_candles.py`: PASS.
- `python -m unittest freqai_bridge.test_http_candles -v`: 37 tests executed in 0.072 s.
- 6 intentional architecture assertion failures:
  - HTTP adapter module absent.
  - T2 context still imports `market_data.store`.
  - T2 context still calls `read_window()`.
  - Strategy still contains `canonical_db_path`.
  - Strategy still calls `canonical_context()` with the legacy DB path.
  - HTTP unavailable path is not yet proven free of SQLite/cache/venue fallback.
- 28 behavior tests were authored but blocked at import with `ModuleNotFoundError: No module named 'freqai_bridge.http_candles'`. These did not reach client behavior; they are an executable acceptance specification for the later adapter, not observed behavior failures.
- 3 assertions PASS: approved freshness formula, approved transport limits, and existing native order-signal disablement.
- No unexpected error types. Workflow verdict: `T2_HTTP_RED=CONFIRMED_ARCHITECTURE_GAPS`; `T2_HTTP_BEHAVIOR_TESTS=AUTHORED_BUT_BLOCKED_BY_MISSING_ADAPTER`; `T2_HTTP_POLICY_ASSERTIONS=PASS`.

## Behavior coverage authored

The 28 adapter-dependent tests specify:
- valid response and dataset-version preservation;
- exact BTCUSDT/M15/range/as-of request;
- Bearer header, no token in URL, no-store and identity encoding;
- timeout, TLS verification, no redirects, streaming and body limit;
- required URL/token/max-lag configuration and remote HTTP rejection;
- 1–32 aligned candle range;
- contract/schema/identity/request echo/dataset hash validation;
- coverage, timestamps, close boundary, OHLCV decimal and as-of integrity;
- 120000 ms accept / 120001 ms reject using ingestion delay;
- normal M15 age not falsely rejected and server-global expected slot treated as diagnostic;
- 401/400/404/405 no retry; 503 and transient timeout bounded retry;
- response body cap, content type, malformed JSON and secret redaction.

These tests are not proof of any of those adapter behaviors until the adapter exists and the tests execute past import.

## Artifact

- Artifact name: `t2-http-consumer-red-8bfc920a949c817fb6065657dda6663373bc2f25`.
- Artifact ID: `13611894815`.
- SHA-256 digest: `27d2f20452c19b50a9d02d0a61935e2b77071b895fa47375469d5fcc022b57ad`.
- Expires: 2026-11-15T09:40:20Z.

## Scope, verdict and limits

**RED TEST SPECIFICATION AUTHORED; ARCHITECTURE GAPS CONFIRMED; CLIENT BEHAVIOR NOT VERIFIED.**

Only test code, the isolated RED workflow, and evidence/documentation were changed. No production module, T2 runtime configuration, direct SQLite path, T0 API/store/DB, Feeder, VPS, exchange, Data Quality Gate, model training, paper order routing, deployment, or live execution was changed.

No GREEN implementation is authorized by this approval. Do not treat the 28 import-blocked tests as passing or as behavior-specific RED evidence. The next implementation increment remains separately gated. Keep `ai_execution_enabled=false`.


## Final fixture-boundary rerun

- The threshold-boundary fixtures were corrected so the as-of cutoff includes the availability timestamp being tested; the normal M15 interval fixture now uses a server generation time consistent with its server-global expected slot.
- Rerun at exact SHA `3222c1bd56ccc089d84f2744f4bafede4747ce50`, run `42468167014`, job `128692428965`: 37 tests; 6 architecture failures; 28 expected missing-adapter import errors; 3 policy/order-signal assertions PASS; zero unexpected error types. Compile, isolated preflight and expected-RED parser PASS.
- The 28 behavior cases remain blocked before client behavior because the adapter module is absent. This rerun confirms the tests and fixture structure are executable, not that the specified HTTP behaviors pass.
- Final artifact ID `13611894815`, SHA-256 `27d2f20452c19b50a9d02d0a61935e2b77071b895fa47375469d5fcc022b57ad`.
