"""Per-5m futures equity from actual Freqtrade fills, not mark-price parity."""
import argparse
import csv
import gzip
import json
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def trades_from_zip(path):
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.endswith(".json") and not n.endswith("_config.json")]
        if len(names) != 1:
            raise ValueError("Expected one backtest report JSON")
        strategies = json.loads(z.read(names[0]))["strategy"]
    if len(strategies) != 1:
        raise ValueError("Expected one strategy")
    report = next(iter(strategies.values()))
    return report["trades"], float(report["starting_balance"]), float(report["final_balance"])


def ts_ms(value):
    return int(datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp() * 1000)


def equity_rows(candles, trades, starting_balance, final_balance=None):
    events = defaultdict(list)
    for ident, trade in enumerate(trades):
        for order in trade.get("orders", []):
            timestamp = order.get("order_filled_timestamp")
            if timestamp is None:
                raise ValueError("Missing fill timestamp")
            events[int(timestamp)].append((ident, "order", order, trade))
        end = trade.get("close_timestamp") or ts_ms(trade["close_date"])
        events[int(end)].append((ident, "settle", None, trade))
    times = sorted(events)
    i = 0
    realized = 0.0
    open_trades = {}
    highwater = float(starting_balance)
    last = None
    for candle in candles:
        close_timestamp = int(candle["timestamp_ms"]) + 300000
        close_price = float(candle["close"])
        while i < len(times) and times[i] <= close_timestamp:
            for ident, kind, order, trade in events[times[i]]:
                if kind == "settle":
                    realized += float(trade["profit_abs"])
                    open_trades.pop(ident, None)
                elif order.get("ft_is_entry"):
                    qty = float(order["amount"])
                    fill = float(order["safe_price"])
                    if qty <= 0 or fill <= 0:
                        raise ValueError("Invalid fill amount or price")
                    pos = open_trades.setdefault(ident, {
                        "qty": 0.0, "value": 0.0, "entry_fee": 0.0,
                        "short": bool(trade["is_short"])
                    })
                    pos["qty"] += qty
                    pos["value"] += qty * fill
                    pos["entry_fee"] += qty * fill * float(trade["fee_open"])
            i += 1
        unrealized = sum(
            (pos["value"] - pos["qty"] * close_price if pos["short"]
             else pos["qty"] * close_price - pos["value"]) - pos["entry_fee"]
            for pos in open_trades.values()
        )
        equity = starting_balance + realized + unrealized
        highwater = max(highwater, equity)
        drawdown = highwater - equity
        last = {
            "timestamp_ms": close_timestamp, "close_price": close_price,
            "realized_pnl_usdt": realized, "unrealized_net_usdt": unrealized,
            "equity_usdt": equity, "open_positions": len(open_trades),
            "equity_high_water_usdt": highwater,
            "drawdown_usdt": drawdown,
            "drawdown_pct": drawdown / highwater * 100 if highwater > 0 else None
        }
        yield last
    if last is None or i < len(times) or open_trades:
        raise ValueError("Incomplete candle coverage or open trades at end")
    if final_balance is not None and abs(last["equity_usdt"] - final_balance) > 0.02:
        raise ValueError(f"Final equity mismatch: {last['equity_usdt']} vs {final_balance}")


def run(backtest_zip, ohlcv_gz, output_csv, output_json):
    trades, start, finish = trades_from_zip(backtest_zip)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(ohlcv_gz, "rt", encoding="utf-8", newline="") as source:
        with gzip.open(output_csv, "wt", encoding="utf-8", newline="") as target:
            writer = None
            count = 0
            maximum = {"drawdown_usdt": -1.0}
            maximum_pct = 0.0
            for row in equity_rows(csv.DictReader(source), trades, start, finish):
                if writer is None:
                    writer = csv.DictWriter(target, fieldnames=list(row))
                    writer.writeheader()
                writer.writerow(row)
                count += 1
                if row["drawdown_usdt"] > maximum["drawdown_usdt"]:
                    maximum = row.copy()
                maximum_pct = max(maximum_pct, row["drawdown_pct"] or 0)
    if not count:
        raise ValueError("No equity candles")
    report = {
        "source": "Freqtrade executed fills and OKX futures OHLCV 5m close",
        "candles": count, "starting_balance_usdt": start,
        "final_balance_usdt": finish, "final_balance_reconciled": True,
        "max_drawdown_usdt": maximum["drawdown_usdt"],
        "drawdown_pct_at_max_absolute_drawdown": maximum["drawdown_pct"],
        "max_drawdown_timestamp_ms": maximum["timestamp_ms"],
        "maximum_percentage_drawdown": maximum_pct,
        "includes_unrealized_position_pnl": True,
        "fees_while_open": "entry fee deducted; realized profit_abs includes fees",
        "funding_timing": "recognized on settlement, not original funding timestamp",
        "uses_exchange_mark_price": False,
        "liquidation_replayed": False, "android_parity_verified": False
    }
    output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    p = argparse.ArgumentParser()
    for name in ("result", "ohlcv", "csv", "json"):
        p.add_argument("--" + name, required=True, type=Path)
    a = p.parse_args()
    print(json.dumps(run(a.result, a.ohlcv, a.csv, a.json), indent=2))


if __name__ == "__main__":
    main()
