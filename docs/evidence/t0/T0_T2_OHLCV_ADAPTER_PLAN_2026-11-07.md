# T0 → T2 OHLCV adapter plan — 2026-11-07

## Purpose

Define a safe, independently testable read-only adapter from T0 SQLite Canonical market data to the T2 Freqtrade/FreqAI research pipeline. This is a design and implementation plan only. It does not authorize canonical database creation, schema migration, ingestion, Feeder startup, changing T2's current OKX source, or live execution.

## Current verified boundary

- T0 store supports Binance USD-M BTCUSDT perpetual OHLCV at 15m and 1h.
- Candle records contain UTC open/close timestamps, decimal-string OHLCV, first-observed availability timestamp, source and quality metadata.
- Read API exposes coverage/gaps and a deterministic `datasetVersion`.
- Missing intervals are not silently forward-filled; API can return HTTP 200 with `coverage.complete=false`.
- SQLite is the approved canonical backend for the current PC-first phase, but the user confirmed the canonical SQLite file does not yet exist.
- Isolated temporary SQLite tests are permitted. No canonical file or production data may be created or written in this work item.
- T0 acceptance evidence: source SHA `1aac449b96c4079004e1cab882280b923e33342c`; GitHub Actions run [42329799499](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42329799499) SUCCESS. This proves isolated acceptance behavior, not a live canonical dataset.

## Adapter boundary

The future adapter must:

1. Open the configured T0 SQLite file in read-only mode (or call the authenticated read-only T0 API); it must never initialize schema or invoke a writer.
2. Request one explicit symbol/timeframe/UTC half-open window `[startMs,endMs)`.
3. Validate response identity: exchange Binance, market type USDT perpetual, symbol BTCUSDT, requested timeframe and exact requested window.
4. Require `coverage.complete=true`, expected candle count equal returned count, no gaps, strictly increasing unique open timestamps, and every candle marked closed and validated.
5. Preserve source provenance and datasetVersion in a sidecar manifest. Do not inject provenance columns into Freqtrade's OHLCV frame unless T2 explicitly defines them.
6. Convert decimal strings to numeric values only at the export boundary, using deterministic Decimal conversion and rejecting non-finite/overflow values.
7. Export to a staging path, verify the exported row count and timestamp range, then atomically publish the output. Never overwrite an existing dataset silently.
8. Keep T2's current OKX source and backtest configuration unchanged until parity acceptance is approved.
9. Have no network access to an exchange, no credential handling, no order/execution capability, and no write access to T0.

## Freqtrade compatibility must be established before implementation

Do not guess Freqtrade's filename, pair naming, timeframe encoding, futures suffix, or storage format. First pin the exact Freqtrade version and configuration used by this repository's T2 research workflow. Then add a compatibility fixture generated or validated by that exact version.

The adapter should initially support only BTCUSDT and the already supported 15m/1h timeframes. Additional pairs/timeframes require a separate contract change.

## Required tests (TDD)

### Unit tests
- Reject incomplete coverage, gaps, duplicate or out-of-order timestamps.
- Reject wrong exchange, market type, symbol, timeframe, or window boundaries.
- Reject unclosed, invalid-quality, malformed decimal, non-finite and invalid OHLCV values.
- Preserve exact timestamp semantics and source metadata in the manifest.
- Produce deterministic output for the same input and pinned exporter version.
- Refuse overwrite and clean up failed staging output.

### Integration tests
- Use a fresh temporary SQLite database only.
- Prove the adapter opens the source read-only: source hash/schema/row count unchanged before and after export.
- Verify exact exported row count, first/last timestamps and OHLCV values against the source.
- Validate output with the pinned Freqtrade version, not a hand-written approximation.
- Compare a bounded identical time window against the current OKX T2 dataset. Differences must be reported; do not silently normalize exchange differences.
- Keep missing intervals as a hard failure; no forward-fill or synthetic candles.

### Acceptance gates
- T0 source remains unchanged and read-only.
- T2 existing source/config remains unchanged.
- Export is reproducible and manifest records T0 datasetVersion, source identity, time window, timeframe, exporter version and output hash.
- Exact Freqtrade compatibility test passes.
- Source parity report exists and explicitly classifies differences.
- GitHub Actions passes on the exact source SHA.
- No live exchange, canonical DB, Feeder, VPS or execution is involved.

## Implementation sequence

1. Inventory the active T2 strategy/config/workflow and pin the exact Freqtrade version and data format.
2. Add failing tests for the adapter contract (RED).
3. Implement a minimal read-only exporter (GREEN).
4. Run focused adapter tests, then relevant T0 and T2 regression suites.
5. Add GitHub Actions workflow using synthetic temporary SQLite fixtures only.
6. Review exact-SHA CI results and record artifacts, source/output hashes and limitations.
7. Only after parity acceptance, propose a separate approval to use T0 as an additional T2 research input. Do not replace OKX by implication.

## Current status

- Adapter design: READY FOR IMPLEMENTATION.
- Exact T2 runtime/version/config inventory: NOT VERIFIED.
- Freqtrade output format compatibility: NOT VERIFIED.
- Adapter code/tests: NOT STARTED.
- T0 Canonical SQLite file: NOT CREATED (user-confirmed).
- Canonical ingestion: NOT RUN.
- Feeder: STOPPED.
- VPS: NOT PROVISIONED.
- Live execution: DISABLED (`ai_execution_enabled=false`).

## Next action

Inspect the active branch's T2 strategy, FreqAI config, dependency pins and GitHub Actions workflow. Record exact version and data-format evidence before writing adapter code. If these assets are not present on this branch, stop and identify the authoritative T2 branch/revision rather than implementing against assumptions.
