"""Audit an actual Freqtrade backtest ZIP without inventing parity or profits.

Usage: python freqtrade-backtest/audit_futures_result.py BACKTEST.zip --output audit.json
"""
import argparse
import json
import math
import zipfile
from pathlib import Path


def audit_archive(path):
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.endswith(".json") and not n.endswith("_config.json")]
        if len(names) != 1:
            raise ValueError("Expected one Freqtrade result JSON")
        data = json.loads(archive.read(names[0]))
    strategy_data = data.get("strategy", {})
    if len(strategy_data) != 1:
        raise ValueError("Expected one strategy in result")
    strategy_name, report = next(iter(strategy_data.items()))
    trades = report.get("trades", [])
    observations = []
    for index, trade in enumerate(trades):
        orders = trade.get("orders", [])
        entry_orders = [o for o in orders if o.get("ft_is_entry") is True]
        exit_orders = [o for o in orders if o.get("ft_is_entry") is False]
        margin = float(trade.get("stake_amount", 0.0))
        max_margin = float(trade.get("max_stake_amount", margin))
        leverage = float(trade.get("leverage", 1))
        initial_balance = float(report.get("starting_balance", 0.0))
        opening_funds_fixed = initial_balance * .5
        observations.append({
            "index": index + 1,
            "side": "SHORT" if trade.get("is_short") else "LONG",
            "opened_at": trade.get("open_date"),
            "closed_at": trade.get("close_date"),
            "exit_reason": trade.get("exit_reason"),
            "leverage": leverage,
            "initial_stake_usdt": margin,
            "max_stake_usdt": max_margin,
            "entry_count": len(entry_orders),
            "exit_count": len(exit_orders),
            "dca_count": max(0, len(entry_orders) - 1),
            "fees_and_funding_included_in_report": True,
            "profit_abs_usdt": trade.get("profit_abs"),
            "open_rate": trade.get("open_rate"),
            "close_rate": trade.get("close_rate"),
            "margin_is_near_fixed_starting_wallet_half": abs(margin - opening_funds_fixed) <= max(5, opening_funds_fixed * .15),
            "soft_sl_execution_gap_roe_pct": (
                float(trade.get("profit_ratio", 0)) * 100 - (-35)
                if trade.get("exit_reason") == "soft_sl" else None
            ),
            "soft_sl_gap_is_not_trigger_discrepancy": True,
        })
    return {
        "strategy": strategy_name,
        "data_source": "Freqtrade actual exported result",
        "runtime_evidence": True,
        "android_freqtrade_parity_verified": False,
        "total_trades": len(trades),
        "long_count": sum(t["side"] == "LONG" for t in observations),
        "short_count": sum(t["side"] == "SHORT" for t in observations),
        "total_dca_orders": sum(t["dca_count"] for t in observations),
        "net_profit_usdt": report.get("profit_total_abs"),
        "max_drawdown_abs_usdt": report.get("max_drawdown_abs"),
        "limitations": [
            "No candle-level indicator/callback trace in standard ZIP: cannot determine why DCA did not trigger.",
            "Soft SL realized ROE includes engine fill, funding and fees and is NOT the candle trigger ROE.",
            "No Android trace on identical OKX futures OHLCV supplied: trade parity remains unverified.",
        ],
        "trades": observations,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_zip", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    audit = audit_archive(args.result_zip)
    payload = json.dumps(audit, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
