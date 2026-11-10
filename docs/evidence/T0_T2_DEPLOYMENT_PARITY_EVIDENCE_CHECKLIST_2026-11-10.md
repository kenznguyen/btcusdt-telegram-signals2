# T0 → T2 Deployment Parity Evidence Checklist — 2026-11-10

## Status

**DOCUMENTARY CHECKLIST: PASS**
**DEPLOYMENT PARITY: NOT VERIFIED**
**VPS ACCESS / PROBES: NOT PERFORMED OR AUTHORIZED BY THIS DOCUMENT**

Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Reviewed source baseline: `80fc3b3e6c8d8aeab7705281c9b887117074e6e6`

Purpose: define sanitized, owner-supplied evidence needed to compare T0 API and T2 HTTP consumer deployment configuration. This checklist is not authorization to access the host or perform runtime tests.

## 1. Configuration parity matrix

| Area | T0 evidence | T2 evidence | Acceptance rule |
|---|---|---|---|
| Source identity | Exact deployed SHA and branch | Exact deployed SHA and branch | Both map to reviewed source; unknown SHA = NOT VERIFIED |
| Service identity | API process/service and launch entrypoint | Freqtrade/FreqAI process/service and launch entrypoint | Identify the actual processes |
| Listener | Bind host/port; expected same-host endpoint `127.0.0.1:8788` | Sanitized `T0_CANDLE_API_BASE_URL` | Same intended local API; no public listener assumed |
| Authentication | `MARKET_DATA_TOKEN` presence only | `T0_CANDLE_API_TOKEN` presence only | Never disclose token value |
| Canonical store | Sanitized `MARKET_DATA_DB` path and backend | No T0 DB path or direct SQLite consumer | T0 SQLite remains canonical; T2 does not open it |
| Freshness | API source/version and timestamp semantics | Explicit `T0_CANDLE_MAX_LAG_MS=120000` | Missing or malformed consumer config fails closed |
| Market contract | Binance USD-M BTCUSDT M15 API | M15 request/window contract | Identity, coverage, closed candles and freshness validated |
| Runtime health | Timestamped, redacted status/log excerpt | Timestamped, redacted status/log excerpt | Health alone does not prove successful data consumption |

## 2. URL transport rule

The reviewed T2 `CandleHttpConfig` accepts HTTPS for non-loopback hostnames and HTTP only for `localhost`, `127.0.0.1` or `::1`. It rejects HTTP for non-loopback hosts, URL credentials, query strings, fragments and non-root base paths.

The T2 README describes the base URL as HTTPS. For same-host deployment, loopback HTTP is additionally permitted by code. This review does not mandate changing either documentation or runtime configuration. The selected endpoint must match actual topology. Never send a Bearer token over non-loopback plaintext HTTP.

## 3. Required owner-supplied evidence package

1. **T0 source identity:** branch, exact commit SHA, checkout identity and launch command with sensitive arguments removed.
2. **T0 service configuration:** bind host/port, API entrypoint, selected backend, redacted database path, and whether `MARKET_DATA_TOKEN` is present.
3. **T2 source identity:** branch, exact commit SHA, Freqtrade/FreqAI launch entrypoint and service/container identity.
4. **T2 process environment:** names and redacted values for `T0_CANDLE_API_BASE_URL`, `T0_CANDLE_API_TOKEN` (presence only), and `T0_CANDLE_MAX_LAG_MS`.
5. **Runtime evidence:** timestamped service status and short redacted startup/health excerpts. Exclude Authorization headers, tokens, database contents and candle payloads.
6. **Data-path evidence:** identify whether any additional T2 process/module reads local SQLite, exchange endpoints, cache or alternate venues.

Items may be omitted if unsafe to disclose; omitted evidence remains NOT VERIFIED and must not be inferred.

## 4. Acceptance gates

- **G1 — Source parity:** exact deployed SHAs are known and reviewed.
- **G2 — Endpoint parity:** T0 listener and T2 base URL identify the same intended loopback service.
- **G3 — Secret/config parity:** required token configuration is present without disclosure; T2 threshold is explicitly 120,000 ms.
- **G4 — Storage ownership:** T0 alone owns canonical SQLite; T2 has no direct DB path or alternate fallback.
- **G5 — Contract parity:** M15 identity, range, as-of cutoff, closed state, full coverage, dataset version and freshness checks are compatible.
- **G6 — Operational observation:** only after separate explicit approval, a bounded non-destructive read test may be planned. Record source SHAs, UTC timestamps, request range, HTTP result, coverage/freshness and redacted evidence. No orders or canonical data mutation.

No aggregate deployment PASS is possible until mandatory gates have actual evidence. Static source review is not deployed-state verification.

## 5. Known limitations

- T2 consumer is M15-only, at most 32 candles per context request. T0 H1 support does not prove an H1 T2 consumer.
- The 120,000 ms bound applies to `latestAvailableAtMs - latestCloseTimeMs`; it is not a measured production latency SLA.
- No measured Binance publication/network/host scheduling distribution is available.
- No deployed service definition, environment, listener, process tree, database path or deployed SHA has been verified.
- T2 README says HTTPS while code additionally permits HTTP on loopback; deployment must choose a topology-consistent endpoint.
- No runtime request, tests, compile, workflow dispatch, SSH/VPS/DB/network probe or data mutation was performed.

## 6. Safety and scope

- T0 canonical SQLite and recovery-required data remain protected.
- CORE_LEDGER, AI_LEDGER, audit/reconstruction and governance evidence remain protected.
- VPS operational-data cleanup is a separate lifecycle proposal; this checklist grants no deletion authority.
- Option C was revoked by the owner on 2026-11-10; revocation does not itself authorize destructive operations.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- PostgreSQL/TimescaleDB remains PARKED.
- No source, test, package, workflow, runtime, VPS, DB, provider, secret, permission, network or data changes are authorized by this checklist.

## 7. Next step

Collect the six evidence categories in Section 3, redact secrets, and map each item to G1–G5. Only after documentary parity is established should separate approval be requested for a bounded G6 connection/read test.