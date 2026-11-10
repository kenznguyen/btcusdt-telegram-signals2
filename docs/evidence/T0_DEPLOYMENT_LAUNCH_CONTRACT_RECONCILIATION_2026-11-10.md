# T0 Deployment Launch Contract Reconciliation — Feeder, Candle API and Gateway

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact source baseline: `9fb2007738c09743ae8efa72ee74a70de115e911`
- Operation class: STATIC SOURCE / DOCUMENTATION REVIEW
- Feeder source blob: `bdcecf6bc98a2ff070f83098d2c50154a160c99c`
- Candle API source blob: `81733c9b6de811cbebb2f5d472d41f37f337990c`
- README baseline blob: `19485ce933e15433c412a54ab15d9cbc1860dfd7`
- Prior DEP protocol: `docs/evidence/T0_OWNER_READONLY_DEPLOYMENT_EVIDENCE_PROTOCOL_2026-11-10.md`
- Prior preflight audit: `docs/evidence/T0_READONLY_PREFLIGHT_STATIC_SAFETY_AUDIT_2026-11-10.md`

## 1. Decision

**DOCUMENTARY CONTRACT RECONCILIATION COMPLETE — HOST PARITY NOT VERIFIED.**

The repository defines two independent process launch targets:

- Feeder: `python -m market_data.feeder_service`
- Candle API: Gunicorn WSGI target `market_data.api:application`, bind `127.0.0.1:8788`

For the selected same-host T0 → T2 topology, the API remains loopback-only and Nginx/reverse proxy is not required. A separate remote/browser gateway would be a distinct architecture and approval scope.

The README wording was clarified to distinguish these two topologies. This is documentation-only; no gateway, service, listener, runtime or network configuration was changed.

## 2. Feeder launch contract — source facts

Static inspection of `market_data/feeder_service.py` confirms:

1. Module entrypoint invokes `main()`, which calls `build_production_runtime()` and then `run_service()`.
2. The production runtime selects `MARKET_DATA_BACKEND` from environment, defaulting to `sqlite`; the canonical SQLite path remains the selected T0 scope. This report does not inspect deployed environment values.
3. Runtime composition requires the SQLite candle store and lease store to resolve to the same database path.
4. Startup returns failure if `runtime.start()` is not true.
5. After successful startup, the service sends `READY=1` through `systemd_notify()`; during shutdown it sends `STOPPING=1` and drains with a 30-second timeout.
6. If `NOTIFY_SOCKET` is absent, `systemd_notify()` returns false. Therefore source behavior alone does not prove that the deployed unit uses `Type=notify`, nor that systemd readiness notification is active.
7. When systemd supplies a notification socket, the effective unit must be compatible with the notification mechanism. The actual `Type`, `NotifyAccess`, `ExecStart`, user, working directory, environment-file references, restart and dependency settings must come from DEP-03 host evidence.

**Important:** `Type=notify` is required only if the deployment intends systemd to gate readiness on `READY=1`. A unit using another service type may still launch the process but does not provide equivalent notification-based readiness semantics. Do not silently treat those configurations as equivalent.

## 3. Candle API launch contract — source facts

Static inspection of `market_data/api.py` and `market_data/README.md` confirms:

- WSGI callable: `market_data.api:application`.
- Documented production command: `gunicorn --bind 127.0.0.1:8788 --workers 1 --threads 4 --timeout 20 market_data.api:application`.
- Development module entrypoint binds `127.0.0.1` and uses `PORT`, default 8788.
- `GET /health` reports process-level API liveness only.
- Authenticated `GET /v1/candles` is the data-path contract. It checks configured token and storage, then reads the selected store.
- No API request, token use, database access or runtime probe was performed during this reconciliation.

The effective deployed command, interpreter, working directory, environment-file references, unit identity and listener ownership remain host facts, not source facts.

## 4. Topology and reverse-proxy clarification

The README now explicitly separates:

**Same-host T0 → T2**
- Candle API binds to `127.0.0.1:8788`.
- T2 consumes the API through loopback.
- No Nginx, HTTPS reverse proxy or public listener is required for this internal path.

**Remote/browser access**
- Do not expose the Candle API directly to the public network.
- Any remote/browser access requires a separately designed and approved TLS gateway/reverse proxy, authentication and routing boundary.
- No gateway implementation or deployment is authorized by this documentation change.

This clarification does not alter the existing same-host loopback decision.

## 5. DEP evidence mapping

| Evidence | Feeder contract comparison | Candle API contract comparison | Status without host evidence |
|---|---|---|---|
| DEP-01 time/host | Collection provenance only | Same | NOT AVAILABLE |
| DEP-02 unit names | Need exact Feeder unit name | Need exact API unit name | NOT VERIFIED |
| DEP-03 Feeder properties | Compare `ExecStart=python -m market_data.feeder_service`, interpreter, cwd, user/group, notify type, restart/dependencies/timeouts | — | NOT VERIFIED |
| DEP-04 API properties | — | Compare Gunicorn WSGI target, loopback bind, workers/threads/timeout, interpreter/cwd/user | NOT VERIFIED |
| DEP-05 process identity | Executable/cwd/comm for Feeder MainPID | Same for API MainPID | NOT VERIFIED |
| DEP-06 listener | No listener required by Feeder contract | Port 8788 must bind loopback only for selected topology | NOT VERIFIED |
| DEP-07 deployed SHA | Exact checkout SHA and clean/dirty state; confirm process working directory points to that checkout | Same | NOT VERIFIED |
| DEP-08 Flask health app | Determine whether separate root Flask app is deployed; if yes, prove provider registration path | Not part of Candle API WSGI contract | NOT VERIFIED |
| DEP-09 gateway | Not required for same-host path | Not required for same-host path | NOT REQUIRED for current topology |

DEP-01–DEP-09 remain an evidence request. This mapping does not itself supply any host evidence.

## 6. Readiness semantics — do not conflate

1. **Process existence:** a PID exists; not proof of successful initialization.
2. **systemd notification readiness:** meaningful only if the deployed service type and notification access are configured compatibly and the service actually sends the notification.
3. **Candle API `/health`:** API process responds; not proof of database or Feeder readiness.
4. **Authenticated `/v1/candles`:** data-path read contract; requires separate runtime authorization and must inspect coverage/freshness rather than HTTP 200 alone.
5. **Feeder health/lease/freshness:** separate operational state; not established by API liveness or a running PID.

No readiness probe was run or authorized in this work.

## 7. Status and exclusions

| Area | Status |
|---|---|
| Feeder source launch contract | MAPPED |
| Candle API source launch contract | MAPPED |
| Same-host loopback topology | DOCUMENTED |
| README proxy wording | CLARIFIED |
| DEP-to-contract field mapping | COMPLETE |
| Installed systemd unit properties | NOT VERIFIED |
| Actual process/listener identity | NOT VERIFIED |
| Deployed source SHA | NOT VERIFIED |
| Flask production provider registration | NOT VERIFIED |
| Runtime readiness / data freshness | NOT RUN |
| Tests / GitHub Actions | NOT RUN / NOT DISPATCHED |
| VPS / SSH / DB / token access | NONE |
| Destructive authority | NOT GRANTED |

No service unit, Nginx config, process, environment, token, database, data, workflow, permission, secret or runtime was changed. No tests or GitHub Actions were dispatched.

## 8. Next step

Collect the owner-supplied sanitized DEP-01–DEP-09 evidence bundle under the existing protocol. Compare it against this launch contract and record discrepancies only. Any runtime probe, host inspection by an agent, service change, gateway work or database operation requires separate exact-scope approval.
