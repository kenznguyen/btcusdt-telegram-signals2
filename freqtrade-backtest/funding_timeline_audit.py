"""Estimate historical funding cashflows from Freqtrade mark and funding observations.

This is an independent audit, not a replay of exact OKX settlement times.
"""
import argparse
import json
from pathlib import Path

from market_risk_audit import exported_trades


def funding_ledger(trades, funding, marks):
    marks = sorted(marks, key=lambda x: x["timestamp_ms"])
    funding = sorted(funding, key=lambda x: x["timestamp_ms"])
    events = []
    totals = []
    for i, trade in enumerate(trades, 1):
        start, end = int(trade["open_timestamp"]), int(trade["close_timestamp"])
        entries = [o for o in trade["orders"] if o.get("ft_is_entry") is True]
        estimated = 0.0
        for observation in funding:
            t = int(observation["timestamp_ms"])
            if not start < t < end:
                continue
            prior_mark = [p for p in marks if p["timestamp_ms"] <= t]
            if not prior_mark:
                continue
            mark = float(prior_mark[-1]["price"])
            amount = sum(float(o["amount"]) for o in entries
                         if int(o["order_filled_timestamp"]) < t)
            if amount <= 0:
                continue
            cashflow = (1 if trade["is_short"] else -1) * amount * mark * float(observation["rate"])
            estimated += cashflow
            events.append({
                "trade_index": i, "timestamp_ms": t,
                "side": "SHORT" if trade["is_short"] else "LONG",
                "active_qty": amount, "mark_reference": mark,
                "rate": float(observation["rate"]),
                "estimated_cashflow_usdt": cashflow
            })
        reported = float(trade.get("funding_fees") or 0)
        totals.append({"trade_index": i, "freqtrade_total_usdt": reported,
                       "estimated_total_usdt": estimated,
                       "difference_usdt": estimated - reported})
    return {
        "events": events, "per_trade": totals,
        "total_freqtrade_usdt": sum(x["freqtrade_total_usdt"] for x in totals),
        "total_estimated_usdt": sum(x["estimated_total_usdt"] for x in totals),
        "funding_settlement_timestamps_verified": False,
        "mark_settlement_price_verified": False,
        "interpretation": "Approximate snapshot ledger; do not overwrite Freqtrade actual PnL"
    }


def load_bars(path, value_name):
    import pandas as pd
    f = pd.read_feather(path)
    if f.empty or "date" not in f or "open" not in f:
        raise ValueError("Incomplete funding/mark OHLCV")
    times = pd.to_datetime(f["date"], utc=True)
    if times.duplicated().any() or not times.is_monotonic_increasing:
        raise ValueError("Invalid UTC observations")
    return [{"timestamp_ms": int(t.timestamp() * 1000), value_name: float(v)}
            for t, v in zip(times, f["open"])]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--result", required=True, type=Path)
    p.add_argument("--datadir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    sources = {}
    for kind, value in (("funding_rate", "rate"), ("mark", "price")):
        files = list(args.datadir.rglob("BTC_USDT_USDT-*-" + kind + ".feather"))
        if len(files) != 1:
            raise ValueError("Missing/ambiguous historical " + kind)
        sources[kind] = load_bars(files[0], value)
    report = funding_ledger(exported_trades(args.result), sources["funding_rate"], sources["mark"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Approximate funding observations:", len(report["events"]))


if __name__ == "__main__":
    main()
