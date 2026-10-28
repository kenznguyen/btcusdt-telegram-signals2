"""Audit Freqtrade liquidation fills and independent mark/funding data presence.

No change to StrategyEngine. Raw funding candles are observations, not proof
of per-position settlement cashflows or liquidation maintenance margin.
"""
import argparse
import json
import zipfile
from pathlib import Path


def exported_trades(result_zip):
    with zipfile.ZipFile(result_zip) as z:
        names = [n for n in z.namelist() if n.endswith(".json") and not n.endswith("_config.json")]
        if len(names) != 1:
            raise ValueError("Expected one trade JSON")
        reports = json.loads(z.read(names[0]))["strategy"]
    if len(reports) != 1:
        raise ValueError("Expected one strategy")
    return next(iter(reports.values()))["trades"]


def audit_liquidations(trades):
    records = []
    for trade in trades:
        if trade.get("exit_reason") != "liquidation":
            continue
        short = bool(trade["is_short"])
        actual, protective = float(trade["close_rate"]), float(trade["stop_loss_abs"])
        records.append({
            "pair": trade["pair"],
            "open_utc": trade["open_date"],
            "liquidated_utc": trade["close_date"],
            "side": "SHORT" if short else "LONG",
            "entry_price": float(trade["open_rate"]),
            "liquidation_fill_price": actual,
            "protective_stop_price": protective,
            "liquidation_minus_stop_price": actual - protective,
            "liquidation_before_stop": actual < protective if short else actual > protective,
            "net_pnl_usdt": float(trade["profit_abs"]),
            "funding_fees_reported": float(trade.get("funding_fees") or 0),
            "liquidation_formula_verified": False,
            "actual_mark_at_liquidation_verified": False,
        })
    return records


def audit_market_data(data_dir):
    import pandas as pd
    result = {}
    for kind in ("funding_rate", "mark"):
        candidates = list(data_dir.rglob(f"BTC_USDT_USDT-*-{kind}.feather"))
        if len(candidates) != 1:
            raise ValueError(f"Missing/ambiguous required {kind} data: {candidates}")
        frame = pd.read_feather(candidates[0])
        if frame.empty or "date" not in frame or "open" not in frame:
            raise ValueError(f"Empty or invalid {kind} data")
        times = pd.to_datetime(frame["date"], utc=True)
        if times.duplicated().any() or not times.is_monotonic_increasing:
            raise ValueError(f"Nonmonotonic/duplicate {kind} timestamps")
        result[kind] = {
            "file": str(candidates[0]), "rows": len(frame),
            "first_utc": times.iloc[0].isoformat(),
            "last_utc": times.iloc[-1].isoformat(),
            "nonzero_rates_or_prices": int((frame["open"] != 0).sum()),
            "missing_values": int(frame["open"].isna().sum())
        }
    return result


def audit(result_zip, data_dir):
    trades = exported_trades(result_zip)
    return {
        "source": "Freqtrade export + OKX historical mark and funding data",
        "trades": len(trades),
        "liquidation_count": len(audit_liquidations(trades)),
        "liquidations": audit_liquidations(trades),
        "market_data": audit_market_data(data_dir),
        "freqtrade_reported_funding_total_usdt": sum(float(x.get("funding_fees") or 0) for x in trades),
        "funding_per_event_cashflow_verified": False,
        "liquidation_buffer_and_maintenance_margin_verified": False,
        "android_parity_verified": False,
        "limitations": [
            "Funding/mark candles are historical observations, not an exchange settlement ledger.",
            "Freqtrade export aggregates funding per trade; exact charge times cannot be inferred.",
            "Liquidation fill vs stop price does not alone prove the maintenance-margin formula."
        ],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--result", required=True, type=Path)
    p.add_argument("--datadir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    output = audit(args.result, args.datadir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
