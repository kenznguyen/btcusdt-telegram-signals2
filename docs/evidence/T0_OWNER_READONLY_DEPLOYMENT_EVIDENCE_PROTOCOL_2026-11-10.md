# T0 Owner Evidence Collection Protocol — Read-Only Deployment Parity

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact repository baseline: `94e42f2725e02ee6e98a7eaef26a30caec75f4ee`
- Operation class: DOCUMENTARY PROTOCOL ONLY; NO HOST ACCESS
- Purpose: define a bounded, non-mutating evidence bundle to compare the deployed T0 Feeder and Candle API with versioned repository contracts.
- This document does not authorize ChatGPT, an agent, or any operator to SSH into the VPS. Host inspection requires separate explicit owner authorization or owner-supplied output.

## 1. Current decision and boundary

The documented same-host T0 → T2 data path is loopback-only:

- Candle API: `http://127.0.0.1:8788`
- Expected WSGI target: `market_data.api:application`
- Expected launch form: Gunicorn, bound to `127.0.0.1:8788`
- Process health: Candle API `GET /health` (not data readiness)
- Data-path readiness contract: authenticated `GET /v1/candles`
- Nginx/reverse proxy is not required for this same-host path.

T0 remains canonical SQLite, independent of T1/T2. This protocol does not authorize service changes, runtime probes, API requests, database access, token use, data reads, or destructive actions.

## 2. Collection rules

The owner may either supply redacted copies of the relevant unit files/effective properties or separately authorize an operator to run the read-only commands below.

1. Do not run `start`, `stop`, `restart`, `reload`, `enable`, `disable`, `daemon-reload`, package installation, deployment, migration, or write commands.
2. Do not print, copy, upload or paste secret values. Never read or disclose the contents of `EnvironmentFile`, credential files, API tokens, passwords, private keys, database URLs or authorization headers.
3. Redact secret-bearing values in `ExecStart`, drop-ins or unit text if any are present. Preserve executable path, module target, bind address, port, non-secret arguments and Python environment path.
4. Record host time in UTC, hostname label (not public IP), collection operator, and collection time. Do not include account IDs, public IPs or unrelated service information.
5. If a command needs elevated read permission, use only the read-only command shown; do not broaden privileges or change permissions to make collection succeed.
6. If any output is unavailable, mark it NOT AVAILABLE. Do not infer it from documentation.
7. Do not call `/health` or `/v1/candles` as part of this evidence collection. Those are runtime probes and need separate authorization.

## 3. Bounded command set

### 3.1 Identify candidate units

```sh
date -u '+%Y-%m-%dT%H:%M:%SZ'
hostname
systemctl list-units --type=service --all --no-pager | grep -Ei 't0|feeder|market|gunicorn|candle' || true
systemctl list-unit-files --type=service --no-pager | grep -Ei 't0|feeder|market|gunicorn|candle' || true
```

Record candidate Feeder and Candle API unit names. Do not assume their names.

### 3.2 Capture effective properties for each identified unit

Replace `UNIT_NAME` with an exact unit name discovered above. Repeat separately for Feeder and Candle API.

```sh
UNIT='UNIT_NAME'
systemctl show "$UNIT" --no-pager \
  -p Id -p LoadState -p ActiveState -p SubState -p MainPID \
  -p FragmentPath -p DropInPaths \
  -p Type -p NotifyAccess -p ExecStart \
  -p User -p Group -p WorkingDirectory -p EnvironmentFiles \
  -p Restart -p RestartUSec -p After -p Requires -p Wants -p PartOf \
  -p TimeoutStartUSec -p TimeoutStopUSec -p WatchdogUSec
```

Redact any secret values that appear in `ExecStart`. Preserve the unit name, executable, module target, bind/port, working directory, environment-file path, dependency and lifecycle properties.

If a unit file copy is supplied instead, redact all `Environment=` values, credential references that expose secret paths, and any secret-bearing command arguments. Keep `EnvironmentFile` path only where it does not expose sensitive naming.

### 3.3 Map the running process without dumping its command line or environment

For each unit with a nonzero `MainPID`, substitute the PID:

```sh
PID='MAIN_PID'
readlink -f "/proc/$PID/exe"
readlink -f "/proc/$PID/cwd"
cat "/proc/$PID/comm"
```

Do not run `cat /proc/$PID/cmdline`, `cat /proc/$PID/environ`, `ps e`, or commands that print environment values. Do not use `systemctl show -p Environment`.

### 3.4 Check only the expected local listener metadata

```sh
sudo ss -ltnp '( sport = :8788 )'
```

Record whether a listener exists, its local bind address, port, and owning process/PID if shown. Redact unrelated process details. Do not probe the port or make an HTTP request.

### 3.5 Confirm the checked-out source revision without changing the worktree

If the unit's working directory is a Git checkout, substitute that exact path:

```sh
WORKDIR='/EXACT_WORKING_DIRECTORY'
git -C "$WORKDIR" rev-parse --show-toplevel
git -C "$WORKDIR" rev-parse HEAD
git -C "$WORKDIR" status --short
```

Record the exact SHA. Do not run fetch, pull, checkout, reset, clean, stash, build, install, or deployment commands. If the working directory is not a Git checkout, mark source SHA NOT AVAILABLE and do not guess.

## 4. Evidence bundle format

Return only the following sanitized items:

| ID | Required item | Acceptance / recording rule |
|---|---|---|
| DEP-01 | Collection timestamp and host label | UTC timestamp; no public IP/account identifiers |
| DEP-02 | Candidate unit names | Exact names; mark absent if none |
| DEP-03 | Feeder effective properties | Exact values for the properties in §3.2, secrets redacted |
| DEP-04 | Candle API effective properties | Exact values for the properties in §3.2, secrets redacted |
| DEP-05 | Process identity | Executable path, working directory, process name; no cmdline/env |
| DEP-06 | Listener metadata | Port 8788 bind address and owning PID/process if visible |
| DEP-07 | Deployed source revision | Exact Git SHA and sanitized worktree status, or NOT AVAILABLE |
| DEP-08 | Flask health app deployment | Present/absent; if present, unit name and non-secret launcher/provider-registration reference |
| DEP-09 | Nginx/gateway relevance | For same-host loopback path mark NOT REQUIRED; only provide gateway routing evidence if a separately approved remote/browser path actually exists |

Do not attach full `/etc` directories, full process listings, database files, logs, environment files, credentials, tokens, SSH keys, or unrelated service configuration.

## 5. Repository comparison criteria

Compare owner-supplied evidence against the repository contracts:

- Feeder `ExecStart` should resolve to the intended Python checkout and `market_data.feeder_service` entrypoint if this is the claimed deployment.
- Because the Feeder sends systemd `READY=1` / `STOPPING=1`, effective unit `Type=notify` and compatible `NotifyAccess` must be checked; do not assume the unit has these values.
- Candle API `ExecStart` should resolve to Gunicorn and `market_data.api:application`, bound only to `127.0.0.1:8788` for the selected same-host topology.
- Listener evidence must agree with the intended loopback-only bind; a wildcard/public bind is a discrepancy requiring owner review, not an automatic fix.
- The deployed Git SHA must be captured exactly and compared to the source revision the owner expects. A mismatch is a deployment-parity finding, not permission to deploy.
- If root Flask `app.py` is not deployed, record its health routes as source-level/tested contracts only, not operational health monitoring.
- If Flask is deployed, the actual `T0_HEALTH_SNAPSHOT_PROVIDER` registration path must be proven without disclosing secrets. A test-only injected provider is not production wiring.
- No Nginx configuration is required for the documented same-host T0 → T2 loopback route.

## 6. Status rules

- **PASS (evidence scope only):** every required item is supplied, internally consistent, and matches the documented launch/bind/dependency contract. This is not a T0 operational readiness or acceptance PASS.
- **PARTIAL:** some unit/process/source evidence exists, but one or more required items are missing.
- **BLOCKED:** evidence collection requires unapproved access, a service/runtime action, a secret, or a permission change.
- **NOT VERIFIED:** no authoritative evidence for the corresponding host fact.

Do not convert a documentation match into proof that a service is running or data is fresh. Operational readiness requires separately authorized runtime verification.

## 7. Explicit exclusions

- No SSH/VPS access is performed by this protocol.
- No systemd service lifecycle action or unit modification.
- No API/health request, DB connection, SQL query, file content read from data stores, or market-data access.
- No source/test/workflow/package/schema/network/firewall/secret/permission change.
- No GitHub Actions dispatch and no test execution.
- No Nginx installation or configuration change.
- No cleanup, deletion, TTL, retention, vacuum, compaction, backup expiry, archive or replica removal.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Option C — No Destructive Authority — ACTIVE.
- T0 and L4-Minimum remain BLOCKED / NOT VERIFIED until their independent evidence gates are satisfied.

## 8. Next step

Obtain the sanitized DEP-01–DEP-09 evidence bundle from the owner, or obtain separate explicit approval for an exact read-only host inspection scope. Then perform a static comparison and record every mismatch and missing fact. Do not change deployment configuration as part of comparison.
