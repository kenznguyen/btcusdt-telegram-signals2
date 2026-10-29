"""Import observed Binance futures collector CSVs into one bounded snapshot."""

import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import json
import os
from pathlib import Path
import tempfile
import time

from pipeline.values import identity, number, stamp

SOURCE_COMMIT = "bc4f0ef633fbeee4a49defd72827f17162693805"
SOURCE = "binance-futures-collector@" + SOURCE_COMMIT
COMMON = "exchange,market,datatype,timestamp_ms,datetime_utc,symbol"
HEADERS = {
    "trades": COMMON + ",trade_id,side,price,quantity,is_buyer_maker,first_update_id,last_update_id",
    "funding": COMMON + ",funding_rate,next_funding_time",
    "openInterest": COMMON + ",mark_price,open_interest,oi_value",
    "liquidations": COMMON + ",side,price,quantity,value",
}
DATATYPES = {"trades": "trades", "funding": "funding_rates", "openInterest": "open_interest", "liquidations": "liquidations"}
METRICS = {
    "trades": ("takerBuyQuote", "takerSellQuote", "netTakerQuote", "largeTradeQuote"),
    "funding": ("fundingRate",),
    "openInterest": ("openInterestBase", "openInterestChangeBase"),
    "liquidations": ("observedLiquidationBuyQuote", "observedLiquidationSellQuote"),
}
SIGNED = {"fundingRate", "netTakerQuote", "openInterestChangeBase"}
MAX_ROWS, MAX_FILES, MAX_FILE_BYTES = 100_000, 16, 64 * 1024 * 1024
MAX_WINDOW_MS = 86_400_000


def _text(value):
    number(str(value), signed=True)
    return format(value, "f") if value else "0"


def _integer(value):
    if not isinstance(value, str) or not value.isascii() or not value.isdigit() or len(value) > 19:
        raise ValueError("Invalid CSV integer")
    return stamp(int(value))


def _window(start, end, available, now):
    for value in (start, end, available, now):
        stamp(value)
    if not 0 < end - start <= MAX_WINDOW_MS or not end <= available <= now:
        raise ValueError("Window must be closed and observed, with at most one day")


def _read(paths, stream, start, end, available, budget):
    paths = [] if paths is None else [paths] if isinstance(paths, (str, Path)) else list(paths)
    if len(paths) > MAX_FILES:
        raise ValueError("Too many CSV files")
    if len({Path(path).resolve() for path in paths}) != len(paths):
        raise ValueError("A CSV file was supplied more than once")
    selected = []
    for path in paths:
        path = Path(path)
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("CSV file too large")
        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames != HEADERS[stream].split(","):
                raise ValueError("Unexpected collector CSV header")
            for row in reader:
                budget[0] += 1
                if budget[0] > MAX_ROWS or None in row or any(v is None or len(v) > 128 for v in row.values()):
                    raise ValueError("CSV row or row count exceeds limits")
                if (row["exchange"], row["market"], row["symbol"], row["datatype"]) != (
                        "binance", "futures", "btcusdt", DATATYPES[stream]):
                    raise ValueError("Only collector BTCUSDT Binance futures rows are accepted")
                timestamp = _integer(row["timestamp_ms"])
                instant = datetime.fromisoformat(row["datetime_utc"].replace("Z", "+00:00"))
                if instant.utcoffset() is None or instant.utcoffset().total_seconds() != 0 or instant.microsecond % 1000:
                    raise ValueError("CSV datetime must be UTC milliseconds")
                delta = instant - datetime(1970, 1, 1, tzinfo=timezone.utc)
                represented = delta.days * 86_400_000 + delta.seconds * 1000 + delta.microseconds // 1000
                if represented != timestamp or timestamp > available:
                    raise ValueError("CSV timestamps disagree or are in the future")
                if start <= timestamp < end:
                    selected.append((timestamp, row))
    return paths, selected


def _positive(value):
    result = number(value)
    if result <= 0:
        raise ValueError("Expected positive price/quantity")
    return result


def _product_matches(actual, price, quantity):
    # Upstream writes f64-derived values with 12 decimal places, so consistency
    # has a declared tolerance rather than pretending the raw tape is exact.
    expected = price * quantity
    if abs(actual - expected) > max(Decimal("1e-8"), abs(expected) * Decimal("1e-9")):
        raise ValueError("Collector quote value disagrees with price and quantity")


def _summarize(stream, selected, supplied, threshold):
    duplicates, values, seen = 0, [], {}
    for timestamp, row in selected:
        if stream == "trades":
            trade_id = _integer(row["trade_id"])
            first, last = _integer(row["first_update_id"]), _integer(row["last_update_id"])
            side, maker = row["side"], row["is_buyer_maker"]
            if first > last or (side, maker) not in (("buy", "0"), ("sell", "1")):
                raise ValueError("Invalid trade ID range or aggressor side")
            price, quantity = _positive(row["price"]), _positive(row["quantity"])
            value = (timestamp, side, price * quantity, first, last, price, quantity)
            key = trade_id
        elif stream == "funding":
            rate = number(row["funding_rate"], signed=True)
            settlement = _integer(row["next_funding_time"])
            if abs(rate) > 1 or (settlement and settlement < timestamp):
                raise ValueError("Invalid funding rate/settlement")
            key, value = timestamp, (timestamp, rate, settlement)
        elif stream == "openInterest":
            price, interest, quoted = _positive(row["mark_price"]), number(row["open_interest"]), number(row["oi_value"])
            _product_matches(quoted, price, interest)
            key, value = timestamp, (timestamp, interest, price, quoted)
        else:
            side = row["side"]
            price, quantity, quoted = _positive(row["price"]), _positive(row["quantity"]), number(row["value"])
            if side not in {"buy", "sell"}:
                raise ValueError("Invalid forced-order side")
            _product_matches(quoted, price, quantity)
            # No globally unique liquidation ID exists in this schema. Preserve
            # every observed row rather than inventing a deduplication identity.
            values.append((timestamp, side, quoted))
            continue
        if key in seen:
            if seen[key] != value:
                raise ValueError("Conflicting repeated event/sample ID")
            duplicates += 1
        else:
            seen[key] = value
            values.append(value)
    values.sort(key=lambda row: row[0])
    coverage = {"status": "OBSERVED" if values else "NO_ROWS" if supplied else "MISSING",
                "rows": len(values), "duplicateRows": duplicates, "complete": False,
                "firstEventAtMs": values[0][0] if values else None,
                "lastEventAtMs": values[-1][0] if values else None}
    metrics = {key: None for key in METRICS[stream]}
    if stream == "trades":
        ids = sorted(seen)
        coverage["tradeIdGaps"] = sum(max(0, right-left-1) for left, right in zip(ids, ids[1:]))
    if not values:
        return metrics, coverage
    if stream == "trades":
        buy = sum((row[2] for row in values if row[1] == "buy"), Decimal(0))
        sell = sum((row[2] for row in values if row[1] == "sell"), Decimal(0))
        metrics = {"takerBuyQuote": _text(buy), "takerSellQuote": _text(sell), "netTakerQuote": _text(buy-sell),
                   "largeTradeQuote": _text(sum((row[2] for row in values if row[2] >= threshold), Decimal(0)))}
    elif stream == "funding":
        metrics = {"fundingRate": _text(values[-1][1]), "fundingAtMs": values[-1][0]}
    elif stream == "openInterest":
        metrics = {"openInterestBase": _text(values[-1][1]),
                   "openInterestChangeBase": _text(values[-1][1]-values[0][1]) if len(values) >= 2 else None}
    else:
        metrics = {"observedLiquidationBuyQuote": _text(sum((v[2] for v in values if v[1] == "buy"), Decimal(0))),
                   "observedLiquidationSellQuote": _text(sum((v[2] for v in values if v[1] == "sell"), Decimal(0)))}
    return metrics, coverage


def build_snapshot(start_ms, end_ms, available_at_ms, *, trades=None, funding=None,
                   open_interest=None, liquidations=None, large_trade_threshold="1000000"):
    _window(start_ms, end_ms, available_at_ms, available_at_ms)
    threshold = _positive(large_trade_threshold)
    result = {"schemaVersion": 1, "exchange": "binance", "marketType": "USDT_PERPETUAL", "symbol": "BTCUSDT",
              "windowStartMs": start_ms, "windowEndMs": end_ms, "availableAtMs": available_at_ms,
              "source": SOURCE, "quality": "OBSERVED_ONLY", "fundingAtMs": None,
              "largeTradeThresholdQuote": _text(threshold), "coverage": {}}
    paths = {"trades": trades, "funding": funding, "openInterest": open_interest, "liquidations": liquidations}
    budget = [0]
    with localcontext() as context:
        context.prec = 100
        for stream, files in paths.items():
            supplied, selected = _read(files, stream, start_ms, end_ms, available_at_ms, budget)
            metrics, coverage = _summarize(stream, selected, bool(supplied), threshold)
            result.update(metrics)
            result["coverage"][stream] = coverage
    result["snapshotId"] = identity("intelligence:", result)
    return validate_snapshot(result, available_at_ms)


def validate_snapshot(snapshot, now_ms):
    if not isinstance(snapshot, dict) or type(snapshot.get("schemaVersion")) is not int or snapshot["schemaVersion"] != 1:
        raise ValueError("Invalid intelligence schema")
    fixed = {"exchange": "binance", "marketType": "USDT_PERPETUAL", "symbol": "BTCUSDT", "source": SOURCE, "quality": "OBSERVED_ONLY"}
    if any(snapshot.get(k) != v for k, v in fixed.items()):
        raise ValueError("Wrong intelligence market/source/quality")
    if any(field not in snapshot for fields in METRICS.values() for field in fields):
        raise ValueError("Missing intelligence metric fields")
    if "largeTradeThresholdQuote" in snapshot:
        _positive(snapshot["largeTradeThresholdQuote"])
    _window(snapshot.get("windowStartMs"), snapshot.get("windowEndMs"), snapshot.get("availableAtMs"), now_ms)
    coverage = snapshot.get("coverage")
    if not isinstance(coverage, dict) or set(coverage) != set(METRICS):
        raise ValueError("Invalid coverage metadata")
    for stream, fields in METRICS.items():
        item = coverage[stream]
        if not isinstance(item, dict) or not isinstance(item.get("status"), str) or item["status"] not in {"MISSING", "NO_ROWS", "OBSERVED"} or item.get("complete") is not False:
            raise ValueError("Unsupported coverage claim")
        for name in ("rows", "duplicateRows"):
            if type(item.get(name)) is not int or not 0 <= item[name] <= MAX_ROWS:
                raise ValueError("Invalid coverage count")
        observed = item["status"] == "OBSERVED"
        if observed != (item["rows"] > 0):
            raise ValueError("Contradictory coverage")
        if not observed and item["duplicateRows"]:
            raise ValueError("Missing stream cannot contain duplicate rows")
        for key in ("firstEventAtMs", "lastEventAtMs"):
            if observed:
                if not snapshot["windowStartMs"] <= stamp(item.get(key)) < snapshot["windowEndMs"]:
                    raise ValueError("Event lies outside snapshot window")
            elif item.get(key) is not None:
                raise ValueError("Missing stream has event time")
        if observed and item["firstEventAtMs"] > item["lastEventAtMs"]:
            raise ValueError("Reversed event range")
        if item["rows"] == 1 and item["firstEventAtMs"] != item["lastEventAtMs"]:
            raise ValueError("One observed row has multiple event times")
        for field in fields:
            value = snapshot.get(field)
            required = observed and not (field == "openInterestChangeBase" and item["rows"] < 2)
            if not required:
                if value is not None:
                    raise ValueError("Unavailable metric must be null")
            elif not isinstance(value, str):
                raise ValueError("Metric must be a decimal string")
            else:
                number(value, signed=field in SIGNED)
        if stream == "trades":
            if type(item.get("tradeIdGaps")) is not int or not 0 <= item["tradeIdGaps"] < 2**63:
                raise ValueError("Invalid aggregate trade gap count")
            if not observed and item["tradeIdGaps"]:
                raise ValueError("Missing trades cannot contain observed ID gaps")
    funding_at = snapshot.get("fundingAtMs")
    if coverage["funding"]["status"] == "OBSERVED":
        if stamp(funding_at) != coverage["funding"]["lastEventAtMs"] or abs(number(snapshot["fundingRate"], signed=True)) > 1:
            raise ValueError("Inconsistent funding sample")
    elif funding_at is not None:
        raise ValueError("Missing funding sample time")
    if coverage["trades"]["status"] == "OBSERVED":
        with localcontext() as context:
            context.prec = 100
            buy, sell = number(snapshot["takerBuyQuote"]), number(snapshot["takerSellQuote"])
            if buy + sell <= 0 or buy - sell != number(snapshot["netTakerQuote"], signed=True) or number(snapshot["largeTradeQuote"]) > buy + sell:
                raise ValueError("Inconsistent observed trade totals")
    if sum(item["rows"] + item["duplicateRows"] for item in coverage.values()) > MAX_ROWS:
        raise ValueError("Coverage exceeds importer row budget")
    payload = {key: value for key, value in snapshot.items() if key != "snapshotId"}
    if snapshot.get("snapshotId") != identity("intelligence:", payload):
        raise ValueError("Intelligence content hash mismatch")
    return snapshot


def write_snapshot(path, snapshot):
    validate_snapshot(snapshot, time.time_ns() // 1_000_000)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as output:
            temporary = Path(output.name)
            json.dump(snapshot, output, allow_nan=False, sort_keys=True)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-ms", type=int, required=True)
    parser.add_argument("--end-ms", type=int, required=True)
    parser.add_argument("--output", required=True)
    for flag in ("trades", "funding", "open-interest", "liquidations"):
        parser.add_argument("--" + flag, action="append", help="Collector CSV path; repeat across daily files")
    parser.add_argument("--large-trade-threshold", default="1000000", help="USDT quote notional per aggregate trade")
    args = parser.parse_args()
    try:
        snapshot = build_snapshot(args.start_ms, args.end_ms, time.time_ns() // 1_000_000,
            trades=args.trades, funding=args.funding, open_interest=args.open_interest,
            liquidations=args.liquidations, large_trade_threshold=args.large_trade_threshold)
        write_snapshot(args.output, snapshot)
    except (ValueError, TypeError, KeyError, OSError, csv.Error, OverflowError):
        parser.exit(1, "Collector import failed: invalid, missing or unsupported source data.\n")
    print(json.dumps({"snapshotId": snapshot["snapshotId"], "quality": snapshot["quality"], "coverage": snapshot["coverage"]}, allow_nan=False))


if __name__ == "__main__":
    main()
