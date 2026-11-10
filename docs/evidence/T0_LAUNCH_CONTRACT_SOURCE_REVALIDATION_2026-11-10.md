# T0 Launch Contract Source Revalidation — DEP Intake Baseline

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact review baseline: `d1617c16da83fc5afd0d97759fbf2666b6d9dffc`
- Operation class: STATIC SOURCE / DOCUMENTATION REVALIDATION ONLY
- Result: SOURCE CONTRACT REFERENCES MATCH CURRENT BRANCH BLOBS; HOST PARITY NOT VERIFIED

## 1. Purpose

Revalidate that the DEP-01–DEP-09 intake sheet and prior launch-contract reconciliation still point to the source files currently present at the branch HEAD. This is a source/documentation consistency check only; it is not host or runtime evidence.

## 2. Exact blob identity

| File | Current branch blob SHA | Reconciliation-recorded SHA | Result |
|---|---|---|---|
| `market_data/feeder_service.py` | `bdcecf6bc98a2ff070f83098d2c50154a160c99c` | `bdcecf6bc98a2ff070f83098d2c50154a160c99c` | MATCH |
| `market_data/api.py` | `81733c9b6de811cbebb2f5d472d41f37f337990c` | `81733c9b6de811cbebb2f5d472d41f37f337990c` | MATCH |
| `market_data/README.md` | `d90f84f8135c8ab9da1b57863e145d86565bf179` | `d90f84f8135c8ab9da1b57863e145d86565bf179` | MATCH |
| Launch reconciliation | `f0d3ad69d07514df7cb5e85631e93a7b0153a3fa` | Existing report blob | MATCH |
| Owner evidence protocol | `56ae166ae90770a775220f71dacfe2498080839f` | Existing protocol blob | MATCH |
| Preflight safety audit | `51b877377cd600dbeaf68b344dd3fa4fe6589bfe` | Existing audit blob | MATCH |

## 3. Static source assertions

| Assertion | Source observation | Result |
|---|---|---|
| Feeder module entrypoint | Module ends by invoking `main()` | PASS |
| Feeder readiness notification | `run_service` invokes `notify_fn("READY=1")` only after `runtime.start() is True` | PASS |
| Feeder stop notification | `finally` invokes `notify_fn("STOPPING=1")` | PASS |
| Feeder graceful drain | `runtime.stop(timeout=30)` follows stop notification | PASS |
| Notification socket optionality | `systemd_notify` returns false when no notification address is supplied | PASS |
| Candle API health/data routes | Source contains `/health` and `/v1/candles` routes | PASS |
| API candle limit | `MAX_API_CANDLES = 2000` | PASS |
| Documented API launch | README contains Gunicorn WSGI target `market_data.api:application`, bind `127.0.0.1:8788`, one worker, four threads and timeout 20 | PASS |
| Same-host topology | README describes loopback T0 → T2 without requiring a reverse proxy | PASS |
| Remote/browser topology | README separates remote/browser gateway as a distinct protected path | PASS |

## 4. Interpretation and limits

- The source references in the launch reconciliation and DEP intake are still current at the reviewed branch HEAD; no source drift was detected in these files.
- Source-level readiness notification does not establish the deployed systemd `Type`, `NotifyAccess`, unit state or effective properties.
- Source-level API routes and README launch commands do not establish a running API, listener ownership, token configuration, database availability, candle coverage or freshness.
- The current branch blob identity does not establish the deployed VPS Git SHA or process checkout.
- DEP-01–DEP-08 still require owner-supplied host evidence. DEP-09 remains NOT REQUIRED for the documented same-host loopback path unless a distinct remote/browser path is actually in use.
- The old preflight script remains NOT APPROVED for metadata-only collection and was not executed.

## 5. Status

| Area | Status |
|---|---|
| Current source blob identity | PASS |
| Launch-contract source references | PASS |
| README topology wording | PASS |
| Owner DEP evidence | NOT SUPPLIED |
| Deployed source parity | NOT VERIFIED |
| systemd unit/process/listener facts | NOT VERIFIED |
| API / Feeder runtime readiness | NOT RUN |
| Data coverage / freshness | NOT VERIFIED |
| Tests / GitHub Actions | NOT RUN / NOT DISPATCHED |
| VPS / SSH / DB / token / secret access | NONE |

No source, test, workflow, service, VPS, network, database, data, secret, permission or runtime was changed. No test or GitHub Actions workflow was run or dispatched. No workflow run or artifact is claimed.

## 6. Next step

Use the existing DEP intake sheet when sanitized owner evidence is available. Compare the exact deployed checkout SHA and unit/process/listener properties against this revalidated source contract. Do not infer deployment parity from branch source identity.
