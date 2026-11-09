# T1 Collector and Data Contract Compatibility Review — 2026-11-09

## Scope

Read-only static review of the T1 collector repository and its current draft pull request, as the next bounded rollout gate after the recorded T0 loopback API and T2 one-shot verification.

Reviewed repository: `kenznguyen/binance-futures-collector`  
Reviewed PR: #1 — `Add durable pre-handshake connection failure evidence`  
PR state: OPEN, DRAFT, not merged  
PR head branch: `feature/t1-connection-sidecar-integration-20261107`  
Exact reviewed source SHA: `6e20fe94f3ad64cc450e73def80a167fe371e49e`

This is a source/contract review only. No T1 deployment, collector execution, VPS command, market-data read, database mutation, T0/T2 change, workflow dispatch, PR review submission, merge, or destructive action was performed.

## Source evidence

Files fetched at the exact reviewed PR head:

| File | Git blob SHA |
|---|---|
| `README.md` | `5e03d3e00bb4b1fe6ed4ed389006e50d5683c5e3` |
| `config.example.toml` | `3436a8b75dc827a9299c083e9af783c8a74196c3` |
| `src/main.rs` | `d3cde50a9fb761a1d6ef711a5a04cbbda359f3ed` |
| `src/config.rs` | `e07fd601986d7a8db18109e3179937579c425f98` |
| `src/utils/csv_writer.rs` | `2c4538dcef7dfa758a854292031239c15f7c282b` |
| `src/utils/gap_registry.rs` | `494db80a855efeebf8b0d9084d9179254c525b6a` |
| `src/constants.rs` | `0bf50b5fe02f4f196b38481cde6ecab9e2adb941` |
| `crates/connection-sidecar/README.md` | `43806ca013aa1b8b8784fd29805dac677729aa12` |
| `crates/connection-sidecar/src/lib.rs` | `0a2c127000ee1c9776b3594e1292b481c42c878c` |

## Findings

### F1 — T1 persistence format is not the T0 canonical store

T1 writes partitioned CSV files under a configurable output directory. It does not write the T0 SQLite schema and does not expose the T0 Candle HTTP contract. Therefore, T1 data cannot be treated as canonical T0 data or consumed by T2's existing canonical HTTP client without a separately designed and tested ingestion/adapter boundary.

### F2 — T1's documented kline stream does not match the current canonical candle intervals

The collector README documents per-symbol 1-minute klines. The current T0/T2 canonical context consumes 15-minute candles and also validates 1-hour data through the T0 API gate. A deterministic 1m→15m/1h aggregation contract is not established by this review. It must define UTC bucket boundaries, closed-bucket rules, missing constituent candles, late arrivals, corrections, duplicate handling and provenance before any promotion to canonical data.

### F3 — T1 CSV headers do not implement the T0 candle envelope

The reviewed CSV headers include collector-specific fields such as exchange, market, datatype, timestamp, symbol and OHLCV values. The reviewed kline schema does not establish T0 envelope semantics such as contract/schema version, datasetVersion, asOfMs, explicit coverage/gaps, quality, availabilityKind, or the exact closed-candle/availability contract expected by T2.

### F4 — CSV flush is not a durable ingestion acknowledgement

The reviewed writer buffers rows and flushes using the buffered writer's `flush()`. This is not equivalent to a database transaction or an `fsync`/durable commit acknowledgement. A future importer must explicitly handle partial final rows, process interruption, replay, duplicate ingestion, source-file rotation, cursor/checkpoint durability and idempotent recovery. No importer or such checkpoint protocol was established here.

### F5 — Connection sidecar does not certify market-data completeness

The sidecar README explicitly labels the crate as a portable offline reference implementation, not integrated into the upstream collector. It also explicitly separates sidecar persistence and manifest consistency from market-data completeness, and states that its watermark is a caller assertion. Its manifest cannot be used as proof of complete trades, klines, order-book continuity or REST coverage.

### F6 — Current CI is code-level evidence only

The reviewed source SHA has GitHub Actions run `42479498182` (workflow `CI`), conclusion SUCCESS. All 5 jobs completed successfully:
- Collector fmt/Clippy/build/tests and sidecar offline checks
- Dashboard backend tests
- Security checks
- Dashboard frontend type-check/build/tests
- Docker image build

No workflow artifact was published for this run. This run does not test T0 schema compatibility, ingestion, live exchange completeness, VPS deployment, T1 runtime behavior or T1→T2 delivery.

## Contract compatibility matrix

| Boundary | Result | Evidence / limitation |
|---|---|---|
| T1 source builds and repository CI | PASS | Exact source SHA and run 42479498182 |
| T1 raw CSV persistence understood | PARTIAL | CSV paths and headers reviewed; runtime file behavior not exercised |
| T1 sidecar event contract | PARTIAL | Offline reference crate reviewed; not integrated |
| T1→T0 canonical SQLite compatibility | BLOCKED | No canonical writer/adapter or schema mapping established |
| T1→T0 Candle API compatibility | BLOCKED | No T1 ingestion endpoint or canonical envelope producer |
| T1 1m→15m/1h aggregation contract | BLOCKED | No approved aggregation/late-data/coverage contract |
| T1→T2 end-to-end delivery | NOT RUN | No importer, runtime test or E2E evidence |
| T1 VPS activation | NOT AUTHORIZED BY THIS REVIEW | Separate rollout gate required |

## Required next work before activation

1. Freeze a versioned T1 source-file contract: file naming/partitioning, CSV schema/version, timestamp units and UTC semantics, symbol normalization, data-type identity, ordering, rotation and partial-file handling.
2. Specify a read-only ingestion adapter into a separate staging/canonicalization boundary. Do not let T1 write directly into T0's canonical database.
3. Define idempotent source cursors and durable checkpoint semantics, including restart/replay, duplicate rows, partial writes and late/corrected records.
4. Define and test 1m→15m/1h aggregation, closed-candle semantics, gap detection, quality and provenance. Missing/incomplete data must fail closed; never synthesize missing market data.
5. Reconcile order-book and trade completeness independently from connection-sidecar status.
6. Build deterministic fixture tests first, then an isolated file→adapter→contract test. Keep T0 canonical store and T2 runtime unchanged during this work.
7. Only after contract tests and independent review pass, prepare a separate explicit T1 activation proposal.

## Guardrails preserved

- T0 remains independent and remains the canonical data foundation.
- No T1 deployment or activation is authorized by this review.
- No T0 SQLite/API, Feeder, T2 consumer, strategy, AI, ledger, shared risk engine or Kill Switch changes.
- No live trading; `AI_EXECUTION_ENABLED=false`.
- No OKX source replacement.
- No data deletion, archive, cleanup, vacuum, compaction, backup expiry or destructive test.
- PR #1 remains OPEN/DRAFT; no review or merge action was submitted.

## Final status

**PARTIAL — T1 repository CI PASS; T1→T0/T2 contract compatibility BLOCKED.**

Tests run in this review: none (read-only static review).  
GitHub Actions run inspected: `42479498182`, SUCCESS, 5/5 jobs.  
Workflow artifact: NONE.  
T1 runtime / VPS: NOT EXECUTED.  
T1→T0/T2 integration: NOT RUN.  
Next gate: define and independently review the T1 source-file and ingestion contract before proposing any T1 activation.
