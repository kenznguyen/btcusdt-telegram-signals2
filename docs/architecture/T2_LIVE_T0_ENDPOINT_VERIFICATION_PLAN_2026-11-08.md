# T2 Live T0 Endpoint — Controlled Read-Only Verification Plan

Date: 2026-11-08 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD inspected: `d45af9aecdc0580a06be05b8dfff7f1fe2dcd670`  
Status: **PLAN PREPARED — EXECUTION NOT AUTHORIZED**

## 1. Objective

Define a bounded verification of the deployed T0 Candle Contract v1 endpoint before considering any T2 connection. The verification must establish:

- HTTPS endpoint identity and valid TLS certificate/hostname verification.
- Bearer authentication behavior without exposing credentials.
- GET-only API behavior and read-only storage access.
- Contract v1 response validity, request-window completeness and freshness.
- Bounded network/resource behavior consistent with the approved T2 client policy.

This plan does not deploy the endpoint, activate T2, start prediction collection, alter T0, or authorize trading.

## 2. Fixed system constraints

The existing T2 consumer uses only:

- `T0_CANDLE_API_BASE_URL`
- `T0_CANDLE_API_TOKEN`
- `T0_CANDLE_MAX_LAG_MS` (explicit integer; approved value: `120000`)

The endpoint contract is `GET /v1/candles`, Bearer-authenticated, contractVersion `1.0.0`, schemaVersion `1`, BTCUSDT, M15/1h, aligned UTC millisecond request boundaries, half-open `[startMs,endMs)`, and at most 2,000 slots.

Approved client transport policy remains:

- Connect timeout 3 s; read timeout 5 s.
- Maximum 3 attempts; fixed backoff 250 ms then 500 ms.
- Maximum response body 256 KiB, enforced while streaming and before JSON decode.
- `Accept-Encoding: identity`; redirects disabled.
- TLS certificate and hostname verification mandatory.
- Retry only transient transport failures, connect/read timeouts and HTTP 503.
- No retries for 400/401/404/405, other status codes, or contract/data validation failures.
- No endpoint/source switching and no SQLite, cache, synthetic-candle or alternate-venue fallback.

## 3. Hard execution boundary

**This document is a plan only. No live probe is authorized by its creation.**

Before any live request, obtain a separate explicit approval covering:
1. Exact endpoint hostname/base URL and the network origin from which the probe may run.
2. Credential provisioning method and authorized operator.
3. A bounded read-only test window and request budget.
4. Whether a disposable isolated GitHub Actions runner is suitable, or whether network allowlisting requires another explicitly approved probe host.

Until then:

- Do not add or request secrets in GitHub.
- Do not place endpoint credentials in source, workflow YAML, command history, issue/PR text, logs, artifacts or chat.
- Do not change VPS firewall, services, environment, systemd, Feeder, database or endpoint deployment.
- Do not start T2/Freqtrade, prediction collection, model training or order routing.
- Keep `ai_execution_enabled=false`; native Freqtrade entry/exit flags and trade-entry confirmation remain disabled.
- Do not run POST/PUT/PATCH/DELETE with a payload, SQL mutation, schema inspection that changes state, or any write probe.

## 4. Phase 0 — Offline readiness review (no network request)

Record the following before requesting live-test approval:

| Check | Required evidence | Pass condition |
|---|---|---|
| Endpoint identity | Approved base URL and owner/operator confirmation | HTTPS URL, expected host and path; no IP/host guess |
| DNS/network path | Approved execution origin and expected egress/allowlist | Probe origin is known and permitted |
| Credential source | Named secret store / protected environment injection | Token never enters Git or command arguments |
| TLS trust | Expected public CA or approved CA bundle | Verification enabled; no insecure override |
| Client policy | Configured timeout/retry/body cap/redirect/encoding values | Matches Section 2 |
| Runtime separation | Probe design and workflow diff | One-shot probe only; no T2/Freqtrade service startup |
| Evidence handling | Redaction and artifact policy | No token, Authorization header, sensitive response body or private endpoint detail leaked |

Any missing endpoint, owner, secret source, network authorization or TLS trust input is **BLOCKED**, not guessed.

## 5. Phase 1 — HTTPS and authentication checks (requires separate approval)

Use the approved one-shot probe environment and inject the token only through its protected secret mechanism. Do not print environment values or request headers.

| ID | Probe | Expected result | Failure disposition |
|---|---|---|---|
| TLS-01 | HTTPS request with certificate verification enabled | Valid chain, hostname match, certificate within validity period | Fail closed; no bypass |
| TLS-02 | Redirect behavior | No redirect followed; endpoint responds directly | Treat redirect as failure; do not forward credentials |
| AUTH-01 | GET without Authorization, after operator confirms `MARKET_DATA_TOKEN` is configured | HTTP 401 | If server token is unset, source returns 503 `UNCONFIGURED` before checking Authorization; classify as configuration BLOCKED, not auth failure |
| AUTH-02 | GET with one deliberately invalid token, after server token configuration is confirmed | HTTP 401 | If server token is unset, 503 `UNCONFIGURED`; stop, do not retry as an auth probe or brute-force |
| AUTH-03 | GET with approved token | HTTP 200 with valid contract response if storage is available; otherwise distinguish 503 `STORE_UNAVAILABLE` from auth outcome | Stop on any unexpected status; never infer auth success from a generic 503 |
| AUTH-04 | Inspect sanitized logs/artifact | No token/header value or secret-bearing error text | Block and rotate/revoke if exposure is suspected |

Source-order note: `market_data/api.py` checks that `MARKET_DATA_TOKEN` is configured before comparing the Authorization header. Therefore an unset server token yields 503 `UNCONFIGURED` for `/v1/candles`, while a configured server token plus absent/invalid Authorization yields 401 `UNAUTHORIZED`. A valid token can still receive 503 `STORE_UNAVAILABLE` if the backing store is unavailable. Do not misclassify these states. `/health` is handled before candle authentication and is only a liveness endpoint; it does not prove readiness or auth.

Do not infer authentication success from a TCP/TLS handshake. AUTH-03 must complete a valid authenticated GET and validate its contract response.

## 6. Phase 2 — GET-only and read-only verification (requires separate approval)

Use only a non-mutating request and an explicitly bounded test. No write payloads or database mutation are permitted.

| ID | Probe | Expected result | Notes |
|---|---|---|---|
| METHOD-01 | GET valid candle query | Contract v1 response | Primary functional request |
| METHOD-02 | HEAD, if supported by the service contract | Either documented behavior or 405 | Do not assume HEAD proves GET-only |
| METHOD-03 | OPTIONS, if supported | No mutation; advertised methods consistent with GET-only policy | Informational only |
| METHOD-04 | One body-free POST/PUT/PATCH/DELETE attempt per method, only if explicitly approved | 405 METHOD_NOT_ALLOWED; no state change | No body; do not repeat; auth middleware may reject earlier |
| STORE-01 | Review server-side configured DB role/transaction mode and sanitized startup configuration | Read-only role/transaction enforced for the endpoint | Evidence must be configuration or operator-attested; never test by attempting a write |
| STORE-02 | Confirm request leaves T0 rows/schema/Feeder state unchanged using existing read-only health/integrity evidence | No mutation attributable to probe | Do not run a write or migration to prove this |

A 405 from the HTTP layer alone does not prove the backing database role is read-only. Both method restriction and storage-level read-only enforcement must be evidenced independently. If server-side configuration evidence cannot be obtained without modifying T0, mark STORE-01 **NOT VERIFIED**.

## 7. Phase 3 — Contract, freshness and resource checks (requires separate approval)

Use one minimal, aligned, already-closed BTCUSDT M15 window, selected within known retained data. Request only the smallest useful range; never exceed 2,000 slots. Do not shift/re-request automatically.

Validate:

1. Exact HTTP success status and expected content type.
2. `contractVersion=1.0.0`, `schemaVersion=1`, symbol/timeframe identity.
3. Exact requested range, half-open semantics, aligned timestamps and expected slot count.
4. No missing slots/gaps, partial coverage, open candle, invalid decimal, invalid timestamp or provenance field.
5. Latest required M15 candle open time equals `endMs - 900000`.
6. `asOfMs` is the approved observation cutoff; no future availability timestamp.
7. Freshness arithmetic:
   - `closeLagMs = generatedAtMs - latestCloseTimeMs`
   - `observationAgeMs = generatedAtMs - latestAvailableAtMs`
   - `ingestionLagMs = latestAvailableAtMs - latestCloseTimeMs`
   - `ingestionLagMs = closeLagMs - observationAgeMs`
8. Require `availableAtMs >= closeTimeMs`; accept ingestion lag exactly 120000 ms and reject values greater than 120000 ms.
9. Do not reject valid candles merely because raw close lag or observation age exceeds 120000 ms within a normal M15 interval.
10. Confirm response is below 256 KiB and that the client enforces the cap during streaming.
11. Confirm bounded timeout/retry behavior from client-side instrumentation without logging secrets or full response bodies.

A single live sample cannot establish long-term availability, 24/7 reliability, completeness across all history, or production readiness.

## 8. Failure handling

- TLS failure, hostname mismatch, unexpected redirect, 401, contract mismatch, stale/incomplete data or body-cap violation: fail closed.
- Do not disable TLS verification, widen freshness limits, add retries, change source, switch endpoint, shift the request window, or fall back to local data.
- Stop after the approved request budget. Preserve sanitized status, timestamps, request identifiers and reason codes only.
- If credentials may have leaked, stop immediately and follow the credential owner's rotation/revocation procedure; do not copy the exposed value into the evidence report.

## 9. Evidence and GitHub recording

After an approved execution, record on the same branch:

- Scope and explicit approval reference.
- Exact repository branch and source SHA used by the probe.
- Workflow run ID, event, checked-out SHA, job IDs and conclusions.
- Artifact ID/name and digest; distinguish GitHub metadata digest from independently recomputed payload hash.
- Sanitized test matrix with PASS / FAIL / BLOCKED / NOT VERIFIED per check.
- Probe origin, endpoint identity in appropriately restricted evidence, UTC timestamps, request count and response status.
- Any limitations, deviations and next approval gate.

Artifacts must exclude credentials, Authorization headers, secret environment dumps, full private payloads and unnecessary infrastructure details. Do not call the result a T2 runtime acceptance test: it is endpoint-only, read-only evidence.

## 10. Acceptance gate

Endpoint verification may be marked **PASS WITH LIMITATIONS** only if TLS, authenticated GET, contract/freshness, bounded transport and independent read-only enforcement evidence all pass at the exact recorded source/config identity.

If any required evidence is absent, use **BLOCKED** or **NOT VERIFIED**. A successful GET alone is insufficient.

Passing this plan does not authorize:
- T2 runtime activation or deployment.
- Prediction scheduler/collector startup.
- Changes to T0 API, Feeder, database, VPS, firewall or services.
- Model training, paper order routing, or live execution.

Those actions require separate explicit approval.
