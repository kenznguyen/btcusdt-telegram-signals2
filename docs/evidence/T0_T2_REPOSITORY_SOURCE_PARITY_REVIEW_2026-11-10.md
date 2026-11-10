# T0 → T2 Repository Source Parity Review — 2026-11-10

## Purpose

Compare the exact source files identified by the historical 2026-11-09 T0 → T2 loopback runtime record with the current GitHub branch HEAD. This is a repository-only, read-only comparison; it does not inspect the VPS or prove which bytes are currently loaded by running processes.

## Comparison identities

- Historical T0 source commit recorded by the runtime report: `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`.
- Current branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Current branch HEAD at comparison: `1b1b4d49c1af9ae63d75343774df229d1249f02e`.
- GitHub commit comparison reports current HEAD ahead by 828 commits, behind by 0.
- Both commit trees were read through GitHub's Git Trees API. The file blob IDs below were compared directly.

## Runtime-relevant source blob comparison

| File | Historical blob | Current blob | Result |
|---|---|---|---|
| `market_data/api.py` | `81733c9b6de811cbebb2f5d472d41f37f337990c` | same | IDENTICAL |
| `market_data/feeder.py` | `935d295ef42c94482a48ce6ccdc927ebfa4c7e22` | same | IDENTICAL |
| `market_data/feeder_service.py` | `bdcecf6bc98a2ff070f83098d2c50154a160c99c` | same | IDENTICAL |
| `market_data/storage.py` | `13fe1ae01ebb5318b69e69eef3e512d207f74c49` | same | IDENTICAL |
| `freqai_bridge/context.py` | `9abe781340dc9b948c40c759d92f340da3e372c1` | same | IDENTICAL |
| `freqai_bridge/http_candles.py` | `eb9aeccdf381e8a2ebc3450a7a31ae4e9da164ac` | same | IDENTICAL |
| `freqai_bridge/config.research.json` | `2ddccabc8a88a66ace251070c03d8623214291ac` | same | IDENTICAL |
| `freqai_bridge/test_context_http.py` | `fdd4eeb7252deee609330b7f3a6ace3c13b36a9a` | same | IDENTICAL |
| `freqai_bridge/test_http_candles.py` | `4e372cd9e6f3ce7047a4f7e0ea91f4c4bb3c6067` | same | IDENTICAL |
| `market_data/test_api.py` | `49df7e0bec12908adae67f18a4aa19063e461093` | same | IDENTICAL |
| `market_data/test_storage.py` | `b2635f575323187f936360d033b4fc630d8138e0` | same | IDENTICAL |
| `.github/workflows/t2-http-consumer-red.yml` | `7690780e076c317345879dcef081951e78cf2c6a` | same | IDENTICAL |
| `.github/workflows/t2-freqtrade-2026-9-strategy-smoke.yml` | `89fe779e88c11c9a1598d2138286b7d4bfe7742b` | same | IDENTICAL |

The listed T0 API, Feeder, storage, T2 HTTP consumer, research config, regression tests and T2 HTTP workflow have identical Git blobs at the historical source commit and current branch HEAD.

## Documentation-only difference

`market_data/README.md` is the only changed file among the explicitly compared paths:

- Historical blob: `660a2f0f4f88c0de4fa8c1be3c4af96df282de0e`.
- Current blob: `d90f84f8135c8ab9da1b57863e145d86565bf179`.
- The current README adds the T0 Active Scope Index reference and clarifies the same-host loopback topology: T0 API at `127.0.0.1:8788`, direct T2 loopback access, no Nginx/HTTPS reverse proxy/public listener required for that internal path. Remote/browser access requires a separate approved gateway design.
- No runtime source file in the comparison set changed.

## Static contract spot-check

- `market_data/api.py` still reads `MARKET_DATA_TOKEN`, defaults `MARKET_DATA_BACKEND` to `sqlite`, rejects missing token/backend configuration with `503 UNCONFIGURED`, validates the Bearer header, then calls `create_store_from_env()` and `read_window()`.
- `freqai_bridge/http_candles.py` still bounds connect/read timeouts (3s/5s), restricts `max_lag_ms` to 1–120,000 ms, allows HTTP only for loopback hosts, sends Bearer authorization in the header, disables redirects and validates ingestion lag.
- `.github/workflows/t2-http-consumer-red.yml` still has read-only repository permissions, paper-only `AI_EXECUTION_ENABLED=false`, no DB/exchange credentials, compile + 45 adapter tests + 11 context/migration tests + 6 exporter tests, and exact-SHA artifact upload when the workflow runs.

These are static source observations only. The workflow file's test counts describe its assertions; they are not a new test run in this review.

## Disposition

**REPOSITORY SOURCE PARITY FOR THE INSPECTED T0/T2 FILE SET: PASS.**

**CURRENT VPS CHECKOUT / PROCESS-LOADED BYTE PARITY: NOT VERIFIED.**

The result materially narrows the remaining parity question: the T0/T2 implementation files inspected have not changed in Git since the historical runtime source commit. However, the current VPS checkout SHA, deployed service configuration, listener state, environment variables and process-loaded bytes still require owner-supplied current evidence or a separately approved bounded read-only check.

## Actions and safety boundary

- GitHub-only static reads were performed; no repository source, test, workflow, dependency or runtime file was modified.
- No tests, compile, workflow dispatch or artifact generation was performed.
- No SSH/VPS/runtime/DB/network/provider probe was performed.
- No service restart, T1 activation, model training, signal publication, ledger/risk mutation, live order or destructive data operation was performed.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders. T1 NOT ACTIVATED. PostgreSQL/TimescaleDB PARKED.
- Option C remains REVOKED; no destructive authority is implied.