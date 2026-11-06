# T0 P0 — PostgreSQL/TimescaleDB Production Architecture Decision

Date: 2026-11-05 (Asia/Ho_Chi_Minh)
Status: DESIGN PROPOSAL — NOT IMPLEMENTED / NOT APPROVED FOR PRODUCTION

## 1. Scope and guardrails

This record defines the target PostgreSQL/TimescaleDB canonical write architecture for T0. It does not merge PR #134, alter runtime code, create a database, provision a VPS, connect to Binance, start the Feeder, or authorize live trading.

- Canonical market: Binance USD-M BTCUSDT USDT perpetual (temporary selection).
- Kraken Spot remains a separate research dataset; OKX remains Shadow/non-canonical.
- T0 remains an independent data asset.
- `ai_execution_enabled=false`; no order endpoints, trading credentials, or live execution.
- Existing SQLiteWriteGateway remains the tested reference implementation and must not be weakened or removed as part of this design.
- PostgreSQL/TimescaleDB is the proposed production canonical backend, subject to disposable integration acceptance.
- GitHub Actions remains the default CI. Codemagic is fallback-only under the existing handoff rule.

## 2. Current verified source boundary

On PR #134 branch `feature/t0-atomic-write-fencing-20261105`:

- `market_data/write_gateway.py` implements SQLite-only atomic lease fencing. It requires CandleStore and LeaseStore to resolve to the same SQLite database and uses `BEGIN IMMEDIATE`, lease validation before writes, a final expiry check, and rollback on failure.
- `market_data/postgres.py` exposes a read-only PostgresCandleStore; `canonical_writes_disabled = True`. It has no `write_batch` or insert API.
- `market_data/storage.py` selects PostgreSQL for reads only; constructors do not run migrations.
- `market_data/migrations.py` applies explicit checksum-verified SQL migrations under a transaction-scoped advisory lock. Migrations are not implicit in read/write construction.
- `market_data/test_timescaledb.py` tests read-only adapter behavior and migrations against a disposable local TimescaleDB service. Fixtures seed rows directly. This is not evidence of lease-fenced canonical writes.

Therefore PostgreSQL canonical writes remain BLOCKED until the writer, lease schema, permissions, and integration tests described below exist and pass.

## 3. Proposed architecture

```text
Feeder / Recovery / Scheduler
            |
            v
    Canonical Write Gateway
            |
            v
  PostgreSQL transaction boundary
    1. Lock the single T0 lease row
    2. Verify owner + generation + expiry
    3. Insert/validate the complete candle batch
    4. Recheck expiry using database wall clock
    5. COMMIT, otherwise ROLLBACK
            |
            v
  TimescaleDB candles hypertable
```

One PostgreSQL database owns both the canonical candle rows and the T0 lease row. The lease and candles must not be split across separate databases or independent transaction managers.

### 3.1 Lease fencing contract

Use a dedicated lease table keyed by a stable lease name, with at least:

- `lease_name` primary key
- `owner_id`
- monotonically increasing `generation BIGINT`
- `expires_at TIMESTAMPTZ`
- `updated_at TIMESTAMPTZ`

Every canonical write transaction must:

1. Begin a transaction with a bounded statement and lock timeout.
2. Acquire a row lock on the relevant lease row using `SELECT ... FOR UPDATE` (or an equivalently proven transaction-scoped lock).
3. Validate exact `owner_id` and `generation`; reject missing, stale, or mismatched authority.
4. Validate expiry with PostgreSQL `clock_timestamp()`, not application time and not `now()`/transaction-start time.
5. Write the entire batch inside this same transaction.
6. Recheck expiry with `clock_timestamp()` immediately before commit.
7. Commit only if all checks pass; otherwise roll back every row in the batch.

Lease acquisition/takeover and heartbeat must lock/update the same lease row. A takeover must increment generation atomically and cannot pass a writer holding that row lock. If the old writer's lease expires while it holds the transaction, its final database-clock check fails and its batch rolls back; only then can the next generation take over. A new writer must never rely on process-local locks or client timestamps.

The implementation must explicitly test database transaction isolation, lock wait timeout, deadlock handling, connection loss, and server restart. Do not assume SQLite's `BEGIN IMMEDIATE` behavior maps directly to PostgreSQL.

### 3.2 Candle batch and idempotency contract

- Preserve the canonical natural key and all market identity dimensions, including exchange, market type, symbol, timeframe, and open time; verify compatibility with TimescaleDB hypertable unique-index rules before freezing the migration.
- Use exact decimal/numeric handling; do not round through binary floating point.
- Duplicate identical closed candles are idempotent no-ops.
- A duplicate natural key with different OHLCV or provenance values is a hard conflict; never overwrite historical canonical data silently.
- Validate the complete batch before commit. Any invalid candle, conflict, lost lease, or SQL error rolls back the entire batch.
- Keep closed-candle availability semantics and source provenance explicit.

### 3.3 Gateway and module boundary

Introduce a backend-neutral canonical writer contract only after the contract tests are specified. Keep backend-specific implementations separate:

- `SQLiteWriteGateway`: existing implementation, retained.
- `PostgresWriteGateway`: new implementation; no fallback to unfenced writes.
- Runtime selects exactly one configured backend and fails closed on incomplete/mixed configuration.
- Recovery and scheduler receive the same gateway instance, as already required by the SQLite composition tests.
- Read-only API credentials cannot write. No direct candle writes from Feeder, API, or migration code outside the gateway.

## 4. Database roles and security

Separate database identities:

- **Migration role:** DDL and extension/hypertable/migration permissions; used only by an explicit migration operation.
- **Feeder runtime role:** least-privilege access to the lease table and canonical candle table required for lease lifecycle and fenced inserts; no schema ownership or DDL.
- **Read API role:** SELECT only on approved canonical views/tables; no lease mutation and no candle writes.
- **Backup/monitoring role:** only the permissions required by the chosen backup and health tooling.

Use TLS with certificate verification where supported, private networking or a restricted allowlist, and secret storage outside the repository and CI logs. No public database listener by default. Do not provide Binance API keys or trading permissions to T0; public market-data access only. Never configure order/trade endpoints.

## 5. Migration and schema ownership

- Preserve explicit, immutable, checksum-verified migrations.
- Run migrations as a separately authorized pre-deployment step using the migration role; never on Feeder startup or API reads.
- Use a transaction-scoped advisory lock to serialize migration runners.
- Verify the exact migration set and checksums before and after applying.
- Confirm TimescaleDB version/extension compatibility and hypertable partitioning/unique-index constraints in CI.
- Runtime startup must verify expected schema version and fail closed on mismatch; it must not auto-migrate.
- A migration rollback plan must distinguish reversible metadata changes from destructive data/schema changes. Prefer forward-fix migrations; destructive rollback requires a verified backup and explicit approval.

## 6. Backup, restore, and continuity

Before production DB creation, select and document the provider-specific backup mechanism. Required capabilities:

- Automated encrypted backups and, where available, WAL/PITR.
- Retention and recovery-point objective (RPO) stated explicitly.
- Recovery-time objective (RTO) stated explicitly and measured in staging.
- Backup stored outside the database host/failure domain.
- Restore into a new isolated database, verify migration checksums, row counts, time-range coverage, candle uniqueness, decimal fidelity, and provenance.
- Verify that the restored runtime starts with a fresh lease generation and that no stale owner can write.
- Test backup during active writes using the provider-supported consistent backup method; never copy live PostgreSQL data files as an ad-hoc filesystem copy.
- Alert on backup age/failure, WAL/archive lag, disk usage, connection saturation, and restore-test age.

No production backup policy or RPO/RTO is selected in this record; these remain deployment decisions.

## 7. Staging acceptance — required before production

All tests must use a dedicated disposable local PostgreSQL/TimescaleDB service, synthetic candles, and test-only credentials. Never use production DSNs, Binance credentials, canonical DB paths, Paper DB paths, or exchange network access in this suite.

Required acceptance matrix:

| ID | Scenario | Required result |
|---|---|---|
| PG-01 | Current owner + generation + unexpired lease | Complete batch commits |
| PG-02 | Missing lease / wrong owner / stale generation | Reject; zero rows written |
| PG-03 | Expired lease before transaction | Reject; zero rows written |
| PG-04 | Lease expires during batch | Final DB-clock check rejects; whole batch rolls back |
| PG-05 | Concurrent takeover while writer holds lease row lock | Takeover waits; cannot authorize concurrent writer |
| PG-06 | Old generation attempts write after takeover | Reject; zero rows written |
| PG-07 | Identical duplicate batch | Idempotent; no duplicate rows |
| PG-08 | Conflicting duplicate candle | Reject and roll back entire batch |
| PG-09 | Invalid candle in middle of batch | Entire batch rolls back |
| PG-10 | Connection loss / backend termination before commit | No partial batch; recovery can acquire next generation |
| PG-11 | Runtime process crash and restart | Readiness remains closed until recovery and fresh lease succeed |
| PG-12 | Read API role attempts mutation | Database permission denial |
| PG-13 | Runtime role attempts DDL | Database permission denial |
| PG-14 | Migration replay and checksum mismatch | Replay is idempotent; mismatch fails closed |
| PG-15 | Concurrent migration runners | Advisory lock serializes; schema remains consistent |
| PG-16 | Backup restore into isolated DB | Data, schema, provenance, and fencing checks pass |
| PG-17 | Long transaction / lock timeout / deadlock | Bounded failure; no partial batch; health becomes not-ready/degraded as specified |
| PG-18 | Timescale hypertable unique key and chunk-boundary conflicts | Uniqueness is enforced across all relevant chunks |

CI must record PR head SHA, checked-out SHA, workflow run ID/event, test summaries, artifact ID and digest. Tests must be source-pinned. A skipped or absent TimescaleDB service is NOT VERIFIED, not PASS.

## 8. VPS deployment choices still open

Do not select or purchase infrastructure until the user approves a cost ceiling and provider/region. Compare these deployment shapes:

1. **VPS app + managed PostgreSQL/TimescaleDB:** preferred operational risk profile if an acceptable provider supports private networking, backups/PITR, TLS, and required Timescale features. App and DB failures are separated.
2. **Single VPS app + self-managed PostgreSQL/TimescaleDB:** potentially lower direct cost, but increases single-host failure risk and operator burden for upgrades, disk, backups, WAL, monitoring, and restore.
3. **Separate VPS app + separate DB host:** stronger failure isolation, higher cost and network/operations complexity.

Decision inputs required before provisioning: provider, region/data residency, OS, CPU/RAM/disk, storage class/IOPS, backup retention, RPO/RTO, firewall/SSH policy, monthly cost ceiling, and whether managed TimescaleDB is acceptable. Do not open public database ports.

## 9. Rollout sequence and stop conditions

1. Freeze the writer contract and schema constraints.
2. Add RED tests for the PostgreSQL Gateway and lease lifecycle.
3. Implement the minimum PostgreSQL writer and migrations.
4. Run isolated PostgreSQL/TimescaleDB acceptance on GitHub Actions.
5. Review permissions, failure handling, lock behavior, migration safety, and code quality.
6. Complete staging backup/restore and restart acceptance.
7. Select provider/VPS and cost envelope.
8. Only after the above gates pass, prepare a production cutover checklist and request confirmation for actual provisioning/DB creation/real Binance market-data sync.

Stop and mark BLOCKED if: lease and candle writes cannot share one transaction; uniqueness cannot be guaranteed; database time is unavailable; permissions are broader than specified; backup restore fails; data schema cannot preserve market identity/provenance; or the selected VPS/provider cannot meet the agreed RPO/RTO and security constraints.

## 10. Current decision status

| Decision / gate | Status |
|---|---|
| Binance USD-M BTCUSDT canonical source | TEMPORARILY SELECTED |
| PostgreSQL/TimescaleDB as proposed production backend | PROPOSED; provider/hosting choice open |
| PostgreSQL atomic lease-fenced writer | BLOCKED — not implemented |
| PostgreSQL writer integration acceptance | NOT RUN |
| Migration/role separation acceptance | NOT RUN |
| Backup/restore on selected target | NOT VERIFIED |
| VPS provider, region, OS, cost ceiling | NOT SELECTED |
| Canonical DB creation | NOT AUTHORIZED YET; conditional rollout only after gates |
| Production Feeder / real market-data sync | NOT STARTED |
| Live trading / order execution | NOT AUTHORIZED |

## 11. Next increment

The next implementation increment, after design review, is **PG-RED**: add isolated failing contract tests for the PostgreSQL lease-fenced writer and takeover lifecycle, using only disposable local TimescaleDB and synthetic data. Do not modify SQLite behavior, enable Postgres writes, create a canonical DB, connect to Binance, provision VPS, or merge PR #134 as part of PG-RED.
