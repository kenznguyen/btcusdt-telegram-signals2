# AI Strategy D1 — T0 Read-Only API Path Assessment

**Date:** 2026-11-11  
**Status:** API PATH IDENTIFIED IN REPOSITORY; LIVE ACCESS AND BUNDLE NOT VERIFIED  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`

## 1. Purpose

Continue the owner-approved D1 read-only verification without bypassing T0 ownership or creating a new dataset. This assessment identifies the documented consumer path and separates what it can prove from what still requires an immutable bundle.

## 2. Repository evidence inspected

- `docs/architecture/T0_READ_ONLY_CANDLE_CONTRACT_V1_2026-11-08.md`
  - Defines authenticated read-only `GET /v1/candles`.
  - Supports BTCUSDT M15 and H1, aligned half-open windows, `asOfMs`, a maximum of 2,000 expected candle slots per request, explicit coverage/gaps, closed-candle state, availability timestamps and `datasetVersion`.
  - Explicitly says `datasetVersion` is a content-and-query hash for the exact response window, not a whole-database digest, source authenticity proof or model-training provenance.
  - Historical contract review labels implementation/runtime verification as not established by that design document.
- `market_data/api.py`
  - Source implements GET-only `/v1/candles`, Bearer authentication, bounded query validation, and read-window access.
  - Response includes `contractVersion=1.0.0`, `schemaVersion=1`, `generatedAtMs`, `freshness`, `coverage` and `datasetVersion` supplied by the store.
  - Source presence does not prove that a deployed endpoint is reachable or that its runtime configuration matches this source.
- `docs/evidence/T0_FEEDER_RUNTIME_VERIFICATION_20261109.md`
  - Records historical VPS SQLite read-only coverage checks and bounded M15/H1 fingerprints, but not an AI research bundle manifest or a current live API response.
- `docs/evidence/T0_OWNER_READONLY_DEPLOYMENT_EVIDENCE_PROTOCOL_2026-11-10.md`
  - Documents same-host loopback API target `http://127.0.0.1:8788`.
  - States that this protocol itself does not authorize SSH, service probes, HTTP requests, token use or database access; host inspection/API requests need their own explicit authorization or owner-supplied evidence.
- `docs/architecture/T2_LIVE_T0_ENDPOINT_VERIFICATION_PLAN_2026-11-08.md`
  - Requires exact endpoint, network origin, credential provisioning, bounded request budget and separate live-probe authorization before any request. Its planned HTTPS cross-host path is not the same as the documented same-host loopback route.

## 3. Key distinction: API response versus immutable dataset bundle

The existing Candle API is the correct T0-owned read boundary for inspecting canonical candle availability. It does **not**, by itself, establish that an immutable research bundle `T0_M15_H1_DATASET_BUNDLE_V1` has been published.

In particular:
- `datasetVersion` identifies the exact query response content/window according to the API contract; it is not a whole-dataset or bundle manifest digest.
- A manifest with stable bundle ID, exact file inventory, per-file SHA-256, coverage and quality report is still required for a frozen research bundle.
- Creating/exporting files from the API would be a separate data-preparation operation and is not authorized by the current verification approval.
- Direct SQLite access by AI Research is not an acceptable shortcut.

## 4. Safe next evidence intake

The next safe step is owner/operator-supplied, sanitized evidence from the already deployed T0 read-only API, or a separately authorized operator-run probe using the exact deployed endpoint and protected credential injection.

Required metadata only for the initial existence/availability check:
1. Exact endpoint origin used (loopback on the T0 host; do not disclose token or public IP).
2. Request symbol/timeframe and exact aligned UTC `[startMs,endMs)` window for M15 and H1.
3. HTTP status and response `contractVersion`, `schemaVersion`, `datasetVersion`, `generatedAtMs`.
4. `coverage.expected`, `coverage.returned`, `coverage.complete`, exact `gaps`.
5. Last candle `openTimeMs`, `closeTimeMs`, `availableAtMs`, `isClosed`, `quality`, `source`; redact all OHLCV values if not needed.
6. `freshness` fields and any API error code.
7. Exact deployed source SHA and sanitized service/listener evidence, if already available from owner records.

Do not paste Authorization headers, token values, environment files, database paths, full logs, or private host details into GitHub or chat.

This metadata can verify a bounded live API response and its reported data quality. It still cannot verify a pre-existing immutable bundle manifest if no such bundle has been published.

## 5. Status and boundaries

| Item | Status |
|---|---|
| T0 read-only API source path | IDENTIFIED IN REPOSITORY |
| API source contract | DOCUMENTED |
| Live API endpoint/reachability | NOT VERIFIED |
| Current deployed source/config parity | NOT VERIFIED |
| Existing immutable AI research bundle | NOT FOUND IN INSPECTED GITHUB TREE; OUTSIDE-GITHUB EXISTENCE UNKNOWN |
| Bundle manifest / per-file SHA-256 | NOT VERIFIED |
| Current M15/H1 API coverage and quality | NOT VERIFIED |
| D1 | PARTIALLY DECIDED / BLOCKED |
| R1 Freeze | NOT FROZEN |
| R2 | NOT AUTHORIZED |

No API request, SSH/VPS access, SQLite read, data export/copy, bundle creation, test/workflow, feature extraction, label generation, model training, calibration, backtest, runtime change, deployment, exchange connection, order or destructive operation was performed.

## 6. Next decision boundary

Owner may provide the sanitized read-only API evidence listed in Section 4, or explicitly authorize a named operator and exact bounded probe origin/endpoint/request budget. Any creation/export of an immutable research bundle must be proposed and approved separately after the read-only source evidence is reviewed.

T0 remains independent and unchanged. Strategy Core remains unchanged. AI DCA remains disabled in v1. Paper-only and `AI_EXECUTION_ENABLED=false` remain.
