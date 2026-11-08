# T0–T1–T2 Synchronization Gap Assessment and Next Contract Plan

- Date: 2026-11-08 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Baseline branch HEAD: `15c3ce26d79812e632b9763e6d51ccd37169467e`
- Status: **ASSESSMENT RECORDED — DATA-PLANE INTEGRATION PARTIAL; RUNTIME NOT AUTHORIZED**
- Scope: read-only source/evidence review and architecture planning. No source-code, workflow, canonical database, VPS, Feeder, exchange, or strategy-runtime changes.

## 1. Executive finding

T0, T1, and T2 have useful components and isolated evidence, but they are **not yet synchronized end-to-end**.

The approved target remains a contract-based, independently owned data plane:

- T0 owns canonical BTCUSDT USD-M candle ingestion, storage, quality publication, and the read-only candle contract.
- T1 consumes eligible T0 candle data through that contract and owns its separate futures microstructure/derivatives observations and intelligence snapshots.
- T2 consumes T0 candles and, after a separately reviewed contract is implemented, selected T1 intelligence outputs. T2 owns its strategy/research state and independent Core/AI ledgers.
- All Core/AI candidate intents converge only at the Shared Risk Engine and paper-execution boundary.

This is **not** approval for a shared SQLite database. The prior SQLite `single/shared` work remains an isolated design/prototype only. The existing approved ownership rule—no direct T1/T2 access to T0 canonical storage—remains in force.

## 2. Current source/evidence inventory

### T0

- T0 read-only Candle Contract v1 defines `GET /v1/candles`, Bearer authentication, BTCUSDT USDT perpetual identity, M15/H1 semantics, closed-candle metadata, availability cutoff, coverage, freshness, and dataset version.
- T2 HTTP consumer migration removes the direct T0 SQLite read from `freqai_bridge/context.py` and fails closed without a local DB/cache/venue fallback.
- Exact evidence recorded in the T2 contract plan:
  - Adapter/consumer CI run `42470569288`, checked-out SHA `65fe065ccdc197a51b969da37ce99d5414201a92`, SUCCESS.
  - Freqtrade 2026.9 strategy-load smoke run `42470559497`, checked-out SHA `f016e82434609d77eb17a10eb48207933dd4040c`, SUCCESS.
- The actual T0 HTTPS endpoint is not established: no approved hostname/DNS, proxy deployment, or remote TLS/Bearer probe is evidenced. T0 API live connectivity remains NOT VERIFIED.

### T1

- `futures_intelligence.import_collector` currently imports bounded BTCUSDT CSV windows for trades, funding, open interest, and liquidations into a JSON snapshot.
- Snapshot v1 carries `snapshotId`, `collectorCommit`, `availableAtMs`, input-file SHA-256/size/row provenance, per-feed coverage, and conservative `OBSERVED_ONLY` quality.
- Missing feeds remain null; no zero-fill. Funding/OI are samples, not settlement/accounting events. Liquidation CSV has no event ID and is not deduplicated. The importer does not currently provide a canonical T0 candle dataset.
- Current importer source pins upstream collector commit `bc4f0ef633fbeee4a49defd72827f17162693805`.
- The importer deliberately reports `connectionStatus=UNVERIFIABLE`. The Python sidecar validator and Rust writer are offline components; the writer is not integrated into the upstream collector.
- User-provided bounded T1 runtime evidence covers 300 seconds on BTCUSDT and graceful SIGTERM only, on older deployed source SHA `d8ac9fc820dcf2e912e66518a1a1c73a8fa81ac7`. It does not prove long-duration continuity, reconnect recovery, complete order-book integrity, or the current PR source.
- T1 collector PR #1 is OPEN / DRAFT / NOT MERGED. Current head SHA observed: `93a3931a3e5098dcac5ab04fa5f535cd1bd252ba`.
  - Exact-head push run `42455219012`: FAILURE; Collector format/Clippy/build/workspace tests passed, but Sidecar writer format failed on one rustfmt line-wrap difference. Sidecar Clippy/tests and artifact steps were skipped. Dashboard frontend/backend, security, and Docker jobs passed.
  - Exact-head PR run `42455222283`: FAILURE.
  - A required review finding remains on the post-hard-link manifest publication failure path: after publishing a manifest, a subsequent cleanup/directory-sync error must permanently poison the writer so no more events can be appended. Do not treat earlier cleanup GREEN evidence as closure of this later finding without verifying the current PR head and exact regression test.
  - No current-head artifact was published in the observed failed push run.

### T2

- T2 FreqAI candle context uses the T0 HTTP adapter, not direct T0 SQLite.
- Existing isolated tests and Freqtrade 2026.9 strategy-load evidence are PASS at their recorded source SHAs.
- T2 currently has no verified T1 intelligence snapshot/API consumer path. T1-to-T2 feature/quality handoff is therefore NOT IMPLEMENTED / NOT VERIFIED.
- No live T0 endpoint, remote TLS, T2 runtime, paper order routing, or live execution is established by the adapter CI.

## 3. Synchronization matrix

| Flow | Intended transport/data | Current state | Gate |
|---|---|---|---|
| T0 → T1 | Versioned read-only Candle Contract v1 | Contract exists; T1 live consumer not verified | **NOT VERIFIED** |
| T1 Collector → T1 Intelligence | Bounded CSV import + immutable snapshot/provenance | Offline importer and fixtures exist; bounded runtime capture exists | **PARTIAL** |
| T1 connection health → T1 Intelligence | Sealed JSONL sidecar + trusted manifest/watermark | Validator/writer offline; upstream collector integration blocked | **BLOCKED** |
| T1 Intelligence → T2 | Versioned read-only snapshot/feature contract | No T2 consumer/API path verified | **NOT IMPLEMENTED** |
| T0 → T2 | Versioned read-only Candle Contract v1 | Adapter and isolated CI PASS | **ISOLATED PASS; LIVE NOT VERIFIED** |
| T2 Core + AI → Shared Risk | Independent ledgers, common risk admission, paper-only execution | Architecture/source evidence exists; current runtime not activated | **RUNTIME NOT AUTHORIZED** |

## 4. Target synchronization topology

```text
                         T0 Data Foundation
                 canonical candles + provenance/quality
                              |
                 GET /v1/candles (read-only, versioned)
                       /                 \
                      v                   v
             T1 Intelligence          T2 Freqtrade/FreqAI
             candle context           candle context
                      ^                   ^
                      |                   |
       T1-owned Collector CSV             |
       trades / funding / OI /             |
       liquidations / order book           |
                      |                   |
                      v                   |
             T1 bounded importer           |
             + sealed connection evidence  |
                      |                   |
                      v                   |
             T1 versioned intelligence ----+
             snapshot/read-only interface
                      |
                      v
              T2 AI feature adapter
                      |
           Strategy Core + independent AI
                      |
             Shared Risk Engine
                      |
                Paper ledgers
```

The diagram is a target, not a claim that these connections are implemented. T1 must not write into T0 storage. T2 must not read T1 files by arbitrary shared filesystem path; the T1 snapshot must be published through a bounded, versioned read-only contract with source identity, coverage, freshness, and fail-closed validation.

## 5. Required contract boundaries before integration

### T0 candle input

Keep the existing Candle Contract v1 as the only approved T0 candle boundary. Do not create a second T0 API or give consumers direct SQLite/PostgreSQL access. T1 and T2 must independently validate market identity, timeframe, closed-candle state, exact request window, freshness, gaps, and dataset version.

### T1 intelligence snapshot v1

Preserve the existing snapshot semantics as the starting contract:
- Market identity: Binance USDT perpetual BTCUSDT.
- Half-open UTC window `[windowStartMs, windowEndMs)`.
- `availableAtMs` is import/observation time; old data imported now must not masquerade as a new event.
- Preserve `snapshotId`, exact collector source SHA, per-file SHA-256 provenance, and per-feed coverage.
- Keep missing/unobserved values null; keep `OBSERVED_ONLY`; do not claim complete market coverage.
- Preserve distinct meanings: funding sample is not settled funding cash flow; OI sample is not a position; liquidation sample stream is not exhaustive.
- T1 connection health remains UNVERIFIABLE until a trusted producer writes a sealed sidecar and the importer validates it against the exact source/session/manifest/watermark.

### T1 → T2 consumer contract

Before T2 consumes T1, specify:
- Which T1 fields are research features versus execution/risk inputs.
- Exact schema/version, source SHA, snapshot ID, window, available-at time, and feature calculation version.
- Maximum age and completeness requirements per feed; unknown/missing/stale states must fail closed.
- No inference that funding/OI/liquidation observations are account funding cash flows or portfolio state.
- Deterministic behavior when T1 is absent: T2 candle-only/Core processing may continue only if the strategy's declared dependencies permit it; AI features requiring T1 must become unavailable, not silently substitute zero/cache/another venue.
- T1 feature data must not change Core RSI/ADX/Smart DCA semantics or bypass Shared Risk Engine.

## 6. Next implementation order

1. **Close T1 collector evidence blocker first:** reconcile the current PR head, correct the exact rustfmt failure, prove the post-hard-link poison regression with a RED/GREEN test, then run exact-head GitHub Actions. Keep PR #1 Draft and do not merge without separate approval.
2. **T1 producer/validator compatibility:** reconcile the event vocabulary and manifest contract between the Rust writer and Python validator; pin one exact collector source SHA and prove the sealed sidecar is consumable offline.
3. **T1 snapshot contract freeze:** define the stable JSON schema and validation rules from the existing importer output; add deterministic compatibility tests without using live CSV or the VPS.
4. **T0 → T1 isolated adapter:** consume only T0 Candle Contract v1 through the HTTP client; use fixtures/mock transport until the live T0 endpoint is separately authorized and verified.
5. **T1 → T2 isolated adapter:** add a read-only, versioned T1 snapshot consumer to T2 only after steps 1–3 pass. Add fail-closed and no-fallback tests.
6. **Cross-layer reconciliation:** prove matching symbol/market/time windows, timestamp alignment, provenance, freshness, duplicate/gap behavior, and deterministic feature output on exact source snapshots.
7. **Live read-only connectivity:** only after DNS/TLS/auth/service prerequisites are reviewed and the user separately authorizes endpoint probes. Do not start T1/T2 runtime or order routing as part of these steps.

## 7. Restrictions

- Do not change canonical T0 schema/storage/backend or grant direct DB/file access to T1/T2.
- Do not adopt the SQLite `single/shared database` prototype as canonical without a new explicit architecture decision and review.
- Do not start/restart/extend T1 capture, add symbols, connect new exchange streams, or run Data Quality Gate without separate authorization.
- Do not deploy Nginx/Caddy, change DNS/firewall/ports, start T0 API, or perform live endpoint probes under this assessment.
- Do not activate T2 runtime, model training, paper order routing, or live execution.
- Keep `ai_execution_enabled=false`; no live orders.

## 8. Verification record

- Main repository branch HEAD at assessment: `15c3ce26d79812e632b9763e6d51ccd37169467e`.
- Main repository architecture source blobs reviewed:
  - T0–T1–T2 data architecture: `1b11883b9d2b93e3039d509ecaed98694afe430e`.
  - T0 read-only candle contract: `dd19fe6f933a5c8b2a192f7bc65b64a00f205e9d`.
  - T2 HTTP consumer plan: `81d7eaef9aa9d2ad98d65e0dad1bac057b80e703`.
  - T1 importer: `5effe6540b86edcb190456c95b6bb11456aec099`.
  - T1 connection validator: `61b569d38fe817322fa8e7956cc1e55a326c50e8`.
- T1 collector PR #1 current head: `93a3931a3e5098dcac5ab04fa5f535cd1bd252ba`; push run `42455219012` FAILURE; PR run `42455222283` FAILURE.
- This assessment itself ran no tests and created no artifacts. Existing CI references above retain their exact historical SHAs and are not re-labeled as tests of this documentation commit.
- Assessment status: T0→T2 isolated adapter **PASS**; T0→T1 **NOT VERIFIED**; T1→T2 **NOT IMPLEMENTED**; T1 sidecar integration **BLOCKED**; end-to-end 3-layer synchronization **NOT VERIFIED**.
