# T0 Simplification — Health Endpoint Ownership and Caller Audit

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact branch HEAD inspected: `78c26ce83a490ec0cee86e34b67d098e6129bbf2`
- Operation class: READ-ONLY STATIC SOURCE / TEST / WORKFLOW REVIEW
- Scope: distinguish Feeder liveness, readiness, canonical-data freshness and Candle API process health; map tracked callers and deployment evidence; assess whether health logic is safely duplicative.
- No source, test, package, workflow, schema, runtime, VPS, database, provider, secret, permission or data changes. No tests or GitHub Actions were run or dispatched.

## 1. Result

**PARTIAL — endpoint ownership and in-repository callers are mapped; production health-provider wiring, external monitoring and deployed reverse-proxy routing are NOT VERIFIED. No safe endpoint consolidation is established.**

The repository has two distinct HTTP applications:

1. Root Flask application in `app.py`: Feeder-oriented health contract:
   - `GET /health/live`
   - `GET /health/ready`
   - `GET /health/data`
   - `GET /health` (aggregate readiness alias)
2. WSGI Candle API in `market_data/api.py`:
   - `GET /health` (API process response only)
   - `GET /v1/candles` (authenticated read-only candle contract)

The two `/health` routes belong to different applications/processes and answer different questions. They must not be merged on the basis of matching path names.

## 2. Exact source evidence

| Path | Blob SHA | Responsibility / finding |
|---|---|---|
| `app.py` | `760d6d8e8a8680160df97f030931fda256205072` | Flask Feeder health routes and response mapping |
| `market_data/feeder.py` | `935d295ef42c94482a48ce6ccdc927ebfa4c7e22` | `HealthEvaluator`, per-timeframe freshness, readiness and lifecycle overlay |
| `market_data/feeder_service.py` | `bdcecf6bc98a2ff070f83098d2c50154a160c99c` | Production Feeder composition, lease/recovery and systemd readiness notifications |
| `market_data/api.py` | `81733c9b6de811cbebb2f5d472d41f37f337990c` | Independent Candle API `/health` and authenticated `/v1/candles` |
| `market_data/test_feeder_health.py` | `80e0b7d042c821d4814d626b69c3196853dc49d9` | Evaluator contract: liveness, readiness, lease, storage and M15/H1 freshness |
| `market_data/test_feeder_health_api.py` | `a3d11257a0c914835a86a8a6b5502bcf93c800a2` | Flask HTTP route status/body contract |
| `market_data/test_feeder_lifecycle.py` | `5797d51e3165721863ceacb1fac76f44055f18a7` | Feeder lifecycle, lease loss, startup recovery and shutdown/readiness ordering |
| `market_data/test_api.py` | `49df7e0bec12908adae67f18a4aa19063e461093` | Candle API health, auth, read-only and fail-closed behavior |
| `ci/t0_systemd_feeder_api_integration.py` | `dd2880c63a3396934aeb19620e522aa20106e7c4` | Disposable integration harness for Feeder/API systemd dependency; probes API `/health` only for post-stop unavailability |
| `.github/workflows/t0-systemd-feeder-api-integration.yml` | `64476a3dd281eb69b92d29f3783570107c4ab48e` | Disposable GitHub-hosted systemd integration workflow; does not establish deployed host monitoring |
| `market_data/README.md` | `19485ce933e15433c412a54ab15d9cbc1860dfd7` | Documents Candle API `/health` as process-only, not database/feed health |
| `control_dashboard/src/api.js` | `38cb5a464b05acd77914c7f333d377d8ac0535ad` | Dashboard HTTP helper permits only `/v1/*` paths; no health endpoint caller |

## 3. Endpoint contract matrix

| Endpoint | Owner | What it answers | Status semantics |
|---|---|---|---|
| Flask `/health/live` | `app.py` + `HealthEvaluator` | Is the Flask/Feeder health process considered running? | 200 when `live`; 503 otherwise. It remains live during storage failure or lease degradation. |
| Flask `/health/ready` | `app.py` + `HealthEvaluator` | Has startup/recovery completed, storage is readable/writable, lease is valid, and all configured timeframes are healthy? | 200 only when evaluator readiness is true; otherwise 503. |
| Flask `/health/data` | `app.py` + `HealthEvaluator` | Are the snapshot provider and each timeframe's freshness/coverage health acceptable? | 200 only when provider is configured, timeframe results exist, aggregate state is not FAILED/STOPPED, and every timeframe is HEALTHY. This is not equivalent to readiness: a lease-only degradation can leave data healthy while readiness is false. |
| Flask `/health` | `app.py` | Aggregate health/readiness compatibility endpoint | Same result body and readiness status as `/health/ready`. Candidate alias, but no complete external caller map exists. |
| Candle API `/health` | `market_data.api` | Can this API WSGI process answer a GET request? | Returns 200 `{"ok":true,"service":"canonical-market-data"}` before token/store checks. Does not verify DB availability, Feeder state, lease or freshness. |

## 4. Ownership and lifecycle findings

### 4.1 Feeder evaluator

- `HealthEvaluator` owns state calculation, not HTTP transport.
- Liveness is derived from `process_running`.
- Readiness requires startup completion, readable and writable storage, valid lease, no fatal error, and all configured timeframe states HEALTHY.
- M15 and H1 are independently evaluated. One full interval of lag is DEGRADED; two intervals is STALE. Unresolved gaps or sync errors also degrade the timeframe.
- `FeederRuntime.health_snapshot()` overlays authoritative runtime lifecycle state (RUNNING, LEASE_LOST, STOPPED, FAILED) onto a supplied source snapshot.
- `feeder_service.run_service()` sends systemd `READY=1` only after `runtime.start()` succeeds, and sends `STOPPING=1` before draining. These notifications are systemd service-manager lifecycle signals, not HTTP health routes.

### 4.2 Flask HTTP adapter and unresolved provider

- `app.py` reads `T0_HEALTH_SNAPSHOT_PROVIDER` from Flask app config; it does not itself construct a snapshot from the production Feeder, database or lease store.
- If the provider is absent/non-callable, the adapter constructs an unavailable-storage snapshot and fails readiness closed.
- The HTTP tests inject a synthetic provider and clock through app config. This proves the route contract under test injection, not production provider wiring.
- No production registration/binding of `T0_HEALTH_SNAPSHOT_PROVIDER` was established in the inspected files. Production Flask health data therefore remains **NOT VERIFIED**; do not treat these routes as a proven operational Feeder monitor.

### 4.3 Candle API

- `market_data.api` handles its own process health before authentication and store construction.
- `market_data/README.md` explicitly states that this route does not confirm database contents or feed activity.
- The disposable integration harness calls this API `/health` to confirm that the dependent API is unreachable after Feeder termination. It does not call the root Flask Feeder health routes.

## 5. Caller / deployment map

| Caller / surface | Evidence | Result |
|---|---|---|
| `market_data/test_feeder_health.py` | Direct evaluator tests | Confirms evaluator semantics |
| `market_data/test_feeder_health_api.py` | Flask test client calls all four Flask routes | Confirms HTTP contract under injected test provider |
| `market_data/test_api.py` | WSGI environ calls Candle API `/health` | Confirms process-only API health contract |
| `ci/t0_systemd_feeder_api_integration.py` | Uses API `/health` after service stop; authenticated candle read before stop | Confirms integration harness uses Candle API health, not Flask health |
| `control_dashboard/src/api.js` | Path guard requires `/v1/` | Dashboard helper does not call health endpoints |
| `control_dashboard/src/App.jsx` | Data Quality Monitor consumes the dashboard's configured API/data response; no health path call found in inspected component | No direct caller of the health routes established |
| Git-tracked Nginx config | Root tree and `ops/` inventory inspected; no Nginx configuration file found | No in-repo proxy routing evidence |
| VPS Nginx / external probes / service manager deployment | Not accessible from repository source inspection | NOT VERIFIED |

The root Flask health application and Candle API are separate route owners. A reverse proxy could route identical `/health` paths to different upstreams, but no checked-in Nginx route map proves which upstream is exposed in deployment.

## 6. Simplification assessment

- **KEEP** `HealthEvaluator` as the single owner of Feeder health-state calculation.
- **KEEP** independent liveness, readiness and data freshness semantics; they answer different operational questions.
- **KEEP** Candle API process-only `/health`; its narrow semantics are documented and tested.
- **DO NOT MERGE** Flask `/health` with Candle API `/health`; distinct process boundaries and contracts.
- **PARK** Flask `/health` versus `/health/ready` alias cleanup. They currently have identical implementation semantics, but removing one requires a complete external caller and reverse-proxy inventory.
- **BLOCKED / NOT VERIFIED** production snapshot-provider wiring for Flask health. This is a more material gap than code duplication.
- No behavior-preserving source simplification candidate is approved by this audit.

## 7. Evidence and verification status

- Static source/test/workflow inspection: **PARTIAL PASS** within listed repository paths.
- Endpoint ownership and semantics: **MAPPED**.
- In-repository caller map: **PARTIAL**; no direct dashboard health caller found; integration harness uses Candle API health.
- Production snapshot provider registration: **NOT VERIFIED**.
- External Nginx, VPS, uptime monitor, load balancer and service-manager health-check configuration: **NOT VERIFIED**.
- Tests: **NOT RUN**.
- GitHub Actions: **NOT DISPATCHED**; no workflow run or artifact is claimed.
- Deployed runtime parity: **NOT VERIFIED**.

## 8. Next step

Perform a read-only deployment/configuration inventory for the exact production/test host contract: identify the Flask app launch target, Candle API launch target, systemd unit ExecStart/health-check behavior, and Nginx upstream/path routing. Do not modify or probe the VPS. If deployment files are not versioned or accessible, record the corresponding items as owner-supplied evidence required and keep the health routes unchanged.

## 9. Restrictions

- No source, test, workflow, dependency, schema or runtime changes.
- No VPS/SSH/Nginx/systemd inspection or probes without separate approval.
- No health endpoint consolidation or response-semantic changes.
- No workflow dispatch, test execution, database access or data collection.
- Option C — No Destructive Authority — ACTIVE.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- T0 and L4-Minimum acceptance remain BLOCKED / NOT VERIFIED.
