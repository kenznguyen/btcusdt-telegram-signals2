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
