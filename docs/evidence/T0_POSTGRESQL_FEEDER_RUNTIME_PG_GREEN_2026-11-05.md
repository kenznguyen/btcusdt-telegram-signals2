# T0 PostgreSQL FeederRuntime adapter — PG-GREEN candidate (2026-11-05)

## Scope

Wire the already-tested PostgreSQL lease and atomic writer into the existing FeederRuntime composition while preserving the SQLite path. PostgreSQL lease expiry remains authoritative on the database clock; FeederRuntime's legacy `now_ms` values are deliberately ignored by the adapter.

No production database, VPS, real Binance API, or live Feeder activation is used in this increment.

## Source identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-atomic-write-fencing-20261105`
- Exact source head submitted to CI: `3a3e81396ec1c9d03039e0139fab260e83efedd1`
- PR: [#134](https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/134), OPEN / DRAFT / NOT MERGED.
- Base branch remains `feature/t0-centralized-data-feeder-p1-20261101`.

## Implementation

- Added `PostgresRuntimeLeaseAdapter` to adapt FeederRuntime's acquire, heartbeat, is_current, authorize_write and release calls to `PostgresLeaseStore` without forwarding the runtime clock.
- `build_runtime()` now accepts either:
  - the existing SQLite candle store + SQLite lease sharing one database; or
  - `PostgresStore` + `PostgresLeaseStore` sharing the exact same DSN.
- PostgreSQL mode creates one `PostgresWriteGateway` using the lease name, owner and live runtime generation. Scheduler and startup recovery both route through this same gateway.
- Recovery heartbeat uses the DB-clock adapter.
- `build_production_runtime()` selects `PostgresLeaseStore` for `MARKET_DATA_BACKEND=postgres`, supports `T0_FEEDER_LEASE_NAME`, and rejects a separate SQLite `T0_FEEDER_LEASE_DB` in PostgreSQL mode.
- SQLite composition remains unchanged. The selected gateway is exposed as `runtime.canonical_write_gateway` for explicit composition inspection.
- Added disposable TimescaleDB runtime integration coverage and wired it into the existing GitHub Actions TimescaleDB service job.

## Local verification

- TDD RED confirmed before implementation: import failed because `PostgresRuntimeLeaseAdapter` did not exist.
- Focused adapter + runtime lifecycle + health tests: **43 passed, 1 skipped**.
- Broader `market_data` static subset: **171 passed, 14 skipped, 3 deselected, 91 subtests passed**. The 3 deselected subprocess tests are affected by this execution environment's injected Python startup warmup, which writes a traceback to child stderr and exceeds the tests' 5-second startup limit. `test_feeder_health_api.py` was excluded because Flask is not installed in this local runtime.
- `compileall market_data`: PASS.
- Workflow YAML parse: PASS.
- The PostgreSQL runtime integration test is skipped locally because this environment has no disposable TimescaleDB service, Docker, or psycopg driver. GitHub Actions is the intended disposable TimescaleDB integration environment.

## GitHub Actions evidence

- Exact-head push run [#42027052569](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42027052569): **SUCCESS** on source SHA `3a3e81396ec1c9d03039e0139fab260e83efedd1`. Static job `127243768694` SUCCESS; TimescaleDB job `127243882931` SUCCESS.
- Push static suite: 197 tests, 14 skipped. The complete market_data unittest discovery step completed successfully.
- Push disposable TimescaleDB: PostgreSQL writer/lease contracts 7/7 PASS; PostgreSQL FeederRuntime adapter/composition/runtime integration 10/10 PASS; read-only TimescaleDB integration 6/6 PASS.
- Push artifacts: static ID `13414222523`, SHA-256 `ebb61daf23e225223ab4efcca8eb481d1e52cffbc93ca3c042a313f1b3de4e2b`; TimescaleDB ID `13414162575`, SHA-256 `77fc8ffd7a1b21ad62491c3ea353327c3ca602f820729aadba06512c8c635d23`.
- PR merge-context run [#42027061402](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42027061402): **SUCCESS**. PR source head `3a3e81396ec1c9d03039e0139fab260e83efedd1`; base `8b196d2720eab804728df7c0227c606c094b16ad`; synthetic merge checkout SHA `a0179e13a83db4a18aa03e1518647e1f32379b0a`. Static job `127243954898` SUCCESS; TimescaleDB job `127244083814` SUCCESS.
- PR merge-context static suite: 197 tests, 14 skipped. Disposable TimescaleDB: writer/lease 7/7 PASS; FeederRuntime adapter/composition/runtime integration 10/10 PASS; read-only integration 6/6 PASS.
- PR artifacts: static ID `13414885785`, SHA-256 `a01a42aba6db339b9aa082d021d0694d8e7a17756e616f4d6521883b0bd2e58d`; TimescaleDB ID `13413668679`, SHA-256 `4e2d5289f4550c026e42c2f2752fd4fec7b9e30430aadd88511baea0b92654da`.
- Earlier exact-head runs #42026587449 and #42026596306 failed in the newly added integration test due to a missing import of `EXCHANGE` and `MARKET_TYPE`. Commit `3a3e81396ec1c9d03039e0139fab260e83efedd1` corrected the test import; both exact-head push and PR workflows above then passed.
- The branch head after this evidence-only update may advance; implementation source tested by both successful workflows remains `3a3e81396ec1c9d03039e0139fab260e83efedd1`.

## Audit note

An intermediate commit `a7646361447fd9e1d386197dece76f0134a84dba` briefly wrote a placeholder into `market_data/feeder_service.py` during the first standard GitHub contents update. It was immediately superseded by corrective commit `99160093dc68223edc20d627abc2f8a5ff68a262`, which restored the complete implementation from the uploaded branch source. The final tested source SHA above contains the complete implementation; no merge or deployment occurred. The intermediate commit is retained in branch history and must not be treated as a valid source state.

## Status and limits

- PostgreSQL lease adapter contracts: **PASS**.
- Runtime composition and single shared Gateway unit contracts: **PASS**.
- Production environment selection and cross-backend/DSN fail-closed contracts: **PASS**.
- Existing SQLite lifecycle/health regression: **PASS**.
- Disposable TimescaleDB FeederRuntime integration: **PASS** (push + PR merge-context).
- Full local `market_data` suite: **NOT VERIFIED** due to local dependency/startup environment limitations noted above.
- VPS, production role separation/grants, backup/restore, RPO/RTO, canonical database creation, real Binance connectivity, and production Feeder activation: **NOT STARTED / NOT AUTHORIZED IN THIS INCREMENT**.
- `ai_execution_enabled=false`; no order execution.

## Next step

Both exact-head push and PR merge-context workflows passed. Next: update the main handoff and continue P0 production architecture with database role separation/grants and backup/restore acceptance design. Do not create a production canonical DB or activate the Feeder in this increment.
