# T0 Candle API — HTTPS Front-Door Design and Security Checklist

- Date: 2026-11-08 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Design baseline HEAD: `8630b609651b066c18df60e8843bff16d7abfb10`
- Status: **DESIGN ONLY — NO DOMAIN, DEPLOYMENT OR LIVE PROBE AUTHORIZED**
- Scope: offline architecture and security planning; no VPS, DNS, firewall, process, database, secret, network or runtime changes.

## 1. Objective and current decision

Prepare a safe HTTPS access path for T2 to consume the T0 Candle Contract v1 without exposing the application server directly.

**Proposed target architecture:** a dedicated DNS name for the T0 API, Caddy as the HTTPS reverse proxy, and the existing WSGI application served by Gunicorn on loopback only.

This is a design recommendation, not an implementation approval. No domain/subdomain currently points to the VPS. Therefore no certificate can be issued and no public endpoint identity exists yet.

The API contract remains unchanged:

- `GET /v1/candles`
- Bearer authentication using `MARKET_DATA_TOKEN`
- Contract v1; BTCUSDT USD-M perpetual; M15/H1
- T0 owns canonical ingestion and storage; T1/T2 remain read-only consumers
- No write, order, exchange credential, or trading route

The current T0 API development entrypoint binds `127.0.0.1:8788`. The documented production process is Gunicorn bound to the same loopback address, behind an HTTPS reverse proxy.

## 2. Target request path

```text
T2 one-shot / future consumer
        |
        | HTTPS :443
        | Hostname + TLS verification
        | Authorization: Bearer <token>
        v
DNS: <approved-api-subdomain>
        |
        v
Caddy reverse proxy
  - TLS certificate and renewal
  - HTTP -> HTTPS redirect
  - request/method/size/time limits
  - no credential logging
        |
        | loopback HTTP only
        v
Gunicorn 127.0.0.1:8788
        |
        v
T0 WSGI API: GET /v1/candles
        |
        | read-only store interface
        v
T0 canonical store
```

Security invariants:

1. Port 8788 must never be bound to a public interface or allowed through the VPS firewall.
2. Only the reverse proxy may reach Gunicorn, and only over loopback.
3. TLS verification remains mandatory in T2. No HTTP downgrade, self-signed bypass, redirect-following workaround, or alternate endpoint fallback.
4. The proxy must preserve the Authorization header for the application but must never log its value.
5. The API remains read-only. HTTPS does not itself prove storage-level read-only enforcement.
6. No route may expose Feeder controls, database operations, migrations, or order execution.

## 3. Reverse-proxy choice

### Recommended candidate: Caddy

Caddy is the preferred candidate for this small single-host deployment because it can obtain and renew public certificates automatically once DNS and inbound reachability are correctly configured. This reduces certificate-renewal operations compared with a manually managed certificate chain.

A later configuration should follow this shape (illustrative only; do not install or apply it now):

```caddyfile
<approved-api-subdomain> {
    encode zstd gzip

    @candle_api {
        path /v1/candles
        method GET
    }

    handle @candle_api {
        reverse_proxy 127.0.0.1:8788
    }

    handle {
        respond 404
    }
}
```

The final configuration must be reviewed against the actual Caddy version and the T0 API's response/body characteristics before deployment. Do not copy this sample into the VPS as-is. In particular, proxy-level request limits, timeouts, health-route policy, access-log redaction, and forwarded-header trust must be explicit in the deployment review.

### Alternative: Nginx

Nginx with a separately managed ACME client is acceptable if Caddy is unavailable or a concrete operational reason favors Nginx. It introduces separate certificate issuance/renewal and configuration-validation responsibilities. Do not install both proxies.

No proxy has been selected or installed. The choice becomes actionable only after the domain and deployment scope are approved.

## 4. DNS and domain prerequisites

Before TLS deployment:

1. Select and register a dedicated domain or subdomain for the T0 API. Domain purchase is a separate owner decision; no purchase is authorized here.
2. Confirm control of the DNS zone and record who administers it.
3. Create an `A` record only after the intended VPS public IPv4 address is confirmed by the operator.
4. Create an `AAAA` record only if IPv6 routing, firewall policy, and proxy reachability are deliberately configured and verified. Do not publish a non-working AAAA record.
5. Use a suitably short TTL during initial cutover; raise it only after the endpoint is stable.
6. Verify DNS propagation from an approved environment before requesting a certificate.
7. Keep the exact hostname in the deployment record. Do not infer a hostname from the VPS label or guess an IP address.

The hostname, public address, DNS provider, registrar, and DNS credentials are currently **NOT PROVIDED / NOT VERIFIED**.

## 5. TLS and network exposure policy

When separately approved for deployment:

- Public inbound TCP/443 is required for API clients.
- Public inbound TCP/80 may be temporarily or continuously required for HTTP-01 ACME validation and HTTP-to-HTTPS redirection. Its final necessity depends on the selected ACME challenge method.
- TCP/8788 remains loopback-only and must not be opened in UFW or a cloud firewall.
- SSH remains restricted to the currently approved access policy; this design does not authorize SSH rule changes.
- Outbound access needed for DNS resolution and ACME certificate issuance must be identified before deployment.
- TLS certificate chain and hostname validation must pass from the actual intended T2 probe origin.
- TLS renewal must be automatic and have a monitored failure/expiry path. A successful first issuance is not proof of renewal.
- Do not enable HSTS until HTTPS routing and renewal are verified. If enabled later, use a conservative policy; do not enable `includeSubDomains` or preload by default.
- Do not expose a management/admin endpoint through this proxy.

Current VPS firewall policy is unchanged. No ports 80/443/8788 are to be opened as part of this design task.

## 6. API process and storage identity

The documented application process is:

```bash
gunicorn --bind 127.0.0.1:8788 --workers 1 --threads 4 --timeout 20 market_data.api:application
```

The eventual deployment should use a supervised service with:

- A dedicated, non-login service identity where storage permissions permit.
- No root process.
- Explicit working directory and executable path.
- A protected credential-injection mechanism; no token in command-line arguments, repository files, logs, or chat.
- Restart policy and bounded stop/start behavior.
- Read-only filesystem access except explicitly required runtime paths.
- No permission to alter T0 schema, migrations, canonical writes, Feeder lifecycle, or exchange configuration.

**Known storage constraint:** the operator-provided snapshot showed the SQLite database owned by `ubuntu:ubuntu` with mode `0600`, and the current Feeder runs as `ubuntu`. This proves that the same `ubuntu` identity can access the file, but does not establish isolation between API and Feeder.

Do not solve this by broadening permissions blindly. Before using a separate API identity, review the actual SQLite journal mode and the access requirements for the database, WAL/SHM sidecar files, and parent directories. Validate the proposed permission model on a disposable copy with concurrent read/write behavior representative of the deployed store. If least-privilege access cannot be proven without unsafe permission changes, keep remote API deployment blocked and evaluate a separately approved read-only PostgreSQL role/transaction path instead.

For PostgreSQL, source-level read-only transaction behavior is not a substitute for verifying the deployed login role's grants. No database role, ACL, ownership, or schema changes are authorized by this document.

## 7. Proxy and application hardening checklist

The deployment review must verify all of the following before a public endpoint is accepted:

| Area | Required control | Acceptance evidence |
|---|---|---|
| Listener | Gunicorn binds only to `127.0.0.1:8788` | Process arguments and socket inventory |
| Public ports | Only approved HTTPS front door is reachable; 8788 is not public | Firewall rules and external port review |
| TLS | Valid chain, hostname match, current certificate, renewal configured | TLS inspection from approved probe origin; renewal configuration review |
| Redirect | HTTP redirects to HTTPS without forwarding credentials to an untrusted host | Redirect test with no Authorization forwarding |
| Methods | Only `GET /v1/candles` is proxied; other paths/methods rejected | Sanitized HTTP method/path test matrix |
| Authentication | Bearer token required on candle route | Missing/invalid token returns expected 401 when server token is configured |
| Secret handling | Token injected from protected secret store/service credentials | Configuration metadata only; never print value |
| Logging | No Authorization header, token, full private payload, or secret-bearing exception | Redacted sample log review |
| Cache | No shared/proxy caching of authenticated candle responses | `Cache-Control: no-store` preserved; proxy cache disabled |
| Request bounds | URI/header/body/time limits are explicit and compatible with the client | Config review and bounded negative tests |
| Upstream | Proxy upstream is fixed to loopback; no dynamic host forwarding | Config review |
| Forwarded headers | Trust only proxy-generated headers from loopback; do not trust client-supplied forwarding metadata | Config review and request test |
| Health | `/health` is not represented as readiness; do not expose diagnostic details | Route policy review |
| Storage | API read path cannot mutate canonical data | DB role/transaction evidence and isolated tests |
| Service | Non-root supervised process; restart and shutdown behavior bounded | Unit/config review and isolated lifecycle test |
| Host | Security updates, SSH policy, time sync, disk capacity and logs reviewed | Read-only host evidence; changes separately approved |
| Recovery | Certificate renewal failure and proxy/API process failure are detectable | Monitoring/alert design and failure test plan |

CORS is not needed for a server-to-server T2 client. Do not enable permissive CORS. Rate limiting should be conservative and compatible with the bounded T2 client; it must not create hidden retries or silently truncate candle responses.

## 8. Staged deployment gates

| Stage | Work | Required approval | Exit condition |
|---|---|---|---|
| D0 — Design | This document and security checklist | Current documentation scope | Design reviewed; no runtime change |
| D1 — Domain | Select/register hostname and configure DNS | Explicit domain/DNS approval | Operator confirms exact hostname and DNS ownership |
| D2 — Deployment plan | Pin proxy version, service identity, TLS challenge, ports, secret injection and rollback | Explicit deployment-plan approval | Reviewed config, permission model and rollback ready |
| D3 — VPS deployment | Install/configure proxy and supervised API service; adjust firewall only as approved | Separate explicit VPS change approval | Loopback upstream, HTTPS, auth, logging and storage checks pass |
| D4 — Endpoint probe | Bounded read-only request from approved origin | Separate explicit live-probe approval | Existing T2 endpoint verification plan passes |
| D5 — T2 connection | Configure T2 endpoint and paper-only consumer | Separate explicit T2 activation approval | Isolated consumer acceptance; no execution authority |

Approval for one stage does not authorize the next stage. A successful TLS handshake or candle GET does not certify T0 production readiness or authorize T2 runtime activation.

## 9. Rollback design

Before D3, record the current firewall, listener, process, service, and configuration state using read-only evidence.

If a later approved deployment fails:

1. Stop the rollout and preserve sanitized logs/config diff.
2. Remove the public DNS record or revert it to the previously approved state only with DNS-change approval.
3. Disable the proxy route and restore the previous approved firewall state only with explicit authorization.
4. Keep the T0 Feeder and canonical store untouched.
5. Do not expose port 8788 directly as a fallback.
6. Do not weaken TLS verification or authentication.
7. Do not activate T2 against an unverified endpoint.

Rollback must not require database migration, canonical data modification, Feeder restart, or a change to T0 ownership.

## 10. Current readiness and next action

| Item | Status |
|---|---|
| T0 API source and documented loopback/Gunicorn design | SOURCE-REVIEWED |
| T2 HTTPS/TLS client policy | SOURCE-REVIEWED |
| VPS currently has no observed 80/443/8788 listener in supplied snapshot | OPERATOR EVIDENCE |
| Feeder/SQLite remain in current observed configuration | PRESERVE UNCHANGED |
| Domain/subdomain pointing to VPS | **ABSENT — BLOCKED** |
| DNS owner/provider and exact hostname | NOT PROVIDED |
| TLS front door and certificate | NOT DEPLOYED |
| API Gunicorn service | NOT RUNNING / NOT ESTABLISHED |
| Dedicated API service identity and SQLite permissions | NOT VERIFIED |
| Public endpoint | NOT ESTABLISHED |
| Live endpoint verification | NOT RUN |
| T2 runtime | NOT ACTIVATED |

**Next action:** owner selects a domain/subdomain and confirms DNS control. Until then, keep this work at D0. No DNS, registrar purchase, firewall, proxy, service, API, Feeder, database, secret, or T2 runtime operation is authorized.

Related documents:

- `docs/architecture/T0_READ_ONLY_CANDLE_CONTRACT_V1_2026-11-08.md`
- `docs/architecture/T2_LIVE_T0_ENDPOINT_VERIFICATION_PLAN_2026-11-08.md`
- `docs/evidence/t2/T2_LIVE_T0_ENDPOINT_OFFLINE_READINESS_AUDIT_2026-11-08.md`
