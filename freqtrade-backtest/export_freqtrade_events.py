"""Export actual Freqtrade fills in a minimal schema for Kotlin parity comparison."""
import argparse
import json
from pathlib import Path
from market_risk_audit import exported_trades


def export_events(trades):
    events = []
    for trade in trades:
        side = "SHORT" if trade["is_short"] else "LONG"
        entered = 0
        for order in sorted(trade.get("orders", []), key=lambda o: o["order_filled_timestamp"]):
            if order.get("ft_is_entry"):
                event_type = "ENTRY" if entered == 0 else "DCA"
                entered += 1
            else:
                reason = str(trade.get("exit_reason", "")).lower()
                event_type = {
                    "tp": "TP", "soft_sl": "SOFT_SL",
                    "stop_loss": "EMERGENCY_SL",
                    "trailing_stop_loss": "EMERGENCY_SL",
                    "liquidation": "LIQUIDATION"
                }.get(reason, "OTHER_EXIT")
            events.append({
                "timestamp_ms": int(order["order_filled_timestamp"]),
                "side": side, "type": event_type,
                "price": float(order["safe_price"]),
                "quantity": float(order["amount"]),
                "source": "actual_freqtrade_export"
            })
    return sorted(events, key=lambda x: (x["timestamp_ms"], x["side"], x["type"]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--result", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    events = export_events(exported_trades(args.result))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(events)} Freqtrade fills for Android comparison")


if __name__ == "__main__":
    main()
