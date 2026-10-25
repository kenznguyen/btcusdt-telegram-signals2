"""Read-only validation boundary for Android backtest analytics reports."""
import json
import math
from pathlib import Path

REQUIRED = {"schema_version", "engine", "symbol", "timeframe", "period_days", "strategy_commit", "verified", "metrics", "trades"}
METRICS = {"net_profit_usdt", "win_rate_pct", "profit_factor", "max_drawdown_pct", "total_fees_usdt"}


def validate_report(report):
    if not isinstance(report, dict) or not REQUIRED.issubset(report):
        raise ValueError("Missing report fields")
    if report["schema_version"] != "1.0" or report["engine"] != "freqtrade":
        raise ValueError("Unsupported report format")
    if report["period_days"] not in (90, 180, 360) or type(report["period_days"]) is not int:
        raise ValueError("Unsupported period")
    if not isinstance(report["symbol"], str) or not report["symbol"].strip():
        raise ValueError("Invalid symbol")
    if report["timeframe"] != "15m":
        raise ValueError("Unsupported timeframe")
    if not isinstance(report["strategy_commit"], str) or not report["strategy_commit"].strip():
        raise ValueError("Missing provenance")
    if type(report["verified"]) is not bool:
        raise ValueError("Invalid verification flag")
    if not isinstance(report["metrics"], dict) or not METRICS.issubset(report["metrics"]):
        raise ValueError("Missing metrics")
    for key in METRICS:
        value = report["metrics"][key]
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
            raise ValueError("Invalid metric: " + key)
    if not isinstance(report["trades"], list):
        raise ValueError("Invalid trades")
    return report


def load_report(path):
    return validate_report(json.loads(Path(path).read_text(encoding="utf-8")))


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python validate_report.py report.json")
    load_report(sys.argv[1])
    print("Report structure valid (not a strategy parity certification)")
