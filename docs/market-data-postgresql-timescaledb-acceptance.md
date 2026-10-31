# Market-data PostgreSQL migration — acceptance criteria

## Purpose

This checklist is the release gate for future implementation and migration PRs. It does not mean any criterion has already been tested or passed. The current design-only PR is accepted for review only; no database or application behavior is changed.

## Gate 0 — documentation-only design PR

- [ ] Diff contains only the market-data PostgreSQL design and acceptance-criteria documents.
- [ ] No Python/TypeScript/Kotlin source, SQL migration, dependency lockfile, environment template, manifest, checksum registry, or `codemagic.yaml` is changed.
- [ ] No SQLite file, model, research artifact, historical candle, or paper-ledger record is added, removed, or rewritten.
- [ ] No migration, database provisioning, data sync, build, or deployment is triggered by this PR.
- [ ] PR remains Draft until documentation review is complete.

## Gate 1 — SQLite baseline and preservation

Before any data copy:

- [ ] Create a consistent backup using SQLite's backup API; do not copy a live database file as if it were a consistent snapshot.
- [ ] `PRAGMA integrity_check` returns `ok`.
- [ ] Record row counts, unique candle-key counts, min/max `open_time_ms`, timeframe distribution, duplicate/conflict findings, and coverage gaps.
- [ ] Record canonical SHA-256 dataset hashes for fixed windows and fixed `as_of_ms` cutoffs.
- [ ] Record Decimal precision/exponent samples and verify no float round-trip is used.
- [ ] Inventory paper ledger tables and counts independently; confirm that paper state is not part of the market-data copy.
- [ ] Preserve the source database and backup unchanged throughout migration.

Any failed integrity or unexplained baseline mismatch blocks migration.

## Gate 2 — schema and repository contract

- [ ] Migration history exists; applied migration IDs and checksums are immutable and reapplication is idempotent.
- [ ] The TimescaleDB extension/version is recorded and available in the target staging database.
- [ ] `open_time_ms BIGINT` is the hypertable time dimension.
- [ ] Every primary/unique index on the hypertable includes `open_time_ms`.
- [ ] Candle key remains `(exchange, market_type, symbol, timeframe, open_time_ms)`.
- [ ] OHLCV uses PostgreSQL `NUMERIC` without a fixed scale that can silently round existing values.
- [ ] Application Decimal bounds and all current candle validation rules remain enforced.
- [ ] Timeframe, alignment, closed-candle, availability, OHLC, volume, source, and quality constraints reject invalid rows.
- [ ] Legacy rows without ingestion-batch provenance remain NULL; no synthetic provenance is generated.
- [ ] `SQLiteRepository` remains supported and is the default/rollback adapter until parity and cutover gates pass.
- [ ] `PostgresRepository` implements the same logical interface, duplicate idempotency, conflicting duplicate rejection, query bounds, ordering, gaps, and `as_of_ms` semantics.

## Gate 3 — backward compatibility and deterministic parity

For the same source snapshot, query parameters, and availability cutoff:

- [ ] SQLite and PostgreSQL return the same candle key set.
- [ ] All OHLCV decimal values are identical after canonical decimal-string serialization.
- [ ] `available_at_ms`, source, quality, and availability classifications are identical.
- [ ] Returned order and half-open `[start_ms, end_ms)` boundaries are identical.
- [ ] Expected/returned counts, completeness, and every gap interval are identical.
- [ ] `as_of_ms` excludes rows not yet observed at that time; it does not use import time as fabricated historical availability.
- [ ] Duplicate inserts are idempotent on both adapters.
- [ ] A same-key/different-OHLCV conflict is rejected with the same all-or-nothing batch semantics.
- [ ] Canonical `datasetVersion` SHA-256 is byte-for-byte identical for a representative matrix of windows, including empty, partial, complete, and as-of queries.
- [ ] API response fields, status codes, authentication, query limits, and missing-store behavior remain compatible.
- [ ] A missing PostgreSQL configuration/database does not cause an empty database to be silently created or a false healthy response.

A mismatch in any candle, availability field, gap, or dataset hash blocks cutover.

## Gate 4 — paper-ledger isolation

- [ ] `MARKET_DATA_DB` retains its existing SQLite meaning during the compatibility period.
- [ ] Market-data PostgreSQL configuration uses a separate variable, `MARKET_DATA_DATABASE_URL`.
- [ ] Paper-ledger reads/writes do not receive a PostgreSQL DSN through `sqlite3.connect()`.
- [ ] Paper ledger remains on SQLite and its schema, transactions, idempotency, audit trail, risk latches, equity history, and persisted state are unchanged.
- [ ] If/when a separate `PAPER_DB_PATH` is introduced, it is a separately reviewed compatibility change with explicit startup validation and regression tests.
- [ ] Existing API endpoints that combine market-data reads and paper-ledger snapshots continue to work without changing their response contract.

## Gate 5 — migration and shadow-read execution

- [ ] Migration runs only against a dedicated staging database until explicit production authorization.
- [ ] Copy is from a consistent, immutable SQLite snapshot and is restartable/idempotent.
- [ ] Batch failures are visible and recoverable; partial progress is not reported as a complete migration.
- [ ] Final parity report records source snapshot identity, target identity, row counts, key ranges, gaps, decimal checks, availability checks, and hashes.
- [ ] Shadow reads use the same parameter matrix against both adapters while SQLite remains authoritative.
- [ ] Mismatches are retained as evidence and investigated; no threshold is weakened and no source data is silently rewritten to obtain a pass.
- [ ] Before cutover, ingestion is paused, the final delta is copied, and the complete parity matrix is rerun.
- [ ] A documented rollback to the preserved SQLite source is tested.
- [ ] SQLite is not deleted or retired automatically.

## Gate 6 — Codemagic evidence

All executable validation belongs in Codemagic, not GitHub Actions.

- [ ] A dedicated manual Codemagic workflow targets a disposable PostgreSQL/TimescaleDB staging service.
- [ ] The workflow records exact source commit SHA, database engine/extension versions, migration IDs/checksums, and test artifact hashes.
- [ ] Unit/contract tests cover both adapters and all compatibility cases above.
- [ ] PostgreSQL integration tests cover transaction rollback, uniqueness, duplicate/conflict behavior, numeric precision, and hypertable query behavior.
- [ ] Migration tests cover clean install, upgrade, interrupted/retried batches, and checksum mismatch fail-closed behavior.
- [ ] Parity tests compare identical SQLite and PostgreSQL datasets and verify identical `datasetVersion`.
- [ ] Artifacts include machine-readable test results and a parity report; logs do not expose database credentials or tokens.
- [ ] A successful Codemagic run is tied to the exact PR head SHA. YAML presence or a locally inferred result is not evidence of a successful run.

## Cutover approval checklist

Production cutover is a separate decision and requires all of the following:

- [ ] Gates 1–6 pass on the exact candidate commit.
- [ ] No unexplained parity differences remain.
- [ ] Paper ledger is demonstrably isolated and unchanged.
- [ ] Backup restoration and rollback have been exercised.
- [ ] Operator approves the exact cutover window and target database.
- [ ] Retention/compression remain disabled unless separately reviewed and benchmarked.

Until these conditions are met, SQLite remains the source of truth. This document grants no permission for production migration, deletion of SQLite, strategy changes, OOS/model changes, or live trading.
