# T0 Read-Only Preflight Script — Static Safety and Scope Audit

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact source baseline inspected: `523fc541f0fba189904e8ce5adf3083b15b16778`
- Script: `ops/ssh/t0-readonly-preflight.sh`
- Script blob SHA-256 (Git blob object ID): `39de5aa7602cdf7dc301ff6bc65a68fad417ea84`
- Operation class: STATIC REPOSITORY REVIEW ONLY
- Execution status: NOT RUN
- Purpose: determine whether the existing script is suitable for the DEP-01–DEP-09 metadata-only owner evidence protocol.

## 1. Result

**PARTIAL / NOT APPROVED FOR DEP-01–DEP-09 METADATA-ONLY COLLECTION.**

The script is non-mutating in its checked-in form: it does not contain service lifecycle commands, Git worktree mutation, HTTP requests, or explicit SQLite write statements. However, its behavior exceeds the narrow metadata-only collection protocol in two important ways:

1. It reads `/proc/[0-9]*/cmdline` across visible processes to identify Feeder PIDs. Process command lines may contain sensitive arguments, even though the script only emits matching PIDs.
2. It opens the canonical SQLite database read-only and executes `PRAGMA integrity_check`. This scans database structures and is not a metadata-only check; its I/O and CPU cost is not bounded by a small fixed amount of work.

Therefore, the script must not be treated as equivalent to the DEP-01–DEP-09 command set, and this audit does not authorize running it.

## 2. Static behavior inventory

| Script behavior | Classification | Finding |
|---|---|---|
| Fixed APP_DIR, DB_PATH and API_PORT constants | Path/config metadata | Hard-coded to `/home/ubuntu/t0/app`, canonical SQLite path and port 8788 |
| `hostname -s`, `id -un` | Host metadata | Emits sanitized hostname and SSH user; avoid publishing identity details beyond the owner-approved evidence bundle |
| `git rev-parse --verify HEAD` | Repository metadata | Emits exact HEAD SHA; does not check dirty/untracked worktree state |
| Iterate `/proc/[0-9]*` and read `cmdline` | Process inspection / potentially sensitive read | Reads command-line bytes for all visible processes; output is only matching PID list, but source arguments may include secrets |
| `ss -H -ltn sport = :8788` | Listener metadata | Emits endpoint addresses and loopback classification; does not identify owning PID/process |
| SQLite URI `mode=ro`, `PRAGMA query_only=ON` | Read-only database access | Prevents ordinary writes through this connection; does not make the operation metadata-only |
| `PRAGMA integrity_check` | Full database integrity scan | Potentially unbounded I/O/CPU relative to database size; may compete with canonical workload; result is not equivalent to Feeder readiness or API data-path readiness |
| Structured key/value output | Evidence formatting | Emits version, host, user, SHA, PID list, listener status and SQLite integrity status |

## 3. Safety and correctness findings

### F-01 — Process command-line read is outside the approved metadata boundary

The loop reads each accessible process's `/proc/<pid>/cmdline`, then filters for `market_data.feeder` or `market_data.feeder_service`. It does not print the full command line, but reading it still exposes potentially secret-bearing arguments to the script's execution context and may match a process based on command-line text rather than authoritative systemd unit ownership.

**Disposition:** Do not use this mechanism for the current DEP evidence protocol. Prefer owner-supplied `systemctl show` properties and the specific unit's `MainPID`, then collect only `/proc/<MainPID>/exe`, `cwd` and `comm` as specified in the protocol. Even these commands require separately authorized host inspection.

### F-02 — SQLite integrity check is not a bounded metadata probe

The script opens the canonical database in read-only mode and executes `PRAGMA integrity_check`. The connection is configured query-only and uses SQLite URI read-only mode, so the script does not intentionally mutate the database. Nevertheless, the integrity check scans database structures and its resource cost scales with the database. It is not limited to a small metadata query and does not prove the Feeder lease, current freshness, API authentication, consumer access or system readiness.

**Disposition:** Exclude it from deployment metadata collection. Any integrity verification must be a separately scoped database operation with an explicit resource/maintenance assessment and approval. Do not run it against the canonical DB as part of this audit.

### F-03 — Script's “read-only” label is narrower than “side-effect-free”

No explicit service or data mutation was found in the script. However, process inspection and full database scanning can still consume resources and disclose operational metadata. “Read-only” must not be interpreted as “zero-impact” or “safe to execute without authorization.”

**Disposition:** Preserve the distinction in future documentation. Do not execute without explicit authorization and a defined scope.

### F-04 — Output is insufficient for deployment parity

The script does not report:

- Effective systemd unit properties, `Type=notify`, `NotifyAccess`, `ExecStart`, user/group, working directory, dependencies, restart and timeout properties.
- Candle API executable, WSGI target, process identity or service unit.
- Process executable/cwd identity for the Feeder PID.
- Git worktree dirty/untracked status.
- Flask health app deployment or `T0_HEALTH_SNAPSHOT_PROVIDER` registration.
- A process owner for the port 8788 listener.

**Disposition:** Its output cannot satisfy DEP-01–DEP-09 or establish deployment parity.

### F-05 — Forced-command security is an external deployment assumption

The script comment says it should be installed root-owned and bound as an `authorized_keys` forced command. The script itself does not verify file ownership/mode, SSH key options, forced-command configuration, restricted shell behavior, or that arbitrary client-supplied commands are rejected by the SSH configuration.

**Disposition:** Do not treat the comment as evidence that a restricted SSH boundary exists. Any future SSH setup review is a separate security/configuration task; no SSH key or authorized_keys inspection is authorized here.

### F-06 — Documentation has a deployment wording ambiguity

`market_data/README.md` describes the Gunicorn server as loopback-bound, then says “When deploying” to place it behind an HTTPS reverse proxy. The selected same-host T0 → T2 decision explicitly does not require a reverse proxy. These statements can be reconciled if the README's proxy sentence is understood as applying only to an externally exposed deployment, but the condition is not explicit.

**Disposition:** Record as a documentation clarification candidate only. Do not add Nginx or alter the loopback architecture. Any README edit should explicitly distinguish same-host loopback consumers from a separately approved remote/browser gateway topology.

## 4. Relationship to DEP-01–DEP-09

| DEP item | Can this script provide it? | Limitation |
|---|---|---|
| DEP-01 timestamp / host label | Partial | No UTC timestamp; hostname and SSH user only |
| DEP-02 unit names | No | Does not enumerate systemd units |
| DEP-03 Feeder effective properties | No | No systemd unit properties |
| DEP-04 API effective properties | No | No API unit properties |
| DEP-05 process identity | Partial | Feeder PID only; no executable/cwd/comm; no API process |
| DEP-06 listener metadata | Partial | Port endpoint only; no owner PID/process |
| DEP-07 deployed source SHA | Partial | Reads one fixed checkout HEAD; no worktree status or proof that processes use that checkout |
| DEP-08 Flask deployment/provider | No | Not inspected |
| DEP-09 gateway relevance | No | Does not inspect gateway configuration |

## 5. Decision

- Keep the script unchanged during this documentary audit.
- Do not execute it on the VPS as a substitute for the DEP protocol.
- Do not add its SQLite integrity scan to a routine preflight or readiness check.
- Prefer the narrowly scoped owner-supplied unit/process/listener/SHA evidence bundle already defined in `T0_OWNER_READONLY_DEPLOYMENT_EVIDENCE_PROTOCOL_2026-11-10.md`.
- If the owner later wants a hardened forced-command preflight, design it as a separate change with a reduced data-access boundary, explicit output allowlist, resource limits, secret review and separate approval. No implementation is authorized by this report.

## 6. Status and evidence limits

| Area | Status |
|---|---|
| Static script inspection | COMPLETE |
| Script non-mutation intent | PARTIAL — no explicit mutation found |
| Metadata-only compliance | NOT PASS |
| Process command-line sensitivity | FINDING F-01 |
| Canonical SQLite scan resource scope | FINDING F-02 |
| DEP-01–DEP-09 coverage | INSUFFICIENT |
| Forced-command deployment security | NOT VERIFIED |
| README reverse-proxy wording | CLARIFICATION CANDIDATE |
| Script execution / VPS access | NOT RUN |
| Tests / GitHub Actions | NOT RUN / NOT DISPATCHED |
| Runtime / source / data changes | NONE |

No claim is made about the actual VPS copy, installed file ownership, authorized_keys configuration, effective SSH policy, live processes, listener state or canonical database integrity.

## 7. Next step

Continue with a documentary-only deployment contract reconciliation: map the exact Feeder and Candle API launch requirements to the DEP evidence fields, and record the README proxy wording clarification as an explicit documentation issue. Do not execute or modify the preflight script.
