# T0 Read-only Candle Contract v1 — Design and Review

- Date: 2026-11-08
- Status: **CONTRACT DESIGN REVIEWED — IMPLEMENTATION NOT VERIFIED**
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Design baseline HEAD: `7a491e1966640319df19033256310ff6616503d0`
- Scope: contract definition and source review only. No implementation, tests, runtime, database, or exchange activity is authorized by this document.

## 1. Decision

Use the existing T0 read-only HTTP API as the intended consumer boundary. Keep the current route `GET /v1/candles`; make the response contract explicit and versioned without creating a second API or allowing consumers to open the canonical SQLite file.

T0 remains the owner of canonical ingestion and storage. T1/T2 are read-only consumers. The contract is a data interface, not a strategy signal, order, or execution interface.

**Historical finding — superseded by later implementation evidence:** at the time of this initial contract review, the T2 bridge used direct SQLite access. The later T2 HTTP consumer migration removed the direct `market_data.store`/`read_window()` dependency from `freqai_bridge/context.py`, wired the strategy context through `CandleHttpClient`, and passed the recorded offline migration acceptance checks. See [T2 HTTP Candle Client GREEN evidence](../evidence/t2/T2_HTTP_CANDLE_CLIENT_GREEN_2026-11-08.md), which records the final migration and CI evidence at its exact source SHA. Current source inspection at the inventory baseline SHA also shows the HTTP client path. This does not prove that a live T0 endpoint, remote TLS, credentials, or deployed runtime is available; those remain NOT VERIFIED. Do not reintroduce direct T0 DB access or a fallback path.

## 2. Endpoint and request

### Endpoint

```http
GET /v1/candles
Authorization: Bearer <MARKET_DATA_TOKEN>
Cache-Control: no-store
```

- Read-only GET only. No POST/PUT/PATCH/DELETE and no write/order routes.
- Token is supplied only in the Authorization header, never in query strings or logs.
- HTTPS is required across host boundaries. Loopback-only binding is acceptable for same-host consumers behind a controlled local boundary.
- No exchange API credentials are required by this consumer API.
- The API must never create, migrate, initialize, or repair the canonical store while serving a read.

### Query parameters

| Field | Required | Contract |
|---|---:|---|
| `symbol` | Yes | Exactly `BTCUSDT` |
| `timeframe` | Yes | `15m` or `1h` |
| `startMs` | Yes | UTC Unix milliseconds; nonnegative; aligned to timeframe |
| `endMs` | Yes | UTC Unix milliseconds; aligned; greater than start |
| `asOfMs` | No | UTC Unix milliseconds; only return rows whose first-observed availability is <= this cutoff |

Window semantics are always **[startMs, endMs)**: include the candle opening at start, exclude the candle opening at end. The contract maximum is **2,000 expected candle slots per request**, matching the current API limit. Larger windows must be split into adjacent, non-overlapping requests; consumers must reconcile the exact combined timestamp sequence and dataset versions.

Reject unknown parameters, duplicate parameters, malformed/non-ASCII numeric timestamps, unaligned windows, unsupported symbol/timeframe, and oversized windows. Never truncate a request silently.

## 3. Market identity and candle schema

The v1 market identity is fixed and explicit:

| Field | Required value |
|---|---|
| `exchange` | `binance` |
| `marketType` | `USDT_PERPETUAL` |
| `symbol` | `BTCUSDT` |
| `timeframe` | `15m` or `1h` |
| `volumeUnit` | `BTC_BASE_ASSET` |
| `source` | `ccxt.binanceusdm` |

Each candle contains:

| Field | Type | Semantics |
|---|---|---|
| `openTimeMs` | integer | UTC candle opening time, inclusive |
| `closeTimeMs` | integer | UTC candle closing boundary, exclusive; equals open + interval |
| `open/high/low/close/volume` | decimal strings | Exact stored decimal representation; no JSON float conversion |
| `isClosed` | boolean | Must be `true`; any false/missing value is rejected by consumers |
| `availableAtMs` | integer | First time T0 observed/persisted the candle, not exchange event time |
| `availabilityKind` | enum | `FIRST_OBSERVED` |
| `quality` | enum | `VALIDATED`; means local schema/OHLC/time validation passed, not guaranteed exchange truth |
| `source` | string | `ccxt.binanceusdm` |

The v1 response must also identify `volumeUnit=BTC_BASE_ASSET` at dataset level. Do not compare or combine this volume with OKX contract-volume or spot-volume fields without a separately reviewed conversion contract.

## 4. Response envelope

Required response fields:

```json
{
  "contractVersion": "1.0.0",
  "schemaVersion": 1,
  "exchange": "binance",
  "marketType": "USDT_PERPETUAL",
  "symbol": "BTCUSDT",
  "timeframe": "15m",
  "volumeUnit": "BTC_BASE_ASSET",
  "startMs": 1793232000000,
  "endMs": 1793239200000,
  "asOfMs": null,
  "generatedAtMs": 1793239210000,
  "datasetVersion": "sha256:<64-lowercase-hex>",
  "candles": [],
  "coverage": {
    "expected": 8,
    "returned": 8,
    "complete": true,
    "gaps": []
  },
  "freshness": {
    "latestExpectedOpenTimeMs": 1793238300000,
    "latestReturnedOpenTimeMs": 1793238300000,
    "latestCloseTimeMs": 1793239200000,
    "latestAvailableAtMs": 1793239205000,
    "observationAgeMs": 5000,
    "closeLagMs": 10000,
    "evaluable": true
  }
}
```

The example values are illustrative only; they are not evidence of a current live response.

### Envelope semantics

- `contractVersion` is the semantic version of this consumer contract. Breaking changes require a new major contract path or an explicitly coordinated major version; additive optional fields may be minor changes.
- `schemaVersion` identifies the response/candle schema shape.
- `generatedAtMs` is the API server's response-generation clock, not the candle availability time.
- `datasetVersion` is the content-and-query hash for this exact response window. It is not a whole-database digest, source authenticity proof, or model-training provenance.
- `coverage.expected` is the number of aligned candle slots in the requested window; `returned` is actual rows returned.
- `coverage.complete=false` with explicit `gaps` is a valid diagnostic response, not a successful strategy input.
- Candle order is ascending by `openTimeMs`; duplicate timestamps are invalid.
- No forward-fill, interpolation, zero-fill, synthetic candle, or silent gap removal is permitted.

### Freshness semantics

- `latestExpectedOpenTimeMs` is the open time of the most recently expected closed candle at `generatedAtMs`, calculated from the timeframe boundary.
- `latestReturnedOpenTimeMs`, `latestCloseTimeMs`, and `latestAvailableAtMs` describe the last actual returned candle; they are null if no candle is returned.
- `observationAgeMs = generatedAtMs - latestAvailableAtMs`.
- `closeLagMs = generatedAtMs - latestCloseTimeMs`.
- `evaluable=false` when no candle is returned, a relevant timestamp is invalid/future, or the server clock cannot produce a valid nonnegative age. Otherwise it means only that the fields can be calculated.
- The API reports observations; it does not decide that data is fresh enough for a strategy. Each consumer must configure explicit max-lag thresholds for each timeframe and fail closed when the latest expected candle is absent, coverage is incomplete, or age exceeds its threshold.
- No numeric staleness threshold is approved by this design. Threshold selection and Data Quality Gate execution remain a separate, explicitly authorized task.

## 5. Deterministic consumer acceptance rules

T1/T2 must reject a response for strategy use unless all checks pass:

1. HTTP status is 200 and JSON parses under the documented size bound.
2. `contractVersion` major is supported and `schemaVersion` is exactly supported.
3. Exchange, market type, symbol, timeframe, and volume unit match the requested identity exactly.
4. Request range in response equals the request; all timestamps are integer UTC milliseconds and aligned.
5. Candle timestamps are strictly increasing, unique, and within [startMs,endMs).
6. Every candle has `isClosed=true`, expected close boundary, valid decimal strings, valid OHLC bounds, and nonnegative volume.
7. `coverage.expected == coverage.returned`, `coverage.complete == true`, and `coverage.gaps == []` for strategy use.
8. `freshness.evaluable == true`; the latest returned candle equals the latest expected closed candle.
9. Freshness thresholds configured by the consumer pass. If no threshold is configured, strategy use is unavailable (fail closed).
10. `datasetVersion` matches the documented digest format and is retained with the consumer's run/decision evidence.
11. No fallback to direct SQLite, another venue, stale cache, or synthetic data when any check fails. Return WAIT/UNAVAILABLE with a machine-readable reason.

For research windows that intentionally contain gaps, a separate research-only path may preserve and report gaps. It must not be reused as a live/paper decision input without an explicit quality policy.

## 6. HTTP errors

Use the existing simple error object consistently:

| HTTP | Error code | Consumer action |
|---|---|---|
| 400 | `INVALID_QUERY` | Reject request; fix caller |
| 401 | `UNAUTHORIZED` | Stop retries; fix credential/config |
| 404 | `NOT_FOUND` | Reject unsupported route |
| 405 | `METHOD_NOT_ALLOWED` | Treat as contract misuse |
| 503 | `UNCONFIGURED` / `STORE_UNAVAILABLE` | Unavailable; bounded retry policy, then fail closed |

Errors must not expose token values, database paths, SQL, exception text, or internal host details. `GET /health` is process liveness only; it is not data readiness, freshness, coverage, or Feeder health.

## 7. Current implementation review

Reviewed on branch `feature/t0-centralized-data-feeder-p1-20261101`, baseline HEAD `7a491e1966640319df19033256310ff6616503d0`:

| File | Current behavior | Contract gap / assessment |
|---|---|---|
| `market_data/api.py` | GET-only `/v1/candles`, Bearer token, bounded query, read through store, `generatedAtMs` | No explicit contract/schema version; no dataset freshness envelope; API uses `MAX_CANDLES` (write/sync bound) for read-window cap |
| `market_data/store.py` | Closed candle validation, decimal strings, provenance fields, `availableAtMs`, gap reporting, dataset hash, SQLite read-only URI | Good foundation; `MAX_READ_CANDLES=3000` differs from API's stricter 2000 cap; no API freshness summary |
| `freqai_bridge/context.py` | Uses `CandleHttpClient` through the T0 read-only HTTP contract | Source integration present; live endpoint/deployment remains NOT VERIFIED |
| `freqai_bridge/ChartProFreqaiResearch.py` | Calls the HTTP-backed context and writes a prediction artifact | Source integration present; artifact/runtime presence NOT VERIFIED |
| `freqai_bridge/README.md` | Documents the HTTP candle contract and no direct local-storage fallback | Aligned with the later T2 HTTP migration evidence |
| `market_data/test_api.py` | Covers auth, GET-only behavior, coverage gaps, as-of, missing DB, query bounds | Existing tests do not yet assert contract/schema version or freshness envelope |
| `market_data/test_store.py` | Covers decimal precision, closed candle, gaps, as-of, dataset version | Store-level tests are a foundation; freshness response tests belong at API boundary |

### Important distinction

The SQLite read path uses read-only mode, which protects against writes through that connection. It does **not** satisfy the architectural boundary that T1/T2 must not access the canonical database directly. Read-only file permissions and service-boundary isolation are different controls.

## 8. Required implementation sequence (not executed)

1. **Contract tests first (RED):** add API tests for version fields, identity, volume unit, freshness metadata, null/empty behavior, timestamp validity, unsupported schema handling, and consistent response shape.
2. **API implementation:** add the versioned envelope and freshness metadata; use a dedicated API read-window limit constant (2,000) instead of coupling the public API to the write/sync limit constant. Keep Store's internal maximum separate.
3. **Live endpoint acceptance:** separately verify the deployed T0 endpoint, remote TLS, credentials, freshness, and coverage using an explicitly approved read-only procedure. The offline migration CI does not prove remote runtime availability.
4. **Independent review:** confirm no direct T0 DB import/path or fallback has reappeared in the current T2 runtime; record exact source SHA and evidence.
5. **Offline tests:** use local WSGI/HTTP test server and deterministic fixtures only; no canonical database, exchange connection, model training, or live runtime.
6. **Independent review:** verify no direct T0 DB imports/path remain in T2 runtime; verify token redaction, request bounds, timeout behavior, and no fallback path.
7. **Evidence:** record exact SHA, GitHub Actions run/job IDs, checked-out SHA, artifact IDs/digests, tests and outcomes before promoting contract conformance.

Do not combine this with Data Quality Gate threshold approval, T0 runtime changes, source promotion, or production deployment.

## 9. Status and restrictions

| Item | Status |
|---|---|
| Existing read-only API as design base | PASS — source inspected |
| Contract v1 design | REVIEWED — implementation not verified |
| T0 API conformance to v1 | NOT VERIFIED |
| T2 FreqAI HTTP integration | PASS — source wiring and recorded offline migration CI; live endpoint NOT VERIFIED |
| T0 Data Quality Gate | PAUSED / NOT VERIFIED |
| T0 as official T2 replacement source | NOT APPROVED |
| T1 complete market-data readiness | PARTIAL / NOT VERIFIED |
| Runtime / canonical DB / exchange activity | NOT RUN |
| Live execution | DISABLED |

Restrictions remain: preserve the supervised Feeder; do not stop/restart/reconfigure it; do not access or modify canonical DB for this task; do not activate T1/T2 runtime; do not add exchange streams; do not enable autostart/deployment/live execution; keep `ai_execution_enabled=false`.

This document is a contract design, not implementation approval for runtime or source promotion. The implementation sequence requires the corresponding user authorization before code changes and tests.
