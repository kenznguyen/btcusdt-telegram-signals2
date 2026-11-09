# T0 → T2 Loopback Deployment Gate — 2026-11-09

## Owner decision and scope

The owner approved the next synchronization sequence and selected same-VPS T0/T2 deployment using loopback. The owner also explicitly allowed changes to the running Feeder/database and activation of T1/T2 runtime, subject to the approved order.

This record covers only source/runtime readiness for the first T0 → T2 deployment gate. It does not authorize live trading, real orders, OKX source replacement, T0 ownership transfer, or any data deletion.

## Verified source state

Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Branch HEAD: `e11f174ea2e9dce4bc528b4de019d94d36be70c2`

Latest recorded T0 VPS source SHA: `9ae2eeae4ece3d657781b68e96b6f4509cd95f24` (from `docs/evidence/T0_FEEDER_RUNTIME_VERIFICATION_20261109.md`).

The following exact Git blob SHAs match between the T0 runtime source commit and current branch HEAD:

| File | Blob SHA | Parity |
|---|---|---|
| `market_data/api.py` | `81733c9b6de811cbebb2f5d472d41f37f337990c` | PASS |
| `market_data/feeder.py` | `935d295ef42c94482a48ce6ccdc927ebfa4c7e22` | PASS |
| `market_data/feeder_service.py` | `bdcecf6bc98a2ff070f83098d2c50154a160c99c` | PASS |
| `market_data/write_gateway.py` | `b2029d9db15fe39dcbe575acfeb6df1b16e16acd` | PASS |
| `market_data/storage.py` | `13fe1ae01ebb5318b69e69eef3e512d207f74c49` | PASS |
| `market_data/store.py` | `4e1b0c54bd56455abe5be0e5c7d0807e63e0bc78` | PASS |

This is file-level source parity. It does not prove the running Python process loaded those exact bytes or establish the current API process state.

## Existing T0 → T2 evidence

- T0 Candle Contract v1 API source exists: GET-only `/v1/candles`, Bearer authentication, versioned response, explicit coverage and freshness metadata.
- T2 uses `CandleHttpClient`; direct T0 SQLite access and `canonical_db_path` were removed from the migrated T2 path.
- Existing isolated evidence: 45 HTTP adapter tests, 11 consumer/migration tests, 6 exporter tests PASS; loopback HTTP integration PASS; Freqtrade 2026.9 strategy-load smoke PASS.
- These are isolated CI/fixture results, not a live canonical T0 endpoint read.
- Latest recorded T0 runtime report (2026-11-09) reports Feeder process PID 22046, post-restart candle ingestion and bounded coverage checks. It does not establish the Candle API listener or a successful T2 read.
- The earlier endpoint audit (2026-11-08) observed no listener on 8788/80/443. That observation is historical; current listener state is NOT VERIFIED.

## Deployment choice

- T0 API base URL for same-host T2: `http://127.0.0.1:8788`.
- Bind only to loopback; do not open a public port, configure public DNS, or add a reverse proxy for this same-host path.
- T2 must use `T0_CANDLE_API_BASE_URL=http://127.0.0.1:8788`, `T0_CANDLE_MAX_LAG_MS=120000`, and a protected token matching T0's `MARKET_DATA_TOKEN`.
- Preserve GET-only access, read-only database access, TLS verification behavior for non-loopback hosts, bounded timeout/retry/body limits, and no-fallback behavior.
- T0 API readiness must be proven with an authenticated GET /v1/candles; `/health` alone is only liveness.
- Run a one-shot T2 context read and verify returned datasetVersion, requested window, complete coverage, latest closed candle, freshness and provenance before activating the broader T2 runtime.

## Execution boundary and current blocker

The current tool connection can inspect and update GitHub, but exposes no authenticated SSH/terminal action for the Scaleway VPS. Plugin discovery did not identify an available SSH/VPS execution connector. No remote command was run.

Therefore:
- Source parity: PASS.
- T2 contract/client/isolated integration: PASS at recorded exact SHAs.
- Current T0 API service/listener state: NOT VERIFIED.
- Live authenticated T0 API request: NOT RUN.
- One-shot T2 read against canonical T0: NOT RUN.
- T2 runtime activation: NOT RUN.
- T1 activation/integration: NOT STARTED, correctly deferred.
- Tests in this documentation increment: NOT RUN.
- GitHub Actions dispatched for this documentation increment: NONE.
- Workflow run/artifact: NONE.
- VPS/Feeder/DB/API/T2 runtime changes: NONE.

No code, runtime, DB, Feeder, process, environment, secret, firewall, network, strategy, ledger, risk, or trading state was changed.

## Next exact gate

Obtain an authenticated remote execution path to the existing VPS, or have the operator execute a reviewed, bounded deployment procedure. Before any source checkout update, re-confirm the runtime SHA and verify the six file blob identities above. Then:

1. Inspect the current listener, process, service, DB read-only path and protected token-file presence without printing secret values.
2. Install/start the T0 API as a loopback-only service without restarting or reconfiguring the Feeder.
3. Prove authenticated GET /v1/candles, 401 without a token, GET-only behavior, response size, full coverage, latest required M15 candle and ingestion lag <= 120000 ms.
4. Run the T2 one-shot context consumer against 127.0.0.1 and preserve sanitized evidence.
5. Only after those checks pass, assess broader T2 runtime activation.

Stop on any source mismatch, missing/invalid token, API/store error, stale/incomplete response, unexpected listener, or any evidence that the API can mutate T0 storage. Do not weaken thresholds or add a fallback.

## Verdict

**PARTIAL / BLOCKED AT VPS EXECUTION.** The T0 → T2 source and isolated contract are ready for the live loopback gate. Actual API deployment and canonical-data consumption cannot be claimed until a remote execution path is available and the bounded runtime evidence is collected.
