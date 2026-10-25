"""Offline Freqtrade summary exporter. Does not certify StrategyEngine parity."""
import argparse
import json
from pathlib import Path
from validate_report import validate_report


def convert(payload, *, symbol, days, commit):
    strategies = payload.get("strategy") if isinstance(payload, dict) else None
    if not isinstance(strategies, dict) or len(strategies) != 1:
        raise ValueError("Expected exactly one Freqtrade strategy summary")
    summary = next(iter(strategies.values()))
    if not isinstance(summary, dict):
        raise ValueError("Invalid strategy summary")

    def number(key):
        value = summary.get(key)
        return value if type(value) in (int, float) else None

    winrate = number("winrate")
    drawdown = number("max_drawdown_account")
    report = {
        "schema_version": "1.0", "engine": "freqtrade",
        "symbol": symbol, "timeframe": "15m", "period_days": days,
        "strategy_commit": commit, "verified": False,
        "metrics": {
            "net_profit_usdt": number("profit_total_abs"),
            "win_rate_pct": winrate * 100 if winrate is not None else None,
            "profit_factor": number("profit_factor"),
            "max_drawdown_pct": drawdown * 100 if drawdown is not None else None,
            "total_fees_usdt": None,
        },
        "trades": [],
    }
    return validate_report(report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--days", type=int, choices=(90, 180, 360), required=True)
    parser.add_argument("--symbol", default="BTC/USDT:USDT")
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    raw = json.loads(args.source.read_text(encoding="utf-8"))
    result = convert(raw, symbol=args.symbol, days=args.days, commit=args.commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
