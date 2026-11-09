# T4 Route / Auth / Control Dependency Mapping

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact branch source baseline: `5309e93e59f51f561ecb5ede16d8225158b00c1b`
- Method: read-only inspection of selected exact-branch source and architecture documents.
- Scope: T4 React dashboard, common `pipeline.api:application`, local development proxy, and documented Gateway boundary.
- Exclusions: no VPS/runtime/network/proxy inspection; no token use; no tests or workflow dispatch; no permission, source, schema, ledger, or risk changes.

## 1. Route inventory

| Route | Method | Auth source | Function / boundary |
|---|---|---|---|
| `/health` | GET | None | Public liveness response; returns service name and `liveTradingSupported=false` |
| `/control`, `/control/*` | GET | None | Serves allowlisted built React static assets under configured dist root |
| `/v1/system` | GET | `MARKET_DATA_TOKEN` | Five-layer status |
| `/v1/candles` | GET | `MARKET_DATA_TOKEN` | Bounded candle read via configured store factory |
| `/v1/order-book` | GET | `MARKET_DATA_TOKEN` | Fixed BTCUSDT order-book snapshot |
| `/v1/intelligence` | GET | `MARKET_DATA_TOKEN` | Validated T1 observation snapshot |
| `/v1/decision`, `/v1/signals` | GET | `MARKET_DATA_TOKEN` | AI decision and independent Core/AI signal snapshot |
| `/v1/paper`, `/v1/equity`, `/v1/audit`, `/v1/quality` | GET | `MARKET_DATA_TOKEN` | Paper state, equity, audit and quality reads |
| `/v1/paper/evaluate` | POST | `CONTROL_TOKEN` | Requests Core or AI paper evaluation and possible paper submission |
| `/v1/paper/pause` | POST | `CONTROL_TOKEN` | Persistent paper pause/resume |
| `/v1/paper/cancel` | POST | `CONTROL_TOKEN` | Cancel remaining paper order quantity |
| `/v1/paper/kill` | POST | `CONTROL_TOKEN` | Persistent Kill Switch activation |
| `/v1/paper/reset-kill` | POST | `CONTROL_TOKEN` | Reset only after server-side readiness checks |

Unknown routes return 404; known routes with the wrong method return 405. POST payloads are bounded to 4096 bytes, duplicate JSON keys are rejected, and each control request is subject to a shared SQLite budget of 30 requests per minute. The backend rejects missing tokens, compares bearer credentials using constant-time comparison, and rejects a POST credential equal to the read token.

## 2. Frontend-to-backend edges

1. `control_dashboard/src/App.jsx` accepts a user-entered API base URL, read token and optional control token. Connection values are held in React component state; the inspected source does not persist them to browser storage.
2. `control_dashboard/src/api.js` permits HTTPS remote origins and HTTP only for loopback. It rejects URL credentials, query strings and fragments; bearer tokens are sent in the Authorization header, not in the URL. Requests omit cookies, reject redirects, disable cache, cap response bodies at 2 MiB and use a 15-second timeout.
3. `control_dashboard/src/useTerminal.js` polls nine GET endpoints through the configured API base every five seconds while the page is visible. The read token is used for all these reads. Paper control POSTs use the separate control token.
4. `control_dashboard/vite.config.js` configures a development-only `/v1` proxy to `http://127.0.0.1:8789`.
5. `pipeline/api.py` binds its direct development entry point to `127.0.0.1:8789`. The common API serves the React build under `/control` when present.

## 3. Findings

### T4-RA-01 — Gateway edge implementation and deployment are not established

- Source confirms React-to-common-API calls and a loopback development listener.
- The architecture decision explicitly records the Gateway as a separate component and says proxy selection, implementation and deployment are not authorized / not verified.
- No inspected source proves an externally deployed edge proxy, TLS termination, firewall policy, private backend port enforcement or route isolation.
- Disposition: architecture DECIDED; implementation and runtime exposure NOT VERIFIED. Do not infer either secure isolation or an actual public bypass.

### T4-RA-02 — Frontend API origin is configurable and not pinned to an approved Gateway

- `apiBase()` accepts any HTTPS remote host (and loopback HTTP) and the dashboard sends both read/control bearer tokens to that configured origin.
- No host allowlist, Gateway identity pin, or server-provided trusted-origin binding appears in the inspected frontend code.
- This is a source-level credential-destination risk if an operator enters an incorrect or untrusted origin. It does not prove a token was leaked or a malicious endpoint exists.
- Disposition: SOURCE-CONFIRMED; deployment usage NOT VERIFIED. A future contract should constrain or explicitly verify the approved Gateway origin before tokens are supplied.

### T4-RA-03 — Existing frontend route contract does not match the documented Gateway route namespace

- Dashboard source calls `/v1/*`; the development proxy forwards `/v1/*` directly to port 8789.
- Gateway architecture document describes target routes `/api/t0/*`, `/api/t1/*`, `/api/t2/*`, optional `/api/dashboard/*`, and health routes.
- No route translation table or deployed mapping between these namespaces was found in the inspected artifacts.
- Disposition: contract gap / NOT IMPLEMENTED. Do not change routes until a versioned route map identifies backend ownership and auth propagation.

### T4-RA-04 — Authentication separates read and control secrets, but does not define operator identity or granular roles

- GET routes share one static `MARKET_DATA_TOKEN`; all POST control routes share one static `CONTROL_TOKEN`.
- Backend checks are authoritative at the API boundary and POST requires a distinct control token. No per-user principal, role, action-specific permission, token expiry, rotation protocol or revocation workflow is visible in these files.
- This is a single-operator shared-secret model, not identity-based authorization. It may be an acceptable personal-use interim boundary only if credential custody and exposure are explicitly accepted.
- Disposition: source-confirmed model; environment secret custody, rotation and actual access population NOT VERIFIED.

### T4-RA-05 — Public liveness and static dashboard are intentionally unauthenticated

- `/health` is unauthenticated and returns a minimal service identity plus paper-only flag.
- `/control/*` serves only index and selected static asset extensions from the resolved dashboard root; path containment and hidden-path checks are present. A restrictive CSP is added to static responses.
- This makes the UI shell public while data APIs remain token-protected. It is not proof that the backend port is externally reachable.
- Disposition: source-confirmed; edge exposure and whether public health is acceptable remain NOT VERIFIED.

### T4-RA-06 — Paper controls remain backend-owned; frontend confirmation is presentation only

- React enables controls only when a control token is present and returned system/paper state explicitly says PAPER and `liveTradingSupported=false`.
- Backend independently validates exact payload shapes and control token. Evaluate obtains server-side inputs; clients cannot submit a prediction, book snapshot or LIVE mode. Core/AI evaluation calls the ledger submission path; reset-kill checks candle, order-book and pending-order readiness.
- Kill/pause/cancel/reset/evaluate are still sensitive paper-state mutations and rely on the shared control credential. UI state is not an authorization boundary.
- Disposition: paper-only source path confirmed; no live executor established. Actual migrated-ledger compatibility remains outside this audit (F5-07 stays deferred).

## 4. Boundary assessment

| Boundary | Static finding | Runtime status |
|---|---|---|
| Browser → React | UI shell may be served at `/control`; credentials entered by operator | Hosting/exposure NOT VERIFIED |
| React → API | Configurable HTTPS origin; `/v1/*` paths | Actual configured origin NOT VERIFIED |
| Dev proxy → API | Vite `/v1` proxy to loopback 8789 | Development-only source configuration |
| Edge Gateway → domain services | Logical architecture defined with target `/api/*` namespaces | Gateway implementation/deployment NOT VERIFIED |
| Read auth → GET routes | Shared `MARKET_DATA_TOKEN` | Secret custody/rotation NOT VERIFIED |
| Control auth → POST routes | Distinct `CONTROL_TOKEN`; all paper controls share it | Secret custody/authorized operator NOT VERIFIED |
| Paper evaluate → ledger/risk | Server-side decision and PaperLedger submission path | Runtime and migrated schema behavior NOT VERIFIED |

## 5. Required design closure before Gateway implementation

1. Freeze a route map from public `/api/*` paths to the current `/v1/*` domain handlers, including allowed methods and explicit deny-by-default behavior.
2. Decide how the dashboard obtains and verifies the approved Gateway origin; do not let bearer credentials be sent to an arbitrary unverified host.
3. Define the personal-use authentication model: secret custody, rotation/revocation, operator identity assumptions, and whether one control secret authorizes every paper mutation.
4. Specify which health/static routes are public and which backend listener(s) must remain private.
5. Define edge/backend request-size, timeout, rate-limit, header-redaction and error semantics without weakening backend enforcement.
6. Test the route/auth contract with mock services only after a separate test authorization. Do not dispatch Actions or touch runtime as part of this static mapping.

## 6. Status and restrictions

- Selected exact-branch source/blob identity: PASS for inspected files.
- Static route/method/auth inventory: PASS for inspected `pipeline.api` and React client.
- End-to-end route mapping to documented Gateway: PARTIAL / contract gap.
- Gateway implementation, direct-port exposure, TLS, firewall and runtime origin: NOT VERIFIED.
- Identity-based authorization and credential lifecycle: NOT ESTABLISHED by inspected source.
- Tests and GitHub Actions: NOT RUN / NOT DISPATCHED.
- Independent review: NOT PERFORMED; this is a static mapping, not an independent security certification.
- F5-07: DEFERRED; no migrated-ledger test or fix.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Option C — No Destructive Authority — unchanged. No data cleanup, retention mutation or deletion.
- No source, test, workflow, permission, secret, proxy, DNS, firewall, VPS, database, ledger, risk or runtime change.

## 7. Evidence anchors

- `pipeline/api.py`: `0540540462b3710a25788e4ff47a88272b7ee9c3`
- `control_dashboard/src/api.js`: `38cb5a464b05acd77914c7f333d377d8ac0535ad`
- `control_dashboard/src/App.jsx`: `f549fa442f23d39b0caec5a822dbd1ad3b25bc75`
- `control_dashboard/src/useTerminal.js`: `3ed925e5b4c27d58ff94cdb1bbf0b64ac99fa28c`
- `control_dashboard/vite.config.js`: `fa29bc959a2ee764396fcf04d444dd6f2887dffd`
- `control_dashboard/src/api.test.js`: `628084e7509f805a1c5248422f36fb75054bacda`
- `control_dashboard/src/App.test.js`: `7eebfb65efacb16a67eb7df9dd4e54fb358abac2`
- `docs/architecture/T4_API_GATEWAY_ARCHITECTURE_DECISION_2026-11-08.md`: `58822c59cf2dd0f4c5d2afe47f09ced41d343d6e`
- `pipeline/test_api.py`: `643b8eefffda05eaceaa1b4a8007ccfea38b4cd9`

No claim is made that these selected blobs constitute a complete repository or runtime inventory.
