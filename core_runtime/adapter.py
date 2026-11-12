"""Strict translation from Strategy Core producer reports to validator signals.

This module is deliberately pure: it performs no I/O, risk admission, ledger
mutation, timestamp synthesis, or order execution.
"""

from collections.abc import Mapping


_ACTION_MAP = {
    "BUY": "LONG",
    "SELL": "SHORT",
    "CLOSE": "FLAT",
}

_REQUIRED_INTENT_FIELDS = (
    "schemaVersion",
    "source",
    "exchange",
    "marketType",
    "symbol",
    "timeframe",
    "action",
    "strategyVersion",
    "datasetVersion",
    "inputSnapshotId",
    "decisionAtMs",
    "validUntilMs",
    "targetPositionBase",
    "limitPrice",
)


def producer_report_to_signal(report):
    """Translate a known Core producer outcome without inventing provenance.

    WAIT is a non-intent outcome. Actionable outcomes must carry a complete
    producer intent whose action agrees with the report-level action.
    """
    if not isinstance(report, Mapping):
        raise ValueError("CORE_PRODUCER_REPORT_INVALID")

    action = report.get("action")
    reason = report.get("reason")
    if action == "WAIT":
        if report.get("intent") is not None:
            raise ValueError("CORE_PRODUCER_INTENT_INVALID")
        result = {
            "schemaVersion": 1,
            "source": "STRATEGY_CORE",
            "action": "WAIT",
        }
        if reason is not None:
            result["reason"] = reason
        return result

    mapped_action = _ACTION_MAP.get(action)
    if mapped_action is None:
        raise ValueError("CORE_PRODUCER_ACTION_INVALID")

    intent = report.get("intent")
    if not isinstance(intent, Mapping):
        raise ValueError("CORE_PRODUCER_INTENT_INVALID")
    if any(field not in intent for field in _REQUIRED_INTENT_FIELDS):
        raise ValueError("CORE_PRODUCER_INTENT_INVALID")
    if (
        intent.get("schemaVersion") != 1
        or intent.get("source") != "STRATEGY_CORE"
        or intent.get("action") != mapped_action
    ):
        if intent.get("action") != mapped_action:
            raise ValueError("CORE_PRODUCER_ACTION_MISMATCH")
        raise ValueError("CORE_PRODUCER_INTENT_INVALID")

    for field in (
        "exchange",
        "marketType",
        "symbol",
        "timeframe",
        "strategyVersion",
        "datasetVersion",
        "inputSnapshotId",
    ):
        value = intent.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("CORE_PRODUCER_INTENT_INVALID")

    result = {
        "schemaVersion": intent["schemaVersion"],
        "source": intent["source"],
        "action": mapped_action,
        "exchange": intent["exchange"],
        "marketType": intent["marketType"],
        "symbol": intent["symbol"],
        "timeframe": intent["timeframe"],
        "strategyVersion": intent["strategyVersion"],
        "datasetVersion": intent["datasetVersion"],
        "inputSnapshotId": intent["inputSnapshotId"],
        "decisionAtMs": intent["decisionAtMs"],
        "validUntilMs": intent["validUntilMs"],
        "targetPositionBase": intent["targetPositionBase"],
        "limitPrice": intent["limitPrice"],
    }
    if reason is not None:
        result["reason"] = reason
    if "candleOpenTimeMs" in intent:
        result["candleOpenTimeMs"] = intent["candleOpenTimeMs"]
    return result
