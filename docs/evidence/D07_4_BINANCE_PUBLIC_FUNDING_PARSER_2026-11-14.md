# D07.4 — Binance USDⓈ-M Public Funding Page Parser

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Disposition: **OFFLINE PARSER + CI PASS / ACQUISITION NOT IMPLEMENTED**

## Scope

Added a strict offline parser for captured responses from Binance USDⓈ-M public market-data endpoint `GET /fapi/v1/fundingRate`, restricted to BTCUSDT. It consumes bytes supplied by the caller; it does not make HTTP requests or use credentials.

Official contract reference: [Binance USDⓈ-M Get Funding Rate History](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History). The documented response fields include `symbol`, `fundingRate`, `fundingTime`, `markPrice` and `rateType`; `markPrice` is associated with the funding fee charge. The endpoint documents inclusive `startTime`/`endTime`, ascending results and a maximum page size of 1,000. The parser maps those records into the internal half-open interval `[startAtMs,endAtMs)`.

## Implemented contract

Added:
- `paper_execution/binance_public_funding.py`
- `paper_execution/test_binance_public_funding.py`

The parser:
- requires raw bytes, declared byte length and matching SHA-256;
- accepts only the exact documented five-field record schema;
- accepts only `BTCUSDT` and `rateType=Regular`; rejects `Special` and unknown values;
- requires string Decimal values for funding rate and mark price, positive finite mark price, and integer funding timestamps;
- rejects duplicate JSON keys, malformed UTF-8/JSON, duplicate timestamps, out-of-order records, records outside the declared half-open scope, and pages above 1,000 records;
- binds every normalized event to the D07.2 `evidenceSnapshotId`;
- emits the exact event input contract consumed by `funding_model.py`.

The parser does not download data, authenticate the issuer, or claim pagination completeness. The endpoint does not provide a source-wide total count in this response contract; D07.2 therefore continues to report `enumerationCompleteness=NOT_VERIFIED` unless separate evidence proves it.

## Exact-source CI evidence

- TDD RED: run [43521263087](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43521263087), source `e121b8680b4d984cbf15d12cbccb7818e2112e37`, failed because the parser implementation module had not yet been added.
- Final GREEN: run [43521409826](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43521409826), SUCCESS, source SHA `c791c0d3e9c5661ee7be85f7fccfd0d312823a9b`.
- Focused Binance public funding parser tests: **19/19 PASS**.
- Focused PAPER funding model tests: **19/19 PASS**.
- D07.2 provenance tests: **17/17 PASS**.
- Full PaperLedger regression: **521/521 PASS** in 152.319s.
- Artifact `14083630474`, name `dual-ledger-bootstrap-proof-c791c0d3e9c5661ee7be85f7fccfd0d312823a9b`, 15,068 bytes, GitHub ZIP digest `sha256:5e2c2eab0a459200ffcc9b7dbda7c9ca69b7abd54dce0f185c0a7fa4b34bbe1a`, expires 2026-11-20T22:42:07Z.

## Remaining gates

- No public HTTP acquisition client, pagination orchestrator or scheduler.
- No read-only projection of as-of PAPER positions from cutover snapshots and verified execution journal coverage.
- No end-to-end test that verifies captured public bytes, projects PAPER positions, builds expected events, stages independently generated observed PAPER events, persists reconciliation and certifies coverage as one workflow.
- No claim of issuer authenticity, global completeness, freshness, or real-account funding equivalence.

D07.4 parser and CI: **PASS**. D07 overall: **PARTIAL**.
