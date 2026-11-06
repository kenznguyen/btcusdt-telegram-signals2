# T0 provider-neutral staging acceptance checklist

## Status and authorization boundary

- Status: **Prepared — NOT EXECUTED; staging not provisioned; no production authorization**.
- Scope: validate the T0 PostgreSQL/TimescaleDB security, writer fencing, TLS, credential rotation, backup/restore, and operational recovery design against one selected provider.
- This checklist is provider-neutral. It does not select a provider, region, plan, VPS, cost, network topology, or database endpoint.
- All executable acceptance must use an isolated staging database, synthetic candles, and non-production credentials. No production canonical database or real Binance ingestion is needed for these tests.
- GitHub Actions remains the default CI/evidence platform. Codemagic is fallback only when GitHub Actions is unavailable or materially constrained.
- T0 remains independent of Paper DB and SWG-F. No Paper DB migration, Paper writer token, or Paper state mutation is permitted.
- `ai_execution_enabled=false`; no exchange order permissions, live order endpoints, or trading credentials are in scope.

## 1. Entry gate — decisions required before staging provisioning

Do not provision staging until the operator has selected and recorded:

- [ ] Provider and exact managed PostgreSQL product/tier.
- [ ] Provider region and data residency.
- [ ] PostgreSQL major version and TimescaleDB extension/version actually available on that tier.
- [ ] Private networking / ingress model and how the Feeder host reaches the database.
- [ ] TLS CA delivery and rotation mechanism.
- [ ] Secret manager and credential rotation mechanism.
- [ ] Backup/PITR product, retention, recovery-point visibility, and restore permissions.
- [ ] Staging and eventual production monthly cost ceilings, including database, VPS, storage, backups, egress, and snapshots.
- [ ] Staging data classification: synthetic only; no production credentials or personal data.
- [ ] Exact source SHA and workflow required for the staging candidate.

**Entry decision:** all items above recorded and reviewed. If a provider cannot offer remote TLS hostname verification, least-privilege roles, isolated restore, and old-primary fencing, reject it rather than weakening controls.

## 2. Gate A — provider and engine identity

Capture machine-readable evidence:

- [ ] Provider, product, region, plan/tier, database endpoint class (private/public), PostgreSQL version, TimescaleDB version, extension availability.
- [ ] Database parameter settings relevant to TLS, logging, connection limits, timeouts, WAL/PITR, and backups.
- [ ] The exact source SHA, migration IDs/checksums, workflow run URL, job IDs, and artifact IDs.
- [ ] Confirm staging is isolated from production projects/accounts/endpoints and has a documented deletion process after evidence retention.
- [ ] Confirm no credentials or DSNs appear in logs, workflow artifacts, Git history, command arguments, or handoff documents.

**PASS criteria:** identity is unambiguous and reproducible; the provider product/version supports every mandatory capability. A marketing-page feature list is not evidence of the actual provisioned tier.

## 3. Gate B — TLS, network, and credential controls

Use a dedicated staging Feeder identity and a separate temporary migration identity.

### TLS positive and negative tests

- [ ] Valid provider CA chain + exact DNS hostname + `sslmode=verify-full`: remote connection succeeds.
- [ ] Wrong hostname / certificate SAN mismatch: connection fails.
- [ ] Untrusted or expired CA/certificate: connection fails.
- [ ] `sslmode=disable`, `allow`, `prefer`, or `require`: production runtime configuration rejects it.
- [ ] Missing hostname or Unix-domain socket DSN: production runtime configuration rejects it.
- [ ] Record TLS protocol, peer certificate subject/SAN, issuer, validity interval, and verification outcome without recording secrets.

### Network tests

- [ ] Database ingress accepts only the selected private network or exact approved source addresses.
- [ ] Unapproved source network cannot connect.
- [ ] No public unauthenticated database endpoint exists.
- [ ] Feeder egress is limited to the database and required Binance USD-M market-data endpoints; no order endpoints or credentials exist.
- [ ] Test that a network interruption causes readiness to fail closed and does not switch to an unfenced fallback writer.

### Rotation test

1. Create replacement Feeder credential while old credential is still valid.
2. Validate the replacement from the intended Feeder host.
3. Switch service to replacement credential and verify lease, heartbeat, write, and readiness.
4. Revoke old credential.
5. Prove old credential can no longer connect or mutate state.
6. Record elapsed time, any ingestion gap, and final credential state.

**PASS criteria:** all positive tests succeed, all negative tests fail closed, and old credentials are unusable after revocation. Do not copy credential values into evidence.

## 4. Gate C — roles, grants, and privilege boundaries

Provision the roles from the approved T0 design using the provider's actual role model. Do not assume managed-provider roles behave exactly like vanilla PostgreSQL.

### Required effective privilege checks

- [ ] Feeder has CONNECT and schema USAGE only as required.
- [ ] Feeder has no direct SELECT/INSERT/UPDATE/DELETE/TRUNCATE on `feeder_leases`.
- [ ] Feeder has no direct INSERT/UPDATE/DELETE/TRUNCATE on `candles`; it can write only through the fenced SECURITY DEFINER API.
- [ ] Feeder can acquire/heartbeat/release/check only `binance-btcusdt-canonical`.
- [ ] Reader can SELECT approved candle read surfaces only; it cannot read or mutate leases or write candles.
- [ ] Migration login is temporary, belongs only to the restricted `t0_migrator` role, and is revoked/dropped after migration.
- [ ] Runtime logins are not members of `t0_db_owner`, `t0_migrator`, SECURITY DEFINER owner roles, `pg_write_all_data`, or privileged provider roles.
- [ ] SECURITY DEFINER owner roles remain NOLOGIN, non-superuser, non-createrole, non-bypass-RLS, and are not granted to runtime logins.
- [ ] No unintended PUBLIC privileges; default privileges for future objects remain restrictive.
- [ ] No unexpected role memberships, ADMIN OPTION, database/schema CREATE, TEMP, or extension privileges.
- [ ] Feeder cannot connect to or write the Paper DB.

### Negative execution tests

Attempt each forbidden operation using the actual Feeder and Reader credentials, not an admin connection:

- [ ] DDL in `market_data` and `public`.
- [ ] Direct lease-table SELECT and DML.
- [ ] Direct candle INSERT/UPDATE/DELETE/TRUNCATE.
- [ ] Access to unrelated schemas/databases.
- [ ] Grant/revoke role membership or alter role.
- [ ] Execute an unapproved function or write using an alternate lease identity.
- [ ] Modify Paper DB or use its SQLite path as a T0 lease store.

**PASS criteria:** all intended operations work and every forbidden operation fails with privilege denial. Capture effective grants and role membership query output alongside negative-test logs.

## 5. Gate D — writer fencing and runtime lifecycle

Run against the selected provider's exact engine/extension version with separate Feeder sessions/processes.

- [ ] One Feeder acquires the canonical lease and receives generation N.
- [ ] A second Feeder cannot acquire while N is active.
- [ ] Heartbeat extends expiry using database time, not host wall clock.
- [ ] After expiry, a replacement acquires generation N+1.
- [ ] Old owner/generation cannot heartbeat, release, or write after takeover.
- [ ] A batch write locks/checks the lease and commits atomically; lease loss rolls back the whole batch.
- [ ] Identical duplicate candles are idempotent; same-key/different-values conflicts are rejected without overwriting canonical history.
- [ ] A write racing expiry/takeover is serialized so the new generation cannot begin writing until the old transaction has committed or rolled back.
- [ ] Kill the Feeder process during a write; verify transaction rollback/atomicity and safe generation takeover.
- [ ] Kill the Feeder process during recovery; restart acquires a higher generation and repairs only the bounded missing closed-candle window.
- [ ] Heartbeat loss closes readiness and stops scheduler admission.
- [ ] Shutdown closes admission before waiting, uses one monotonic deadline, drains in-flight work, and releases only the exact current generation after successful drain.
- [ ] Heartbeat/drain timeout retains the lease and reports a visible non-ready state.
- [ ] Startup recovery and scheduled sync use the same fenced write gateway.
- [ ] No alternate unfenced write path or implicit schema migration is selected.

**PASS criteria:** all fencing, process restart, lifecycle, atomicity, and readiness tests pass on the provider-specific staging engine. No two active writers can commit concurrently to the same canonical database.

## 6. Gate E — data integrity and SQLite parity

SQLite remains the source of truth until a separate, approved migration/cutover decision. The Paper ledger is not copied into T0.

- [ ] Take a consistent SQLite market-data snapshot and preserve it unchanged.
- [ ] Run SQLite integrity check and record counts, keys, timeframe distribution, time range, gaps, duplicate/conflict findings, Decimal samples, and canonical dataset hashes.
- [ ] Apply versioned PostgreSQL migrations; record migration IDs and SHA-256 checksums.
- [ ] Verify hypertable identity/key constraints, timeframe alignment, closed-candle/availability constraints, OHLCV constraints, and Decimal precision.
- [ ] Load only the approved synthetic fixture for staging acceptance; any later parity exercise uses a consistent snapshot and a separately approved scope.
- [ ] Compare SQLite/PostgreSQL responses for fixed windows and `as_of_ms`: candle keys, exact decimal values, ordering, gaps, coverage, availability, and `datasetVersion`.
- [ ] Confirm no fabricated historical `available_at_ms` and no fabricated ingestion provenance.
- [ ] Verify restartable/idempotent bounded batches and all-or-nothing conflict handling.
- [ ] Verify the public read API contract and authentication are unchanged.
- [ ] Confirm Paper DB tables, counts, hashes, and behavior are unchanged.

**PASS criteria:** all canonical outputs match byte-for-byte where the contract requires identical serialization/hash; every unexplained mismatch blocks migration/cutover.

## 7. Gate F — backup, PITR, restore, and old-primary fencing

The backup failure domain must be independent of the Feeder VPS and primary database failure domain.

### Backup capability

- [ ] Provider confirms automated base backup and continuous WAL/PITR (or an equivalent mechanism proven to meet the RPO).
- [ ] At least 7 days of recovery history is available and visible on the selected plan.
- [ ] Backups are encrypted in transit and at rest; key control is separate from Feeder credentials.
- [ ] Feeder cannot delete, overwrite, shorten retention, or alter backup policies.
- [ ] Backup health, latest recoverable point, archive lag, retention, and last successful restore are observable.
- [ ] A separate encrypted logical export of T0 schema and migration metadata is available for portability; it is not treated as a replacement for PITR.

### Timed restore drill

1. Seed a known synthetic dataset and record a durable marker for each committed write.
2. Record the incident declaration time and chosen recovery point.
3. Restore into a separate isolated endpoint; do not connect the Feeder.
4. Verify engine/extension compatibility, migration checksums, integrity, row/key ranges, decimal values, gaps, and canonical hashes.
5. Determine the newest committed marker present in the restored database and calculate actual RPO.
6. Fence the former primary and every old Feeder instance. Prove the old endpoint/credential cannot accept a writer.
7. Invalidate the restored lease and advance the generation before allowing a new Feeder to start.
8. Rotate the Feeder credential; prove old credentials fail.
9. Start exactly one Feeder on the restored endpoint; verify new generation, bounded recovery, and readiness.
10. Record restore start/end, read-service verification, healthy Feeder time, actual RTO, actual RPO, and all relevant SHA/run/artifact references.

### Measurable acceptance thresholds

| Measure | Target | Evidence |
|---|---:|---|
| PITR history | >= 7 days | Provider configuration + selectable recovery point |
| RPO | <= 5 minutes | Incident timestamp vs newest committed marker restored |
| RTO | <= 60 minutes | Incident declaration vs verified read service + one healthy Feeder |
| Restore integrity | 100% of recorded keys/values/hashes | Machine-readable parity report |
| Old-primary fencing | 0 successful old-writer connections after fence | Connection/write denial evidence |
| Lease recovery | New generation strictly greater than restored/old generation | SQL query + Feeder event log |
| Backup isolation | Feeder cannot mutate/delete backups | Negative permission test |

If RPO or RTO misses target, record **BLOCKED**. Do not silently weaken the targets or infer capability from provider marketing. Any revised objective requires explicit operator approval.

## 8. Gate G — operational readiness and rollback

- [ ] Feeder runs as a dedicated unprivileged OS service identity.
- [ ] Secret files/variables are protected; no secret is exposed in process arguments, shell history, logs, crash dumps, or artifacts.
- [ ] Restart policy does not create concurrent uncontrolled Feeder instances.
- [ ] Health/readiness reports DB connectivity, current lease generation state, heartbeat age, recovery coverage, backup freshness, and last restore drill.
- [ ] Missing/stale backup telemetry blocks go-live.
- [ ] Disk, connection, storage, CPU, memory, WAL, and backup capacity alerts have thresholds and owners.
- [ ] Rollback procedure is exercised: stop Feeder, fence writer credential, preserve PostgreSQL evidence, and return reads only to a verified SQLite snapshot if parity allows.
- [ ] No dual-write or automatic copy-back is used as a rollback shortcut.
- [ ] Operator has a documented incident owner, access path, and break-glass audit procedure.

## 9. Final staging verdict

A staging run is **PASS** only when Gates A–G pass on the exact selected provider/version and exact application source SHA, with reproducible artifacts.

The final evidence bundle must contain:

- Provider/region/plan and engine/extension identity (no secret values).
- Exact source SHA, migration IDs/checksums, GitHub workflow/run/job IDs.
- TLS positive/negative test logs and certificate metadata.
- Effective role/grant snapshots and privilege-denial tests.
- Writer fencing, process-kill, lifecycle, and readiness logs.
- Data parity report and canonical hashes.
- Backup configuration evidence, restore logs, actual RPO/RTO calculations, old-primary fencing proof, and new lease generation.
- Artifact IDs/digests and an explicit list of evidence not independently verified.

### Current state before provider selection

| Gate | State |
|---|---|
| Source-level PostgreSQL writer/runtime/role contracts on disposable TimescaleDB 2.17.2 | PASS |
| Runtime TLS DSN rejection logic | PASS |
| Real provider TLS handshake / CA / hostname | NOT VERIFIED |
| Provider-specific effective roles/grants | NOT VERIFIED |
| Credential rotation | NOT VERIFIED |
| Provider network isolation | NOT VERIFIED |
| Backup/PITR availability and 7-day retention | NOT VERIFIED |
| Restore drill and measured RPO/RTO | NOT VERIFIED |
| Old-primary fencing on provider failover | NOT VERIFIED |
| VPS service hardening / cost ceiling | NOT SELECTED |

No staging or production resource should be created until the entry gate is approved. No production provisioning, canonical ingestion, Binance connection, or Feeder activation is authorized by this checklist.
