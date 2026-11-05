# T0 PostgreSQL FeederRuntime adapter — PG-GREEN candidate (2026-11-05)

## Scope

Wire the already-tested PostgreSQL lease and atomic writer into the existing FeederRuntime composition while preserving the SQLite path. PostgreSQL lease expiry remains authoritative on the database clock; FeederRuntime's legacy `now_ms` values are deliberately ignored by the adapter.

No production database, VPS, real Binance API, or live Feeder activation is used in this increment.

## Source identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-atomic-write-fencing-20261105`
- Exact source head submitted to CI: `61813f3d74162d82b0bee505a05f8181da82566d`
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

- Exact-head push run [#42026587449](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42026587449): Static Gateway contract job **SUCCESS**; TimescaleDB integration job was **IN PROGRESS** when this report was prepared.
- Exact-head pull-request run [#42026596306](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42026596306): Static Gateway contract job **SUCCESS**; TimescaleDB integration job was **IN PROGRESS** when this report was prepared.
- Exact source SHA for both runs: `61813f3d74162d82b0bee505a05f8181da82566d`.
- Artifact IDs and final job conclusions: pending; update this report after workflow completion.

## Audit note

An intermediate commit `a7646361447fd9e1d386197dece76f0134a84dba` briefly wrote a placeholder into `market_data/feeder_service.py` during the first standard GitHub contents update. It was immediately superseded by corrective commit `99160093dc68223edc20d627abc2f8a5ff68a262`, which restored the complete implementation from the uploaded branch source. The final tested source SHA above contains the complete implementation; no merge or deployment occurred. The intermediate commit is retained in branch history and must not be treated as a valid source state.

## Status and limits

- PostgreSQL lease adapter contracts: **PASS**.
- Runtime composition and single shared Gateway unit contracts: **PASS**.
- Production environment selection and cross-backend/DSN fail-closed contracts: **PASS**.
- Existing SQLite lifecycle/health regression: **PASS**.
- Disposable TimescaleDB FeederRuntime integration: **PENDING CI**.
- Full local `market_data` suite: **NOT VERIFIED** due to local dependency/startup environment limitations noted above.
- VPS, production role separation/grants, backup/restore, RPO/RTO, canonical database creation, real Binance connectivity, and production Feeder activation: **NOT STARTED / NOT AUTHORIZED IN THIS INCREMENT**.
- `ai_execution_enabled=false`; no order execution.

## Next step

Wait for exact-head push and PR workflow completion. If both PostgreSQL runtime integration jobs pass, update this evidence and `docs/PROJECT_SESSION_HANDOFF.md` with exact run/job/artifact IDs and hashes. If either fails, fix the failing contract before proceeding to VPS production architecture.
