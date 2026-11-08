# T2 HTTP Consumer — RED Baseline Evidence

- Date: 2026-11-08 (UTC)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact source / checked-out SHA: `d8ba2e1cf7e7e23977dc5eb0bd6484ed1d1d4745`
- Test file: `freqai_bridge/test_http_candles.py`
- Workflow: `.github/workflows/t2-http-consumer-red.yml`
- Workflow run: `42467842637`
- Run URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42467842637
- Event: `push`
- Job: `Confirm T2 HTTP migration contract gaps`
- Job ID: `128691379082`
- Job conclusion: `success` (the workflow validates a known RED baseline; this is not a GREEN implementation result).

## Executed evidence

- Isolated preflight: PASS; `MARKET_DATA_DB`, `PAPER_DB`, exchange credentials empty; `AI_EXECUTION_ENABLED=false`.
- `python -m py_compile freqai_bridge/test_http_candles.py`: PASS.
- `python -m unittest freqai_bridge.test_http_candles -v`: 7 tests executed in 0.003 s.
- Expected RED assertions: 5 failures.
  1. T2 HTTP adapter module does not exist.
  2. `freqai_bridge/context.py` still imports `market_data.store`.
  3. T2 context still calls `read_window()`.
  4. FreqAI strategy still contains `canonical_db_path`.
  5. FreqAI strategy still passes the legacy DB argument to `canonical_context()`.
- Policy assertions: 2 PASS (approved freshness formula and approved transport limits are recorded in the contract plan).
- Unexpected test errors: 0.
- Workflow parser: `T2_HTTP_RED=CONFIRMED_ARCHITECTURE_GAPS`; `T2_HTTP_POLICY_ASSERTIONS=PASS`.
- Artifact: `t2-http-consumer-red-d8ba2e1cf7e7e23977dc5eb0bd6484ed1d1d4745`.
- Artifact ID: `13612118332`.
- Artifact SHA-256 digest: `39140a7a10cf3c723c67cab728784f836a6e89446cbf0c8c2e27618704d35de8`.
- Artifact expires: 2026-11-15T09:35:37Z.

## Interpretation and limits

This run proves the currently visible architectural migration gaps at the exact checked-out source SHA. The workflow's green job status means the expected RED result was detected and recorded; the five failing assertions are intentionally not passing product tests.

This is the first RED baseline, not the full 47-case HTTP behavioral suite. It does not yet execute client-side request/auth/TLS/timeout/retry/body-cap/schema/coverage/candle/freshness/no-fallback behavior because the HTTP adapter does not exist. Those tests must be added before the later implementation is considered complete. No local Termux run was performed in this increment.

## Scope and safety

- Changed only the RED contract test file, its isolated GitHub Actions evidence workflow, and this evidence record.
- No production source, strategy, configuration, T0 API/store/database, Feeder, VPS, exchange, Data Quality Gate, or runtime was changed.
- No HTTP requests to a live T0 endpoint, DB access, model training, paper order routing, deployment, or live execution.
- T2 HTTP adapter implementation and direct SQLite removal remain NOT AUTHORIZED by this RED-only approval.
- Keep `ai_execution_enabled=false`.

## Verdict

**RED BASELINE CONFIRMED — LIMITED SCOPE.** Architecture-gap tests are observed and exact-SHA evidence is retained. Full HTTP behavior RED coverage remains incomplete; do not authorize GREEN implementation based on this baseline alone.
