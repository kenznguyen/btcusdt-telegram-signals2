# T0 Deployment Configuration Inventory — Health and Launch Targets

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact branch HEAD inspected: `ed842b61d95287db50acab32431ab1d97f579362`
- Operation class: READ-ONLY REPOSITORY / DEPLOYMENT-DOCUMENT INVENTORY
- Scope: identify versioned launch targets, systemd unit definitions, Candle API bind contract, reverse-proxy decision, and available evidence for Flask health deployment.
- No VPS/SSH access, runtime probes, source changes, tests, workflow dispatch, database access, secret access, permission changes, or data operations.

## 1. Result

**PARTIAL — repository deployment intent is mapped; deployed service configuration and process state remain NOT VERIFIED.**

The versioned deployment decision for same-host T0 → T2 is a loopback-only Candle API at `http://127.0.0.1:8788`, with no public listener, public DNS, or reverse proxy for this same-host path. The documented API launch command is Gunicorn:

```sh
gunicorn --bind 127.0.0.1:8788 --workers 1 --threads 4 --timeout 20 market_data.api:application
```

This documents the intended Candle API launch target, not proof that the VPS has installed or started it.

The repository does not contain a production Feeder/API `.service` unit, Nginx configuration, or other versioned deployment manifest establishing the actual production launch command and health-check wiring. The root Flask health application in `app.py` has no established production launch target or provider binding in the inspected tracked configuration.

## 2. Evidence inventory

| Artifact | Blob SHA | What it establishes | What it does not establish |
|---|---|---|---|
| `market_data/README.md` | `19485ce933e15433c412a54ab15d9cbc1860dfd7` | Documented Gunicorn Candle API command; loopback bind; `/health` is process liveness only | Installed command, running service, live listener or host configuration |
| `docs/evidence/t2/T0_T2_LOOPBACK_DEPLOYMENT_GATE_2026-11-09.md` | `4919abb30afc5f6fd7a98e013633d1e19d112325` | Owner-selected same-VPS loopback URL `http://127.0.0.1:8788`; reverse proxy/public exposure not part of this path; authenticated `/v1/candles` is readiness proof | Current service/listener/token state; successful live API read |
| `docs/evidence/t0/T0_SYSTEMD_FEEDER_API_INTEGRATION_CONTRACT_2026-11-08.md` | `b4c5b222d27dbbcdeb78e73e1804a5e0eff3dd63` | No checked-in production service unit at that audit; disposable systemd test requirements | Actual VPS service definitions |
| `docs/evidence/t0/T0_SYSTEMD_FEEDER_API_INTEGRATION_TEST_PLAN_2026-11-08.md` | `aceafac91b4d58801e8e7e593935ee8bdf20200b` | CI-only transient unit design and explicit non-equivalence to VPS deployment | VPS kernel/systemd/filesystem/service identity or unit parity |
| `ci/t0_systemd_feeder_api_integration.py` | `dd2880c63a3396934aeb19620e522aa20106e7c4` | Test-only transient units; API loopback port 18788; dependency semantics tested in disposable runner | Production unit names, ports, paths or launch commands |
| `.github/workflows/t0-systemd-feeder-api-integration.yml` | `64476a3dd281eb69b92d29f3783570107c4ab48e` | Workflow for disposable GitHub-hosted systemd integration | Any VPS deployment or production monitoring |
| `ops/ssh/t0-readonly-preflight.sh` | `39de5aa7602cdf7dc301ff6bc65a68fad417ea84` | Existing bounded preflight script can report Feeder PIDs and API port 8788 listener scope | This script was not executed; it does not define service installation |
| `market_data/feeder_service.py` | `bdcecf6bc98a2ff070f83098d2c50154a160c99c` | Python Feeder service entrypoint logic and systemd notify lifecycle | Actual installed unit `ExecStart`, user, environment, restart policy or watchdog configuration |
| `app.py` | `760d6d8e8a8680160df97f030931fda256205072` | Flask Feeder health HTTP routes and config-injected snapshot provider | Production Flask launch target and provider registration |

## 3. Repository deployment-file inventory

A complete recursive tracked-tree inventory at the inspected commit found 707 tracked files. Relevant deployment search found:

- No production `*.service`, `*.socket`, or `*.target` files.
- No checked-in Nginx configuration.
- No Docker/Compose, Supervisor, Caddy, Traefik or Procfile deployment definition for T0.
- One CI-only systemd integration workflow and its transient-unit harness.
- One read-only SSH preflight script.
- Documentation for Gunicorn Candle API launch and loopback-only T0 → T2 routing.

This is a repository inventory only. It cannot establish files installed outside Git.

## 4. Health routing and service interpretation

1. **Candle API process health:** `GET /health` on the Candle API WSGI process. HTTP 200 confirms the API process answers; it does not verify the canonical database, Feeder lease, freshness or authenticated candle reads.
2. **Candle API data-path check:** authenticated `GET /v1/candles` on `127.0.0.1:8788`; this is the documented T0 → T2 readiness proof.
3. **Feeder service readiness:** the Python service entrypoint sends systemd `READY=1` after successful `FeederRuntime.start()`, and sends `STOPPING=1` before draining. The actual installed unit's `Type=notify`, `NotifyAccess`, `ExecStart`, `User`, `EnvironmentFile`, `Restart`, `TimeoutStartSec`, and dependency settings are not present in the repository.
4. **Flask health routes:** the route adapter exposes liveness/readiness/data endpoints but its provider is supplied through Flask app config. No production app factory binding, launcher or service unit was found in the inspected deployment artifacts. Production use remains NOT VERIFIED.

Because the selected T0 → T2 path is loopback-only, absence of Nginx is not itself a defect for that path. If a future browser dashboard or remote client is to access multiple services, that is a separate gateway architecture decision and must not be inferred from the T0 → T2 loopback gate.

## 5. Deployment facts still required

The following evidence must come from an owner-supplied copy of deployment configuration or a separately authorized read-only host inspection:

- Exact Feeder unit name and complete effective unit properties (especially `ExecStart`, `Type`, `NotifyAccess`, `User`, `Group`, `EnvironmentFile`, `WorkingDirectory`, `Restart`, dependency ordering and timeouts).
- Whether the Feeder service runs `market_data.feeder_service` and which Python interpreter / checkout path it uses.
- Exact Candle API unit name and effective `ExecStart`; verify it matches the documented Gunicorn WSGI target and loopback bind.
- Actual listener addresses on port 8788 and whether any other port exposes either application.
- Whether root Flask `app.py` is deployed at all; if yes, its launcher, bind address and `T0_HEALTH_SNAPSHOT_PROVIDER` registration path.
- Effective systemd dependency relationship between Feeder and API, including startup gating, crash propagation and reverse-order shutdown.
- Any installed Nginx configuration only if a separate remote/browser gateway path exists; it is not a prerequisite for the documented same-host T0 → T2 loopback connection.
- Sanitized service status and exact deployed source SHA; never disclose token values or secret-file contents.

## 6. Status and boundaries

| Area | Status |
|---|---|
| Repository deployment intent | MAPPED |
| Candle API documented launch target | MAPPED — NOT VERIFIED ON HOST |
| Loopback-only T0 → T2 routing decision | DOCUMENTED |
| Reverse proxy required for same-host T0 → T2 | NO |
| Production Feeder unit definition | NOT FOUND IN REPOSITORY |
| Production Candle API unit definition | NOT FOUND IN REPOSITORY |
| Root Flask health app production launch/provider binding | NOT VERIFIED |
| Actual VPS processes/listeners/unit properties | NOT VERIFIED |
| Tests / Actions | NOT RUN / NOT DISPATCHED |
| Runtime and database changes | NONE |

## 7. Next step

Do not access the VPS under this documentary authorization. Obtain the effective Feeder and Candle API systemd unit contents (with secrets redacted) and, if Flask is claimed to be deployed, its launcher/provider registration. Then compare these against the repository contracts and record exact differences. If the owner wants host inspection rather than supplying files, obtain separate explicit approval for a strictly read-only inspection command set before using SSH.

## 8. Restrictions

- No VPS/SSH/systemd/Nginx inspection or probes in this step.
- No service install/start/restart/stop or environment changes.
- No source, test, workflow, dependency, database, secret, permission, network, firewall or data changes.
- No health endpoint consolidation or response-semantic changes.
- No tests or GitHub Actions dispatch; no run/artifact claimed.
- Option C — No Destructive Authority — ACTIVE.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- T0 and L4-Minimum acceptance remain BLOCKED / NOT VERIFIED.
