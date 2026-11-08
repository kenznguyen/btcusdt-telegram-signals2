# T2 Dataset Provenance Schema Discovery — 2026-11-08

## Scope

Read-only inspection of the current T2 branch to identify an existing, authoritative dataset row format before implementing dataset-level provenance checks. No code, runtime, T0/T1 database, feeder, exchange or strategy behavior was changed.

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`
- Inspected branch HEAD: `96266de7e514e45389e24ce5b23391d177872fc9`
- Working tree: NOT VERIFIED (GitHub API inspection only).

## Existing dataset formats found

### 1. T0 API snapshot consumed by the offline T0 → Freqtrade adapter

Source: `quant_system/t0_freqtrade_adapter.py`.

The current adapter contract accepts one timeframe per snapshot and validates:

- Top-level identity: `exchange=binance`, `marketType=USDT_PERPETUAL`, `symbol=BTCUSDT`.
- Timeframe: exactly `15m` or `1h`.
- Window: `startMs`, `endMs`, optional `asOfMs`; aligned to the selected interval.
- Source dataset identity: `datasetVersion` equals SHA-256 of canonical JSON over `exchange`, `marketType`, `symbol`, `timeframe`, `startMs`, `endMs`, `asOfMs`, and `candles`.
- Coverage: exact expected/returned count, `complete=true`, empty `gaps`.
- Candle rows: `exchange`, `marketType`, `symbol`, `timeframe`, `openTimeMs`, `closeTimeMs`, `availableAtMs`, OHLCV decimal strings, `isClosed=true`, `availabilityKind=FIRST_OBSERVED`, `quality=VALIDATED`, `source=ccxt.binanceusdm`.
- Candle intervals are contiguous; `closeTimeMs = openTimeMs + interval`; availability cannot precede close; OHLC bounds and decimal/float conversion are checked.

The adapter reads a saved snapshot file only. It does not open the T0 database, start a feeder, fetch from an exchange or submit orders.

### 2. ChartPro parity CSV

Source: `freqtrade_parity/dataset_io.py` and `freqtrade_parity/dataset_hash.py`.

- CSV columns required: `open_time, open, high, low, close, volume, closed`.
- Closed rows only; open timestamps aligned to a caller-provided step.
- Rows must be non-empty, sorted, unique and exactly contiguous.
- OHLCV values must be finite.
- Canonical hash protocol is `CHARTPRO-OHLCV-V2` binary encoding.

This format does not include exchange, market type, symbol, source provenance, per-candle availability timestamp or quality classification. It is therefore not sufficient by itself to establish canonical T0 source identity for the signed AI dataset.

## Existing AI provenance gap

Source: `quant_system/ai_provenance_validator.py`.

The signed manifest has one opaque `dataset` artifact role and a free-form `dataset_version` identity. Prediction rows repeat that identity. The validator currently verifies artifact bytes and row-to-manifest version equality, but does not parse the dataset artifact. No signed dataset format/version or multi-timeframe container contract is declared.

## Blocking contract decision

The T0 API snapshot format contains exactly one timeframe. The intended T2 model/strategy context uses M15 and closed H1 data. No existing source defines how both snapshots are packaged as the single signed `dataset` artifact or how the aggregate dataset version is calculated.

Do not guess whether the signed artifact is:
1. one timeframe snapshot only, or
2. a versioned bundle containing both M15 and H1 snapshots.

Recommended direction is a versioned two-timeframe bundle that embeds the existing T0 snapshot payloads unchanged and defines an aggregate dataset fingerprint. This would keep T0's API contract independent and let T2 validate both timeframe rows and prediction coverage without touching T0 runtime. This is a recommendation only; no bundle schema has been implemented or assumed.

## Status

- Existing T0 snapshot row schema discovery: PASS.
- Existing CSV schema discovery: PASS.
- Sufficient existing contract for a single canonical T0 timeframe: PASS.
- Signed dataset artifact format and M15/H1 packaging: BLOCKED pending explicit contract selection.
- Dataset row-level validator: NOT IMPLEMENTED.
- Prediction timestamp/outcome-window reconciliation against candle coverage: NOT IMPLEMENTED.
- Recomputing labels/outcomes from OHLCV: NOT AUTHORIZED / NOT IMPLEMENTED; price basis, candle-close convention and label horizon remain unspecified.
- Real BTCUSDT OOS dataset: NOT PROVIDED.
- AI calibration attestation: NOT ISSUED; AI leverage authorization: NOT ISSUED.
- `AI_EXECUTION_ENABLED=false`; no paper or live runtime.

## Next step

Confirm whether the signed `dataset` artifact must be a single timeframe snapshot or a bundle containing both M15 and H1 snapshots. If the bundle is selected, define the aggregate fingerprint and prediction-to-candle coverage convention before writing RED tests and the validator.
