# T0–T2 Binance/OKX OHLCV Parity Manifest Specification

Date: 2026-11-07  
Status: DESIGN ONLY — no dataset acquisition or parity run authorized/performed.

## 1. Purpose

Define a reproducible, offline comparison package for Binance USD-M T0 candles and the existing OKX perpetual T2 research/backtest candles. The goal is to quantify source differences on the same UTC window, not to assert that the two exchanges must produce identical OHLCV.

The manifest is evidence metadata. It does not authorize a canonical database, market sync, Feeder, exchange execution, source switch, branch merge, or backtest publication.

## 2. Required source identity

Each source record must state all of:

- exchange name and API/adapter identity;
- market type and instrument identifier;
- canonical project symbol;
- candle timeframe;
- source timezone and timestamp unit;
- OHLCV volume unit;
- closed-candle confirmation rule;
- source file SHA-256;
- row count, first open time and last open time;
- exact half-open UTC window [start_ms, end_ms);
- raw/source dataset version where available;
- independent CHARTPRO-OHLCV-V2 digest.

Expected source identities:

| Field | T0 source | Existing T2 source |
|---|---|---|
| Exchange | Binance | OKX |
| Market | USD-M linear perpetual | USDT perpetual swap |
| Instrument | BTC/USDT:USDT (BTCUSDT) | BTC-USDT-SWAP |
| M15/H1 | Required | Required |
| Timestamp | UTC milliseconds | UTC milliseconds |
| Volume | Base-asset BTC | volCcy BTC from OKX history-candles response |
| Closed rule | T0 validated closed-candle record | OKX confirm == 1 and close time <= observation time |

Do not compare OKX contract-count volume (vol) with Binance base-asset volume. The existing T2 bot.py maps OKX response volCcy (column 6) into its volume field; record that mapping in the export evidence.

## 3. Hash contracts

Keep three independent hashes where applicable:

1. source_file_sha256: exact bytes of each CSV file, including header and line endings.
2. t0_dataset_version: T0 market_data.store.read_window() hash for the Binance source. This is a JSON-envelope hash and includes source/window/as-of and decimal candle metadata.
3. chartpro_ohlcv_v2_sha256: T2 V2 binary hash over sorted closed M15 and H1 rows, each encoded as signed int64 UTC open milliseconds plus five IEEE754 float64 values in big-endian order, preceded by the exact CHARTPRO-OHLCV-V2\0, M15\0, and H1\0 markers.

These hashes have different meanings and MUST NOT be compared to each other. Preserve original decimal strings in the source CSV. Conversion to float64 is solely for the V2 hash and comparison calculations; record conversion implementation/version and do not overwrite raw decimals.

## 4. Manifest shape

Illustrative schema only; no actual values or dataset hashes are pre-filled.

~~~json
{
  "schema": "T0-T2-BINANCE-OKX-PARITY-MANIFEST-V1",
  "pair_id": "BTCUSDT-M15-H1-<window-start>-<window-end>",
  "window": {
    "start_ms": 0,
    "end_ms": 0,
    "interval_semantics": "[start_ms,end_ms)",
    "time_unit": "unix_ms",
    "timezone": "UTC"
  },
  "sources": {
    "binance_t0": {
      "exchange": "BINANCE",
      "market_type": "USD_M_LINEAR_PERPETUAL",
      "instrument": "BTC/USDT:USDT",
      "symbol": "BTCUSDT",
      "volume_unit": "BTC_BASE_ASSET",
      "m15_csv": "external-input",
      "h1_csv": "external-input",
      "source_file_sha256": {},
      "t0_dataset_version": {},
      "chartpro_ohlcv_v2_sha256": {},
      "coverage": {}
    },
    "okx_t2": {
      "exchange": "OKX",
      "market_type": "USDT_PERPETUAL_SWAP",
      "instrument": "BTC-USDT-SWAP",
      "symbol": "BTCUSDT",
      "volume_unit": "BTC_BASE_ASSET_VOLCCY",
      "volume_field_mapping": "history-candles[6]",
      "m15_csv": "external-input",
      "h1_csv": "external-input",
      "source_file_sha256": {},
      "chartpro_ohlcv_v2_sha256": {},
      "coverage": {}
    }
  },
  "conversion": {
    "ohlcv_numeric_format": "IEEE754_BINARY64",
    "byte_order": "BIG_ENDIAN",
    "timestamp_format": "SIGNED_INT64_UTC_MILLISECONDS",
    "source_decimal_strings_preserved": true,
    "implementation_revision": "required"
  },
  "comparison": {
    "row_alignment_key": ["timeframe", "open_time_ms"],
    "metrics": ["open", "high", "low", "close", "volume"],
    "exact_ohlcv_equality_required": false
  }
}
~~~

## 5. Acceptance gates before comparison

- Both sources cover exactly the same UTC [start_ms,end_ms) window for each timeframe.
- M15 and H1 timestamps align to their respective interval boundaries.
- Every row is explicitly closed; no current/in-progress candle is accepted.
- No duplicate, unsorted, missing or non-finite rows.
- OHLC validity and non-negative volume checks pass.
- M15 and H1 coverage is independently complete; no forward-fill, zero-fill or synthetic candles.
- Source files are immutable for the run and their raw-byte SHA-256 values are recorded.
- The T0 datasetVersion is captured from the exact T0 source window and is retained separately from the V2 hash.
- Comparison code version and exact source SHA are recorded.

Any failed gate makes the report NOT_COMPARABLE; do not compute aggregate similarity metrics over silently filtered rows.

## 6. Comparison outputs

Produce a machine-readable JSON and human-readable Markdown report containing:

- exact source identities and time window;
- independent file hashes, T0 datasetVersion and V2 hashes;
- M15/H1 row counts, missing/extra timestamps and coverage;
- per-field exact match count;
- mean/median/p95/max absolute and relative differences for OHLC;
- volume differences separately, explicitly labelled BTC base-asset volume;
- largest-difference rows with timestamps and both source values;
- price basis/contract metadata caveats;
- a statement that differences are market-source differences, not necessarily data corruption.

Do not collapse all metrics into one opaque similarity score.

## 7. Safety and publication

- Inputs must be operator-supplied immutable exports or generated in a separately approved isolated read-only process.
- Do not create or write the PC Canonical SQLite DB as part of this parity task.
- Do not replace OKX as T2's current source based on this report alone.
- No live execution, exchange credentials, Feeder or VPS.
- Report is research evidence, not a profitability claim or signal certification.


## Offline harness invocation and CSV contract

Implementation: `market_data/t0_t2_parity.py` (Python standard library only).

Each of the four input CSV files (Binance M15/H1 and OKX M15/H1) must contain these columns:

`open_time,open,high,low,close,volume,closed`

- `open_time`: Unix UTC milliseconds.
- OHLCV values: original decimal strings; prices strictly positive; volume non-negative.
- `closed`: `1` or `true`.
- Rows must be sorted, unique, gap-free and exactly cover the manifest's half-open UTC window for that timeframe. No forward fill, zero fill, filtering or synthetic candles.
- CSV paths are resolved relative to the manifest file's directory.
- The manifest must include Binance `t0_dataset_version.m15` and `t0_dataset_version.h1` values from the corresponding T0 `read_window()` calls. These are provenance values, not recomputed from CSV bytes.

Example invocation (only after operator supplies paired exports and provenance):

~~~bash
python -m market_data.t0_t2_parity \\
  --manifest /path/to/parity/manifest.json \\
  --json-output /path/to/parity/report.json \\
  --markdown-output /path/to/parity/report.md
~~~

Successful output is `COMPARABLE`; invalid/missing inputs fail closed with exit code 2 and `NOT_COMPARABLE` on stderr. The tool does not contact exchanges, open a database, or create market data.

## Harness verification evidence

- TDD RED: run `42332542018`, source SHA `0fb76a394b62a87b1c014559ea6437a4156914ec`, missing harness module as expected.
- Final CI: run `42332748148`, exact SHA `4664c28eaf0ae40f5e797b022284a378d2309c49`, all 4 jobs SUCCESS.
- Static Gateway 270 tests PASS; Paper consumer 52 tests PASS including 7 parity tests; restricted provider bootstrap PASS; isolated TimescaleDB integration PASS.
- Consumer artifact `13558540383` digest `sha256:0311b7e5b3b0264b6f2f5ac3e5442cb3e3061109b5ccc597177dcefcbc532673`.
- Static/Gateway artifact `13558003133` digest `sha256:c50838261cd0fffcbf1a772f2b355334da3277a5c33440a96f779b3fbc5b739e`.
- Provider artifact `13558347616` digest `sha256:f876d226d421801a453a887494dc89dddf59030a6991dda761058407e1df5129`.
- Timescale artifact `13557404226` digest `sha256:9d0ec699740b570d2578071582b6a6a03561dcb5d4b864866381faf429401f7c`.
- Real Binance/OKX parity is still NOT RUN; no paired CSV exports supplied.
