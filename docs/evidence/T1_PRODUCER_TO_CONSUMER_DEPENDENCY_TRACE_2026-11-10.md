# T1 Producer-to-Consumer Dependency Trace — 2026-11-10

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact source baseline: `5480ba9cfc138e1f629b2ba11d897dacb464a36c`
- Method: static inspection of pinned source blobs and existing T1 evidence/design records only.
- Scope: T1 futures-intelligence CSV producer/importer/sidecar and its in-scope consumers. This is not an activation or integration task.
- No tests, workflow dispatch, VPS/SSH, collector start, exchange request, DB, source repository write, or runtime operation performed.

## 1. T1 has multiple distinct source/data paths

| Path | Producer/source | In-repo consumer | Output | Current boundary/status |
|---|---|---|---|---|
| T1 futures observations | External `waynemason1/binance-futures-collector` pinned at `bc4f0ef633fbeee4a49defd72827f17162693805`; CSV files supplied by operator/capture | `futures_intelligence.import_collector` | JSON intelligence snapshot with input file hashes and `OBSERVED_ONLY` | Importer implemented; no automatic collector start/capture/scheduler established |
| Connection lifecycle evidence | Separate Rust reference writer under `futures_intelligence/collector_sidecar_writer` | `futures_intelligence.connection_events.load_and_validate_connection_events` | Offline connection-status report from sealed JSONL + externally trusted digest/watermark | Writer and validator exist; not integrated into pinned upstream collector, importer, quality or decision |
| T1 1m kline producer contract | Separate source-file contract v1.1 design for a future Binance USD-M BTCUSDT 1m producer | No accepted in-repo ingestion adapter identified in this trace | Target manifest + durable committed-prefix/watermark contract | DESIGN ONLY; NOT APPROVED FOR IMPLEMENTATION; no promotion to T0/T2 |
| T0 canonical candles | T0 Feeder, not T1 | T0 API and T2/Core consumers | Canonical M15/H1 candles | Independent source of truth; not replaced by T1 |

These paths must not be conflated. In particular, the T1 intelligence CSV importer is not the proposed 1m kline canonicalization adapter, and the connection sidecar is not a market-data feed.

## 2. Confirmed CSV observation path

1. External collector source identity is pinned in `import_collector.py` as `bc4f0ef633fbeee4a49defd72827f17162693805`.
2. The CLI accepts explicit `--trades`, `--funding`, `--open-interest`, and `--liquidations` CSV paths, a half-open time window and an output path. Flags may repeat for daily files.
3. Importer enforces exact headers, Binance futures BTCUSDT identity, UTC millisecond timestamp consistency, bounded file/row counts, numeric constraints, duplicate semantics, file stability during read and per-file SHA-256.
4. It builds a deterministic content-identified snapshot with `quality=OBSERVED_ONLY`, `collectorCommit`, `inputFiles`, per-feed coverage and `complete=false`.
5. `write_snapshot()` validates the snapshot, writes a temporary file in the target directory, flushes/fsyncs the file, then atomically replaces the target. This is snapshot publication, not source CSV durability or producer completeness.
6. `pipeline.api.intelligence_snapshot()` loads only the configured `INTELLIGENCE_REPORT_PATH` JSON file and calls `validate_snapshot()`.
7. The API quality and decision path evaluates feed freshness. The decision module consumes trade flow only after quality gates; funding/OI/liquidation are exposed for dashboard/downstream analysis, not currently direction-setting inputs.
8. The README explicitly states that importer CLI does not start the collector, download fixture data, contact the exchange or place orders.

### CSV path limits

- A CSV hash proves the bytes read matched the recorded digest at import; it does not authenticate the collector or prove that no events were omitted upstream.
- Trade-ID gap counts are local observations over supplied rows; no observed gap is not proof of transport continuity.
- Funding/OI sample timestamps and liquidation observations have their own limitations; liquidation rows have no unique event ID and are not deduplicated by invented identity.
- Importer hard-codes `connectionStatus=UNVERIFIABLE`; it rejects a snapshot claiming a different state.
- Snapshot availability time is import/server time, so old source rows imported now do not become fresh market events.
- No in-repository scheduler, watched-directory consumer, or automatic invocation of the CLI was established in this trace. Actual operator procedure, file locations and artifact existence remain unknown.

## 3. Connection sidecar path is intentionally disconnected

- Rust writer is under `futures_intelligence/collector_sidecar_writer`; it is a portable offline reference implementation.
- It creates append-only JSONL with exclusive create, flush + `sync_data()`, Ping/Pong correlation, lifecycle validation, finalized manifest, sidecar size/hash and capture watermark.
- Python validator independently checks the supplied digest, pinned source SHA, session identity, ordered unique events, lifecycle state, heartbeat pairing, expected routes and capture watermark.
- Both components are explicitly described as separate from the legacy CSV importer.
- Pinned upstream collector source does not write this sidecar; its lifecycle events are logs. The implementation evidence records that process session ID, per-socket connection IDs, Ping/Pong payload correlation, lifecycle persistence and reconnect integration are not implemented in upstream.
- The validator is not called from `import_collector.py`, `feed_quality()`, `pipeline.api` or decision gating. Therefore its synthetic test PASS cannot be used to upgrade current CSV snapshot `connectionStatus` from UNVERIFIABLE.

## 4. Separate 1m kline contract — no adapter edge proven

- `T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md` is explicitly DESIGN ONLY / NOT APPROVED FOR IMPLEMENTATION.
- It concerns Binance USD-M BTCUSDT 1m klines, not the trades/funding/OI/liquidations intelligence CSVs.
- It requires a versioned FINAL_ONLY manifest, bound USD-M endpoint and ExchangeInfo identity, producer-owned durable committed offset, reconciliation-backed watermark and fail-closed source-health semantics.
- It prohibits writing to T0 SQLite or promoting the T1 staging result to T0/T2 without a separate approval.
- No in-scope adapter implementation, source watcher, staging DB, consumer edge or promotion path was identified in this static trace.
- Do not interpret the contract document or existing generic collector CSV writer as evidence that these requirements are implemented.

## 5. T1 findings / dispositions

### T1-DEP-01 — CSV importer is pull/CLI driven, not a proven continuous ingestion service
- Evidence: importer exposes `main()` arguments requiring explicit input paths, time window and output path; README instructs manual invocation.
- Impact: presence of importer does not establish an automated producer-to-consumer pipeline or continuous freshness.
- Status: SOURCE-CONFIRMED; runtime scheduling/operator process NOT VERIFIED.
- Disposition: KEEP importer; PARK orchestration/activation until separately designed and approved.

### T1-DEP-02 — Observation provenance is stronger than transport completeness
- Evidence: input SHA-256, pinned source commit, row validation and snapshot content identity coexist with `complete=false`, `continuityStatus=UNVERIFIED`, `connectionStatus=UNVERIFIABLE`.
- Impact: hashes and clean CSV rows cannot certify no missed events or continuous connection.
- Status: SOURCE-CONFIRMED.
- Disposition: KEEP fail-closed semantics; do not weaken quality gates.

### T1-DEP-03 — Sidecar writer/validator are not connected to the real collector or decision path
- Evidence: README, Rust README, evidence report and code comments all explicitly state offline reference only; importer does not call validator.
- Impact: sidecar unit tests prove offline component behavior only, not live transport continuity.
- Status: SOURCE-CONFIRMED.
- Disposition: PARK upstream fork/integration and separate validator-to-importer design; do not infer operational status.

### T1-DEP-04 — Sidecar trust is incomplete even when digest validation succeeds
- Evidence: validator accepts caller-supplied expected SHA/source/session/watermark; writer README states manifest is unsigned and SHA-256 is not producer authentication.
- Impact: if expected digest and manifest are not obtained through an independently protected capture path, checksum match alone does not establish trusted provenance.
- Status: SOURCE-CONFIRMED limitation; current trusted capture custody NOT VERIFIED.
- Disposition: keep offline validator; do not claim authenticated connection evidence.

### T1-DEP-05 — 1m kline v1.1 contract is a separate, unimplemented data product
- Evidence: contract status DESIGN ONLY / NOT APPROVED; no adapter edge found in current T1 intelligence importer path.
- Impact: do not combine the kline contract with the existing intelligence CSV path or promote it into T0.
- Status: SOURCE-CONFIRMED design boundary; implementation NOT VERIFIED.
- Disposition: PARK; independent review/approval gates remain required.

## 6. KEEP / PARK / NOT VERIFIED

### KEEP
- Existing T1 CSV importer and strict validation/provenance.
- Existing `OBSERVED_ONLY`, `complete=false`, `connectionStatus=UNVERIFIABLE` fail-closed semantics.
- Offline connection sidecar writer/validator as separately scoped reference/test components.
- T1-to-API JSON snapshot contract and decision freshness gate.

### PARK
- Automatic collector scheduling, file watcher, continuous import orchestration.
- Upstream collector fork and connection-sidecar integration.
- Trusted sidecar manifest/digest custody and validator integration.
- T1 1m kline adapter and any promotion path.
- Any T1-to-T0 canonical data path.

### NOT VERIFIED
- Active upstream collector process and exact runtime source SHA.
- Actual CSV file set, capture path, rotation, publication/durability behavior and snapshot artifact.
- Current operational invocation/schedule and API environment path.
- Live WebSocket heartbeat/reconnect continuity and sidecar capture.
- Trusted independent custody of sidecar digest/manifest.
- Any deployed T1 service or continuous producer-to-consumer edge.

No T1 source, test, workflow, schema, runtime, VPS, DB, collector or exchange was changed or operated.

## 7. Evidence anchors at inspected source baseline

- `futures_intelligence/import_collector.py`: `5effe6540b86edcb190456c95b6bb11456aec099`
- `futures_intelligence/connection_events.py`: `61b569d38fe817322fa8e7956cc1e55a326c50e8`
- `futures_intelligence/collector_sidecar_writer/README.md`: `e4aa4f8cfa65ea5134383421182a6331d2803f31`
- `futures_intelligence/README.md`: `9fd972b2873d619524782411b8a9ec2bb0b84991`
- `pipeline/api.py`: `0540540462b3710a25788e4ff47a88272b7ee9c3`
- `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`: `bafe555b6e3941bed4188575c7b7591c4ce3b473`
- `docs/evidence/t1/T1_COLLECTOR_SIDECAR_WRITER_IMPLEMENTATION_2026-11-07.md`: `9a8ae6b221142c49558a203f1a42b20741855a92`
- `docs/evidence/t1/T1_CONNECTION_EVENT_SIDECAR_CONTRACT_2026-11-07.md`: `c51bb4dfe247a8306e386325562cc2ded9e48e1f`

## 8. Status and next safe step

- T1 static producer-to-consumer trace: PASS for inspected source boundaries; PARTIAL for complete repo/runtime inventory.
- T1 importer and sidecar code presence: SOURCE-CONFIRMED.
- Actual continuous producer-to-consumer runtime: NOT VERIFIED.
- Tests and GitHub Actions: NOT RUN / NOT DISPATCHED in this increment.
- No independent review claimed.
- L4-Minimum operational acceptance remains BLOCKED / NOT VERIFIED.
- G2 exact-SHA CI and G3 independent review remain NOT VERIFIED / PENDING.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Option C — No Destructive Authority remains in force; no TTL, automatic deletion, archive, cleanup, vacuum, compaction, backup expiry or replica removal.

Next safe increment: map T4 route/auth/control dependencies and identify whether any current in-scope API route bypasses the intended gateway or authorization boundary. Continue static-only; no deployment or permission changes.
