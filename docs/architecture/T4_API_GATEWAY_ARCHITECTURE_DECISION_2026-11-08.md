# T4 Dashboard and API Gateway Architecture Decision

- Decision date: 2026-11-08 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Baseline branch HEAD before this documentation increment: `364942d738b0e7f534197991ab7b5ea77461c070`
- Status: **ARCHITECTURE DECISION RECORDED — IMPLEMENTATION NOT AUTHORIZED / NOT VERIFIED**
- Decision type: documentation-only architecture decision
- Related decisions:
  - `docs/architecture/T0_T1_T2_DATA_CONSUMPTION_ARCHITECTURE_2026-11-08.md`
  - `docs/architecture/T0_CANDLE_API_HTTPS_FRONT_DOOR_DESIGN_2026-11-08.md`
  - `docs/architecture/T2_HTTP_CANDLE_CONSUMER_CONTRACT_AND_TEST_PLAN_2026-11-08.md`

## 1. Decision

Keep the API Gateway and T4 Dashboard as **two independent architectural components**:

- **API Gateway** is the edge/network layer. It terminates approved external HTTP(S) access, applies transport-level controls, and routes requests to the correct service.
- **T4 Dashboard** is the user-facing application. React runs in the browser, displays system state and analytics, and calls versioned backend APIs through the Gateway.
- T4 must not embed backend routing, service credentials, database access, strategy execution, or risk authority.
- The Gateway must not implement trading logic, strategy selection, ledger mutation, risk approval, or business aggregation.

This is a logical architecture decision. It does **not** select or authorize installation of Nginx, Caddy, or another proxy.

## 2. Target request topology

```text
User browser
    |
    | HTTPS / same-origin
    v
Edge reverse proxy / API Gateway
    |-- serves T4 React static assets (or routes to a separately hosted frontend)
    |
    |-- /api/t0/*  -> T0 read-only Data API
    |-- /api/t1/*  -> T1 Intelligence API
    |-- /api/t2/*  -> T2 Strategy / Paper API
    |-- /api/t3/*  -> T3 endpoints only when separately approved
    |-- /api/health/* -> explicitly scoped health endpoints
    |
    +-- optional /api/dashboard/* -> T4 Backend-for-Frontend (BFF), if aggregation is later justified

T4 React application
    |
    +-- calls same-origin /api/* routes through the Gateway
    +-- renders normalized data; does not connect directly to databases or bot ports
```

The frontend may be served by the same reverse proxy or hosted separately. In either case, browser-to-service traffic must pass through the approved edge boundary. A BFF is optional and must not be introduced unless concrete aggregation, session, or response-shaping needs justify it.

## 3. Responsibility boundaries

| Concern | Gateway | T4 frontend | Optional T4 BFF | Domain services |
|---|---|---|---|---|
| TLS termination / HTTP routing | Owns | No | No | No |
| Rate limits / request-size / transport timeouts | Owns edge policy | No | May add app limits | Own service limits |
| User-facing charts / tables / controls | No | Owns | Supplies data | Supplies domain data |
| Combine multiple API responses for a dashboard view | No | Minimal client composition only | Owns if needed | Own domain semantics |
| Authentication and authorization | Edge enforcement/integration | No secrets or trusted authorization | Session/user-context enforcement as designed | Authoritative domain authorization |
| Strategy signals / ledger state | No | Display only | No decision authority | T2 / strategy services |
| Shared Risk Engine / Kill Switch | No | Display status only | No decision authority | Sole risk authority |
| Canonical T0 storage and writes | No | Denied | Denied | T0 only |

## 4. Required invariants

1. T4 accesses T0/T1/T2 only through documented, versioned APIs. It never opens SQLite/PostgreSQL files or connects directly to database ports.
2. Backend service ports remain private/loopback-bound or on a restricted private network; only the approved Gateway is externally reachable.
3. Browser code contains no service-to-service token, exchange credential, database credential, or Freqtrade administrative secret.
4. Freqtrade or other bot control APIs must not be exposed wholesale through a public reverse proxy. Use an allowlisted facade with explicit authorization; deny order/trade-changing routes unless a separate future approval explicitly permits them.
5. Dashboard actions are requests, not authority. Every strategy intent that could become a paper trade must pass the common Shared Risk Engine. The Gateway and T4 cannot bypass it.
6. Preserve independent T0/T1/T2 ownership and failure domains. A T4 outage must not stop ingestion, intelligence collection, strategy evaluation, or risk-state integrity.
7. Apply bounded connection/read timeouts, request/body limits, safe error handling, and credential/header redaction at the edge. Each backend must also enforce its own limits.
8. Health aggregation may report per-service state but must not convert a failed or stale dependency into an overall healthy trading state.
9. T4 is replaceable. Backend contracts must remain usable by non-T4 consumers.
10. Paper-only boundary remains. `ai_execution_enabled=false`; no live orders or exchange execution.

## 5. Relationship to the existing T0 HTTPS front-door design

The existing T0-specific design names **Caddy as the preferred candidate** for the single-host T0 Candle API HTTPS front door, with Nginx as an alternative if a concrete operational reason favors it. It also states that no proxy has been selected or installed.

This new decision does not silently replace that design:
- Nginx is accepted as a possible implementation of the general Gateway role, not selected as the current T0 proxy.
- Do not install Nginx alongside Caddy.
- Do not change the T0 API hostname, DNS, TLS, ports, firewall, Gunicorn binding, API contract, or deployment plan under this decision.
- A future consolidated Gateway implementation must explicitly reconcile the T0-specific Caddy candidate and any T4/API routing needs before selecting one proxy.

## 6. Delivery sequence

1. **Contract/design:** define route map, API versions, auth boundaries, allowed methods, timeout/body limits, health semantics, and error envelope. No runtime changes.
2. **Isolated verification:** use mock backends to test route selection, authentication propagation/redaction, denied routes, timeout behavior, backend isolation, and unavailable-service handling.
3. **T4 contract integration:** make React consume same-origin API routes; add BFF only if the tests/design show a concrete need.
4. **Security and failure review:** inspect direct-port exposure, browser secret leakage, Freqtrade route restrictions, request limits, and Shared Risk Engine non-bypass.
5. **Deployment gate:** require a separate explicit user approval and a reviewed deployment plan. No deployment is implied by this decision.

## 7. Current status and restrictions

| Item | Status |
|---|---|
| Gateway and T4 are separate components | **DECIDED** |
| T4 consumes APIs through the Gateway | **DECIDED** |
| Gateway owns edge routing/security controls, not business decisions | **DECIDED** |
| Optional BFF | **DEFERRED — add only with demonstrated need** |
| Nginx as selected proxy | **NOT SELECTED** |
| Caddy vs Nginx consolidated edge choice | **NOT RESOLVED** |
| Route map / API contract | **NOT IMPLEMENTED** |
| Mock-backend tests | **NOT RUN** |
| T4 implementation | **NOT STARTED / NOT VERIFIED by this decision** |
| VPS / DNS / firewall / proxy deployment | **NOT AUTHORIZED** |
| T0/T1/T2 runtime changes | **NOT AUTHORIZED** |
| Live trading | **NOT AUTHORIZED** |

No source code, test, workflow, database, runtime configuration, VPS, DNS, firewall, process, service, credential, Feeder, exchange, or trading state is changed by this architecture decision.
