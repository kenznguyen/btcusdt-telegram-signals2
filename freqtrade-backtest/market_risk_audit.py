"""Audit Freqtrade liquidation fills and independent mark/funding data presence.

No change to StrategyEngine. Raw funding candles are observations, not proof
of per-position settlement cashflows or liquidation maintenance margin.
"""
import argparse
import json
import zipfile
from datetime import datetime, timezone, timedelta
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


def normalize_market_frame(frame, kind):
    """Freqtrade >=2026.8 funding data uses funding_rate, not OHLCV.open."""
    import pandas as pd
    if frame.empty:
        raise ValueError(f"empty {kind} data")
    if "date" not in frame.columns:
        raise ValueError(f"missing date in {kind} data")
    if kind == "funding_rate":
        column = next((x for x in ("funding_rate", "fundingRate", "open") if x in frame.columns), None)
    elif kind == "mark":
        column = "open" if "open" in frame.columns else None
    else:
        raise ValueError(f"unsupported candle kind: {kind}")
    if column is None:
        raise ValueError(f"invalid {kind} columns: {list(frame.columns)}")
    times = pd.to_datetime(frame["date"], utc=True, errors="coerce")
    values = pd.to_numeric(frame[column], errors="coerce")
    if times.isna().any() or values.isna().any():
        raise ValueError(f"missing or invalid {kind} timestamps/values")
    if times.duplicated().any() or not times.is_monotonic_increasing:
        raise ValueError(f"nonmonotonic or duplicate {kind} timestamps")
    return times, values, column


def audit_market_data(data_dir):
    import pandas as pd
    result = {}
    for kind in ("funding_rate", "mark"):
        candidates = list(data_dir.rglob(f"BTC_USDT_USDT-*-{kind}.feather"))
        if len(candidates) != 1:
            raise ValueError(f"Missing/ambiguous required {kind} data: {candidates}")
        frame = pd.read_feather(candidates[0])
        times, values, column = normalize_market_frame(frame, kind)
        result[kind] = {
            "file": str(candidates[0]), "rows": len(frame),
            "value_column": column,
            "first_utc": times.iloc[0].isoformat(),
            "last_utc": times.iloc[-1].isoformat(),
            "nonzero_rates_or_prices": int((values != 0).sum()),
            "missing_values": int(values.isna().sum()),
        }
    return result



def funding_coverage_status(market_data, trades):
    """Explicitly distinguish funding coverage from OHLCV completeness."""
    if not trades:
        return {"complete_for_trade_period": False, "reason": "no_trades"}
    funding = market_data.get("funding_rate", {})
    if not funding.get("first_utc") or not funding.get("last_utc"):
        return {"complete_for_trade_period": False, "reason": "missing_funding_data"}
    first_trade = min(datetime.fromisoformat(str(t["open_date"]).replace("Z", "+00:00")) for t in trades)
    last_trade = max(datetime.fromisoformat(str(t["close_date"]).replace("Z", "+00:00")) for t in trades)
    first_rate = datetime.fromisoformat(funding["first_utc"])
    last_rate = datetime.fromisoformat(funding["last_utc"])
    # Funding is periodic, not an OHLCV candle. Allow one day around edges,
    # but NEVER accept multi-month absent history as complete.
    complete = first_rate <= first_trade + timedelta(days=1) and last_rate >= last_trade - timedelta(days=1)
    return {
        "complete_for_trade_period": complete,
        "first_trade_utc": first_trade.isoformat(),
        "last_trade_utc": last_trade.isoformat(),
        "first_funding_utc": first_rate.isoformat(),
        "last_funding_utc": last_rate.isoformat(),
        "reason": "coverage_verified" if complete else "funding_history_incomplete",
        "funding_event_schedule_verified": False,
    }


def audit(result_zip, data_dir):
    trades = exported_trades(result_zip)
    market_data = audit_market_data(data_dir)
    return {
        "source": "Freqtrade export + OKX historical mark and funding data",
        "trades": len(trades),
        "liquidation_count": len(audit_liquidations(trades)),
        "liquidations": audit_liquidations(trades),
        "market_data": market_data,
        "funding_coverage": funding_coverage_status(market_data, trades),
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
