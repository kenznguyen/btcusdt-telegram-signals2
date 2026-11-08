# T2 Live T0 Endpoint — Offline Readiness Audit

Date: 2026-11-08 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Audit baseline HEAD: `aa608fa9288fe45ec32b7d6b56f40695f137b4ac`  
Scope: repository/document inspection only; no network request, VPS access, runtime action, or secret access.  
Verdict: **BLOCKED — LIVE ENDPOINT IDENTITY AND DEPLOYMENT PATH NOT ESTABLISHED**

## 1. Executive result

The repository contains a T0 WSGI candle API implementation and a T2 HTTP client, but the inspected evidence does not identify a deployed HTTPS hostname/base URL, TLS termination layer, production process manager, or approved probe origin.

The API module's direct-development entrypoint binds plain HTTP to loopback `127.0.0.1:8788`. This is not itself a remotely reachable HTTPS endpoint. A separately configured reverse proxy or TLS gateway may exist outside the inspected source, but it has not been evidenced and must not be assumed.

Therefore Phase 0 is **BLOCKED** for live endpoint verification. No URL should be guessed from the VPS label, IP, repository, or local development port.

## 2. Inspected source evidence

| Item | Evidence | Finding |
|---|---|---|
| T0 API source | `market_data/api.py`, blob `81733c9b6de811cbebb2f5d472d41f37f337990c` | Implements GET `/v1/candles`, Bearer token from `MARKET_DATA_TOKEN`, versioned response envelope and bounded query |
| API development entrypoint | Same source, `__main__` block | Uses `wsgiref.simple_server.make_server("127.0.0.1", PORT default 8788, application)`; plain HTTP loopback only |
| T2 client | `freqai_bridge/http_candles.py`, blob `eb9aeccdf381e8a2ebc3450a7a31ae4e9da164ac` | Requires HTTPS for non-loopback hosts; enables certificate verification, disables redirects, and uses bounded timeout/retry/body policy |
| T2 configuration | `freqai_bridge/README.md` and consumer code | Requires `T0_CANDLE_API_BASE_URL`, `T0_CANDLE_API_TOKEN`, `T0_CANDLE_MAX_LAG_MS`; no endpoint hostname or token value is embedded in source |
| T0 API configuration | `market_data/api.py` | Reads `MARKET_DATA_TOKEN`; backend selection via `MARKET_DATA_BACKEND` (default sqlite) and backend-specific environment |
| Contract design | `docs/architecture/T0_READ_ONLY_CANDLE_CONTRACT_V1_2026-11-08.md` | Defines HTTPS across host boundaries; loopback-only is acceptable only for same-host controlled use |
| Existing verification plan | `docs/architecture/T2_LIVE_T0_ENDPOINT_VERIFICATION_PLAN_2026-11-08.md` | Separates endpoint/TLS/auth/read-only checks and requires separate explicit approval before live probes |

## 3. Phase 0 readiness matrix

| Check | Result | Evidence / gap |
|---|---|---|
| Contract route and method | PASS — source-level only | `GET /v1/candles`; non-GET requests return 405 with `Allow: GET` |
| Bearer auth implementation | PASS — source-level only | Compares Authorization header against `MARKET_DATA_TOKEN`; no live credential tested |
| T2 HTTPS enforcement | PASS — source-level only | T2 client rejects non-loopback plain HTTP and always requests with `verify=True` |
| Actual deployed HTTPS hostname/base URL | **BLOCKED** | No approved endpoint identity found in inspected repository docs/config |
| TLS termination / certificate authority | **NOT VERIFIED** | No reverse-proxy, ingress, certificate, or TLS deployment evidence identified |
| API process/service deployment | **NOT VERIFIED** | Source development entrypoint is loopback WSGI; no evidence here that this process is deployed or exposed |
| Probe origin / egress allowlist | **BLOCKED** | No approved probe host or network origin established |
| Credential provisioning owner/store | **BLOCKED** | Variable names are known; secret store, owner and injection route are not evidenced |
| Storage-level read-only enforcement | **NOT VERIFIED** | API calls `store.read_window()`; source inspection alone does not prove deployed DB role/transaction settings |
| T0 runtime health/readiness | **NOT VERIFIED** | No health or live API request made; `/health` is documented as process liveness only |
| T2 runtime isolation | PASS — source/config scope | This audit did not start T2/Freqtrade or alter runtime |

## 4. Important technical distinction

The T0 API's development server is plain HTTP on loopback. T2's client permits plain HTTP only for loopback names/addresses and requires HTTPS for non-loopback hosts. Consequently:

- A same-host loopback deployment could be tested locally only after its actual process/port and authorization are confirmed.
- A remote VPS endpoint requires a separately evidenced HTTPS/TLS front door; the loopback WSGI entrypoint does not provide TLS.
- Do not substitute a public IP, guessed DNS name, VPS hostname, or port 8788 as the endpoint.
- Do not weaken the T2 client's HTTPS requirement to make an unverified deployment work.

## 5. Inputs required to unblock Phase 0

The system owner/operator must provide or confirm through an approved secure operational channel:

1. Exact T0 API base URL (hostname and any non-default port/path); no token.
2. Whether TLS terminates at a reverse proxy/load balancer or another managed ingress, and which CA trust chain is expected.
3. The authorized network origin for a one-shot probe (for example, an isolated GitHub Actions runner only if its egress is allowed).
4. Who owns `MARKET_DATA_TOKEN` and how a short-lived/rotatable credential can be injected without exposing it.
5. Evidence source for the deployed API process and storage-level read-only DB role/transaction mode, without changing T0.

Do not request or record the token in chat. The operator should configure it only in the approved secret manager after the probe scope and environment are authorized.

## 6. Next action and restrictions

**Next action:** resolve endpoint identity, TLS front door, credential owner/store, and approved probe origin. Then update the readiness matrix. Only after those facts are established should a separate explicit approval be requested for a bounded live read-only probe.

This audit does not authorize:
- DNS/TCP/TLS/HTTP requests to any T0 host.
- Adding GitHub secrets or creating a probe workflow.
- VPS, firewall, reverse-proxy, service, environment, Feeder, API, database or schema changes.
- Starting T2/Freqtrade, prediction collection, model training, or order routing.
- Paper order routing or live execution.

Keep `ai_execution_enabled=false`. T2 remains **NOT ACTIVATED**; live endpoint verification remains **NOT RUN**.


## Follow-up: operator-provided VPS listener snapshot

Timestamp: `2026-11-08 11:22:57 UTC`  
Host: `btcquant-t0-t1-test-01`  
Evidence type: operator-pasted read-only command output; not independently collected by CI.

Observed:
- `ss -lntp` showed only SSH on TCP/22 and local system resolver listeners; no listeners on TCP/80, TCP/443, or TCP/8788.
- No running service matching nginx, caddy, apache, traefik, market, feeder, or docker appeared in the filtered running-service list.
- Nginx sites-enabled/conf.d summary and Caddyfile summary produced no entries.
- `docker ps` produced no container rows.
- Nginx config validation produced no output; nginx binary/service availability is not established by this alone.

Assessment:
- At the observation time, this VPS did not expose a listening T0 Candle API on the development port 8788 or a web front door on 80/443. No running reverse proxy or Docker container was observed by the supplied checks.
- This does not prove that T0 API is absent from every host, nor does it prove no API code or stopped service definition exists on this VPS.
- Endpoint identity remains unresolved. Do not infer a public IP, hostname, or base URL.

Next bounded action: read-only inventory of local checkout directories, relevant stopped service definitions, and process command names to determine whether T0 code/service is present but stopped. Do not read environment files, credentials, private keys, or secret values. No start/restart/reload, network probe, firewall/configuration change, DB access, or T2 activation is authorized by this observation.

Status: endpoint deployment **BLOCKED / NOT ESTABLISHED**; live verification **NOT RUN**; T2 runtime **NOT ACTIVATED**; `ai_execution_enabled=false`.


## Follow-up: operator-provided local T0 checkout and process inventory

Evidence type: operator-pasted read-only command output; observation timestamp was not included in the supplied output.

Observed on the VPS previously identified as `btcquant-t0-t1-test-01`:
- T0 checkout exists at `/home/ubuntu/t0/app`, with `.git` and `market_data` directories.
- A tmux session named `t0-feeder` is running a command that changes to that checkout, sets `MARKET_DATA_BACKEND=sqlite` and `MARKET_DATA_DB=/home/ubuntu/t0/app/.data/market-data.sqlite3`, then executes `/home/ubuntu/t0/venv/bin/python -m market_data.feeder_service`.
- Process list shows the tmux server (PID 6583) and active Python Feeder process (PID 6584).
- The filtered systemd unit-file inventory returned no matching market/feeder/nginx/caddy/API service definitions.
- The filtered installed-package inventory returned no matching nginx/caddy/apache2/docker package rows.

Assessment:
- This supersedes the earlier uncertainty about whether T0 checkout/Feeder exists locally: the checkout is present and the Feeder process is running at the time represented by the operator output.
- It does not establish that the Candle HTTP API is running. The prior socket inventory showed no TCP/8788, TCP/80 or TCP/443 listener; this new output does not show an API process or HTTPS front door either.
- The process command establishes the Feeder's selected SQLite backend and configured DB path, but does not prove DB integrity, ingestion freshness, API readiness, or storage-level read-only enforcement for API consumers.
- Absence from the filtered unit/package results is limited to those filters; it does not prove no alternative process manager or externally hosted API exists.

Updated verdict:
- Local T0 checkout: **OBSERVED PRESENT**.
- T0 Feeder process: **OBSERVED RUNNING** (operator snapshot; no independent process probe).
- T0 Candle API listener / HTTPS front door: **NOT OBSERVED / NOT ESTABLISHED**.
- T2 live endpoint verification: **BLOCKED**; no endpoint identity or approved probe origin.
- Live verification: **NOT RUN**; T2 runtime: **NOT ACTIVATED**.

No service, process, DB, environment file, secret, network, firewall, VPS configuration, or T2 runtime was changed or accessed by this assessment. No tests or workflows were run. Do not stop/restart the Feeder, start an API, install packages, expose a port, or alter runtime configuration without separate explicit approval.

Next bounded step: if the operator wants to continue local discovery, inspect only the T0 checkout's tracked API entrypoint/deployment documentation and safe process metadata. Do not read `.env`, secret files, credentials, private keys, or DB contents. Establish API deployment intent and ownership before proposing any activation.


## 2026-11-08 — API service-user and SQLite filesystem permission check

Operator supplied read-only permission output; command timestamp was not included.

Observed:
- Intended API process identity: `ubuntu`, UID 1000, primary GID 1000.
- Path traversal permissions: `/home` is root-owned 755; `/home/ubuntu` is ubuntu-owned 750; `/home/ubuntu/t0`, checkout, and `.data` are ubuntu-owned and traversable.
- SQLite file: regular file, owner/group `ubuntu:ubuntu`, mode `0600`, size 634880 bytes.
- Gunicorn executable: owner/group `ubuntu:ubuntu`, mode `0775`.

Assessment:
- **PASS — filesystem access prerequisite** for running the API as `ubuntu` against the observed SQLite path. No ownership or permission broadening is required.
- This does not prove the database is healthy, that the API is running, or that the API endpoint is reachable.
- The file is mode 0600, so a different service identity would not have read access without a separately reviewed permission design. Keep the proposed service identity as `ubuntu` unless a future security review explicitly approves another model.
- The Feeder and API would share the same OS identity if the API runs as `ubuntu`; SQLite API reads are source-level read-only, but this filesystem check is not proof of database-level isolation from writes by that identity.

Verification boundary:
- No file was opened or modified by this permission check; no ownership/mode changed.
- No process/service, Feeder, API, database, environment, secret, network, firewall, or VPS configuration was changed.
- No tests or GitHub Actions workflows were run. This is operator-supplied metadata, not an independently executed permission test.

Updated status:
- API process identity prerequisite: **PASS**.
- SQLite path/file read permission prerequisite: **PASS**.
- API service deployment/process: **NOT VERIFIED**.
- HTTPS front door and hostname: **BLOCKED / NOT ESTABLISHED**.
- T2 live endpoint verification: **NOT RUN**; T2 runtime: **NOT ACTIVATED**.

Next bounded step: prepare and review a deployment design only. Do not create a service, start Gunicorn, configure TLS/reverse proxy, change firewall or environment, or restart the Feeder without separate explicit approval and the missing endpoint/network/credential details.
