# T0 Feeder/API systemd integration test plan

Date: 2026-11-08
Status: **IMPLEMENTED — PASS ON DISPOSABLE GITHUB ACTIONS RUNNER; VPS NOT VERIFIED**

## 1. Purpose

Verify real systemd dependency and lifecycle behavior between a disposable T0 Feeder process and the existing read-only WSGI Candle API. This test runs only on a disposable GitHub Actions Linux runner and uses a synthetic SQLite database. It must not target the VPS or canonical data.

## 2. Existing verified prerequisites

- `FeederRuntime` acquires the fencing lease, opens `SQLiteWalKeeper`, completes optional recovery, starts the scheduler and heartbeat, and only then returns success from `start()`.
- `run_service()` sends `READY=1` only after successful runtime start and sends `STOPPING=1` before runtime drain.
- The API exposes authenticated GET `/v1/candles`; `/health` is liveness only and is not a readiness assertion.
- Notification unit/lifecycle tests passed at source SHA `2484cc73edc155b2566b9d73199ad713e04acb10`; the existing isolated WAL sandbox also passed at that SHA.
- These results do not prove actual two-unit systemd ordering, dependency propagation, or API access while the keeper is active.

## 3. Disposable harness architecture

- Use a temporary directory and synthetic SQLite file created by the test harness. Seed only one synthetic BTCUSDT 15m candle before starting services.
- Start a real `FeederRuntime` with the real `LeaseStore` and `SQLiteWalKeeper`. Use deterministic in-process scheduler/recovery adapters so no exchange connection, credentials, live data sync, or order path is involved.
- Start the existing `market_data.api:application` through a small WSGI server bound only to `127.0.0.1`.
- Feeder unit: `Type=notify`, `NotifyAccess=all`, finite startup timeout.
- API unit: `After=` and `Requires=` the Feeder unit, plus `BindsTo=` so loss of the Feeder stops the API. The API must have the database directory mounted read-only; WAL/SHM sidecars must already exist and remain owned by the Feeder keeper.
- Both units run only on the GitHub Actions disposable runner. Unit names, ports, DB paths, tokens, and event logs are test-scoped and generated for the job.

## 4. Required assertions

1. **Readiness gating:** hold Feeder recovery in a deterministic startup barrier; request API startup; prove API remains inactive until Feeder emits systemd READY and becomes active.
2. **Data-path readiness:** after both units are active, authenticated GET `/v1/candles` returns HTTP 200 and the seeded synthetic candle; unauthenticated request returns 401. Do not use `/health` as proof of data readiness.
3. **Crash propagation:** SIGKILL the Feeder unit; prove the API unit becomes inactive through `BindsTo=` and no API data request remains available.
4. **Restart:** start a fresh Feeder unit against the same disposable DB; verify a new lease generation and successful authenticated API read after starting its dependent API unit.
5. **Orderly shutdown:** stop the Feeder unit; prove the API receives termination before the Feeder begins graceful drain, and both units become inactive.
6. **Filesystem boundary:** while the keeper holds WAL/SHM, API can read through the existing read-only store path but cannot mutate the DB directory or candles.

## 5. Evidence requirements

The workflow must record:
- exact source SHA and runner OS/systemd version;
- unit properties and dependency graph;
- timestamped Feeder/API lifecycle events;
- HTTP status and response assertions without exposing the test bearer token;
- SIGKILL/restart and orderly-stop outcomes;
- test verdict and artifact digest.

The job must fail closed if systemd, `systemd-run`, or required privileges are unavailable. It must never silently downgrade to mocked systemd behavior.

## 6. Explicit non-goals

- No production `.service` files or VPS deployment.
- No changes to the existing VPS, firewall, packages, permissions, secrets, ports, DNS, reverse proxy, or processes.
- No canonical database, exchange credentials, external exchange calls, data ingestion, or market-data deletion.
- No T2 runtime activation, live trading, or change to `ai_execution_enabled=false`.

## 7. Acceptance boundary

A passing job proves only that the tested transient systemd units and synthetic SQLite/API/Feeder composition behave as asserted on that GitHub runner image. It does not certify the Scaleway VPS kernel, systemd version, filesystem, service identities, production unit files, or deployed API.


## 8. Executed evidence — 2026-11-08

- Harness: `ci/t0_systemd_feeder_api_integration.py`.
- Workflow: `.github/workflows/t0-systemd-feeder-api-integration.yml`.
- Exact source SHA: `0e73f9184bb15561341e76c31f698ba96e2a2703`.
- GitHub Actions run: `42488536321` — SUCCESS; job `128755620737` — SUCCESS.
- Runner systemd: `systemd 259 (259.9-0ubuntu0.1)`.
- Observed timestamped events prove:
  - `FEEDER_READY_GENERATION_1` precedes API process start;
  - authenticated candle read succeeds and unauthenticated request returns 401;
  - API write probe is denied in both API service instances while the API can read the synthetic candle;
  - SIGKILL of Feeder causes API termination via `BindsTo=`;
  - a new Feeder lease generation (`2`) is acquired on restart and the dependent API reads successfully;
  - during orderly shutdown, `API_SIGTERM` precedes `FEEDER_SIGTERM`, followed by Feeder STOPPING/drain and exit.
- Final marker: `T0_SYSTEMD_FEEDER_API_INTEGRATION=PASS`.
- Evidence artifact: `t0-systemd-feeder-api-integration-0e73f9184bb15561341e76c31f698ba96e2a2703`, ID `13620800948`, digest `sha256:5a0e932e6145958a2aa9b88be14a5198075b107d9b1b01d3cd58849747f2305c`.
- Scope remains synthetic disposable SQLite and transient systemd units on the GitHub runner. This does not certify VPS systemd/kernel/filesystem behavior, production service identities, production unit definitions, or deployment readiness.

- Final self-review cleanup removed unused harness imports; exact final source SHA was rerun and remained PASS (run `42488536321`). No behavioral code changed in this cleanup.
