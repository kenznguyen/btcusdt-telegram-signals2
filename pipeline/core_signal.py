"""Strict adapter for independently published Strategy Core paper signals.

The RSI/ADX/Smart-DCA producer writes a small, versioned report. This adapter
validates its provenance and timestamps; it never fabricates a signal.
"""
from pipeline.values import identity, number, stamp


def validate(report, now_ms):
    if not isinstance(report, dict) or report.get("schemaVersion") != 1 or report.get("source") != "STRATEGY_CORE":
        return {"source": "STRATEGY_CORE", "action": "WAIT", "reason": "CORE_SIGNAL_INVALID", "intent": None}
    action = report.get("action")
    if action not in ("LONG", "SHORT", "FLAT", "WAIT"):
        return {"source": "STRATEGY_CORE", "action": "WAIT", "reason": "CORE_ACTION_INVALID", "intent": None}
    if action == "WAIT":
        return {"source": "STRATEGY_CORE", "action": "WAIT",
                "reason": str(report.get("reason") or "CORE_NO_SIGNAL")[:160], "intent": None}
    try:
        if (report.get("exchange"), report.get("marketType"), report.get("symbol"), report.get("timeframe")) != (
                "binance", "USDT_PERPETUAL", "BTCUSDT", "15m"):
            raise ValueError("CORE_WRONG_MARKET")
        version = report.get("strategyVersion")
        dataset = report.get("datasetVersion")
        snapshot = report.get("inputSnapshotId")
        if any(not isinstance(value, str) or not value.strip() or len(value) > 200 for value in (version, dataset, snapshot)):
            raise ValueError("CORE_PROVENANCE_MISSING")
        decided, expiry, now = stamp(report.get("decisionAtMs")), stamp(report.get("validUntilMs")), stamp(now_ms)
        if not 0 < expiry-decided <= 60_000 or not decided <= now <= expiry:
            raise ValueError("CORE_SIGNAL_EXPIRED")
        target = number(report.get("targetPositionBase"), signed=True)
        price = number(report.get("limitPrice"))
        if price <= 0 or (action == "LONG" and target <= 0) or (action == "SHORT" and target >= 0) or (action == "FLAT" and target != 0):
            raise ValueError("CORE_INTENT_INVALID")
        intent = {
            "intentId": identity("core-intent:", {key: report[key] for key in (
                "strategyVersion", "datasetVersion", "inputSnapshotId", "decisionAtMs",
                "validUntilMs", "targetPositionBase", "limitPrice", "action")}),
            "symbol": "BTCUSDT", "exchange": "binance", "marketType": "USDT_PERPETUAL",
            "strategyVersion": version, "modelVersion": "strategy-core",
            "datasetVersion": dataset, "targetPositionBase": str(target),
            "limitPrice": str(price), "decisionAtMs": decided, "validUntilMs": expiry,
            "inputSnapshotId": snapshot, "mode": "PAPER",
        }
        return {"source": "STRATEGY_CORE", "action": "BUY" if action == "LONG" else "SELL" if action == "SHORT" else "CLOSE",
                "reason": str(report.get("reason") or "CORE_SIGNAL_VALIDATED")[:160], "intent": intent}
    except (KeyError, TypeError, ValueError, OverflowError):
        return {"source": "STRATEGY_CORE", "action": "WAIT", "reason": "CORE_SIGNAL_INVALID", "intent": None}
