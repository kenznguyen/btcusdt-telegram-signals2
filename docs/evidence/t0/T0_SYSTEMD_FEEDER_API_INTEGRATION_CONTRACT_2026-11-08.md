# T0 Feeder/API systemd integration contract — 2026-11-08

## Status

**DESIGN REVIEW ONLY — NOT IMPLEMENTED / NOT VERIFIED.**

This document defines the next disposable-CI integration boundary after the SQLite WAL Keeper implementation. It does not authorize production service files, VPS changes, canonical database creation, Feeder startup, API startup, or T2 activation.

## Source baseline inspected

- Repository: kenznguyen/btcusdt-telegram-signals2
- Branch: feature/t0-centralized-data-feeder-p1-20261101
- Inspected branch HEAD: 6360fc8ad04931423c6c293046bd025d3da71f46
- market_data/feeder_service.py blob: a31fdf05af6bdcc007373f4d8fa6b319a08de63b
- market_data/api.py blob: 81733c9b6de811cbebb2f5d472d41f37f337990c
- market_data/feeder.py blob: 22e57bfd24557b538bf314e8aef3369843c07949
- Existing sandbox workflow: .github/workflows/t0-sqlite-readonly-sandbox.yml, blob a41e63cc7581606c6fb1bea264c1340d6448355d

## Findings

1. FeederRuntime.start() acquires its fencing lease, opens the optional WAL Keeper, completes recovery, starts the scheduler, marks its internal state RUNNING/ready, and starts heartbeat.
2. run_service() waits for stop/lease loss and drains the runtime, but does not send a systemd readiness notification. A Type=notify unit therefore cannot truthfully become READY with the current entrypoint.
3. The WSGI /health route returns a liveness response without checking Feeder readiness, lease ownership, or whether SQLite WAL/SHM are available. It must not be used as proof of API data readiness.
4. /v1/candles performs the actual store read and returns 503 on storage errors; this is the correct data-path probe for the disposable integration test.
5. Repository tree inspection found no checked-in Feeder/API .service unit. The existing systemd workflow exercises a transient read-only sandbox, not two dependent services.
6. The Feeder lifecycle already preserves the WAL Keeper until scheduler drain and exact lease release. A systemd stop order must preserve that contract.

## Required service contract

### Feeder

- Unit type must not report READY before FeederRuntime.start() returns true.
- The production entrypoint must send READY=1 only after lease acquisition, WAL Keeper open, recovery completion, scheduler startup, and heartbeat startup.
- On orderly shutdown, stop scheduler admission, stop/join heartbeat, drain writers, release the exact lease generation, close WAL Keeper, then report stopping/exit.
- If lease ownership is lost or startup fails, readiness must be withdrawn and the process must exit non-zero after safe cleanup.
- If drain or lease release is unresolved, do not close WAL Keeper or report a clean stop.

### API

- API service must start only after Feeder readiness, not merely after Feeder process creation.
- The API service runs under a distinct unprivileged identity and receives a read-only mount of the SQLite data directory. Filesystem ownership alone is not accepted as isolation.
- API data-path readiness is verified with an authenticated GET /v1/candles against the disposable database. GET /health is liveness only.
- If the Feeder unit becomes inactive or fails, systemd dependency semantics must stop the API service. API must not remain available against a database whose WAL Keeper lifecycle is no longer guaranteed.
- Normal shutdown must stop API before Feeder.

### Dependency semantics to validate

The test must prove the effective behavior of Requires=, After=, and BindsTo= (or a justified equivalent) using actual transient systemd units. Configuration text alone is not evidence. In particular:
- API does not enter active state before Feeder's readiness notification.
- Feeder unexpected termination causes API to stop.
- An orderly stop stops API before Feeder releases the lease and closes the Keeper.
- Feeder restart re-establishes lease, Keeper, and recovery before API is allowed to restart.

## Disposable CI acceptance matrix

| Scenario | Required observation | Current status |
|---|---|---|
| Feeder starts and recovers | systemd sees READY only after runtime ready | NOT RUN |
| API starts after readiness | authenticated candle read succeeds under ReadOnlyPaths | NOT RUN |
| API starts while Feeder is starting | API remains inactive | NOT RUN |
| Feeder SIGKILL | API becomes inactive; no orphan API process | NOT RUN |
| Orderly shutdown | API stops before Feeder Keeper closes | NOT RUN |
| Feeder restart | API stays down until new READY; then data read succeeds | NOT RUN |
| WAL/SHM absent on cold start | API remains blocked until Feeder Keeper establishes sidecars | Prior sandbox evidence only; integrated case NOT RUN |
| API write attempt | filesystem and SQLite mutation are denied | Prior sandbox evidence only; two-service case NOT RUN |

## TDD implementation sequence

1. RED: add a disposable systemd integration harness and prove the current Feeder entrypoint cannot satisfy a Type=notify readiness gate; demonstrate API liveness is not data readiness.
2. GREEN: add the smallest systemd notification adapter to the Feeder entrypoint, with unit tests for READY/STOPPING and failure behavior. Do not change lease, WAL Keeper, or scheduler ordering.
3. Add transient systemd Feeder and API units in CI. Use a disposable SQLite database, real FeederRuntime, real SQLiteWalKeeper, and the existing WSGI API application. Keep all network bindings on loopback.
4. Prove startup ordering, authenticated API data read, Feeder crash propagation, orderly shutdown, and restart.
5. Run focused lifecycle/API tests and the full market_data regression. Upload logs, exact checked-out SHA, unit properties, event ordering, and artifact digest.
6. Update this handoff with exact source SHA, workflow run, artifact ID/digest, and per-scenario verdict before any production design is reconsidered.

## Explicit non-goals and safety boundaries

- No production .service files or package installation in this increment.
- No VPS access or mutation.
- No canonical T0 database creation, Feeder/API runtime activation, exchange connection, market-data ingestion, or T2 activation.
- No firewall, secret, filesystem permission, DNS, reverse proxy, or public network changes.
- No change to the T0 canonical data provider or database choice.
- ai_execution_enabled=false; no live orders or trading execution.
