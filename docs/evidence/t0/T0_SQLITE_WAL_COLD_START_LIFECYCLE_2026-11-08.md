# T0 SQLite WAL Cold-start and Restart Lifecycle Proof

- Date: 2026-11-08
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact tested source SHA: `718c1eefe391e4907b777cc109e12ef7c1cccc0d`
- Probe: `ci/t0_sqlite_readonly_sandbox.py`
- Scope: disposable GitHub Linux runner only; no canonical VPS/database/service touched.
- Verdict: **PASS for fail-closed cold-start guard and WAL-ready startup on the disposable runner. Production API deployment remains BLOCKED pending the real Feeder service lifecycle and VPS compatibility review.**

## 1. Exact workflow evidence

- GitHub Actions run: `42483585220`
- Workflow: `T0 SQLite Read-only systemd Sandbox`
- Job: `Disposable SQLite WAL under systemd ReadOnlyPaths`, ID `128740536980`
- Conclusion: **SUCCESS**
- Artifact: `t0-systemd-readonly-sandbox-718c1eefe391e4907b777cc109e12ef7c1cccc0d`
- Artifact ID: `13617664165`
- SHA-256: `877aa71838130c492e73886546ebc4c360469ab000477572a7d16dbc4486de1a`
- [Workflow run](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42483585220)

## 2. Results

| Scenario | Expected | Observed |
|---|---|---|
| Existing SQLite database in WAL mode, no `-wal` / `-shm`, read-only systemd mount | Read fails closed | PASS — blocked as expected |
| Writer starts and establishes WAL/SHM; sandboxed read-only reader | Read succeeds | PASS |
| Writer holds an uncommitted transaction | Reader sees only committed snapshot | PASS |
| Writer commits | Fresh reader sees committed row | PASS |
| Clean checkpoint / writer closes / sidecars absent; API restart attempt | Read fails closed | PASS — blocked as expected |
| Writer restarts and commits, sidecars re-established | API reader succeeds | PASS |
| API process filesystem/SQLite writes | Denied | PASS |
| Writer can continue commit | Allowed | PASS |

The workflow log explicitly records:
- `T0_COLD_START_WITHOUT_WAL_SHM=BLOCKED_AS_EXPECTED` for both cold startup and restart after clean checkpoint.
- `T0_SYSTEMD_READONLY_WAL_READ=PASS`.
- `T0_SYSTEMD_READONLY_FILESYSTEM_WRITE=DENIED`.
- `T0_SYSTEMD_READONLY_SQLITE_WRITE=DENIED`.
- `T0_SYSTEMD_READONLY_WAL_COLD_START_GUARD=PASS`.

## 3. Operational implication

The API cannot be assumed to start successfully against a WAL-mode SQLite database when the `-wal` and `-shm` sidecars are absent and its service namespace denies writes to the data directory. It must fail closed until the Feeder has initialized the WAL lifecycle.

Do not work around this with `immutable=1`, writable directory exceptions, or by letting the API create sidecars. Those approaches would weaken the concurrent-writer isolation proven in the previous test.

## 4. Candidate systemd dependency/readiness design (not deployed)

Once the actual Feeder service unit name and lifecycle are verified, the API unit should adopt the following dependency shape:

```ini
# Illustrative only — do not install as-is.
[Unit]
Requires=<verified-t0-feeder-unit>.service
After=<verified-t0-feeder-unit>.service

[Service]
User=<verified-api-user>
NoNewPrivileges=true
ProtectSystem=strict
ReadOnlyPaths=<verified-t0-data-directory>
ExecStartPre=<readiness-check-that-only-verifies-db-wal-shm-readable-and-feeder-active>
ExecStart=<gunicorn-command-bound-to-127.0.0.1:8788>
```

Before adopting this:
1. Identify whether the current Feeder is managed by systemd or another supervisor; the previous operator snapshot did not establish a matching systemd unit.
2. Define Feeder readiness as: database exists, WAL and SHM sidecars exist and are readable, and the writer is operational. A mere process-active state is insufficient.
3. Ensure API is stopped before Feeder during orderly shutdown. Confirm exact systemd dependency semantics and failure behavior; consider a stronger binding dependency if unexpected Feeder exit must stop API.
4. Verify API restart after Feeder restart, Feeder crash/recovery, checkpoint, and host reboot using a disposable environment first.
5. Ensure the readiness check is read-only and does not create files, open a writer connection, or mutate the database.

## 5. Status

- SQLite read-only mutation rejection: **PASS**.
- WAL reader with concurrent writer: **PASS**.
- systemd `ReadOnlyPaths` filesystem isolation: **PASS — disposable runner**.
- Cold-start without WAL/SHM: **BLOCKED AS EXPECTED**; readiness guard required.
- Restart after clean checkpoint without WAL/SHM: **BLOCKED AS EXPECTED**; Feeder must be ready first.
- API read after writer readiness: **PASS — disposable runner**.
- Actual VPS systemd/kernel compatibility: **NOT VERIFIED**.
- Actual Feeder service manager/unit/readiness: **NOT VERIFIED**.
- Gunicorn production unit: **NOT CREATED**.
- T0 API deployment / live endpoint / T2 runtime: **BLOCKED / NOT ACTIVATED**.
- `ai_execution_enabled=false`.

## 6. Scope boundary and next step

No source runtime implementation, canonical database, Feeder process, VPS, systemd service, permissions, secrets, firewall, network, DNS, proxy, or T2 runtime was accessed or changed. No live trading or exchange access.

Next bounded step: inspect the current Feeder launch/supervision model and define a read-only readiness contract from tracked source and existing operator evidence. Do not create/install service units or alter VPS state until a separate deployment approval.


## 7. Actual Feeder writer lifecycle — additional verification

The previous persistent-writer probe did not model the exact production connection lifecycle. Source inspection established:
- `SQLiteWriteGateway.write_batch()` opens a SQLite connection for each batch and closes it after commit.
- `LeaseStore` operations (including heartbeat) also open and close their own connections.
- `FeederRuntime.start()` acquires the lease, runs recovery, starts the scheduler, marks RUNNING and starts heartbeat; `stop()` drains work and releases the lease. There is currently no persistent WAL-keeper lifecycle hook in this runtime.
- The operator VPS snapshot had not established a systemd Feeder unit; the current observed process was managed through tmux.

A follow-up disposable probe now exercises the actual `CandleStore`, `LeaseStore`, and `SQLiteWriteGateway` classes:
- After `write_batch()` closes its connection: both `-wal` and `-shm` are absent.
- After a Feeder-equivalent lease heartbeat closes its connection: both sidecars remain absent.
- The read-only API sandbox is blocked in this state, as expected.
- A candidate long-lived connection opened in WAL mode and used for a SELECT keeps both sidecars present; while it remains open, the sandboxed API read succeeds.

Exact GitHub Actions evidence:
- Run `42483989133`, exact SHA `e929cdbc072221121581be0e573be7641b4cb7f3`, **SUCCESS**; job `128741767394` PASS.
- Artifact `t0-systemd-readonly-sandbox-e929cdbc072221121581be0e573be7641b4cb7f3`, ID `13618796077`, SHA-256 `cb99b979931bf2f56b36a043edd013935bc1cfd359671f628a6528b916bf8fed`.
- [Workflow run](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42483989133).

This reveals a production integration blocker: with the current short-lived writer/heartbeat connections, the read-only API may be unable to read between writes when the data directory is sandboxed read-only. A persistent WAL-keeper connection owned by the Feeder is a viable candidate and passed the disposable read probe, but its production lifecycle is not implemented or proven.

### Required lifecycle contract before implementation

1. Feeder acquires its fencing lease.
2. Feeder opens a dedicated WAL-keeper connection and verifies WAL/SHM sidecars exist and are readable.
3. Feeder completes recovery and starts scheduling; only then may it report service readiness.
4. API starts only after Feeder readiness, with `Requires=`, `After=` and a read-only sidecar readiness check. Consider `BindsTo=` so unexpected Feeder exit stops the API; validate exact systemd semantics in an isolated test.
5. On orderly shutdown, API must stop before Feeder. Feeder stops scheduler admission, drains in-flight writes, stops heartbeat, releases the exact lease, and only then closes the WAL keeper.
6. On Feeder crash, the API must fail closed and be stopped/restarted only after the Feeder re-establishes WAL/SHM readiness.

No production code was changed in this follow-up. The persistent keeper is a candidate design, not an adopted runtime behavior.

## 8. Feeder-owned WAL Keeper implementation — TDD and CI evidence

### Implementation

- Added `SQLiteWalKeeper` in `market_data/write_gateway.py`. It opens the existing database using `mode=rw`, verifies WAL mode and the canonical `candles` table, and retains one idle SQLite connection. It does not write candles or lease rows.
- Added optional `wal_keeper` lifecycle ownership to `FeederRuntime:
  - Open after the fencing lease is acquired and before startup recovery.
  - If open/recovery/startup fails, stop admission, drain, release the exact lease, then close the keeper.
  - On normal shutdown, stop admission, wait for heartbeat and active writers, release the exact lease, then close the keeper.
  - If writer drain times out or lease release is not confirmed, retain the keeper; do not close it prematurely.
  - If lease is lost, drain and close the keeper without attempting to release a replacement generation.
- `build_runtime()` wires a keeper for SQLite only. PostgreSQL runtime remains unchanged.
- `SQLiteWalKeeper` permits close from the shutdown thread (`check_same_thread=False`); a regression test caught and corrected SQLite's default thread-affinity failure.
- Startup cleanup marks the keeper as owned before calling `open()`, so partially initialized custom keepers are also closed on failure.

### TDD evidence

- RED tests were committed first in `market_data/test_feeder_lifecycle.py`; exact SHA `d2ad3e85236fa9367a639d0dd874afb49e51fd6f` failed because `FeederRuntime` did not yet accept `wal_keeper`.
- First GREEN attempt exposed two further lifecycle defects:
  - Keeper close from a different thread raised `sqlite3.ProgrammingError`.
  - A keeper whose `open()` raised was not sent through cleanup.
- Both were corrected and regression-tested.
- Added actual disposable runtime coverage: start runtime, retain WAL/SHM across actual `SQLiteWriteGateway.write_batch()` and `LeaseStore.heartbeat()`, read committed candles, drain/release lease, then close keeper and verify sidecars disappear.

### Final exact-source verification

- Final implementation/test source SHA: `702e366882c1f585e14f2700497b9f7290d841ca`.
- T0 Single Writer Gateway Contracts run: `42484777981`; target job `Static Gateway contract verification`, ID `128744313677`, **SUCCESS**. At evidence capture, other independent jobs in the same workflow run were still executing; overall workflow conclusion was therefore still in progress.
- Target job results:
  - Feeder lifecycle and gateway focused/regression tests: `73 tests`, **OK**.
  - Health/readiness tests: `21 tests`, **OK**.
  - Process restart/fencing tests: `2 tests`, **OK**.
  - Full `market_data` suite: `289 tests`, **OK (42 skipped)**.
- Target job artifact: `t0-swg-contract-evidence-702e366882c1f585e14f2700497b9f7290d841ca`, ID `13618638809`, SHA-256 `ad887590c4b4b52c28c032f09e041bb79604446c60104c4eb3b8a8985e79d4ef`.
- Disposable systemd WAL sandbox run `42484778028`: **SUCCESS**, job ID `128744166456`; artifact ID `13618563920`, SHA-256 `ff9f8b45ded427971988958347996ae52a32fd5d750671d04e7a3ca4e1277118`.
- T2 Freqtrade 2026.9 strategy load smoke run `42484777986`: **SUCCESS** at the same source SHA. This is a CI smoke only; it does not activate T2 runtime.
- Workflow links:
  - [T0 Single Writer Gateway Contracts](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42484777981)
  - [T0 SQLite Read-only systemd Sandbox](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42484778028)
  - [T2 strategy load smoke](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42484777986)

### Status after implementation

- Keeper startup, readiness ordering, and shutdown lifecycle: **PASS — disposable tests**.
- Sidecars persist across short-lived write and heartbeat connections while Keeper remains open: **PASS — disposable tests**.
- API read-only `ReadOnlyPaths` with live WAL: **PASS — disposable systemd runner**.
- Keeper startup failure and partial initialization cleanup: **PASS — tests**.
- Shutdown drain timeout preserves keeper and lease: **PASS — tests**.
- Actual VPS systemd/kernel behavior and process manager: **NOT VERIFIED**.
- Production Feeder/API service units and readiness integration: **NOT DEPLOYED**.
- T0 API endpoint: **NOT RUN**; T2 runtime: **NOT ACTIVATED**; `ai_execution_enabled=false`.
- No VPS, canonical database, secrets, permissions, firewall, DNS, proxy, or live runtime was changed.

### Next bounded step

Review the final diff and the full workflow conclusion; add an isolated systemd integration probe that runs the actual `FeederRuntime` with `SQLiteWalKeeper` as the writer service and a separate read-only API service. Verify readiness ordering, Feeder crash, and shutdown ordering on the disposable runner. Only after that may a deployment unit be proposed for explicit approval.
