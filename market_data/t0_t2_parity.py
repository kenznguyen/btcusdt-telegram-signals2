"""Offline Binance USD-M vs OKX OHLCV parity report; no network or database access."""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import struct
import sys


SCHEMA = "T0-T2-BINANCE-OKX-PARITY-MANIFEST-V1"
INTERVALS = {"m15": 900_000, "h1": 3_600_000}
FIELDS = ("open", "high", "low", "close", "volume")
CSV_COLUMNS = {"open_time", *FIELDS, "closed"}
SHA256_PREFIX = "sha256:"
MAX_ROWS_PER_FILE = 1_000_000


class ParityInputError(ValueError):
    """Input data cannot safely be compared."""


def _require(condition, message):
    if not condition:
        raise ParityInputError(message)


def _sha256(data):
    return SHA256_PREFIX + hashlib.sha256(data).hexdigest()


def _valid_digest(value):
    if not isinstance(value, str) or not value.startswith(SHA256_PREFIX):
        return False
    digest = value[len(SHA256_PREFIX):]
    return len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)


def _validate_manifest(manifest):
    _require(isinstance(manifest, dict) and manifest.get("schema") == SCHEMA,
             "Unsupported parity manifest schema")
    window = manifest.get("window")
    _require(isinstance(window, dict), "Missing UTC window")
    start, end = window.get("start_ms"), window.get("end_ms")
    _require(type(start) is int and type(end) is int and 0 <= start < end,
             "Window must contain non-negative integer start_ms < end_ms")
    for timeframe, step in INTERVALS.items():
        _require(start % step == 0 and end % step == 0,
                 f"Window is not aligned to {timeframe}")
        _require((end - start) // step <= MAX_ROWS_PER_FILE,
                 f"{timeframe} window exceeds the row safety limit")

    sources = manifest.get("sources")
    _require(isinstance(sources, dict), "Missing source identities")
    expected = {
        "binance_t0": {
            "exchange": "BINANCE", "market_type": "USD_M_LINEAR_PERPETUAL",
            "instrument": "BTC/USDT:USDT", "symbol": "BTCUSDT",
            "volume_unit": "BTC_BASE_ASSET",
        },
        "okx_t2": {
            "exchange": "OKX", "market_type": "USDT_PERPETUAL_SWAP",
            "instrument": "BTC-USDT-SWAP", "symbol": "BTCUSDT",
            "volume_unit": "BTC_BASE_ASSET_VOLCCY",
            "volume_field_mapping": "history-candles[6]",
        },
    }
    for name, identity in expected.items():
        source = sources.get(name)
        _require(isinstance(source, dict), f"Missing source: {name}")
        for key, value in identity.items():
            _require(source.get(key) == value, f"Invalid {name}.{key}; expected {value}")
        for timeframe in INTERVALS:
            file_key = f"{timeframe}_csv"
            _require(isinstance(source.get(file_key), str) and source[file_key],
                     f"Missing {name}.{file_key}")
    provenance = sources["binance_t0"].get("t0_dataset_version")
    _require(isinstance(provenance, dict), "Missing T0 datasetVersion provenance")
    for timeframe in INTERVALS:
        _require(_valid_digest(provenance.get(timeframe)),
                 f"Invalid T0 datasetVersion for {timeframe}")
    conversion = manifest.get("conversion")
    _require(isinstance(conversion, dict) and
             isinstance(conversion.get("implementation_revision"), str) and
             conversion["implementation_revision"].strip(),
             "Missing conversion implementation_revision")
    return start, end, sources


def _read_source_csv(path, timeframe, start_ms, end_ms):
    source_path = Path(path)
    try:
        raw = source_path.read_bytes()
    except OSError as error:
        raise ParityInputError(f"Cannot read source CSV {source_path}: {error}") from error
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ParityInputError(f"CSV is not UTF-8: {source_path}") from error

    reader = csv.DictReader(io.StringIO(text, newline=""))
    _require(CSV_COLUMNS.issubset(set(reader.fieldnames or [])),
             f"{source_path}: missing required CSV columns")
    rows = []
    try:
        for line_number, row in enumerate(reader, start=2):
            _require(line_number <= MAX_ROWS_PER_FILE + 1,
                     f"{source_path}: row safety limit exceeded")
            _require(str(row.get("closed", "")).strip().casefold() in {"1", "true"},
                     f"{source_path}:{line_number}: candle is not confirmed closed")
            try:
                timestamp = int(row["open_time"])
            except (TypeError, ValueError) as error:
                raise ParityInputError(
                    f"{source_path}:{line_number}: invalid open_time"
                ) from error
            _require(timestamp >= 0 and timestamp % INTERVALS[timeframe] == 0,
                     f"{source_path}:{line_number}: unaligned open_time")
            values = {}
            for field in FIELDS:
                try:
                    value = Decimal(row[field])
                except (InvalidOperation, TypeError, ValueError) as error:
                    raise ParityInputError(
                        f"{source_path}:{line_number}: invalid {field}"
                    ) from error
                _require(value.is_finite(), f"{source_path}:{line_number}: non-finite {field}")
                numeric = float(value)
                _require(math.isfinite(numeric),
                         f"{source_path}:{line_number}: {field} exceeds float64 range")
                values[field] = value
            _require(all(values[field] > 0 for field in ("open", "high", "low", "close")),
                     f"{source_path}:{line_number}: OHLC prices must be positive")
            _require(values["high"] >= max(values["open"], values["low"], values["close"]),
                     f"{source_path}:{line_number}: high is below another OHLC value")
            _require(values["low"] <= min(values["open"], values["high"], values["close"]),
                     f"{source_path}:{line_number}: low is above another OHLC value")
            _require(values["volume"] >= 0,
                     f"{source_path}:{line_number}: volume cannot be negative")
            rows.append({"open_time": timestamp, **values, "closed": True})
    except csv.Error as error:
        raise ParityInputError(f"{source_path}: malformed CSV: {error}") from error

    expected_times = list(range(start_ms, end_ms, INTERVALS[timeframe]))
    actual_times = [row["open_time"] for row in rows]
    _require(actual_times == expected_times,
             f"{source_path}: timestamps must be sorted, unique, gap-free and exactly cover "
             f"[{start_ms},{end_ms}) for {timeframe}")
    return rows, _sha256(raw), source_path


def chartpro_v2_hash(m15, h1):
    """Match T2 freqtrade_parity.dataset_hash canonical binary V2 contract."""
    payload = bytearray(b"CHARTPRO-OHLCV-V2\0")
    for label, candles in ((b"M15", m15), (b"H1", h1)):
        payload.extend(label + b"\0")
        closed_rows = sorted(
            (row for row in candles if row.get("closed") is True),
            key=lambda row: row["open_time"],
        )
        for row in closed_rows:
            values = [float(row[field]) for field in FIELDS]
            _require(all(math.isfinite(value) for value in values),
                     "OHLCV must be finite for CHARTPRO-OHLCV-V2")
            try:
                payload.extend(struct.pack(">q5d", int(row["open_time"]), *values))
            except (OverflowError, struct.error, ValueError) as error:
                raise ParityInputError("OHLCV row cannot be encoded as V2") from error
    return _sha256(bytes(payload))


def _percentile(values, percentile):
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _field_metrics(binance_rows, okx_rows):
    metrics = {}
    for field in FIELDS:
        absolute, relative, exact = [], [], 0
        for left, right in zip(binance_rows, okx_rows):
            a, b = left[field], right[field]
            if a == b:
                exact += 1
            difference = abs(a - b)
            absolute.append(float(difference))
            if b != 0:
                relative.append(float(difference / abs(b)))
        metrics[field] = {
            "exact_match_count": exact,
            "compared_count": len(binance_rows),
            "mean_abs_diff": statistics.fmean(absolute) if absolute else 0.0,
            "median_abs_diff": statistics.median(absolute) if absolute else 0.0,
            "p95_abs_diff": _percentile(absolute, 0.95),
            "max_abs_diff": max(absolute, default=0.0),
            "mean_rel_diff": statistics.fmean(relative) if relative else None,
            "median_rel_diff": statistics.median(relative) if relative else None,
            "p95_rel_diff": _percentile(relative, 0.95),
            "max_rel_diff": max(relative) if relative else None,
            "relative_diff_denominator": "OKX" if relative else None,
        }
    return metrics


def _largest_differences(binance_rows, okx_rows, limit=5):
    """Return deterministic top absolute-difference rows for each OHLCV field."""
    result = {}
    for field in FIELDS:
        differences = []
        for left, right in zip(binance_rows, okx_rows):
            a, b = left[field], right[field]
            absolute = abs(a - b)
            relative = (absolute / abs(b)) if b != 0 else None
            differences.append({
                "open_time": left["open_time"],
                "binance_value": str(a),
                "okx_value": str(b),
                "abs_diff": float(absolute),
                "rel_diff": float(relative) if relative is not None else None,
            })
        differences.sort(key=lambda item: (-item["abs_diff"], item["open_time"]))
        result[field] = differences[:limit]
    return result



def build_report(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ParityInputError(f"Cannot load manifest: {error}") from error
    start, end, sources = _validate_manifest(manifest)
    loaded = {}
    source_reports = {}
    for source_name, source in sources.items():
        loaded[source_name] = {}
        file_reports = {}
        for timeframe in INTERVALS:
            csv_path = (manifest_path.parent / source[f"{timeframe}_csv"]).resolve()
            rows, digest, resolved_path = _read_source_csv(csv_path, timeframe, start, end)
            loaded[source_name][timeframe] = rows
            file_reports[timeframe] = {
                "path": str(resolved_path),
                "sha256": digest,
                "row_count": len(rows),
                "first_open_ms": rows[0]["open_time"],
                "last_open_ms": rows[-1]["open_time"],
                "coverage_complete": True,
            }
        combined_hash = chartpro_v2_hash(
            loaded[source_name]["m15"], loaded[source_name]["h1"]
        )
        source_reports[source_name] = {
            "exchange": source["exchange"],
            "market_type": source["market_type"],
            "instrument": source["instrument"],
            "symbol": source["symbol"],
            "volume_unit": source["volume_unit"],
            "files": file_reports,
            "chartpro_ohlcv_v2_sha256": combined_hash,
        }
        if source_name == "binance_t0":
            source_reports[source_name]["t0_dataset_version"] = dict(
                source["t0_dataset_version"]
            )

    metrics = {}
    largest_differences = {}
    for timeframe in INTERVALS:
        binance_rows = loaded["binance_t0"][timeframe]
        okx_rows = loaded["okx_t2"][timeframe]
        metrics[timeframe] = _field_metrics(binance_rows, okx_rows)
        largest_differences[timeframe] = _largest_differences(binance_rows, okx_rows)
    return {
        "schema": SCHEMA,
        "status": "COMPARABLE",
        "pair_id": manifest.get("pair_id"),
        "window": {"start_ms": start, "end_ms": end, "timezone": "UTC",
                   "semantics": "[start_ms,end_ms)"},
        "coverage": {
            timeframe: {
                "expected_rows": (end - start) // step,
                "rows_per_source": len(loaded["binance_t0"][timeframe]),
                "missing_timestamps": [],
                "extra_timestamps": [],
                "complete_for_both_sources": True,
            }
            for timeframe, step in INTERVALS.items()
        },
        "sources": source_reports,
        "conversion": {
            "ohlcv_numeric_format": "IEEE754_BINARY64",
            "byte_order": "BIG_ENDIAN",
            "timestamp_format": "SIGNED_INT64_UTC_MILLISECONDS",
            "source_decimal_strings_preserved": True,
            "implementation_revision": manifest["conversion"]["implementation_revision"],
        },
        "metrics": metrics,
        "largest_differences": largest_differences,
        "interpretation": (
            "Differences describe distinct exchange market data and contract feeds; "
            "they do not by themselves indicate corruption. OHLCV equality is not required."
        ),
    }


def render_markdown(report):
    lines = [
        "# Binance–OKX OHLCV Parity Report",
        "",
        f"- Status: **{report['status']}**",
        f"- Pair: {report.get('pair_id') or 'unspecified'}",
        f"- UTC window: [{report['window']['start_ms']}, {report['window']['end_ms']})",
        "",
        "## Sources and hashes",
        "",
        "| Source | Instrument | M15 rows | H1 rows | V2 SHA-256 |",
        "|---|---|---:|---:|---|",
    ]
    for name, source in report["sources"].items():
        files = source["files"]
        lines.append(
            f"| {name} | {source['instrument']} | {files['m15']['row_count']} | "
            f"{files['h1']['row_count']} | {source['chartpro_ohlcv_v2_sha256']} |"
        )
    lines.extend(["", "## Per-field differences", ""])
    for timeframe, fields in report["metrics"].items():
        lines.extend([
            f"### {timeframe.upper()}",
            "",
            "| Field | Exact | Mean abs | P95 abs | Max abs | Max relative |",
            "|---|---:|---:|---:|---:|---:|",
        ])
        for field, values in fields.items():
            relative = values["max_rel_diff"]
            relative_text = "n/a" if relative is None else f"{relative:.12g}"
            lines.append(
                f"| {field} | {values['exact_match_count']}/{values['compared_count']} | "
                f"{values['mean_abs_diff']:.12g} | {values['p95_abs_diff']:.12g} | "
                f"{values['max_abs_diff']:.12g} | {relative_text} |"
            )
        lines.append("")
    lines.extend(["## Largest difference rows", ""])
    for timeframe, fields in report["largest_differences"].items():
        lines.extend([
            f"### {timeframe.upper()}",
            "",
            "| Field | Open time (UTC ms) | Binance | OKX | Abs diff | Relative diff (OKX base) |",
            "|---|---:|---:|---:|---:|---:|",
        ])
        for field, rows in fields.items():
            for item in rows:
                relative = item["rel_diff"]
                relative_text = "n/a" if relative is None else f"{relative:.12g}"
                lines.append(
                    f"| {field} | {item['open_time']} | {item['binance_value']} | "
                    f"{item['okx_value']} | {item['abs_diff']:.12g} | {relative_text} |"
                )
        lines.append("")
    lines.extend(["## Interpretation", "", report["interpretation"], ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Path to an operator-supplied JSON manifest")
    parser.add_argument("--json-output", required=True, help="Output JSON report path")
    parser.add_argument("--markdown-output", required=True, help="Output Markdown report path")
    args = parser.parse_args(argv)
    try:
        report = build_report(args.manifest)
        json_path = Path(args.json_output)
        markdown_path = Path(args.markdown_output)
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        markdown_path.write_text(render_markdown(report), encoding="utf-8")
    except (ParityInputError, OSError) as error:
        print(f"NOT_COMPARABLE: {error}", file=sys.stderr)
        return 2
    print(f"PARITY_REPORT={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
