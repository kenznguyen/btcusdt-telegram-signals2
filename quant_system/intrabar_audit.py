"""Phase 3 independent OHLCV consistency and 1m/5m fill diagnostics.

This is NOT an independently attested Freqtrade/Kotlin backtest or proof of
live fills. It rejects missing, gapped, mismatched or fabricated market data,
records observed stop touches and preserves unknown actual fills as null.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from freqtrade_parity.dataset_io import generate_manifest, read_closed_csv
from freqtrade_parity.rules import StrategyRules

M15_MS = 900_000
H1_MS = 3_600_000
DAY_MS = 86_400_000
ALLOWED_KINDS = {
    "LONG ENTRY", "SHORT ENTRY", "DCA", "TAKE PROFIT", "SOFT SL", "EMERGENCY SL",
}


def _check_ohlc(row):
    if not (
        row["open"] > 0 and row["high"] > 0 and row["low"] > 0
        and row["close"] > 0 and row["volume"] >= 0
        and row["low"] <= min(row["open"], row["close"])
        and row["high"] >= max(row["open"], row["close"])
    ):
        raise ValueError("INVALID_OHLCV_RANGE")


def _matches(a, b):
    return math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-10)


def _aggregate(rows):
    return {
        "open": rows[0]["open"], "high": max(row["high"] for row in rows),
        "low": min(row["low"] for row in rows), "close": rows[-1]["close"],
        "volume": math.fsum(row["volume"] for row in rows),
    }


def _check_aggregate(parent, children):
    summary = _aggregate(children)
    for name in ("open", "high", "low", "close"):
        if not _matches(parent[name], summary[name]):
            raise ValueError("INTRABAR_OHLC_MISMATCH")
    if not math.isclose(
        parent["volume"], summary["volume"],
        rel_tol=1e-6, abs_tol=1e-8,
    ):
        raise ValueError("INTRABAR_VOLUME_MISMATCH")


def _details(events, detail_by_candle, step_ms):
    if events is None:
        events = []
    if not isinstance(events, list):
        raise ValueError("INVALID_EVENT_TRACE")
    results = []
    rules = StrategyRules()
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("INVALID_EVENT_TRACE")
        kind, side, opened = event.get("kind"), event.get("side"), event.get("candleTime")
        if kind not in ALLOWED_KINDS or side not in ("LONG", "SHORT") or type(opened) is not int:
            raise ValueError("INVALID_EVENT_TRACE")
        if opened not in detail_by_candle:
            raise ValueError("EVENT_OUTSIDE_TEST_WINDOW")
        reported_actual = event.get("actual_fill_price")
        if reported_actual is not None:
            if isinstance(reported_actual, bool) or not math.isfinite(float(reported_actual)) or float(reported_actual) <= 0:
                raise ValueError("INVALID_ACTUAL_FILL")
        result = {
            "event_kind": kind, "side": side, "candleTime": opened,
            "confirmed_at_ms": event.get("confirmed_at_ms"),
            "first_touch_open_ms": None, "touch_window_ms": None,
            "expected_fill_price": None,
            "actual_fill_price": float(reported_actual) if reported_actual is not None else None,
            "fill_difference": None,
            "fill_verified": False,
        }
        if kind in ("SOFT SL", "TAKE PROFIT"):
            if event.get("confirmed_at_ms") != opened + M15_MS:
                raise ValueError("EXIT_CANDLE_CONFIRMATION_MISMATCH")
        if kind == "EMERGENCY SL":
            average, stop = float(event["avg_entry"]), float(event["stop_price"])
            if not math.isfinite(average) or average <= 0 or not math.isfinite(stop) or stop <= 0:
                raise ValueError("INVALID_STOP_PRICE")
            expected_stop = rules.threshold_price(side, average, abs(rules.p.emergency_sl_roe))
            if not _matches(stop, expected_stop):
                raise ValueError("EMERGENCY_THRESHOLD_CHANGED")
            for bar in detail_by_candle[opened]:
                touched = bar["low"] <= stop if side == "LONG" else bar["high"] >= stop
                if touched:
                    reference = min(bar["open"], stop) if side == "LONG" else max(bar["open"], stop)
                    expected = rules.execution_fill(reference, "SELL" if side == "LONG" else "BUY")
                    result["first_touch_open_ms"] = bar["open_time"]
                    result["touch_window_ms"] = step_ms
                    result["expected_fill_price"] = expected
                    if reported_actual is not None:
                        result["fill_difference"] = float(reported_actual) - expected
                    break
            if result["first_touch_open_ms"] is None:
                raise ValueError("EMERGENCY_STOP_NOT_OBSERVED")
        results.append(result)
    return results


def audit_history(m15_path, h1_path, detail_path, *, days, detail_minutes,
                  events=None):
    """Offline data quality gate. A valid data report still has parity_verified=False."""
    if type(days) is not int or days not in (1, 180, 360):
        raise ValueError("INVALID_AUDIT_PERIOD")
    if type(detail_minutes) is not int or detail_minutes not in (1, 5):
        raise ValueError("INVALID_DETAIL_TIMEFRAME")
    step = detail_minutes * 60_000
    primary = read_closed_csv(m15_path, M15_MS)
    hourly = read_closed_csv(h1_path, H1_MS)
    fine = read_closed_csv(detail_path, step)
    for row in (*primary, *hourly, *fine):
        _check_ohlc(row)
    end = primary[-1]["open_time"] + M15_MS
    start = end - days * DAY_MS
    if start < 0 or start % H1_MS:
        raise ValueError("UNALIGNED_AUDIT_PERIOD")
    primary = [row for row in primary if start <= row["open_time"] < end]
    hourly = [row for row in hourly if start <= row["open_time"] < end]
    fine = [row for row in fine if start <= row["open_time"] < end]
    expected_primary = days * 96
    expected_hours = days * 24
    expected_fine = days * DAY_MS // step
    if (len(primary), len(hourly), len(fine)) != (
        expected_primary, expected_hours, expected_fine
    ):
        raise ValueError("HISTORY_INCOMPLETE")
    if (primary[0]["open_time"], hourly[0]["open_time"], fine[0]["open_time"]) != (start, start, start):
        raise ValueError("HISTORY_MISALIGNED")
    if (primary[-1]["open_time"] + M15_MS, hourly[-1]["open_time"] + H1_MS,
        fine[-1]["open_time"] + step) != (end, end, end):
        raise ValueError("HISTORY_END_MISMATCH")

    for index, row in enumerate(primary):
        begin = index * (M15_MS // step)
        children = fine[begin:begin + M15_MS // step]
        if len(children) != M15_MS // step or children[0]["open_time"] != row["open_time"]:
            raise ValueError("INTRABAR_MISSING_BAR")
        _check_aggregate(row, children)
    for index, hour in enumerate(hourly):
        children = primary[4 * index:4 * index + 4]
        if len(children) != 4 or children[0]["open_time"] != hour["open_time"]:
            raise ValueError("H1_M15_GAP")
        _check_aggregate(hour, children)

    detail_by_candle = {
        row["open_time"]: fine[index * (M15_MS // step):(index + 1) * (M15_MS // step)]
        for index, row in enumerate(primary)
    }
    diagnostics = _details(events, detail_by_candle, step)
    source_manifest = generate_manifest(m15_path, h1_path)
    detail_hash = "sha256:" + hashlib.sha256(Path(detail_path).read_bytes()).hexdigest()
    counts = {kind: sum(f["event_kind"] == kind for f in diagnostics) for kind in sorted(ALLOWED_KINDS)}
    return {
        "schemaVersion": 1, "days": days, "detail_timeframe": f"{detail_minutes}m",
        "start_ms": start, "end_ms": end,
        "m15_count": len(primary), "h1_count": len(hourly),
        "detail_count": len(fine), "dataset_sha256": source_manifest["dataset_sha256"],
        "detail_sha256": detail_hash, "ohlcv_verified": True,
        "event_counts": counts, "event_diagnostics": diagnostics,
        "source_attested": False, "native_runtime_verified": False,
        "kotlin_trace_verified": False, "freqai_oos_verified": False,
        "parity_verified": False, "full_core_parity_certified": False,
        "reason": "DATA_ONLY_NOT_RUNTIME_PARITY",
    }


def main():
    parser = argparse.ArgumentParser(description="Strict offline market-data audit, not trade certification")
    parser.add_argument("--m15", required=True)
    parser.add_argument("--h1", required=True)
    parser.add_argument("--detail", required=True)
    parser.add_argument("--detail-minutes", type=int, choices=(1, 5), required=True)
    parser.add_argument("--days", type=int, choices=(180, 360), required=True)
    parser.add_argument("--events", help="Optional independently produced exit event JSON array")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    try:
        events = json.loads(Path(args.events).read_text(encoding="utf-8")) if args.events else None
        report = audit_history(
            args.m15, args.h1, args.detail,
            days=args.days, detail_minutes=args.detail_minutes, events=events,
        )
        ok = report["ohlcv_verified"]
    except (ValueError, OSError, TypeError, KeyError, OverflowError, IndexError) as error:
        report = {
            "ohlcv_verified": False, "parity_verified": False,
            "full_core_parity_certified": False,
            "reason": type(error).__name__ + ":" + str(error)[:128],
        }
        ok = False
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("ohlcv_verified", "parity_verified", "reason")}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
