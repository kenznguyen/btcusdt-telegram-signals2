# T0 production security, backup and recovery architecture

## Status

- Status: **P0 proposal — design only; not production authorization**.
- Applies to the independent T0 canonical market-data database and its VPS Feeder.
- Canonical source remains Binance USD-M BTCUSDT, stored identity `binance / USDT_PERPETUAL / BTCUSDT`, timeframes M15/H1.
- T0 database ownership is independent from the Paper DB and SWG-F writer admission state.
- No database, VPS, credential, network rule, migration, backup job, or Feeder service is created or changed by this document.
- PostgreSQL runtime adapter and atomic writer are implemented and pass disposable TimescaleDB CI; production role grants and recovery remain unverified.

## 1. Security principals and privilege boundaries

Use separate PostgreSQL roles. Do not reuse one login for migrations, ingestion, read APIs, backup, and administration.

| Principal | Login policy | Allowed scope | Explicitly denied |
|---|---|---|---|
| `t0_db_owner` | NOLOGIN | Owns `market_data` schema, tables, migration history | Application login; routine Feeder use |
| `t0_migrator` | NOLOGIN group role; a separate ephemeral LOGIN is temporarily granted membership in this role for a controlled migration window | Apply approved, checksum-verified migrations | Feeder runtime; public API; persistent credentials on VPS |
| `t0_feeder` | LOGIN, dedicated secret | Connect to the one T0 database; schema USAGE; membership in `t0_feeder_writer` and `t0_feeder_lease_manager` for EXECUTE on fenced candle-write and lease-transition/lease-validity functions; no direct lease-table access | Direct INSERT/UPDATE/DELETE/TRUNCATE on `feeder_leases` or `candles`, DDL, DROP, role grants, extension management, other schemas, Paper DB |
| `t0_reader` | LOGIN, separate secret per consumer where practical | Connect; schema USAGE; SELECT on explicitly approved canonical read tables/views | Any write, lease access, DDL, migration |
| Backup identity | Prefer provider-managed backup/PITR identity outside SQL login; if logical export is required, dedicated read-only identity | Read required T0 objects and migration metadata | Feeder lease mutation, DDL, application write, Paper DB |
| `t0_admin` | Human/provider break-glass, MFA, audited, time-limited | Emergency maintenance only | Routine application configuration |

### Required grant posture

### Controlled migration identity

Before applying migrations, a separate bootstrap/break-glass identity provisions the NOLOGIN roles `t0_db_owner`, `t0_migrator`, `t0_feeder_writer`, `t0_candle_writer_owner`, `t0_feeder_lease_manager`, and `t0_lease_manager_owner`. The bootstrap identity also creates the target database owned by `t0_db_owner` and installs the approved TimescaleDB extension. The NOLOGIN `t0_migrator` role receives membership in `t0_db_owner` and the two SECURITY DEFINER owner roles. A separate ephemeral LOGIN receives membership only in `t0_migrator` for the migration window; it is not granted either function-owner role directly. `t0_migrator` is the sole explicitly allowed direct member of the two owner roles; the migration runner and SQL migrations reject every other direct member. After migrations and checksum verification, revoke the ephemeral LOGIN's membership in `t0_migrator`, then revoke the three memberships held by `t0_migrator` and drop/disable the ephemeral LOGIN. The Feeder login must never be a member of either function-owner role. The migration runner does not need persistent CREATEROLE or superuser privileges when all roles and the extension have been pre-provisioned.


- Revoke unnecessary privileges from `PUBLIC`; do not grant database-wide write privileges to application roles.
- `t0_feeder` must not be a member of `t0_db_owner`, `t0_migrator`, `pg_write_all_data`, or any superuser role.
- Grant privileges explicitly. The Feeder login receives no direct privilege on `feeder_leases`; it uses narrowly scoped SECURITY DEFINER acquire/heartbeat/release/current-check functions through `t0_feeder_lease_manager`. It also uses `t0_feeder_writer` for the fenced candle-write function. It must not receive direct SELECT/INSERT/UPDATE/DELETE/TRUNCATE on `feeder_leases` or direct candle write privileges. It must not receive direct INSERT/UPDATE/DELETE/TRUNCATE on `market_data.candles` or schema CREATE. The SECURITY DEFINER owner role—not the Feeder login—holds the narrowly scoped candle SELECT/INSERT privileges.
- `t0_reader` receives SELECT only on approved read surfaces; it must not read or mutate lease ownership.
- The runtime always generates a fresh high-entropy owner capability per process. `T0_FEEDER_OWNER_ID` is rejected; do not configure a shared owner token or include generated capabilities in logs. The Feeder login has no direct lease-table SELECT.
- Fix each login's `search_path` to a trusted schema and fully qualify security-sensitive SQL. Revoke CREATE on shared schemas from application roles.
- Apply default privileges for future tables so new objects do not silently become accessible to PUBLIC or application logins.

### Privileges derived from the current runtime SQL

Reviewed against `market_data/postgres.py`, `market_data/feeder_service.py`, `market_data/storage.py`, and migration `002_t0_feeder_leases.sql` at the PG-RUNTIME-ADAPTER implementation SHA `3a3e81396ec1c9d03039e0139fab260e83efedd1`:

- Database: `CONNECT` for Feeder and reader identities; no `CREATE` or `TEMPORARY` needed by the current application path.
- Schema `market_data`: `USAGE` only for Feeder and reader. No `CREATE`.
- `market_data.feeder_leases`: Feeder receives no direct table privileges. Acquire/heartbeat/release/expiry takeover and initial row creation run through SECURITY DEFINER functions owned by the dedicated NOLOGIN `t0_lease_manager_owner`; lease-validity checks also run through a SECURITY DEFINER function. The Feeder login has EXECUTE only through `t0_feeder_lease_manager`, and cannot read or mutate lease ownership directly. Reader receives no lease-table privileges.
- `market_data.candles`: the Feeder login receives no direct write privilege. It receives `EXECUTE` on `market_data.write_canonical_candle()` through membership in `t0_feeder_writer`; the SECURITY DEFINER function runs as the dedicated NOLOGIN `t0_candle_writer_owner`, which has only `SELECT, INSERT` on candles and the lease privileges required to lock/check fencing state. The function checks lease owner/generation/expiry, inserts missing rows, treats exact duplicates as idempotent, and rejects conflicting candle values. Reader receives `SELECT` only.
- Migration metadata/schema DDL is not used by the runtime. `PostgresStore.initialize()` is read-only/no-op and migrations are explicitly applied through the migration command. Therefore Feeder must not own schema/tables and must not receive CREATE/ALTER/DROP or extension privileges.
- Current code selects PostgreSQL DSN from `MARKET_DATA_POSTGRES_DSN`. The older design document names `MARKET_DATA_DATABASE_URL`; that naming mismatch is a deployment blocker until docs/config are reconciled in a separately reviewed change. Do not set both or silently introduce an alias.
- These grants are a source-derived minimum hypothesis, not yet database acceptance. Verify them with role-based integration tests, including negative tests and the exact provider/extension version, before production.

- Verify actual effective privileges using `has_database_privilege`, `has_schema_privilege`, `has_table_privilege`, role membership queries, and negative integration tests. A written grant list alone is not acceptance evidence.
- Keep migration ownership separate from runtime ownership. Runtime must fail closed if a required migration is missing or has a checksum mismatch.

The exact grants must be derived from SQL statements executed by the current runtime and tested against the selected PostgreSQL/TimescaleDB version before they are frozen. Do not guess grants from role names.

## 2. Credential and network controls

- Store DSNs/passwords in the selected VPS/provider secret manager or protected service environment; never commit them to GitHub, workflow YAML, artifacts, logs, shell history, or evidence documents.
- Use distinct credentials for Feeder, readers, migration, and break-glass. No shared admin DSN in `.env` for routine runtime.
- Require TLS with certificate and hostname verification (`sslmode=verify-full` where supported); reject plaintext remote database connections.
- Restrict database ingress to the VPS private network or fixed, explicitly approved source addresses. Do not expose PostgreSQL publicly to the internet.
- Restrict outbound Feeder access to required Binance USD-M market-data endpoints and the database endpoint. No exchange order endpoint or trading credential is required for T0 ingestion.
- Use OS service identity with least privilege; protect environment files (owner-only read), disable core dumps where they could contain secrets, and ensure logs redact DSNs/tokens.
- Rotation must be testable without an unbounded ingestion outage: provision replacement credential, validate it, switch service, verify health, then revoke old credential. Record rotation time and result.
- GitHub Actions is the default CI/evidence system. Codemagic may be used only as an explicit fallback when GitHub Actions is unavailable or materially constrained; it is not the assumed deployment or execution platform.

## 3. Backup design

Production backup must be independent of the VPS failure domain and the primary database failure domain.

Required capabilities:
- Provider-managed automated base backups plus continuous WAL/PITR, or an equivalently proven mechanism for the selected provider.
- Encrypted backup at rest and encrypted transport; keys managed separately from the database host.
- At least 7 days of point-in-time recovery history for the initial operating profile. Longer retention is a separate cost/retention decision.
- A periodic logical export of the T0 schema and migration metadata for portability, in addition to physical/PITR backup. Logical export is not a substitute for PITR.
- Backup destination/account/project must not be writable by the Feeder identity and must not share the VPS disk as its only copy.
- Backup completion, age, WAL/archive health, retention, and last successful restore must be observable. Missing or stale backup state is a readiness/operations warning and blocks production go-live.
- Do not back up secrets into the database backup. Preserve configuration templates and version identifiers separately, with secret values held in the secret manager.

### Backup schedule proposal

- Continuous WAL archiving/PITR when supported by the chosen provider.
- Daily automated recovery point/base backup.
- Weekly encrypted logical export of `market_data` schema and migration history.
- Monthly restore drill in an isolated database, and an additional restore drill after a major schema migration or provider change.
- Alert if the last verified recovery point is older than the approved RPO or if the last restore drill exceeds the approved interval.

These are target controls, not claims about any provider plan. The chosen provider must demonstrate the capabilities and actual retention before approval.

## 4. Restore and failover safety

A restore is not complete merely because PostgreSQL accepts connections.

1. Declare incident and stop the Feeder service. Prevent automated restart.
2. Fence the old primary and all old Feeder instances: revoke/rotate old credentials or enforce network isolation; confirm no old writer can reach either the old or restored database.
3. Restore into an isolated target endpoint from the selected recovery point. Do not point the live service at it yet.
4. Verify engine/extension compatibility and migration checksums. Run database integrity checks and canonical row/key-range/count checks.
5. In a controlled transaction, invalidate restored lease ownership before any Feeder can start: clear owner, set an expired finite timestamp, and advance the lease generation/epoch using the supported lease schema. Confirm no restored lease is considered current.
6. Rotate the Feeder credential before reconnecting. Use a new service identity/secret where practical.
7. Run read-only verification: M15/H1 coverage, gaps, duplicate/conflict checks, timestamp bounds, Decimal values, and representative canonical dataset hashes.
8. Start one Feeder instance only. Verify it acquires a new lease generation, performs a bounded recovery window, and becomes healthy only after recovery coverage is complete.
9. Verify consumers read from the intended endpoint and record recovery point, restore duration, data-loss window, migration version, new lease generation, and exact application SHA.
10. Keep the former primary isolated until an explicit disposition decision. Never allow two writable canonical primaries.

If the provider cannot prove old-primary fencing, the restore/failover is BLOCKED. Do not use lease generation alone as a split-brain defense across two independent database endpoints.

## 5. Proposed RPO/RTO service objectives

Initial proposed targets for operator review:

| Measure | Proposed target | Measurement |
|---|---:|---|
| RPO | <= 5 minutes | Difference between incident time and newest recoverable committed canonical write |
| RTO | <= 60 minutes | From declared incident to verified read service and one healthy Feeder on restored primary |
| Backup restore drill | At least monthly | Timed isolated restore with integrity/parity evidence |
| Backup recovery-point age | <= 5 minutes where continuous WAL/PITR is available | Provider backup/WAL telemetry |
| Feeder recovery after restore | Bounded and observable | Closed-candle coverage check before readiness |

These are proposed service objectives, not proven guarantees. A provider without continuous WAL/PITR may not meet the RPO. If staging cannot demonstrate both targets, production approval must either remain blocked or the operator must explicitly approve revised objectives and their data-loss/availability trade-off. Do not silently weaken targets to fit a low-cost plan.

RPO excludes candles not yet observed/committed by T0. It does not authorize fabricating historical `available_at_ms` values after recovery.

## 6. Staging acceptance matrix

All tests use a disposable PostgreSQL/TimescaleDB staging database, synthetic candles, and non-production credentials.

### Role/grant tests
- Migration identity can apply an approved migration; Feeder and reader cannot.
- Feeder can acquire/heartbeat/release only the fixed `binance-btcusdt-canonical` lease and write through the fenced gateway; direct function calls using any alternate lease identity fail closed.
- Feeder cannot CREATE/DROP/ALTER objects, TRUNCATE/DELETE candles, grant roles, access unrelated schemas, or write Paper DB.
- Reader can execute approved reads but cannot SELECT/UPDATE lease state or write any canonical table.
- PUBLIC has no unintended access; default privileges remain least-privilege after a new test table is created.
- No login/runtime role other than the temporary `t0_migrator` identity is a member of either SECURITY DEFINER owner role; a fresh database migration succeeds as `t0_migrator` after bootstrap provisioning.
- Credential rotation works; old credential fails after revocation.
- Remote TLS hostname/certificate verification succeeds; invalid certificate and unapproved source network fail closed.

### Backup/restore tests
- Create a known synthetic dataset and record row counts, key ranges, gaps, decimal samples, and canonical hashes.
- Produce a recovery point; restore into a separate isolated database.
- Verify all recorded data and hashes match exactly.
- Demonstrate restored lease invalidation and generation advance.
- Demonstrate old Feeder credentials and old primary endpoint are fenced before new writer starts.
- Measure restore time and recoverable data-loss window; record actual RTO/RPO.
- Verify backup retention and that Feeder cannot delete or alter backup objects.
- Repeat after a schema migration to prove migration checksums and restore compatibility.

### Operational tests
- Restart service with valid credentials and verify single-writer lease.
- Simulate DB loss/connection failure; readiness fails closed and no alternate unfenced writer is selected.
- Simulate backup telemetry missing/stale; operations status reports degraded and blocks go-live.
- Confirm no secrets appear in logs, CI artifacts, process arguments, or Git history.
- Confirm no order endpoint, order credential, live trading, Paper DB mutation, or strategy parameter change is involved.

## 7. Production go-live blockers

Production canonical DB creation, real Binance ingestion, and Feeder activation remain blocked until all are true:

- Provider and VPS are selected with explicit cost ceiling and region.
- Staging role/grant negative tests pass on the exact provider engine/extension version.
- TLS, ingress allowlist, secret storage, and credential rotation pass.
- Backup/PITR and isolated restore pass with measured RPO <= 5m and RTO <= 60m, or revised objectives are explicitly approved.
- Old-primary fencing and restored-lease invalidation pass.
- Existing PG writer/runtime CI remains green on the exact candidate SHA.
- Binance market-data-only connectivity is validated without order permissions.
- Operator approves the exact database target, VPS, cost, deployment window, and activation step.

No individual item in this document is production authorization. PR merge, database creation, exchange connectivity, and Feeder activation are separate approvals.

## 8. Rollback

- Before production data ingestion: remove staging resources only after preserving evidence; no canonical data rollback is needed.
- After any future production ingestion: stop Feeder, fence writer credentials, preserve the PostgreSQL database and logs, and route reads back only to a verified SQLite snapshot if the parity/consistency contract allows it. Do not silently dual-write or copy partial state back.
- Do not delete PostgreSQL or SQLite source data during incident response.
- Strategy execution remains paper-only; `ai_execution_enabled=false`.
