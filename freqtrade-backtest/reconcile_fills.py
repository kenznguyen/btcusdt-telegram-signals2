"""Match actual Freqtrade exit fills to trace estimates without assuming parity."""
import argparse
import csv
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def load_trades(result_zip):
    with zipfile.ZipFile(result_zip) as z:
        names = [n for n in z.namelist() if n.endswith(".json") and not n.endswith("_config.json")]
        if len(names) != 1:
            raise ValueError("Expected exactly one Freqtrade backtest result JSON")
        report = json.loads(z.read(names[0]))["strategy"]
        if len(report) != 1:
            raise ValueError("Exactly one strategy required")
        return next(iter(report.values()))["trades"]


def read_exit_trace(path):
    if not path or not path.exists():
        return []
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def as_epoch_ms(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    return int(datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp() * 1000)


def reconcile(trades, events):
    rows = []
    used = set()
    for index, trade in enumerate(trades, 1):
        reason = str(trade.get("exit_reason", "")).lower()
        end = trade.get("close_timestamp") or as_epoch_ms(trade.get("close_date"))
        start = trade.get("open_timestamp") or as_epoch_ms(trade.get("open_date"))
        side = "SHORT" if trade.get("is_short") else "LONG"
        candidates = []
        for j, event in enumerate(events):
            when = as_epoch_ms(event.get("callback_time"))
            if (j not in used and when is not None and end is not None
                and start is not None and start <= when <= end
                and event.get("pair") == trade.get("pair")
                and event.get("side") == side
                and str(event.get("reason", "")).lower() == reason):
                candidates.append((when, j, event))
        matched = max(candidates, key=lambda v: v[0]) if candidates else None
        if matched is not None:
            used.add(matched[1])
        event = matched[2] if matched else {}
        expected = event.get("android_expected_stop_fill")
        actual = trade.get("close_rate")
        diff = float(actual) - float(expected) if expected is not None and actual is not None else None
        rows.append({
            "trade_index": index,
            "pair": trade.get("pair"),
            "side": side,
            "entry_time": trade.get("open_date"),
            "exit_time": trade.get("close_date"),
            "exit_reason": trade.get("exit_reason"),
            "expected_fill_price": expected,
            "actual_fill_price": actual,
            "fill_difference": diff,
            "fill_difference_pct": (diff / float(expected) * 100 if diff is not None and float(expected) else None),
            "trace_match": matched is not None,
            "expected_price_basis": "Android stop_fill_price from closed M15 candle; not order execution guarantee" if expected is not None else "unavailable",
            "entry_count": sum(bool(o.get("ft_is_entry")) for o in trade.get("orders", [])),
            "pnl_usdt": trade.get("profit_abs"),
        })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--exit-trace", type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--json", required=True, type=Path)
    args = parser.parse_args()
    rows = reconcile(load_trades(args.result), read_exit_trace(args.exit_trace))
    for path in (args.csv, args.json):
        path.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as stream:
        fieldnames = list(rows[0]) if rows else [
            "trade_index", "pair", "side", "exit_reason", "expected_fill_price",
            "actual_fill_price", "fill_difference", "trace_match"
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    args.json.write_text(json.dumps({
        "rows": rows,
        "trades": len(rows),
        "matched_expected_prices": sum(r["expected_fill_price"] is not None for r in rows),
        "unmatched_or_unpriced": sum(r["expected_fill_price"] is None for r in rows),
        "parity_verified": False,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
