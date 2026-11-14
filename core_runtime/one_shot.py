"""One-shot, Bundle-v1-only Strategy Core paper decision runner."""

from decimal import Decimal, DecimalException
import json
import os
from pathlib import Path
import time

import rfc8785

from core_runtime.input_bundle import BundleValidationError, validate_bundle
from core_runtime.preflight import PreflightError, _load_config, _preflight
from pipeline.values import identity


def _strict_json(path):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    try:
        return json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("JSON_CONSTANT_INVALID")),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        raise ValueError("BUNDLE_FILE_INVALID") from None


def _runner_policy(config):
    config_limits = config.get("risk_limits")
    if config_limits is None:
        config_limits = {}
    if not isinstance(config_limits, dict):
        raise PreflightError("RUNNER_RISK_LIMITS_REQUIRED")
    env_keys = {
        "maxDrawdownPct": "PAPER_MAX_DRAWDOWN_PCT",
        "maxDailyLossUsdt": "PAPER_MAX_DAILY_LOSS_USDT",
        "maxExposureUsdt": "PAPER_MAX_EXPOSURE_USDT",
    }
    if set(config_limits) - set(env_keys):
        raise PreflightError("RUNNER_RISK_LIMITS_REQUIRED")
    limits = {}
    for key, env_key in env_keys.items():
        env_value = os.environ.get(env_key)
        if isinstance(env_value, str) and env_value.strip():
            value = env_value.strip()
        else:
            value = config_limits.get(key)
        if not isinstance(value, str) or not value:
            raise PreflightError("RUNNER_RISK_LIMITS_REQUIRED")
        try:
            parsed = Decimal(value)
        except (DecimalException, TypeError, ValueError):
            raise PreflightError("RUNNER_RISK_LIMIT_INVALID") from None
        if not parsed.is_finite() or parsed <= 0:
            raise PreflightError("RUNNER_RISK_LIMIT_INVALID")
        limits[key] = value
    max_age = config.get("max_book_age_ms")
    if type(max_age) is not int or not 0 < max_age <= 5_000:
        raise PreflightError("RUNNER_BOOK_AGE_POLICY_INVALID")
    max_position = config.get("max_position_base", "0.01")
    if not isinstance(max_position, str):
        raise PreflightError("RUNNER_POSITION_LIMIT_INVALID")
    try:
        parsed_position = Decimal(max_position)
    except (DecimalException, TypeError, ValueError):
        raise PreflightError("RUNNER_POSITION_LIMIT_INVALID") from None
    if not parsed_position.is_finite() or parsed_position <= 0:
        raise PreflightError("RUNNER_POSITION_LIMIT_INVALID")
    return limits, max_age, max_position


def _state_matches(bundle_state, ledger_state):
    strategy = ledger_state.get("strategyState")
    if not isinstance(strategy, dict):
        return False
    expected_strategy = bundle_state.get("strategyState")
    if not isinstance(expected_strategy, dict):
        return False
    return (
        bundle_state.get("positionBase") == ledger_state.get("positionBase")
        and bundle_state.get("averageEntryPrice") == ledger_state.get("averageEntryPrice")
        and all(strategy.get(key) == expected_strategy.get(key)
                for key in ("owner", "dcaUsed", "strategyId"))
    )


def _result(bundle, run_status, *, signal=None, risk=None, ledger_ref=None, reason=None):
    bundle = bundle if isinstance(bundle, dict) else {}
    market_data = bundle.get("marketData", {})
    market_data = market_data if isinstance(market_data, dict) else {}
    m15 = market_data.get("m15", {})
    h1 = market_data.get("h1", {})
    m15 = m15 if isinstance(m15, dict) else {}
    h1 = h1 if isinstance(h1, dict) else {}
    order_book = bundle.get("orderBook", {})
    evidence = order_book.get("t1Evidence", {}) if isinstance(order_book, dict) else {}
    evidence = evidence if isinstance(evidence, dict) else {}
    return {
        "runId": identity("core-run:", {
            "bundleId": bundle.get("bundleId"),
            "strategyId": "STRATEGY_CORE",
        }),
        "decisionAtMs": bundle.get("decisionAtMs"),
        "bundleId": bundle.get("bundleId"),
        "strategyId": "STRATEGY_CORE",
        "runStatus": run_status,
        "signal": signal,
        "riskDecision": risk,
        "paperLedgerReference": ledger_ref,
        "reasonCode": reason,
        "sourceEvidence": {
            "m15DatasetVersion": m15.get("datasetVersion"),
            "h1DatasetVersion": h1.get("datasetVersion"),
            "t1SnapshotId": evidence.get("snapshotId"),
        },
    }


def run_once(config_path, bundle_path, *, now_ms=None, on_intent_prepared=None):
    """Validate inputs and submit at most once; journal actionable intent before submit."""
    now = time.time_ns() // 1_000_000 if now_ms is None else now_ms
    bundle = {}
    try:
        config, ledger_path = _load_config(config_path)
        limits, max_book_age_ms, max_position_base = _runner_policy(config)
        preflight = _preflight(
            config_path, now_ms=now, allow_risk_unready=True,
        )
        bundle = _strict_json(bundle_path)
        validation = validate_bundle(bundle, max_book_age_ms=max_book_age_ms)
        if validation["strategyId"] != "STRATEGY_CORE":
            raise ValueError("RUNNER_STRATEGY_SCOPE_INVALID")

        from paper_execution.ledger import read_account_risk_snapshot, read_snapshot
        current_risk = read_account_risk_snapshot(ledger_path, now_ms=now)
        expected_risk = bundle["accountRisk"]["snapshot"]
        if rfc8785.dumps(current_risk) != rfc8785.dumps(expected_risk):
            raise ValueError("RISK_SNAPSHOT_CHANGED")
        current_paper = read_snapshot(ledger_path, strategy_id="STRATEGY_CORE")
        if not _state_matches(bundle["paperState"], current_paper):
            raise ValueError("PAPER_STATE_CHANGED")
    except (PreflightError, BundleValidationError, OSError, ValueError, TypeError,
            KeyError, DecimalException):
        reason = "INPUT_REJECTED"
        try:
            if bundle and "bundleId" in bundle:
                reason = "INPUT_REJECTED"
        except Exception:
            pass
        return _result(bundle, "INPUT_REJECTED", reason=reason)
    except Exception:
        return _result(bundle, "RUN_FAILED", reason="RUN_PREFLIGHT_FAILED")

    try:
        from pipeline.core_strategy import produce
        from core_runtime.adapter import producer_report_to_signal
        from pipeline.core_signal import validate as validate_signal

        state = bundle["paperState"]
        risk_snapshot = bundle["accountRisk"]["snapshot"]
        report = produce(
            bundle["marketData"]["m15"],
            bundle["marketData"]["h1"],
            {
                "positionBase": state["positionBase"],
                "averageEntryPrice": state["averageEntryPrice"],
            },
            state["strategyState"],
            bundle["orderBook"],
            bundle["decisionAtMs"],
            account_equity_quote=risk_snapshot["accountEquityQuote"],
            max_position_base=max_position_base,
        )
        adapted = producer_report_to_signal(report)
        if adapted.get("action") == "WAIT":
            return _result(
                bundle, "NO_SIGNAL",
                signal={"action": "WAIT", "reason": adapted.get("reason")},
                reason=adapted.get("reason", "CORE_NO_SIGNAL"),
            )
        signal = validate_signal(adapted, now)
        if signal.get("action") == "WAIT" or not isinstance(signal.get("intent"), dict):
            return _result(bundle, "INVALID_SIGNAL", signal={
                "action": signal.get("action", "WAIT"),
                "reason": signal.get("reason"),
            }, reason="CORE_SIGNAL_VALIDATION_FAILED")

        position = Decimal(state["positionBase"])
        target = Decimal(signal["intent"]["targetPositionBase"])
        if position == 0 or position * target < 0:
            strategy_event = "ENTRY"
        elif target == 0 or abs(target) < abs(position):
            strategy_event = "EXIT"
        elif abs(target) > abs(position):
            strategy_event = "DCA"
        else:
            return _result(bundle, "NO_SIGNAL", signal={
                "action": signal["action"], "reason": "CORE_TARGET_UNCHANGED",
            }, reason="CORE_TARGET_UNCHANGED")
        if preflight.get("riskReady") is not True and strategy_event != "EXIT":
            return _result(
                bundle, "RISK_UNAVAILABLE",
                signal={"action": signal["action"], "reason": "RISK_STATE_BLOCKED"},
                reason="RISK_STATE_BLOCKED",
            )
    except Exception:
        return _result(bundle, "RUN_FAILED", reason="CORE_PRODUCER_FAILED")

    if on_intent_prepared is not None:
        try:
            if not callable(on_intent_prepared):
                raise TypeError("INTENT_PREPARE_CALLBACK_NOT_CALLABLE")
            on_intent_prepared(signal["intent"])
        except Exception:
            return _result(
                bundle, "RUN_FAILED",
                signal={"action": signal["action"], "reason": signal.get("reason")},
                reason="INTENT_PREPARE_CALLBACK_FAILED",
            )

    try:
        from paper_execution.ledger import PaperLedger
        ledger = PaperLedger(
            ledger_path,
            strategy_id="STRATEGY_CORE",
            risk_limits=limits,
            require_risk_limits=True,
            apply_migrations=False,
        )
        order = ledger.submit(
            signal["intent"], bundle["orderBook"], now,
            strategy_event=strategy_event,
        )
    except Exception:
        return _result(bundle, "PAPER_COMMIT_FAILED", signal={
            "action": signal["action"], "reason": signal.get("reason"),
        }, reason="PAPER_LEDGER_SUBMIT_FAILED")

    signal_view = {"action": signal["action"], "reason": signal.get("reason")}
    ledger_ref = {
        "orderId": order.get("orderId"),
        "reservationId": order.get("reservationId"),
        "status": order.get("status"),
    }
    if order.get("status") == "REJECTED":
        rejection_reason = order.get("reason", "RISK_REJECTED")
        run_status = (
            "RISK_UNAVAILABLE"
            if rejection_reason in {
                "RISK_INPUTS_UNAVAILABLE", "RISK_INPUTS_STALE_OR_CORRUPT",
            }
            else "RISK_REJECTED"
        )
        return _result(bundle, run_status, signal=signal_view,
                       risk={"decision": "REJECT", "reason": rejection_reason},
                       ledger_ref=ledger_ref, reason=rejection_reason)
    if order.get("status") not in ("FILLED", "OPEN", "PARTIALLY_FILLED"):
        return _result(bundle, "PAPER_COMMIT_FAILED", signal=signal_view,
                       ledger_ref=ledger_ref, reason="PAPER_ORDER_STATUS_INVALID")
    return _result(bundle, "PAPER_ACCEPTED", signal=signal_view,
                   risk={"decision": "ACCEPT", "reason": None},
                   ledger_ref=ledger_ref, reason=None)
