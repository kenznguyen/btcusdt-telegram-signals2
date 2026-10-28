"""Five-minute Freqtrade Futures equity with explicit funding-timing limitations."""
import argparse
import csv
import gzip
import json
import math
import zipfile
from pathlib import Path


def read_report(path):
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist()
                 if name.endswith(".json") and not name.endswith("_config.json")]
        if len(names) != 1:
            raise ValueError("One Freqtrade backtest JSON required")
        strategies = json.loads(archive.read(names[0]))["strategy"]
        if len(strategies) != 1:
            raise ValueError("One strategy required")
        return next(iter(strategies.values()))


def read_candles(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", newline="") as handle:
        candles = list(csv.DictReader(handle))
    if not candles:
        raise ValueError("Empty 5m history")
    previous = None
    for bar in candles:
        timestamp = int(bar["timestamp_ms"])
        if previous is not None and timestamp - previous != 300_000:
            raise ValueError("Missing, unordered or duplicate 5m candles")
        previous = timestamp
        bar["timestamp_ms"] = timestamp
        for field in ("open", "high", "low", "close"):
            bar[field] = float(bar[field])
    return candles


def compute_equity(report, candles):
    """Reconcile close-equity with realized Freqtrade PnL and each fill.

    Funding is available as a per-trade aggregate only: record its effect
    at closing, never fabricate intratrade timestamps or mark-price equity.
    """
    events = []
    for index, trade in enumerate(report["trades"]):
        for order in trade.get("orders", []):
            when = order.get("order_filled_timestamp")
            if when is None:
                raise ValueError("Missing order timestamp")
            events.append((int(when), 0 if order["ft_is_entry"] else 1,
                           index, trade, order))
    events.sort(key=lambda e: (e[0], e[1]))
    cash = float(report["starting_balance"])
    position = {}
    history = []
    index = 0
    peak = cash
    max_drawdown = max_relative = 0.0
    fee_total = funding_total = correction_total = 0.0
    for bar in candles:
        timestamp = bar["timestamp_ms"]
        while index < len(events) and events[index][0] <= timestamp:
            _, _, trade_id, trade, order = events[index]
            index += 1
            amount = float(order["amount"])
            price = float(order["safe_price"])
            if amount <= 0 or price <= 0:
                raise ValueError("Invalid filled order")
            if order["ft_is_entry"]:
                state = position.setdefault(trade_id, {
                    "amount": 0.0, "cost": 0.0, "fees": 0.0,
                    "direction": -1 if trade["is_short"] else 1})
                state["amount"] += amount
                state["cost"] += amount * price
                fee = amount * price * float(trade["fee_open"])
                state["fees"] += fee
                cash -= fee
                fee_total += fee
            else:
                state = position.get(trade_id)
                if state is None or abs(state["amount"] - amount) > max(1e-6, amount * 1e-5):
                    raise ValueError("Partial exit or missing position; refusing estimate")
                gross = state["direction"] * (amount * price - state["cost"])
                fee = amount * price * float(trade["fee_close"])
                fee_total += fee
                # This correction equals the funding effect and precision
                # adjustments needed to reproduce realized Freqtrade PnL.
                adjustment = float(trade["profit_abs"]) - (gross - state["fees"] - fee)
                correction_total += adjustment
                funding_total += float(trade.get("funding_fees") or 0.0)
                cash += gross - fee + adjustment
                del position[trade_id]
        floating = sum(
            state["direction"] * (state["amount"] * bar["close"] - state["cost"])
            for state in position.values())
        equity = cash + floating
        if not math.isfinite(equity):
            raise ValueError("Non-finite equity")
        peak = max(peak, equity)
        drawdown = peak - equity
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            max_relative = drawdown / peak if peak else 0.0
        history.append({
            "timestamp_ms": timestamp, "close": bar["close"],
            "realized_cash_balance": cash, "floating_pnl": floating,
            "equity_close_5m": equity, "open_positions": len(position),
            "drawdown_from_peak": drawdown,
            "drawdown_pct": drawdown / peak * 100 if peak else 0.0,
            "cumulative_entry_exit_fees": fee_total,
            "trade_funding_recorded_at_exit": funding_total})
    if position or index != len(events):
        raise ValueError("Trade open past final candle or unprocessed fills")
    difference = history[-1]["equity_close_5m"] - float(report["final_balance"])
    if abs(difference) > max(0.05, abs(report["final_balance"]) * 0.0001):
        raise ValueError(f"Final Freqtrade equity mismatch: {difference:.8f}")
    summary = {
        "candles": len(history), "trades": len(report["trades"]),
        "equity_final": history[-1]["equity_close_5m"],
        "reported_final_balance": float(report["final_balance"]),
        "reconciliation_difference": difference,
        "max_drawdown_close_5m_usdt": max_drawdown,
        "max_drawdown_close_5m_pct": max_relative * 100,
        "estimated_entry_exit_fees": fee_total,
        "total_reported_funding": funding_total,
        "funding_and_rounding_settled_at_trade_exit": correction_total,
        "mark_price_used": False, "exact_funding_times_known": False,
        "liquidation_replayed": False, "android_parity_verified": False,
        "scope": "5m candle close equity including realized/unrealized PnL, DCA, fill fees and aggregate funding at exit"}
    return history, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--candles", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    rows, summary = compute_equity(read_report(args.result), read_candles(args.candles))
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    args.json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
