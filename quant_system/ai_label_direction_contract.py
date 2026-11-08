"""Strict parser for the independent AI label/direction contract V1.

Parsing this contract does not certify training, OOS, calibration, provenance,
or authorize trading. It only validates explicit, internally consistent inputs.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json


class ContractValidationError(ValueError):
    """Raised when a V1 contract is incomplete, ambiguous, or unsafe."""


@dataclass(frozen=True)
class AILabelDirectionContract:
    schema_version: int
    contract_id: str
    model_id: str
    exchange: str
    market_type: str
    symbol: str
    horizon_m15_candles: int
    decision_price_basis: str
    outcome_price_basis: str
    label_end_rule: str
    outcome_available_at_rule: str
    formula_id: str
    short_threshold: Decimal
    long_threshold: Decimal
    neutral_action: str
    feature_timeframes: tuple[str, ...]
    feature_cutoff_semantics: str
    confidence_source: str


_ROOT_KEYS = {
    "schema_version", "contract_id", "model_id", "market", "label",
    "direction", "features", "confidence",
}
_MARKET_KEYS = {"exchange", "market_type", "symbol"}
_LABEL_KEYS = {
    "horizon_m15_candles", "decision_price_basis", "outcome_price_basis",
    "label_end_rule", "outcome_available_at_rule", "formula_id",
}
_DIRECTION_KEYS = {"short_threshold", "long_threshold", "neutral_action"}
_FEATURE_KEYS = {"timeframes", "cutoff_semantics"}
_CONFIDENCE_KEYS = {"source"}
_LEGACY_MODEL_IDS = {"chart-pro-okx-shadow-v1"}


def _require_exact_keys(value, expected, path):
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ContractValidationError(f"{path}: keys or object shape invalid")


def _require_text(value, path):
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{path}: non-empty string required")
    return value.strip()


def _parse_threshold(value, path):
    # Strings avoid binary-float ambiguity in a signed protocol.
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{path}: decimal string required")
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ContractValidationError(f"{path}: invalid decimal") from None
    if not parsed.is_finite():
        raise ContractValidationError(f"{path}: finite decimal required")
    return parsed


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractValidationError("duplicate JSON key")
        result[key] = value
    return result


def _parse_input(raw):
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise ContractValidationError("contract must be UTF-8") from None
    if isinstance(raw, str):
        try:
            return json.loads(
                raw,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ContractValidationError(f"non-finite JSON value: {value}")
                ),
            )
        except (json.JSONDecodeError, TypeError):
            raise ContractValidationError("contract JSON invalid") from None
    return raw


def parse_ai_label_direction_contract(raw):
    """Parse a complete V1 contract; never supply missing protocol defaults."""
    value = _parse_input(raw)
    _require_exact_keys(value, _ROOT_KEYS, "contract")

    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ContractValidationError("schema_version: unsupported version")

    contract_id = _require_text(value["contract_id"], "contract_id")
    model_id = _require_text(value["model_id"], "model_id")
    if model_id in _LEGACY_MODEL_IDS:
        raise ContractValidationError("model_id: legacy frozen model cannot be reused")

    market = value["market"]
    _require_exact_keys(market, _MARKET_KEYS, "market")
    exchange = _require_text(market["exchange"], "market.exchange")
    market_type = _require_text(market["market_type"], "market.market_type")
    symbol = _require_text(market["symbol"], "market.symbol")
    if (exchange, market_type, symbol) != ("binance", "USDT_PERPETUAL", "BTCUSDT"):
        raise ContractValidationError("market: unsupported V1 market identity")

    label = value["label"]
    _require_exact_keys(label, _LABEL_KEYS, "label")
    horizon = label["horizon_m15_candles"]
    if type(horizon) is not int or horizon <= 0:
        raise ContractValidationError("label.horizon_m15_candles: positive integer required")
    decision_basis = _require_text(label["decision_price_basis"], "label.decision_price_basis")
    outcome_basis = _require_text(label["outcome_price_basis"], "label.outcome_price_basis")
    label_end_rule = _require_text(label["label_end_rule"], "label.label_end_rule")
    availability_rule = _require_text(
        label["outcome_available_at_rule"], "label.outcome_available_at_rule"
    )
    formula_id = _require_text(label["formula_id"], "label.formula_id")

    direction = value["direction"]
    _require_exact_keys(direction, _DIRECTION_KEYS, "direction")
    short_threshold = _parse_threshold(direction["short_threshold"], "direction.short_threshold")
    long_threshold = _parse_threshold(direction["long_threshold"], "direction.long_threshold")
    if short_threshold >= long_threshold:
        raise ContractValidationError("direction: short threshold must be below long threshold")
    neutral_action = _require_text(direction["neutral_action"], "direction.neutral_action")
    if neutral_action != "ABSTAIN":
        raise ContractValidationError("direction.neutral_action: ABSTAIN required")

    features = value["features"]
    _require_exact_keys(features, _FEATURE_KEYS, "features")
    timeframes = features["timeframes"]
    if (not isinstance(timeframes, list)
            or timeframes != ["15m", "1h"]):
        raise ContractValidationError("features.timeframes: exact M15 and H1 feature set required")
    cutoff_semantics = _require_text(
        features["cutoff_semantics"], "features.cutoff_semantics"
    )
    if cutoff_semantics != "closed_validated_first_observed_available_by_prediction":
        raise ContractValidationError("features.cutoff_semantics: unsupported semantics")

    confidence = value["confidence"]
    _require_exact_keys(confidence, _CONFIDENCE_KEYS, "confidence")
    confidence_source = _require_text(confidence["source"], "confidence.source")
    if confidence_source != "separate_calibration_artifact":
        raise ContractValidationError(
            "confidence.source: independent calibration artifact required"
        )

    return AILabelDirectionContract(
        schema_version=1,
        contract_id=contract_id,
        model_id=model_id,
        exchange=exchange,
        market_type=market_type,
        symbol=symbol,
        horizon_m15_candles=horizon,
        decision_price_basis=decision_basis,
        outcome_price_basis=outcome_basis,
        label_end_rule=label_end_rule,
        outcome_available_at_rule=availability_rule,
        formula_id=formula_id,
        short_threshold=short_threshold,
        long_threshold=long_threshold,
        neutral_action=neutral_action,
        feature_timeframes=("15m", "1h"),
        feature_cutoff_semantics=cutoff_semantics,
        confidence_source=confidence_source,
    )
