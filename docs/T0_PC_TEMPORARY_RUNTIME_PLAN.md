# T0 PC Temporary Runtime Plan

Updated: 2026-11-06 (Asia/Ho_Chi_Minh)

## 1. Decision boundary

**Status: PLAN ONLY — NOT AUTHORIZED TO START.**

The PC is the proposed temporary validation host while VPS suitability is unproven. This plan does not designate the PC as a production/canonical host and does not authorize:
- creating or opening the canonical T0 database;
- starting the production Feeder or any runtime that writes canonical data;
- connecting to Binance/OKX or synchronizing live market data;
- provisioning PostgreSQL, VPS, cloud resources, credentials, TLS, firewall rules, or paid services;
- enabling Paper execution or live trading.

Any transition from source-level/offline checks to a running Feeder, even on a PC-local disposable database, requires an explicit scope approval because the current project handoff prohibits Feeder startup absent authorization.

The PC and a future VPS must never operate as concurrent canonical writers. A VPS cutover requires a separately approved stop → fence → verify → restore/initialize → advance lease generation → start-one-writer sequence.

## 2. Source-derived architecture

Repository: `kenznguyen/btcusdt-telegram-signals2`  
Active branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Branch HEAD at plan creation: `a743295f7b5399f0555e8d292041a7b41b864925`.

Reviewed source:
- `market_data/feeder_service.py` — production composition, injected `build_runtime()`, production `build_production_runtime()`, and `run_service()`.
- `market_data/storage.py` — SQLite default; PostgreSQL opt-in; constructors are side-effect free; migrations are explicit.
- `.github/workflows/t0-single-writer-gateway-red.yml` — GitHub Actions push/PR checks, source-only static job, disposable TimescaleDB jobs.
- `docs/T0_STAGING_ACCEPTANCE_CHECKLIST.md` — provider staging gates A–G.

Source facts relevant to PC planning:
- `build_runtime()` accepts injected exchange, store, lease store and clock; this is the appropriate composition seam for deterministic offline tests.
- SQLite candle storage and lease storage must point to the same database file.
- PostgreSQL candle storage, lease store and fenced write gateway must use the same DSN.
- SQLite remains the default; PostgreSQL is opt-in.
- Schema initialization/migrations are explicit; runtime constructors must not be treated as permission to provision storage.
- `build_production_runtime()` constructs a Binance USD-M CCXT client. It is not an offline/synthetic test entrypoint.
- The production PostgreSQL path requires remote-host TLS `sslmode=verify-full`, fixed canonical lease identity, no configured shared owner ID, and a per-process generated owner capability.
- Runtime shutdown uses bounded drain; lease loss/failure closes the runtime rather than switching to an unfenced writer.

## 3. Proposed PC validation topology

### Stage 0 — repository and environment inspection (read-only)
- Confirm branch and exact HEAD; inspect handoff and workflow definitions.
- Record PC OS/version, Python version, available disk/RAM, filesystem type, time synchronization and network characteristics only when the operator supplies/access authorizes this information.
- Do not install packages, alter OS power settings, create DBs, or start services in this stage.

### Stage 1 — offline deterministic validation
- Use the injected `build_runtime()` seam with a fake exchange implementation returning synthetic closed M15/H1 candles.
- Use a disposable temporary SQLite database only after a separate runtime-test approval.
- Initialize the disposable schema explicitly; point candle and lease stores to the exact same DB path.
- Assert there are no external network calls, no exchange credentials, no Paper DB path, and no production DSN.
- Exercise scheduler timing, retry, bounded recovery, idempotent duplicate writes, conflicting-candle rejection, health/readiness and graceful stop.
- Do not call `build_production_runtime()` or `main()` for offline tests.

### Stage 2 — local process lifecycle and fault tests
Only after explicit approval to run the isolated test runtime:
- Start exactly one test process against a disposable local database.
- Test process stop/restart, SIGTERM/SIGKILL, DB lock/storage errors, disk-full simulation, clock drift handling and lease expiry/takeover.
- Confirm readiness closes on lease loss and no old generation can write after takeover.
- Keep all test data synthetic and all network access disabled.
- Never reuse a canonical database or production lease identity.

### Stage 3 — PC endurance test
Only after Stage 1–2 pass and a separate approval defines the exact runtime/data source:
- 72-hour initial observation, then 7-day endurance window.
- Record process uptime, host uptime, M15/H1 schedule lag, heartbeat age, lease generation, recovery/gap counts, write latency/errors, duplicate/conflict counts, CPU/RAM/disk, time drift and restart history.
- Define alert thresholds and evidence retention before starting the clock.
- A test with synthetic input proves process/runtime stability only; it does not prove exchange connectivity, canonical data correctness, VPS readiness or production availability.

### Stage 4 — live market-data source on PC (separate approval required)
- Only after the user explicitly authorizes the exchange market-data connection and a disposable/noncanonical destination.
- Use public market-data access only; no API key, trading permission, private account endpoint or order endpoint.
- Validate closed-candle boundaries, rate limits, reconnect, backfill, data provenance and gap detection.
- Do not promote the PC database to canonical based solely on this test.

### Stage 5 — VPS staging and cutover proof
- VPS remains undecided and unprovisioned until separately approved.
- Repeat relevant tests against the exact selected host/provider, engine/extension version and source SHA.
- Complete staging acceptance gates A–G, including TLS, effective roles, backup/PITR, restore, measured RPO/RTO, old-primary fencing and lease-generation advancement.
- PC remains stopped and fenced before any VPS canonical writer is admitted.
- Do not perform cutover until every required gate is PASS and the user explicitly approves it.

## 4. Acceptance matrix

| Area | Required evidence | Current status |
|---|---|---|
| Source composition seam | Review of injected `build_runtime()` | SOURCE REVIEWED |
| SQLite same-file invariant | Existing source contract | SOURCE REVIEWED |
| PostgreSQL same-DSN invariant | Existing source contract | SOURCE REVIEWED |
| Offline fake-source runtime | Exact PC run + synthetic fixture logs | NOT RUN |
| Process lifecycle on PC | Restart/fault-injection logs | NOT RUN |
| PC 72-hour / 7-day endurance | Timestamped telemetry and incident log | NOT RUN |
| Live source correctness on PC | Separately approved market-data evidence | NOT AUTHORIZED |
| PC backup/restore | Independent restore + row/key/hash comparison | NOT RUN |
| VPS provider/engine compatibility | Provider-specific staging evidence | BLOCKED / NOT VERIFIED |
| VPS PITR, RPO/RTO, old-primary fencing | Gates A–G evidence | NOT VERIFIED |
| Canonical writer cutover | Explicit approval + single-writer proof | NOT AUTHORIZED |

Suggested operational targets for a future approved PC endurance test (not achieved evidence):
- 7 consecutive days without an unexplained process interruption;
- zero undetected missing closed candles in the tested synthetic/source window;
- zero duplicate-key/different-value candle overwrites;
- exactly one active writer;
- recovery, lease fencing and backup/restore all PASS;
- zero unresolved critical errors.

## 5. Safety and rollback invariants

1. No simultaneous PC/VPS canonical writers.
2. No fallback to an unfenced writer when lease or database connectivity fails.
3. No weakening of `_assert_writer_roles_safe()`, owner-role constraints, TLS checks or write-gateway fencing to make a provider/PC test pass.
4. No Paper DB, Paper WriterToken or Paper execution state is stored in T0.
5. No production credentials or trading permissions on the PC.
6. Stop admission before draining; on drain timeout retain the lease and remain non-ready.
7. Preserve source SHA, workflow run, job IDs, artifact ID/digest, test logs and exact verdict for each increment.
8. PC test success is not VPS certification and is not production authorization.

## 6. Current blockers and next safe action

- PostgreSQL 16 non-superuser CREATEROLE bootstrap is BLOCKED by automatic ADMIN membership that conflicts with the existing strict T0 role guard. Keep the guard unchanged.
- Provider-specific role bootstrap, TLS CA/SAN, backup/PITR, restore, RPO/RTO and failover fencing remain NOT VERIFIED.
- No VPS/provider has been selected or provisioned.
- The latest recorded core source/CI evidence applies to its exact historical SHAs; do not transfer PASS to a newer source tip without exact-source evidence.

Next safe action: prepare a PC capability inventory and a read-only local test checklist. Do not install dependencies, change OS settings, create/open a database, start a Feeder, connect an exchange or sync market data until the user approves the exact next test scope.
