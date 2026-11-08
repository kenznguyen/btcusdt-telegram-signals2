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
