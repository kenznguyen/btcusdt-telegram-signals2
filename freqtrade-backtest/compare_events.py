"""Compare Android and Freqtrade replay event traces. No network or trading."""
import argparse
import json
import math
from pathlib import Path

FIELDS = ("timestamp_ms", "symbol", "kind", "side", "price", "quantity", "avg_entry", "margin", "roe_pct")
NUMERIC = {"price", "quantity", "avg_entry", "margin", "roe_pct"}


def validate_event(event):
    if not isinstance(event, dict) or any(key not in event for key in FIELDS):
        raise ValueError("Incomplete event trace")
    if type(event["timestamp_ms"]) is not int or event["timestamp_ms"] < 0:
        raise ValueError("Invalid timestamp")
    if event["kind"] not in {"ENTRY", "DCA", "TP", "SOFT_SL", "EMERGENCY_SL"}:
        raise ValueError("Invalid event kind")
    if event["side"] not in {"LONG", "SHORT"}:
        raise ValueError("Invalid side")
    if not isinstance(event["symbol"], str) or not event["symbol"]:
        raise ValueError("Invalid symbol")
    for key in NUMERIC:
        value = event[key]
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("Invalid numeric field: " + key)
    return event


def compare(android_events, freqtrade_events, *, abs_tolerance=1e-8):
    if abs_tolerance < 0 or not math.isfinite(abs_tolerance):
        raise ValueError("Invalid tolerance")
    for trace in (android_events, freqtrade_events):
        if not isinstance(trace, list):
            raise ValueError("Expected event list")
        for event in trace:
            validate_event(event)
        if any(trace[i]["timestamp_ms"] > trace[i+1]["timestamp_ms"] for i in range(len(trace)-1)):
            raise ValueError("Trace not ordered")
    mismatches = []
    for index in range(max(len(android_events), len(freqtrade_events))):
        if index >= len(android_events) or index >= len(freqtrade_events):
            mismatches.append({"index": index, "field": "event_count"})
            continue
        left, right = android_events[index], freqtrade_events[index]
        for key in FIELDS:
            same = (math.isclose(left[key], right[key], rel_tol=0, abs_tol=abs_tolerance)
                    if key in NUMERIC else left[key] == right[key])
            if not same:
                mismatches.append({"index": index, "field": key, "android": left[key], "freqtrade": right[key]})
    return {"passed": not mismatches, "android_events": len(android_events),
            "freqtrade_events": len(freqtrade_events), "mismatches": mismatches}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("android_trace", type=Path)
    parser.add_argument("freqtrade_trace", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = compare(json.loads(args.android_trace.read_text(encoding="utf-8")),
                     json.loads(args.freqtrade_trace.read_text(encoding="utf-8")))
    serialized = json.dumps(report, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
