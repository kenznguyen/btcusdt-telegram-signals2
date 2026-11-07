# T0 PostgreSQL Lifecycle Acceptance Matrix

Updated: 2026-11-07  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## 1. Scope and authorization

This matrix covers PostgreSQL/TimescaleDB lifecycle and ordinary data-integrity behavior using disposable local CI services and synthetic fixtures only.

Included:
- connection and pool behavior;
- explicit database initialization and migrations;
- writer transaction lifecycle and atomicity;
- lease acquire, heartbeat, expiry, takeover, release and fencing;
- FeederRuntime startup/recovery, readiness and shutdown/drain;
- restart behavior and controlled writer concurrency;
- fail-closed behavior when lease authority is lost.

Explicitly excluded:
- backup/PITR provisioning or validation;
- restore drills, disaster recovery, failover recovery objectives, RPO/RTO;
- offsite or immutable/WORM retention;
- provider/VPS provisioning or external provider endpoint tests;
- canonical T0 database creation, production Feeder activation, real exchange access or market-data synchronization.

All test targets must be disposable and synthetic. Do not use a production/canonical DSN, Paper DB, exchange credentials, or real market data. Preserve SQLite as the default and preserve all role/fencing guards.

## 2. Existing test coverage

The source audit on 2026-11-06 recorded these test files and contracts on the active branch. The file paths below are current source references; historical CI evidence applies only to its recorded SHA/run, not automatically to the current documentation tip.

| Lifecycle area | Existing test source | Observed coverage | Current assessment |
|---|---|---|---|
| PostgreSQL runtime composition | `market_data/test_postgres_feeder_runtime.py` | Same DSN for store/lease/gateway; scheduler and recovery share one fenced gateway; reject mixed SQLite/PostgreSQL stores; DB-clock lease adapter; TLS DSN and canonical lease identity contracts | Source coverage present; current-tip CI NOT VERIFIED |
| PostgreSQL startup recovery | `market_data/test_postgres_feeder_runtime.py` | Synthetic exchange; runtime startup recovery; scheduler reuses the same PostgreSQL fenced gateway; graceful stop/release | Historical disposable TimescaleDB integration PASS; current-tip CI NOT VERIFIED |
| Heartbeat and lease renewal | `market_data/test_postgres_feeder_runtime_lifecycle.py` | Runtime heartbeat renews lease expiry using database clock | Historical disposable TimescaleDB integration PASS (1 of 4 lifecycle tests) |
| Lease expiry/takeover and readiness | `market_data/test_postgres_feeder_runtime_lifecycle.py` | Replacement receives higher generation; old runtime enters LEASE_LOST; scheduler stops; health reports not-ready; old runtime cannot release replacement lease | Historical disposable TimescaleDB integration PASS (1 of 4 lifecycle tests) |
| Shutdown/drain timeout | `market_data/test_postgres_feeder_runtime_lifecycle.py` | Drain timeout raises and retains current lease; successful later drain releases exact generation | Historical disposable TimescaleDB integration PASS (1 of 4 lifecycle tests) |
| Restart generation | `market_data/test_postgres_feeder_runtime_lifecycle.py` | New runtime acquires a strictly higher fencing generation after clean stop | Historical disposable TimescaleDB integration PASS (1 of 4 lifecycle tests) |
| Atomic writer and rollback | `market_data/test_postgres_write_gateway.py` | Current generation commit; stale/wrong owner rejection; DB-clock expiry; duplicate idempotence; conflicting duplicate rollback; invalid middle candle; takeover waits for writer transaction; generation-bound heartbeat/release | Historical disposable TimescaleDB integration PASS (7/7) |
| Role and privilege boundary | `market_data/test_postgres_role_privileges.py` | Feeder/Reader least privilege, lease API restrictions, SECURITY DEFINER ownership, restricted migrator memberships and ADMIN OPTION checks | Historical disposable TimescaleDB integration PASS (18/18) |
| Fresh-cluster role bootstrap | `market_data/test_postgres_provider_bootstrap.py` | Clean-cluster role creation, restricted migration identity, ownership and membership assertions | BLOCKED on PostgreSQL 16 non-superuser CREATEROLE implicit ADMIN membership; keep the migration guard unchanged |
| Process restart/fencing regression | `market_data/test_feeder_process_restart.py` and static Gateway workflow | Static restart/fencing regression suite | Historical CI PASS; not equivalent to PostgreSQL process-kill-during-transaction coverage |

## 3. Historical evidence boundary

The handoff records workflow run [42166319563](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42166319563), exact tested source SHA `7c41ac990a7a0842b773a2d07b8db2f1d769a855`:
- PostgreSQL atomic writer: 7/7 PASS.
- PostgreSQL FeederRuntime/composition: 18/18 PASS.
- PostgreSQL FeederRuntime lifecycle: 4/4 PASS.
- Least-privilege role integration: 18/18 PASS.
- Read-only TimescaleDB integration: 6/6 PASS.
- Fresh-cluster provider bootstrap: BLOCKED at the existing role-safety guard due to PostgreSQL 16 non-superuser CREATEROLE semantics.

This evidence is for that exact source SHA and disposable PostgreSQL 16 / TimescaleDB 2.17.2 CI service. It does not establish provider compatibility. The active branch has advanced with later source and documentation commits; exact current-tip CI is **NOT VERIFIED** unless a later workflow proves the checked-out SHA.

## 4. Lifecycle gaps requiring explicit acceptance tests

The following cases were not established by the inspected test files/evidence and must not be inferred from adjacent tests:

| ID | Missing or incomplete scenario | Required safe assertion | Status |
|---|---|---|---|
| PG-LC-01 | PostgreSQL unavailable before runtime startup | Startup fails closed; no scheduler admission, no SQLite fallback, no lease-less writer | **PASS** — RED reproduced on SHA `514d22b`; GREEN verified on SHA `819d5f8`, static + TimescaleDB integration
| PG-LC-02 | Connection loss during heartbeat / lease checks | Runtime becomes non-ready and stops admission; no stale generation can write | **PASS** — unit regression + exact-SHA disposable TimescaleDB integration, FeederRuntime 20/20; workflow 42322039770, job 128248711729 |
| PG-LC-03 | Database disconnect during an in-flight writer transaction | Whole batch rolls back; no partial candle batch; failure is surfaced unambiguously | **PASS** — real backend termination during second-row trigger; writer 8/8, zero rows after interrupted batch; workflow 42322449766, job 128250015010 |
| PG-LC-04 | Connection establishment timeout / concurrent connection churn | Bounded failure under the adapter's per-operation connection model; no unbounded thread growth or readiness false-positive | NOT VERIFIED |
| PG-LC-05 | Database returns after transient outage | Runtime either performs an explicitly designed safe recovery or remains stopped pending restart; never resumes with stale lease | NOT VERIFIED |
| PG-LC-06 | Process termination during PostgreSQL writer transaction | No partial batch; a new owner must acquire a higher generation before writing | NOT VERIFIED |
| PG-LC-07 | Migration interruption / retry on a disposable clean database | Migration state is deterministic and fail-closed; no implicit migration from runtime constructors | PARTIAL / NOT VERIFIED |
| PG-LC-08 | Readiness during database connectivity loss (not only lease loss) | Readiness becomes false within a bounded interval and remains false until lease and DB authority are re-established | NOT VERIFIED |

Do not implement automatic reconnect/recovery behavior merely to make these tests pass. First derive the intended state machine and bounded timeout semantics from the existing runtime contract. A safe terminal failure may be correct where automatic resumption could violate fencing.

### Source-derived observations (read-only audit, 2026-11-07)

- `market_data/postgres.py::connection()` opens a new psycopg connection per operation; there is no connection pool in the current adapter. It uses `connect_timeout=5`, `statement_timeout=5000`, and `lock_timeout=5000`. Therefore, pool-exhaustion tests are not applicable unless a pool is introduced later; PG-LC-04 targets bounded connection establishment and concurrent connection churn instead.
- `FeederRuntime.start()` sets state to `STARTING`, then calls `lease_store.acquire()` before entering its startup `try` block. If PostgreSQL is unavailable and acquire raises, the exception propagates while state remains `STARTING`; the scheduler is not started, and the same runtime cannot be started again because only `NEW` is accepted. Readiness remains fail-closed, but the terminal state/diagnostic behavior is not explicitly tested. Proposed first RED test: inject a `StoreUnavailable` from acquire and assert the runtime fails closed, does not start the scheduler, does not attempt to release a lease it never acquired, and exposes a deterministic terminal state.
- `_heartbeat_loop()` already converts heartbeat exceptions to lease loss and calls `on_lease_lost()`, which stops scheduler admission. `run_once()` likewise calls `on_lease_lost()` if `is_current()` raises. Existing takeover tests cover stale/expired lease loss, but a database-connection exception path is not independently tested. Do not add automatic reconnect/resume without a separate state-machine design.

## 5. Acceptance sequence

1. Confirm the intended runtime state transitions and timeout policy for PG-LC-01 through PG-LC-08 from existing source; do not change behavior yet.
2. Add focused RED tests for one lifecycle gap at a time, using only the dedicated disposable TimescaleDB CI service and synthetic data.
3. Preserve existing passing writer, lease, role and SQLite regression contracts.
4. Implement only after the corresponding RED failure is observed and reviewed.
5. Run GitHub Actions on the exact candidate source SHA. Record PR/head SHA, checked-out SHA, run/event, job IDs/conclusions, test summaries and artifact ID/digest.
6. Reconcile the artifact payload and exact source identity before recording PASS.
7. Update this matrix and `docs/PROJECT_SESSION_HANDOFF.md` after each meaningful increment.

## 6. Current verdict and boundaries

### PG-LC-01 RED/GREEN evidence (2026-11-07)

- RED source SHA `514d22b00097f8b3af87e04904ca0f92b3a38b8d`, workflow run `42321683647`, job `128247465461`: the new test failed exactly as expected (`STARTING` observed, `FAILED` expected). RED artifact `13553666452`, digest `sha256:2c1e1ab498ef0aab199f1dce0c3e4d7f8dcd4e62ab130ce481332e16e81b9b1a`; downloaded ZIP hash matched.
- Minimal fix on source SHA `819d5f843e6d1d7cac9326b2173c9e2b01c89ce4`: catch lease-acquisition exception, transition runtime to terminal `FAILED`, re-raise original exception. No release is attempted because no lease was acquired. Scheduler and readiness remain untouched.
- GREEN workflow run `42321809275`, job `128247868529`, checked-out SHA matches `819d5f843e6d1d7cac9326b2173c9e2b01c89ce4`: full market_data suite 234 tests, 37 skipped, OK; static contracts 10/10; behavioral/feeder regressions 63/63; health/readiness 21/21; process restart 2/2.
- Disposable TimescaleDB job `128247942819`: atomic writer 7/7, FeederRuntime 19/19 (includes PG-LC-01), lifecycle 4/4, role privileges 18/18, read-only TimescaleDB 6/6 — all PASS.
- GREEN static artifact `13553462059`, size 10,665 bytes, GitHub digest `sha256:f9d7fff493ed3767759ff67d529784ff3d11a0435699033708e50c536f2ac0a2`; downloaded ZIP SHA-256 matched.
- TimescaleDB artifact `13553532015`, size 4,286 bytes, GitHub digest `sha256:e371ec5f6cf437b9c4f4f4dca9303c8207a1528a6fdfd70465bbde4350c3ee38`; downloaded ZIP SHA-256 matched.
- Workflow overall conclusion is **FAILURE** only because fresh-cluster PostgreSQL 16 non-superuser bootstrap job `128247868783` remains BLOCKED by the known implicit ADMIN membership (`t0_migrator` is granted to bootstrap login, contrary to the strict guard). Do not weaken the guard. Provider bootstrap artifact `13553820702`, digest `sha256:13ca3c7b578d21ebcc87f319c58d07746d3ab2666505a165870a36fede984b69`; downloaded ZIP hash matched.


### PG-LC-01 RED evidence (2026-11-07)

- Test added at source SHA `514d22b00097f8b3af87e04904ca0f92b3a38b8d`: `FeederRuntimeStartupFailureTest.test_database_unavailable_during_lease_acquire_fails_closed`.
- GitHub Actions run `42321683647`, job `128247465461` (`Static Gateway contract verification`), checked-out SHA equals test source SHA. Compile, static contracts, behavioral/feeder regressions, health/readiness and process SIGKILL tests passed; complete market_data suite failed on the intended new RED assertion.
- Exact assertion: expected `runtime.state == FAILED`, observed `STARTING` after `StoreUnavailable` from `lease_store.acquire()`. Full suite: 234 tests, 1 failure (the intended RED), 37 skipped.
- Artifact `13553666452`, name `t0-swg-contract-evidence-514d22b00097f8b3af87e04904ca0f92b3a38b8d`, size 10,877 bytes, GitHub digest `sha256:2c1e1ab498ef0aab199f1dce0c3e4d7f8dcd4e62ab130ce481332e16e81b9b1a`; downloaded ZIP SHA-256 independently matched the GitHub digest.
- This confirms the startup state defect. No runtime fix has yet been made. Overall workflow remains in progress at the time of this record; do not label the workflow PASS.


- Existing PostgreSQL writer/runtime/role integration: historical PASS on the exact SHA and run stated above.
- Fresh-cluster PostgreSQL 16 non-superuser CREATEROLE bootstrap: BLOCKED; do not weaken the role guard.
- Connection interruption, pool exhaustion, in-flight disconnect, process kill during PostgreSQL transaction and post-outage behavior: NOT VERIFIED.
- Current branch-tip CI: NOT VERIFIED.
- Exact managed-provider compatibility: NOT VERIFIED; no provider selected.
- Backup/DR: DEFERRED — NOT IN CURRENT SCOPE.
- PostgreSQL staging, VPS, canonical database and production Feeder: NOT AUTHORIZED.
- T0 remains independent; `ai_execution_enabled=false`; paper-only; no live orders.

Next permitted work: review the PG-LC state machine and choose the first isolated RED test. No provider provisioning, runtime activation, canonical DB, exchange connection or market-data sync is implied by this matrix.
