# T0 DEP-01–DEP-09 Owner Evidence Intake Sheet

- Date prepared: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Preparation baseline: `fa65e4d5e4817be1273f4f5646d4c526357975ec`
- Related protocol: `docs/evidence/T0_OWNER_READONLY_DEPLOYMENT_EVIDENCE_PROTOCOL_2026-11-10.md`
- Launch contract: `docs/evidence/T0_DEPLOYMENT_LAUNCH_CONTRACT_RECONCILIATION_2026-11-10.md`
- Preflight audit: `docs/evidence/T0_READONLY_PREFLIGHT_STATIC_SAFETY_AUDIT_2026-11-10.md`
- Intake status: AWAITING OWNER-SUPPLIED EVIDENCE
- Host access / commands run by ChatGPT: NONE

## Purpose

Provide a bounded place to paste owner-collected, sanitized deployment metadata for comparison with the repository launch contract. This sheet is a template, not evidence. Blank fields remain NOT AVAILABLE; no status is inferred from repository documentation.

## Submission and redaction rules

- Use the existing owner protocol's exact read-only command set only if the owner independently chooses to collect host evidence.
- Do not include secret values, tokens, passwords, private keys, database URLs, authorization headers, complete environment values, public IPs, account identifiers, unrelated process listings, database files, logs or full environment files.
- Redact secret-bearing portions of `ExecStart` while preserving executable path, module/WSGI target, bind address, port and non-secret arguments.
- Do not paste `/proc/*/cmdline`, `/proc/*/environ`, `ps e`, `systemctl show -p Environment`, or output from the old `ops/ssh/t0-readonly-preflight.sh`.
- Do not run that old preflight script: its static audit found process command-line reads and an SQLite `PRAGMA integrity_check` outside the metadata-only boundary.
- Do not call `/health` or `/v1/candles`, connect to SQLite/PostgreSQL, read market data, or change services as part of this intake.
- If any field is unavailable, write `NOT AVAILABLE`; if not applicable, write `NOT REQUIRED` with a short reason.
- Owner-supplied evidence is not authorization for ChatGPT/agent SSH access or runtime probing.

## Evidence intake

### DEP-01 — Collection provenance

- UTC timestamp:
- Host label (no public IP):
- Collection operator:
- Time source / clock confidence, if known:
- Evidence status: NOT AVAILABLE

### DEP-02 — Candidate systemd unit names

- Feeder unit name:
- Candle API unit name:
- Root Flask health app unit (if any):
- Other relevant unit (name and reason only):
- Evidence status: NOT AVAILABLE

### DEP-03 — Feeder effective unit properties

Record only the properties specified by the protocol. Redact secret-bearing command arguments and never include environment values.

- Id / LoadState / ActiveState / SubState:
- MainPID:
- FragmentPath / DropInPaths:
- Type / NotifyAccess:
- ExecStart (redacted, preserving executable + module):
- User / Group:
- WorkingDirectory:
- EnvironmentFiles (path only; no contents):
- Restart / RestartUSec:
- After / Requires / Wants / PartOf:
- TimeoutStartUSec / TimeoutStopUSec / WatchdogUSec:
- Evidence status: NOT AVAILABLE

### DEP-04 — Candle API effective unit properties

- Id / LoadState / ActiveState / SubState:
- MainPID:
- FragmentPath / DropInPaths:
- Type / NotifyAccess:
- ExecStart (redacted; preserve Gunicorn target, bind, workers, threads, timeout):
- User / Group:
- WorkingDirectory:
- EnvironmentFiles (path only; no contents):
- Restart / RestartUSec:
- After / Requires / Wants / PartOf:
- TimeoutStartUSec / TimeoutStopUSec / WatchdogUSec:
- Evidence status: NOT AVAILABLE

### DEP-05 — Process identity

Do not include command line or environment.

| Process | PID | Executable path | Working directory | Process name (`comm`) | Status |
|---|---:|---|---|---|---|
| Feeder | | | | | NOT AVAILABLE |
| Candle API | | | | | NOT AVAILABLE |
| Root Flask health app (if deployed) | | | | | NOT AVAILABLE |

### DEP-06 — Listener metadata

- Port checked: 8788
- Listener present: NOT AVAILABLE
- Local bind address:
- Owning PID/process (if shown):
- Loopback-only confirmed: NOT AVAILABLE
- Unrelated listener details redacted: YES / NOT APPLICABLE
- Evidence status: NOT AVAILABLE

### DEP-07 — Deployed source revision

| Process / checkout | Repository root | Exact HEAD SHA | Worktree status (sanitized) | Matches owner-intended revision? |
|---|---|---|---|---|
| Feeder | | | | NOT AVAILABLE |
| Candle API | | | | NOT AVAILABLE |
| Root Flask health app (if deployed) | | | | NOT AVAILABLE |

Do not fetch, pull, checkout, reset, clean, stash, build, install or deploy while collecting this evidence.

### DEP-08 — Root Flask health app / provider registration

- Root Flask app deployed: YES / NO / NOT AVAILABLE
- Unit / process reference (if present):
- Non-secret launcher reference:
- `T0_HEALTH_SNAPSHOT_PROVIDER` production registration reference:
- Registration is production wiring (not test injection): YES / NO / NOT AVAILABLE
- Evidence status: NOT AVAILABLE

If the root Flask app is absent, record its health routes as source-level contracts only, not operational monitoring.

### DEP-09 — Gateway / reverse proxy relevance

- Same-host T0 → T2 loopback topology in use: YES / NO / NOT AVAILABLE
- Nginx/reverse proxy present for this path: NOT REQUIRED / YES / NO / NOT AVAILABLE
- If a separately approved remote/browser path exists, record only its approved gateway routing/TLS/auth reference:
- Public exposure of Candle API directly: NO / YES / NOT AVAILABLE
- Evidence status: NOT AVAILABLE

For the documented same-host loopback path, Nginx/reverse proxy is NOT REQUIRED. Do not add one merely to satisfy this evidence item.

## Reconciliation result (to be completed only after evidence is supplied)

| Area | Expected contract | Owner evidence | Result |
|---|---|---|---|
| Feeder entrypoint | Intended Python environment + `market_data.feeder_service` | NOT AVAILABLE | NOT VERIFIED |
| Feeder readiness | Compatible systemd notification configuration if readiness gating is intended | NOT AVAILABLE | NOT VERIFIED |
| Candle API entrypoint | Gunicorn + `market_data.api:application` | NOT AVAILABLE | NOT VERIFIED |
| Candle API bind | `127.0.0.1:8788` | NOT AVAILABLE | NOT VERIFIED |
| Listener owner | Candle API process | NOT AVAILABLE | NOT VERIFIED |
| Deployed source | Exact expected SHA and checkout identity | NOT AVAILABLE | NOT VERIFIED |
| Flask health provider | Production provider registration proven if app is deployed | NOT AVAILABLE | NOT VERIFIED |
| Gateway | Not required for same-host loopback | NOT AVAILABLE | NOT REQUIRED unless remote/browser route is approved |

## Final evidence disposition

- DEP-01: NOT AVAILABLE
- DEP-02: NOT AVAILABLE
- DEP-03: NOT AVAILABLE
- DEP-04: NOT AVAILABLE
- DEP-05: NOT AVAILABLE
- DEP-06: NOT AVAILABLE
- DEP-07: NOT AVAILABLE
- DEP-08: NOT AVAILABLE
- DEP-09: NOT REQUIRED for same-host loopback; otherwise NOT AVAILABLE
- Overall evidence-scope status: BLOCKED / AWAITING OWNER-SUPPLIED EVIDENCE
- Deployment parity: NOT VERIFIED
- Operational readiness: NOT VERIFIED
- Runtime probes: NOT RUN
- Tests / GitHub Actions: NOT RUN / NOT DISPATCHED

## Decision boundary

This intake sheet grants no authority to access VPS/SSH, inspect services, make API requests, read databases/data/secrets, change networking, deploy, restart, or perform destructive operations. Any such activity requires separate exact-scope owner approval. Option C — No Destructive Authority — remains active.
