"""Offline, read-only exporter for canonical T0 candles into Freqtrade JSON.

The exporter consumes a saved T0 API response. It never opens T0 storage,
starts a feeder, calls an exchange, changes strategy code, or enables orders.
Each dataset is written into a new immutable-by-convention directory; an
existing export is never overwritten.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
from decimal import Decimal, InvalidOperation
from pathlib import Path

INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000}
MAX_CANDLES = 2_000
PRICE_FIELDS = ("open", "high", "low", "close", "volume")
DATASET_HASH_FIELDS = (
    "exchange", "marketType", "symbol", "timeframe",
    "startMs", "endMs", "asOfMs", "candles",
)


class T0FreqtradeAdapterError(ValueError):
    """Raised when a T0 snapshot cannot safely become a Freqtrade dataset."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise T0FreqtradeAdapterError(code)


def _is_int(value) -> bool:
    return type(value) is int and 0 <= value < 2**63 - 1


def _decimal(value, field: str) -> Decimal:
    _require(isinstance(value, str) and 1 <= len(value) <= 128,
             "INVALID_DECIMAL_FIELD")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise T0FreqtradeAdapterError("INVALID_DECIMAL_FIELD") from exc
    _require(number.is_finite() and len(number.as_tuple().digits) <= 40,
             "INVALID_DECIMAL_FIELD")
    _require(-30 <= number.as_tuple().exponent <= 30 and number.adjusted() <= 30,
             "INVALID_DECIMAL_FIELD")
    _require(number >= 0 and (field == "volume" or number > 0),
             "INVALID_DECIMAL_FIELD")
    return number


def _dataset_version(snapshot: dict) -> str:
    identity = {key: snapshot[key] for key in DATASET_HASH_FIELDS}
    encoded = json.dumps(
        identity, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _validate_snapshot(snapshot: dict) -> tuple[list[list[float]], dict]:
    required = set(DATASET_HASH_FIELDS) | {"datasetVersion", "coverage"}
    _require(isinstance(snapshot, dict) and required <= snapshot.keys(),
             "INVALID_T0_RESPONSE_SCHEMA")
    _require(
        snapshot["exchange"] == "binance"
        and snapshot["marketType"] == "USDT_PERPETUAL"
        and snapshot["symbol"] == "BTCUSDT"
        and snapshot["timeframe"] in INTERVAL_MS,
        "UNSUPPORTED_SOURCE_IDENTITY",
    )

    timeframe = snapshot["timeframe"]
    interval = INTERVAL_MS[timeframe]
    start, end = snapshot["startMs"], snapshot["endMs"]
    _require(_is_int(start) and _is_int(end), "INVALID_WINDOW")
    _require(
        start % interval == 0
        and end % interval == 0
        and 0 < end - start <= MAX_CANDLES * interval,
        "INVALID_WINDOW",
    )
    as_of = snapshot["asOfMs"]
    _require(as_of is None or _is_int(as_of), "INVALID_AS_OF")
    _require(snapshot["datasetVersion"] == _dataset_version(snapshot),
             "DATASET_VERSION_MISMATCH")

    coverage = snapshot["coverage"]
    expected = (end - start) // interval
    _require(
        isinstance(coverage, dict)
        and coverage.get("complete") is True
        and coverage.get("expected") == expected
        and coverage.get("returned") == expected
        and coverage.get("gaps") == [],
        "INCOMPLETE_T0_WINDOW",
    )
    candles = snapshot["candles"]
    _require(isinstance(candles, list) and len(candles) == expected,
             "INCOMPLETE_T0_WINDOW")

    rows: list[list[float]] = []
    cursor = start
    for candle in candles:
        _require(isinstance(candle, dict), "INVALID_CANDLE")
        _require(
            candle.get("exchange") == "binance"
            and candle.get("marketType") == "USDT_PERPETUAL"
            and candle.get("symbol") == "BTCUSDT"
            and candle.get("timeframe") == timeframe
            and candle.get("source") == "ccxt.binanceusdm",
            "CANDLE_SOURCE_MISMATCH",
        )
        opened, closed, available = (
            candle.get("openTimeMs"), candle.get("closeTimeMs"),
            candle.get("availableAtMs"),
        )
        _require(
            _is_int(opened) and _is_int(closed) and _is_int(available)
            and opened == cursor and opened % interval == 0
            and closed == opened + interval and available >= closed,
            "CANDLE_GAP_OR_OVERLAP",
        )
        _require(
            candle.get("isClosed") is True
            and candle.get("availabilityKind") == "FIRST_OBSERVED"
            and candle.get("quality") == "VALIDATED",
            "CANDLE_NOT_CLOSED_AND_VALIDATED",
        )
        if as_of is not None:
            _require(available <= as_of, "CANDLE_AFTER_AS_OF_CUTOFF")

        values = {name: _decimal(candle.get(name), name) for name in PRICE_FIELDS}
        _require(
            values["low"] <= values["high"]
            and values["low"] <= values["open"] <= values["high"]
            and values["low"] <= values["close"] <= values["high"],
            "INVALID_OHLC_BOUNDS",
        )
        floats = [float(values[name]) for name in PRICE_FIELDS]
        _require(all(math.isfinite(value) for value in floats),
                 "FLOAT64_CONVERSION_OUT_OF_RANGE")
        _require(all(value > 0 for value in floats[:4]) and floats[4] >= 0,
                 "FLOAT64_CONVERSION_OUT_OF_RANGE")
        rows.append([opened, *floats])
        cursor = closed

    _require(cursor == end, "CANDLE_GAP_OR_OVERLAP")
    return rows, {
        "start_ms": start,
        "end_ms": end,
        "as_of_ms": as_of,
        "row_count": len(rows),
        "timeframe": timeframe,
        "source_dataset_version": snapshot["datasetVersion"],
    }


def export_t0_snapshot(snapshot_path, output_root) -> dict:
    """Validate a saved T0 response and write one isolated Freqtrade JSON set."""
    source_path = Path(snapshot_path)
    _require(source_path.is_file() and not source_path.is_symlink(),
             "T0_SNAPSHOT_FILE_UNAVAILABLE")
    try:
        raw = source_path.read_bytes()
        snapshot = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise T0FreqtradeAdapterError("INVALID_T0_SNAPSHOT_FILE") from exc

    rows, metadata = _validate_snapshot(snapshot)
    data_bytes = (
        json.dumps(rows, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")
    output_sha = hashlib.sha256(data_bytes).hexdigest()
    source_sha = hashlib.sha256(raw).hexdigest()
    dataset_id = metadata["source_dataset_version"].split(":", 1)[1][:16]
    dataset_dir = Path(output_root) / (
        f"binance-BTCUSDT-{metadata['timeframe']}-{dataset_id}"
    )
    _require(not dataset_dir.exists() and not dataset_dir.is_symlink(),
             "EXPORT_ALREADY_EXISTS")

    # Freqtrade 2026.9 maps BTC/USDT:USDT to BTC_USDT_USDT and stores
    # non-spot candle types below the futures/ subdirectory.
    filename = f"BTC_USDT_USDT-{metadata['timeframe']}-futures.json"
    relative_filename = f"futures/{filename}"
    manifest = {
        "schema_version": 1,
        "adapter": "T0_TO_FREQTRADE_OFFLINE_V1",
        "source": "T0_CANONICAL_BINANCE_USDT_PERPETUAL",
        "source_exchange": "binance",
        "source_market_type": "USDT_PERPETUAL",
        "source_symbol": "BTCUSDT",
        "freqtrade_pair": "BTC/USDT:USDT",
        "timeframe": metadata["timeframe"],
        "source_dataset_version": metadata["source_dataset_version"],
        "source_payload_sha256": source_sha,
        "freqtrade_data_file": relative_filename,
        "freqtrade_data_sha256": output_sha,
        "row_count": metadata["row_count"],
        "start_ms": metadata["start_ms"],
        "end_ms": metadata["end_ms"],
        "as_of_ms": metadata["as_of_ms"],
        "float64_conversion": True,
        "decimal_strings_preserved_in_source": True,
        "existing_okx_shadow_model_compatible": False,
        "strategy_core_modified": False,
        "native_orders_enabled": False,
        "ai_execution_enabled": False,
        "runtime_integration": False,
    }
    manifest_bytes = (
        json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")

    dataset_dir.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        dataset_dir.mkdir(exist_ok=False)
        created = True
        futures_dir = dataset_dir / "futures"
        futures_dir.mkdir()
        (futures_dir / filename).write_bytes(data_bytes)
        (dataset_dir / "t0-provenance.json").write_bytes(manifest_bytes)
    except OSError as exc:
        if created:
            shutil.rmtree(dataset_dir, ignore_errors=True)
        if isinstance(exc, FileExistsError):
            raise T0FreqtradeAdapterError("EXPORT_ALREADY_EXISTS") from exc
        raise T0FreqtradeAdapterError("EXPORT_WRITE_FAILED") from exc

    return {
        "dataset_dir": str(dataset_dir),
        "data_file": str(dataset_dir / "futures" / filename),
        "manifest_file": str(dataset_dir / "t0-provenance.json"),
        "row_count": metadata["row_count"],
        "source_dataset_version": metadata["source_dataset_version"],
        "data_sha256": output_sha,
        "source_payload_sha256": source_sha,
        "existing_okx_shadow_model_compatible": False,
        "runtime_integration": False,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Export a saved canonical T0 JSON window to an isolated Freqtrade data directory."
    )
    parser.add_argument("--snapshot", required=True, help="Saved T0 /v1/candles JSON response")
    parser.add_argument("--output-root", required=True, help="Parent directory for a new isolated export")
    args = parser.parse_args()
    result = export_t0_snapshot(args.snapshot, args.output_root)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
