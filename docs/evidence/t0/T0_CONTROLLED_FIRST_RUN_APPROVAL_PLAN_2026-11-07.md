# T0 Controlled First Run — Approval Plan (No Execution)

Date: 2026-11-07  
Status: **PLAN ONLY / NOT AUTHORIZED**  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Acceptance implementation SHA: `1aac449b96c4079004e1cab882280b923e33342c`  
Acceptance workflow: [42329799499](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42329799499) — SUCCESS

## 1. Purpose and authorization boundary

This document defines the preconditions, bounded procedure, evidence, stop conditions, and recovery plan for a possible first canonical T0 ingestion. It does not authorize execution.

Current state:
- P1.9 public read-only connectivity: PASS for the recorded PC sample.
- Offline Controlled Ingestion acceptance: PASS on the exact source SHA and CI workflow above.
- Canonical ingestion: NOT RUN.
- Controlled First Run: NOT AUTHORIZED.
- Production Feeder: STOPPED.
- VPS: not selected or provisioned.
- `ai_execution_enabled=false`.

No command in this plan has been run against a canonical database. No canonical DB has been created, opened for writing, or modified as part of this plan.

## 2. What the existing acceptance proves — and does not prove

Verified offline acceptance used synthetic Binance USD-M-compatible candles, a temporary SQLite file, a temporary lease, and the existing `SQLiteWriteGateway`:
- one aligned 24-hour window contains exactly 96 M15 and 24 H1 candles;
- first sync inserts the expected rows; second sync inserts zero;
- `datasetVersion` remains stable for the same bounded snapshot;
- read-only API returns HTTP 200 and its `datasetVersion` matches `read_window()`;
- a conflicting duplicate in a batch rejects the batch and rolls back the attempted new row;
- tests are isolated from repository/canonical DB paths.

CI additionally passed the provider bootstrap and isolated PostgreSQL/TimescaleDB integration jobs.

This does **not** prove a production database target is configured, a backup is recoverable, production credentials/permissions are correct, a live exchange window is complete, or that the production API is correctly pointed at the intended canonical store. Those remain preflight gates.

## 3. Repository configuration inspection — read-only result (2026-11-07)

Inspected the committed configuration and workflow files on the active branch; no runtime process, host environment, secret value, database, or exchange endpoint was accessed.

- `market_data/storage.py`: SQLite is the backwards-compatible default when `MARKET_DATA_BACKEND` is absent; PostgreSQL requires explicit `MARKET_DATA_BACKEND=postgres` and `MARKET_DATA_POSTGRES_DSN`.
- `market_data/README.md`: `.data/market-data.sqlite3` is a documented local CLI example, not evidence of the canonical production path.
- `.gitignore`: `.data/` and `.env*` are excluded from Git, so their machine-local contents cannot be inferred from the repository.
- T0 CI workflow `.github/workflows/t0-single-writer-gateway-red.yml`: static job sets `MARKET_DATA_DB` empty; PostgreSQL integration jobs use disposable loopback `t0_test` and explicitly empty `MARKET_DATA_DB` / `MARKET_DATA_POSTGRES_DSN`. This is test isolation, not a production target.
- T0 manual validation workflow checks that production-like DB variables are absent in its component-test job; its optional Timescale test consumes a dedicated disposable test DSN.
- Connectivity-probe workflow explicitly asserts DB environment variables are empty. It is not an ingestion workflow.
- `market_data/feeder_service.py` composes the runtime from environment-selected storage, but committed source does not identify an actual operator host, environment values, or canonical database location.

Conclusion: repository source proves backend selection rules, not the selected runtime backend or target. No committed production target identity was found in the inspected configuration. Do not infer that the default SQLite backend means `.data/market-data.sqlite3` is the canonical database. Target/backend remains unresolved and no runtime secrets were inspected.

## 4. Mandatory unresolved inputs — execution is BLOCKED until recorded

The following values must be explicitly resolved and reviewed before requesting approval:

| Input | Required evidence | Current state |
|---|---|---|
| Backend | Explicit choice of existing SQLite canonical store or an already provisioned PostgreSQL/TimescaleDB target; no implicit migration | NOT PROVIDED |
| Target identity | Absolute SQLite path plus filesystem/volume identity, or DB host/port/database/schema identity (never credentials) | NOT PROVIDED |
| Existing schema | Read-only schema fingerprint; expected candle PK and lease schema; migration state | NOT VERIFIED |
| API target | Effective backend and DB identity from the running read-only API configuration | NOT VERIFIED |
| Window | Exact UTC `start_ms` inclusive and `end_ms` exclusive, aligned to both 15m and 1h, exactly 24 hours | NOT SELECTED |
| Exchange identity | Binance USD-M; `BTC/USDT:USDT`, market id BTCUSDT, active linear USDT perpetual | PC connectivity PASS; run-time market metadata NOT VERIFIED |
| Backup | Pre-run snapshot location, byte size, SHA-256, creation time, and successful isolated restore/read verification | NOT VERIFIED |
| Operator | Named operator and maintenance window/timezone | NOT PROVIDED |
| Stop/rollback owner | Person authorized to stop and perform recovery; separate approval for any destructive restore | NOT PROVIDED |

Never place secrets, API keys, access tokens, passwords, or private connection strings in the plan, GitHub issue, workflow log, or evidence artifact.

## 4. Read-only preflight — must complete before any write approval

1. Confirm branch and exact source SHA; require a clean worktree and passing required GitHub Actions on that SHA.
2. Read the configured backend and target identity without constructing `CandleStore` or any object that can create schema/files.
3. Confirm the target already exists. Do not create a database or schema as part of first-run acceptance.
4. Inspect schema read-only. Confirm the expected candle primary key:
   `(exchange, market_type, symbol, timeframe, open_time_ms)`.
   Confirm lease table/schema is compatible with the writer. Any mismatch is a hard stop.
5. Confirm API configuration resolves to the same target identity, using configuration metadata only; do not expose secret values.
6. Confirm no other writer/Feeder is running and establish an exclusive maintenance window. Verify lease ownership and generation expectations without acquiring a production write lease during preflight.
7. Select a closed 24h UTC window. Record exact epoch milliseconds and UTC ISO values. Verify both exchange server time and local observation time are beyond the window end. Do not infer completeness from the earlier P1.9 connectivity sample.
8. Query existing target rows read-only for both intervals. Record counts, gaps, key range, and pre-run dataset hashes. If any target rows already exist in the selected range, stop and revise the plan; do not overwrite or silently merge history.
9. Create a consistent pre-run backup/snapshot. For SQLite with WAL, use SQLite's online backup mechanism or a quiesced, verified snapshot; do not copy only the main DB file while WAL may contain committed state. Record SHA-256 and restore it to a separate temporary path/database, then verify schema and pre-run read hashes. For PostgreSQL/TimescaleDB, use the provider-supported consistent backup/snapshot and prove restore to an isolated target.
10. Produce a signed-off preflight report with all table entries above resolved. No write is permitted during these steps.

## 5. Bounded first-run procedure — requires a separate explicit approval

The approval request must identify the exact source SHA, backend, target identity, UTC window, backup hash, operator, and runbook version. Approval for one target/window does not authorize another.

After approval only:

1. Reconfirm all preflight gates immediately before execution; abort if target identity or source SHA changed.
2. Keep the normal Feeder service stopped. Use a one-shot, manually supervised invocation through the approved write gateway and a bounded `sync_window()` call; do not remove `--shadow-only` from the existing CLI or repurpose the shadow command.
3. Acquire only the dedicated lease for the approved owner/window. Record lease name, owner, generation, acquisition/expiry timestamps. No concurrent writer is allowed.
4. Sync only BTCUSDT USDT perpetual, M15 and H1, for the exact approved 24-hour `[start_ms, end_ms)` range. No other symbols, intervals, historical backfill, catch-up, or continuous scheduler.
5. Stop immediately on any fetch/schema/identity/coverage/lease/write conflict. Do not retry with a wider window or silently skip gaps.
6. After first sync, perform read-only verification:
   - exactly 96 M15 and 24 H1 records in the selected window;
   - timestamps are aligned and continuous, no gaps or duplicate primary keys;
   - all candles are closed and OHLC bounds/decimal values valid;
   - exchange/market/symbol identity is Binance USD-M / USDT_PERPETUAL / BTCUSDT;
   - record inserted counts, canonical `datasetVersion` hashes, counts and first/last timestamps.
7. Repeat the exact same sync once. Expected inserted count is zero for both intervals. Re-read the exact same snapshot and require identical hashes, counts and coverage.
8. Call the read-only API with the exact same symbol, intervals and window. Require HTTP 200, complete coverage, exact expected counts, and API hash equal to the canonical `read_window()` hash for each interval.
9. Release/expire the one-shot lease and verify no Feeder process remains active. Do not enable scheduler or persistent Feeder.
10. Preserve all command output, sanitized configuration identity, source SHA, workflow links, artifact IDs/digests, UTC timestamps, pre/post backup hashes, before/after counts, insert counts, API responses and dataset hashes.

## 6. Stop conditions

Any one of these means **STOP / BLOCKED**; preserve evidence and do not improvise:
- target/backend identity is missing, ambiguous, or differs between writer and API;
- source SHA differs from the approved SHA or required CI is not green;
- backup cannot be restored and verified in isolation;
- selected window is not fully closed, not aligned, or not exactly 24 hours;
- wrong exchange, contract type, symbol, interval, or unexpected market metadata;
- M15 count is not 96, H1 count is not 24, or any gap/duplicate exists;
- second sync inserts anything other than zero;
- hash changes between identical snapshots without a documented and approved explanation;
- API is not HTTP 200, coverage is incomplete, or API/canonical hashes differ;
- lease is missing, expired, superseded, or another writer is detected;
- any write conflict, partial batch, unexpected schema/migration, or process failure.

Do not weaken validation, overwrite a conflicting candle, widen the window, use proxy/VPN, or start the persistent Feeder to work around a failed gate.

## 7. Rollback and recovery evidence

Rollback is a recovery action, not a routine cleanup:
- On a failed batch, rely first on the gateway's atomic transaction rollback; verify the attempted batch inserted no partial rows.
- Stop the one-shot process and prevent any further writer from acquiring the lease.
- Capture post-failure read-only counts and hashes before recovery.
- Compare target state with the pre-run snapshot. If there are no committed changes, record that fact; do not restore needlessly.
- If committed unexpected changes exist, preserve the failed target and logs. Restore the pre-run snapshot only to an isolated recovery target first, verify schema/counts/hashes, then prepare a separate recovery approval.
- Do not delete rows manually, drop/recreate schema, overwrite the live DB, or perform a destructive restore without explicit separate approval.
- After approved recovery, verify target identity, schema, row counts, hashes and API read path again. Keep the original failed snapshot and evidence immutable.

Required rollback evidence: pre-run snapshot hash and restore proof; transaction error/rollback result; before/after counts and hashes; lease/process stop evidence; isolated restore verification; any separate recovery approval reference.

## 8. Acceptance report template

Record one row per interval:

| Field | M15 | H1 |
|---|---:|---:|
| Expected candles | 96 | 24 |
| Pre-run count / hash | pending | pending |
| First sync inserted | pending | pending |
| Post-first count / hash | pending | pending |
| Gaps / duplicates | pending | pending |
| Second sync inserted | must be 0 | must be 0 |
| Post-second hash | must equal post-first | must equal post-first |
| API status | must be 200 | must be 200 |
| API count / hash | must match canonical | must match canonical |
| Backup/restore evidence | shared evidence reference | shared evidence reference |

Final verdict may be PASS only if every mandatory gate passes. Otherwise record BLOCKED or NOT VERIFIED and preserve the exact failure. A successful one-shot acceptance does not authorize continuous Feeder operation.

## 9. Approval request — intentionally not submitted

No approval is being requested or implied by this document. The next user decision should occur only after the mandatory inputs and read-only preflight report are complete.

The eventual approval must explicitly say that a single bounded write is authorized for the exact source SHA, target identity, and UTC window, and acknowledge the backup/rollback plan. Silence, “continue”, or approval of this document alone must not be interpreted as write authorization.
