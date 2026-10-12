"""Run independent, sequential historical backtests for multiple OKX USDT swaps.

Each symbol gets its own fresh subprocess and output directory. This script does not
read or write the live scanner state (state.json) and never sends Telegram messages.
"""
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "LINKUSDT"]
SUPPORTED_SYMBOLS = set(DEFAULT_SYMBOLS)
ROOT = Path.cwd()
OUT = ROOT / "multi_backtest_results"
SUMMARY = OUT / "multi_backtest_summary.json"


def main():
    raw = os.getenv("BACKTEST_SYMBOLS", ",".join(DEFAULT_SYMBOLS))
    symbols = list(dict.fromkeys(s.strip().upper() for s in raw.split(",") if s.strip()))
    if not symbols:
        raise ValueError("Cần chọn ít nhất một symbol.")
    invalid = [s for s in symbols if s not in SUPPORTED_SYMBOLS]
    if invalid:
        raise ValueError("Symbol không hỗ trợ: " + ", ".join(invalid))
    days = int(os.getenv("BACKTEST_DAYS", "360"))
    if not 1 <= days <= 365:
        raise ValueError("BACKTEST_DAYS phải từ 1 đến 365.")
    capital = float(os.getenv("BACKTEST_INITIAL_CAPITAL", "100"))
    entry_margin = float(os.getenv("ENTRY_MARGIN_PCT", "50"))
    dca_ratio = float(os.getenv("DCA_MARGIN_RATIO", "100"))
    if capital < 1:
        raise ValueError("Vốn mô phỏng phải >= 1 USDT.")
    if not 1 <= entry_margin <= 100:
        raise ValueError("ENTRY_MARGIN_PCT phải từ 1 đến 100.")
    if not 0 <= dca_ratio <= 500:
        raise ValueError("DCA_MARGIN_RATIO phải từ 0 đến 500.")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    results = []
    for symbol in symbols:
        target = OUT / symbol
        target.mkdir()
        env = os.environ.copy()
        env.update({
            "BACKTEST_SYMBOL": symbol,
            "BACKTEST_DAYS": str(days),
            "BACKTEST_INITIAL_CAPITAL": str(capital),
            "ENTRY_MARGIN_PCT": str(entry_margin),
            "DCA_MARGIN_RATIO": str(dca_ratio),
            "BACKTEST_RUN_ID": f"{os.getenv('GITHUB_RUN_ID', 'local')}-{symbol}",
        })
        print(f"\n=== Backtest {symbol}: {days} days ===", flush=True)
        run = subprocess.run([sys.executable, "backtest.py"], cwd=ROOT, env=env, text=True)
        report_path = ROOT / "backtest_last_result.json"
        report = {}
        if report_path.exists():
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                report = {}
        status_path = ROOT / "backtest_status.json"
        status = {}
        if status_path.exists():
            try:
                status = json.loads(status_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                status = {}
        # Copy this symbol's files before the next run overwrites the root output names.
        for name in ("backtest_last_result.json", "backtest_status.json", "backtest_trades.csv",
                     "backtest_equity.csv", "backtest_equity_m15.csv"):
            src = ROOT / name
            if src.exists():
                shutil.copy2(src, target / name)
        if run.returncode != 0 or report.get("status") != "completed" or report.get("symbol", "").split()[0] != symbol or status.get("status") != "completed":
            item = {"symbol": symbol, "status": "failed",
                    "error": report.get("error") or status.get("message") or f"returncode={run.returncode}, report_status={report.get('status')}, status_file={status.get('status')}"}
        else:
            item = {k: report.get(k) for k in (
                "symbol", "timeframe", "period_days", "start", "end", "candle_count",
                "trade_count", "closed_trade_count", "win_rate_pct", "initial_capital_usdt",
                "final_balance_usdt", "net_profit_usdt", "return_pct", "profit_factor",
                "max_drawdown_usdt", "max_drawdown_pct", "max_intrabar_drawdown_usdt",
                "max_intrabar_drawdown_pct", "fees_usdt", "dca_count", "tp_count",
                "soft_sl_count", "emergency_sl_count", "end_of_test_close_count",
            )}
            item.update({"symbol_code": symbol, "status": "completed",
                         "result_file": f"{symbol}/backtest_last_result.json",
                         "trades_file": f"{symbol}/backtest_trades.csv",
                         "equity_file": f"{symbol}/backtest_equity_m15.csv"})
        results.append(item)
        print(json.dumps(item, ensure_ascii=False), flush=True)

    summary = {
        "status": "completed" if all(x["status"] == "completed" for x in results) else "partial",
        "generated_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "period_days": days, "initial_capital_usdt_per_symbol": capital,
        "entry_margin_pct": entry_margin, "dca_margin_ratio_pct": dca_ratio,
        "symbols_requested": symbols, "symbols_completed": sum(x["status"] == "completed" for x in results),
        "symbols_failed": sum(x["status"] != "completed" for x in results), "results": results,
        "note": "Mỗi symbol có tài khoản mô phỏng riêng; kết quả không cộng gộp vốn/PnL giữa các symbol.",
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Summary written to {SUMMARY}", flush=True)
    if summary["symbols_completed"] == 0:
        raise SystemExit("Không có symbol nào backtest thành công.")


if __name__ == "__main__":
    main()
