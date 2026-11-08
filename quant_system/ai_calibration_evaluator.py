"""Offline, fail-closed evaluator for out-of-sample AI probability calibration.

This module scores supplied observations only. It does not load market data,
fit a model, authenticate external artifacts, issue a leverage attestation, or
authorize trading. Every acceptance threshold and regime taxonomy is explicit.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json


@dataclass(frozen=True)
class CalibrationObservation:
    outcome: object
    confidence: object
    side: str
    regime: str
    out_of_sample: bool


@dataclass(frozen=True)
class CalibrationGatePolicy:
    max_ece: object
    min_total_samples: int
    min_group_samples: int
    ece_bins: int
    required_regimes: tuple


@dataclass(frozen=True)
class CalibrationEvaluation:
    accepted: bool
    reasons: tuple
    sample_count: int
    group_count: int
    metrics: dict
    report_sha256: str
    input_sha256: str
    trade_authorized: bool = False
    attestation_issued: bool = False


def _finite_decimal(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not a probability")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("not a decimal") from None
    if not number.is_finite():
        raise ValueError("not finite")
    return number


def _policy_is_valid(policy):
    if not isinstance(policy, CalibrationGatePolicy):
        return False
    try:
        max_ece = _finite_decimal(policy.max_ece)
    except ValueError:
        return False
    if max_ece < 0 or max_ece > 1:
        return False
    if (type(policy.min_total_samples) is not int or policy.min_total_samples <= 0
            or type(policy.min_group_samples) is not int or policy.min_group_samples <= 0
            or type(policy.ece_bins) is not int or not 1 <= policy.ece_bins <= 100):
        return False
    if (not isinstance(policy.required_regimes, (tuple, list))
            or not policy.required_regimes
            or any(not isinstance(item, str) or not item.strip()
                   for item in policy.required_regimes)
            or len(set(policy.required_regimes)) != len(policy.required_regimes)):
        return False
    return True


def _metrics(rows, bins):
    count = len(rows)
    positives = sum(row[0] for row in rows)
    prevalence = Decimal(positives) / Decimal(count)
    brier = sum((row[1] - Decimal(row[0])) ** 2 for row in rows) / Decimal(count)
    baseline = sum((prevalence - Decimal(row[0])) ** 2 for row in rows) / Decimal(count)

    weighted_error = Decimal(0)
    for bin_index in range(bins):
        lower = Decimal(bin_index) / Decimal(bins)
        upper = Decimal(bin_index + 1) / Decimal(bins)
        members = [
            row for row in rows
            if (row[1] >= lower and (row[1] < upper or bin_index == bins - 1))
        ]
        if not members:
            continue
        mean_confidence = sum(row[1] for row in members) / Decimal(len(members))
        mean_outcome = Decimal(sum(row[0] for row in members)) / Decimal(len(members))
        weighted_error += (
            Decimal(len(members)) / Decimal(count)
            * abs(mean_confidence - mean_outcome)
        )
    return {
        "sample_count": count,
        "ece": float(weighted_error),
        "brier_score": float(brier),
        "reference_brier_score": float(baseline),
        "brier_beats_reference": brier < baseline,
    }


class CalibrationEvaluator:
    """Evaluate total, LONG/SHORT and declared regime calibration gates."""

    def evaluate(self, observations, policy):
        reasons = []
        metrics = {}
        if not _policy_is_valid(policy):
            reasons.append("GATE_POLICY_INVALID")
            return self._report(False, reasons, 0, 0, metrics)

        if not isinstance(observations, (list, tuple)) or not observations:
            reasons.append("OBSERVATIONS_MISSING")
            return self._report(False, reasons, 0, 0, metrics)

        normalized = []
        allowed_regimes = set(policy.required_regimes)
        for observation in observations:
            if not isinstance(observation, CalibrationObservation):
                reasons.append("OBSERVATION_INVALID")
                continue
            if observation.out_of_sample is not True:
                reasons.append("NON_OOS_OBSERVATION_PRESENT")
                continue
            if (observation.side not in ("LONG", "SHORT")
                    or not isinstance(observation.regime, str)
                    or not observation.regime.strip()):
                reasons.append("OBSERVATION_INVALID")
                continue
            if observation.regime not in allowed_regimes:
                reasons.append(f"UNDECLARED_REGIME:{observation.regime}")
                continue
            try:
                if type(observation.outcome) is not int or observation.outcome not in (0, 1):
                    raise ValueError("outcome must be integer 0 or 1")
                confidence = _finite_decimal(observation.confidence)
                if confidence < 0 or confidence > 1:
                    raise ValueError("confidence outside [0, 1]")
            except ValueError:
                reasons.append("OBSERVATION_INVALID")
                continue
            normalized.append((
                observation.outcome, confidence, observation.side, observation.regime
            ))

        if reasons:
            return self._report(False, sorted(set(reasons)), len(observations), 0, metrics)

        if len(normalized) < policy.min_total_samples:
            reasons.append("TOTAL_SAMPLE_COUNT_BELOW_MINIMUM")

        grouped = {}
        for outcome, confidence, side, regime in normalized:
            grouped.setdefault((side, regime), []).append((outcome, confidence))

        required_groups = [
            (side, regime)
            for side in ("LONG", "SHORT")
            for regime in policy.required_regimes
        ]
        for side, regime in required_groups:
            key = f"{side}:{regime}"
            rows = grouped.get((side, regime), [])
            if not rows:
                reasons.append(f"GROUP_MISSING:{key}")
                continue
            if len(rows) < policy.min_group_samples:
                reasons.append(f"GROUP_SAMPLE_COUNT_BELOW_MINIMUM:{key}")
                continue
            group_metrics = _metrics(rows, policy.ece_bins)
            metrics[key] = group_metrics
            if group_metrics["ece"] > float(policy.max_ece):
                reasons.append(f"ECE_LIMIT_EXCEEDED:{key}")
            if not group_metrics["brier_beats_reference"]:
                reasons.append(f"BRIER_NOT_BETTER_THAN_BASELINE:{key}")

        overall_rows = [(row[0], row[1]) for row in normalized]
        metrics["overall"] = _metrics(overall_rows, policy.ece_bins)
        if metrics["overall"]["ece"] > float(policy.max_ece):
            reasons.append("ECE_LIMIT_EXCEEDED:overall")
        if not metrics["overall"]["brier_beats_reference"]:
            reasons.append("BRIER_NOT_BETTER_THAN_BASELINE:overall")

        canonical_rows = [
            {
                "outcome": outcome,
                "confidence": format(confidence, "f"),
                "side": side,
                "regime": regime,
            }
            for outcome, confidence, side, regime in normalized
        ]
        input_payload = json.dumps(
            canonical_rows, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        input_sha256 = hashlib.sha256(input_payload.encode("utf-8")).hexdigest()
        policy_payload = {
            "max_ece": format(_finite_decimal(policy.max_ece), "f"),
            "min_total_samples": policy.min_total_samples,
            "min_group_samples": policy.min_group_samples,
            "ece_bins": policy.ece_bins,
            "required_regimes": list(policy.required_regimes),
        }
        return self._report(
            not reasons, sorted(set(reasons)), len(normalized), len(grouped), metrics,
            input_sha256=input_sha256, policy_payload=policy_payload,
        )

    @staticmethod
    def _report(accepted, reasons, sample_count, group_count, metrics,
                *, input_sha256="", policy_payload=None):
        payload = {
            "accepted": bool(accepted),
            "reasons": list(reasons),
            "sample_count": sample_count,
            "group_count": group_count,
            "metrics": metrics,
            "input_sha256": input_sha256,
            "policy": policy_payload,
            "trade_authorized": False,
            "attestation_issued": False,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        return CalibrationEvaluation(
            accepted=bool(accepted),
            reasons=tuple(reasons),
            sample_count=sample_count,
            group_count=group_count,
            metrics=metrics,
            report_sha256=digest,
            input_sha256=input_sha256,
        )


def approved_calibration_gate_policy(*, ece_bins, required_regimes):
    """Build the user-approved production thresholds with explicit bin/regime inputs.

    The user-approved numeric gates are fixed here. Binning and regime taxonomy
    remain caller-supplied because neither was part of the approval decision.
    """
    if type(ece_bins) is not int or not 1 <= ece_bins <= 100:
        raise ValueError("ece_bins must be an integer in [1, 100]")
    if (not isinstance(required_regimes, (tuple, list))
            or not required_regimes
            or any(not isinstance(item, str) or not item.strip()
                   for item in required_regimes)
            or len(set(required_regimes)) != len(required_regimes)):
        raise ValueError("required_regimes must be non-empty, unique regime names")
    return CalibrationGatePolicy(
        max_ece="0.05",
        min_total_samples=1000,
        min_group_samples=200,
        ece_bins=ece_bins,
        required_regimes=tuple(required_regimes),
    )
