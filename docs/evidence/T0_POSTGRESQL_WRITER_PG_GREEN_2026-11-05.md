# T0 PostgreSQL writer PG-GREEN evidence — 2026-11-05

## Scope

Implemented the first standalone PostgreSQL lease lifecycle and canonical candle write gateway following the P0 architecture and PG-RED contract tests.

This increment does NOT connect the PostgreSQL gateway to `build_runtime()` / `build_production_runtime()`, does not switch the production storage backend, and does not create a production database. It is an isolated implementation and integration-test increment only.

## Implementation

- `market_data/postgres.py`
  - Added `PostgresLeaseStore` with acquire, heartbeat, is_current, and generation-bound release.
  - Added `PostgresWriteGateway` with full batch revalidation, lease row locking, owner/generation checks, DB-clock expiry checks, idempotent duplicate handling, conflicting-candle rejection, and all-or-nothing transaction semantics.
  - Lease expiry uses PostgreSQL `clock_timestamp()`; no client wall-clock is authoritative.
  - Lease expiry is re-read in a separate query after `SELECT ... FOR UPDATE` acquires the row lock. This avoids a stale projected expiry result after waiting for a concurrent lock holder.
  - The final expiry check occurs immediately before transaction exit/commit.
  - Existing `PostgresCandleStore` remains read-only; no unfenced write methods were added to it.
- `market_data/migrations/002_t0_feeder_leases.sql`
  - Added the lease table with a monotonic generation and an explicit finite inactive expiry sentinel (1970-01-01 UTC), avoiding Psycopg's inability to load PostgreSQL timestamp `-infinity` as a Python datetime.
  - Migration remains explicit and checksum-verified; no runtime auto-migration.
- `market_data/test_postgres_write_gateway.py`
  - Seven isolated PostgreSQL writer/lease contracts.
- `.github/workflows/t0-single-writer-gateway-red.yml`
  - Runs the writer tests against the disposable local TimescaleDB service, then runs the existing read-only TimescaleDB integration tests.

## Source-pinned CI evidence

- Branch: `feature/t0-atomic-write-fencing-20261105`
- Exact tested source SHA: `3818d729ceca0577b59a22e922088b346bc42471`
- GitHub Actions run [#42021445350](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42021445350)
- Static Gateway/Feeder job `127224938761`: SUCCESS.
- Isolated TimescaleDB job `127225048939`: SUCCESS.
- PostgreSQL writer/lease contracts: 7/7 PASS.
- Existing read-only TimescaleDB integration: 6/6 PASS.
- Static full `market_data` regression: 187 tests, 13 skipped because the static job has no TimescaleDB DSN; the six existing read-only integration tests and seven writer tests ran separately in the TimescaleDB service job.
- Static job sub-suites: Gateway 10, focused Gateway/Feeder 58, Health/Readiness 21, process restart 2 — all PASS.

Artifacts:
- Static evidence ID `13411592265`; SHA-256 `de95a12b985160be04d2ce3f87a45f5d5f9d0b5ad1609123aadb00f57e0e1c2c`.
- TimescaleDB evidence ID `13412206069`; SHA-256 `84344ae6299dab5358df91bc9cab2d7aed5616627998a4f5bfdbcc43f5663c91`.

## TDD/debugging findings

1. Initial implementation used PostgreSQL timestamp `-infinity` as the inactive lease sentinel. CI exposed Psycopg `DataError: timestamp too small (before year 1)`. Replaced it with a finite UTC sentinel and re-ran the suite.
2. The first concurrency run exposed a lease-takeover race: `expires_at > clock_timestamp()` projected in the same `SELECT ... FOR UPDATE` could be evaluated before waiting for the row lock. A takeover then saw stale active status after the old writer had expired and rolled back. Fixed by acquiring the row lock first, then issuing a separate database-clock expiry query. Applied the same pattern to the writer's initial authorization.
3. Final exact-head run passed all seven writer contracts, including expiry during an in-flight write, concurrent takeover waiting, rollback, and stale-generation rejection.

## Code review and remaining boundary

- SQLite Gateway and its behavior were not modified.
- PostgreSQL writer uses one transaction for lease row lock, validation, candle writes, final expiry check, and commit.
- DB errors remain surfaced as generic `StoreUnavailable`; raw DSN or SQL details are not returned in exception text.
- The PostgreSQL writer is currently standalone. `build_runtime()` still requires a same-path SQLite CandleStore and LeaseStore; `build_production_runtime()` still constructs SQLite `LeaseStore`. The new Postgres lease API also does not yet match the current FeederRuntime method signatures. Production runtime selection/integration is therefore **NOT IMPLEMENTED**.
- Separate Migration/Feeder/Read API database roles, grant-level negative tests, PostgreSQL backup/restore, VPS provisioning, and provider-specific RPO/RTO remain NOT VERIFIED.
- The existing read-only PostgreSQL adapter remains read-only; no direct write path was enabled outside the new explicit Gateway.

## Status

- PostgreSQL lease lifecycle and standalone writer: **IMPLEMENTED; 7/7 disposable integration tests PASS**.
- Existing TimescaleDB read-only integration: **6/6 PASS**.
- Static SQLite Gateway/Feeder regression: **PASS**.
- PostgreSQL runtime composition: **BLOCKED / NOT IMPLEMENTED**.
- Role separation and permission acceptance: **NOT RUN**.
- Backup/restore: **NOT VERIFIED**.
- Production DB / VPS / Binance connection / Feeder activation: **NOT STARTED**.
- PR #134: **OPEN / DRAFT / NOT MERGED**.

## Next increment — PG-RUNTIME-ADAPTER

Define and test the shared lease protocol expected by FeederRuntime, then add a PostgreSQL runtime composition path that uses PostgresLeaseStore + PostgresWriteGateway + PostgresCandleStore against one DSN. Preserve the current SQLite composition and default behavior. Add RED tests for startup recovery, scheduler reuse of the same gateway, heartbeat, readiness, lease loss, shutdown drain, and restart/takeover using disposable TimescaleDB only. Keep migrations explicit and roles least-privilege. No production DB creation, VPS provisioning, real Binance connection, Feeder activation, or PR merge.
