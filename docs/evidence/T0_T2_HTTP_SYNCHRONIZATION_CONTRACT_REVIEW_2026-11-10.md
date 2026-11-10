# T0 → T2 Synchronization Contract Review — 2026-11-10

## Disposition

**DOCUMENTARY REVIEW: PASS WITH OPEN OPERATIONAL GATES**  
**SOURCE/TEST EXECUTION: NOT RUN IN THIS REVIEW**  
**VPS DEPLOYMENT PARITY: NOT VERIFIED**  
**LIVE/PAPER EXECUTION: PAPER-ONLY; AI_EXECUTION_ENABLED=false**

This review is limited to the existing T0 read-only Candle API and T2 HTTP consumer on `feature/t0-centralized-data-feeder-p1-20261101`. It does not authorize source changes, runtime probes, VPS access, workflow dispatch, or trading execution.

## Exact source baseline

- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Branch HEAD observed from GitHub ref: `80fc3b3e6c8d8aeab7705281c9b887117074e6e6`
- `market_data/README.md` blob: `d90f84f8135c8ab9da1b57863e145d86565bf179`
- `market_data/api.py` blob: `81733c9b6de811cbebb2f5d472d41f37f337990c`
- `market_data/feeder.py` blob: `935d295ef42c94482a48ce6ccdc927ebfa4c7e22`
- `freqai_bridge/context.py` blob: `9abe781340dc9b948c40c759d92f340da3e372c1`
- `freqai_bridge/http_candles.py` blob: `eb9aeccdf381e8a2ebc3450a7a31ae4e9da164ac`
- `freqai_bridge/test_context_http.py` blob: `fdd4eeb7252deee609330b7f3a6ace3c13b36a9a`
- `freqai_bridge/test_http_candles.py` blob: `4e372cd9e6f3ce7047a4f7e0ea91f4c4bb3c6067`
- `.github/workflows/t2-http-consumer-red.yml` blob: `7690780e076c317345879dcef081951e78cf2c6a`
- `freqai_bridge/config.research.json` blob: `2ddccabc8a88a66ace251070c03d8623214291ac`

## Contract findings

### 1. Transport and ownership

- T0 remains the canonical owner of Binance USD-M BTCUSDT M15/H1 data in SQLite.
- T0 exposes a read-only authenticated `GET /v1/candles` API.
- Same-host T0 → T2 topology is loopback `127.0.0.1:8788`; Nginx, public listener and remote HTTPS gateway are not required for this local consumer.
- T2 obtains endpoint/token/lag threshold from process environment. The token is sent only in the Bearer header; it is not embedded in the URL or committed research config.
- The inspected T2 context path uses `CandleHttpClient`; no local SQLite, paper DB, exchange API or alternate-venue fallback is present in that path.
- Current T2 adapter is M15-only and caps one context window at 32 candles. T0's H1 API capability is not consumed by this adapter. This is a scope distinction, not evidence of a defect: the inspected research configuration also declares M15 as its FreqAI timeframe. Do not add H1 to T2 without a separate strategy/data-contract requirement.

### 2. Fail-closed contract checks

The T2 adapter:
- restricts the market identity to Binance USD-M BTCUSDT M15;
- requires an exact bounded window, closed candles, exact candle count and complete coverage;
- rejects gaps, identity/schema mismatch, duplicate JSON keys, invalid decimals/OHLCV, oversized bodies and unsupported content encoding;
- enforces `asOfMs` and first-observed availability timestamps;
- requires the freshness envelope to be evaluable;
- uses bounded connect/read timeouts, no redirects and a bounded retry policy for selected transient failures;
- does not silently fill gaps, convert missing data to zero, or fall back to local storage.

T0's API limits reads to 2,000 candles and reports coverage, gaps, `datasetVersion`, `asOfMs`, `availableAtMs`, `generatedAtMs` and freshness metadata. HTTP 200 alone is not proof of complete data; the T2 consumer correctly requires complete coverage for its requested context.

### 3. `T0_CANDLE_MAX_LAG_MS=120000` — calculation and qualification

The adapter applies `max_lag_ms` to:

```
ingestion_lag_ms = latestAvailableAtMs - latestCloseTimeMs
```

It does **not** apply the 120,000 ms threshold to `observationAgeMs` or `closeLagMs`. This distinction is correct for a 15-minute candle: a candle may naturally be many minutes past close when queried, even if it was first observed promptly after closing.

The source scheduler currently declares:
- close grace: 5 seconds;
- poll interval: 5 seconds.

Nominal scheduling contribution before the sync request is therefore approximately 5–10 seconds after the candle close boundary, plus exchange publication/response and local processing latency. The 120-second ceiling is a 12× allowance over that nominal 10-second scheduling contribution. Tests encode the exact boundary: 120,000 ms is accepted and 120,001 ms is rejected.

**Qualification:** this source-based calculation does not establish a measured production latency distribution or a hard upper bound for Binance publication, network delay, host scheduling, or transient retries. The feeder retry policy can back off beyond 120 seconds. Therefore 120,000 ms is defensible as a conservative fail-closed acceptance ceiling for the current paper/research consumer, but it is **not production-validated** and must not be described as a measured SLA. Keep the threshold explicit and mandatory; missing, malformed, zero or out-of-range configuration must continue to fail closed. Any production threshold change requires measured evidence and separate approval.

### 4. Historical validation evidence

- The repository handoff previously records the T2 migration suite as 45 + 11 + 6 = 62 tests PASS at the migration source baseline `65fe065ccdc197a51b969da37ce99d5414201a92`.
- The current review did not rerun those tests or dispatch GitHub Actions.
- A read of the combined commit status for `65fe065...` returned no status contexts. This review therefore does not independently establish a workflow run ID, artifact ID, or current CI status.
- Current workflow definition explicitly sets `AI_EXECUTION_ENABLED=false`, clears T0/PAPER DB and exchange credentials, and runs adapter/context/exporter tests on GitHub Actions.

## Remaining synchronization gates

1. **Configuration parity:** owner/deployment evidence must confirm the actual T2 process has the intended loopback base URL, secret token and explicit `T0_CANDLE_MAX_LAG_MS`; source defaults do not prove deployed environment values.
2. **Service parity:** verify separately, only with explicit host-access approval, that T0 API is bound to loopback port 8788 and is served by the intended source SHA. No host probe was performed here.
3. **Consumer parity:** verify separately that the deployed T2 process invokes this HTTP context path and does not have another active data path outside the inspected repository scope.
4. **Freshness evidence:** collect non-destructive operational measurements of close-to-first-observed ingestion lag before claiming a production latency bound. Do not change the 120-second threshold based only on synthetic fixtures.
5. **CI evidence:** a future approved GitHub Actions run must record exact source SHA, workflow run, job results and artifact. No run is claimed by this review.

## Scope and prohibitions

- No source, test, package, workflow, schema or config file was changed.
- No tests, compile, dry-run, GitHub Actions dispatch, VPS/SSH/runtime/DB/network/provider probe was performed.
- No secrets, credentials, data, services, permissions or runtime state were read or changed.
- No cleanup, TTL, deletion, archive, vacuum, compaction or other destructive lifecycle operation was performed.
- T0 canonical SQLite remains selected; PostgreSQL/TimescaleDB remains PARKED.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Option C was revoked by the owner on 2026-11-10. This review grants no deletion authority and does not change the separately defined VPS operational-data lifecycle proposal.

## Next step

Prepare a deployment-parity evidence checklist for the T0 API and T2 consumer, using owner-supplied sanitized configuration/service evidence first. Do not access the VPS or run operational probes until separately authorized.
