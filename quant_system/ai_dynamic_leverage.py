"""Fail-closed AI-only dynamic leverage policy.

This module is a pure contract: it does not size orders, route intents, read
runtime state, or submit paper/live orders. Confidence-domain endpoints are
explicit configuration; they are intentionally not inferred from Core rules.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_DATASET_VERSION = re.compile(r"^sha256:([0-9a-f]{64})$")


def _decimal(value, field, *, positive=False):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite decimal")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field} must be a finite decimal") from None
    if not number.is_finite() or (positive and number <= 0):
        raise ValueError(f"{field} must be a finite positive decimal")
    return number


def _identity(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(f"{field} is required")
    return value


@dataclass(frozen=True)
class CalibrationAttestation:
    """Externally produced evidence that a model calibration passed its own gate."""

    model_version: str
    strategy_version: str
    dataset_version: str
    report_sha256: str
    protocol_sha256: str
    validated_at_ms: int
    expires_at_ms: int
    out_of_sample: bool
    leakage_free: bool
    acceptance_passed: bool


@dataclass(frozen=True)
class LeverageDecision:
    accepted: bool
    reason: str
    leverage: Decimal | None = None
    model_version: str | None = None
    report_sha256: str | None = None
    protocol_sha256: str | None = None


class AIDynamicLeveragePolicy:
    """Map calibrated AI confidence linearly into explicit leverage bounds."""

    def __init__(self, *, min_leverage, max_leverage,
                 confidence_floor, confidence_ceiling):
        self.min_leverage = _decimal(min_leverage, "min_leverage", positive=True)
        self.max_leverage = _decimal(max_leverage, "max_leverage", positive=True)
        self.confidence_floor = _decimal(confidence_floor, "confidence_floor")
        self.confidence_ceiling = _decimal(confidence_ceiling, "confidence_ceiling")

        if (self.min_leverage < Decimal("1")
                or self.max_leverage > Decimal("3")
                or self.min_leverage > self.max_leverage):
            raise ValueError("AI leverage bounds must satisfy 1 <= min <= max <= 3")
        if (self.confidence_floor < 0
                or self.confidence_ceiling > 1
                or self.confidence_floor >= self.confidence_ceiling):
            raise ValueError("Confidence domain must satisfy 0 <= floor < ceiling <= 1")

    @staticmethod
    def _validate_calibration(calibration, *, now_ms, model_version,
                              strategy_version, dataset_version):
        if not isinstance(calibration, CalibrationAttestation):
            return "CALIBRATION_ATTESTATION_MISSING"
        if type(calibration.acceptance_passed) is not bool or not calibration.acceptance_passed:
            return "CALIBRATION_NOT_ACCEPTED"
        if (type(calibration.out_of_sample) is not bool or not calibration.out_of_sample
                or type(calibration.leakage_free) is not bool or not calibration.leakage_free):
            return "CALIBRATION_VALIDATION_INVALID"

        if (not _SHA256.fullmatch(calibration.report_sha256 or "")
                or not _SHA256.fullmatch(calibration.protocol_sha256 or "")
                or not _DATASET_VERSION.fullmatch(calibration.dataset_version or "")):
            return "CALIBRATION_PROVENANCE_INVALID"
        if (type(calibration.validated_at_ms) is not int
                or type(calibration.expires_at_ms) is not int
                or type(now_ms) is not int
                or calibration.validated_at_ms <= 0
                or calibration.expires_at_ms <= calibration.validated_at_ms
                or now_ms <= 0
                or calibration.validated_at_ms > now_ms):
            return "CALIBRATION_TIME_INVALID"
        if now_ms >= calibration.expires_at_ms:
            return "CALIBRATION_EXPIRED"

        try:
            expected = (
                _identity(model_version, "model_version"),
                _identity(strategy_version, "strategy_version"),
                _identity(dataset_version, "dataset_version"),
                _identity(calibration.model_version, "calibration.model_version"),
                _identity(calibration.strategy_version, "calibration.strategy_version"),
            )
        except ValueError:
            return "CALIBRATION_PROVENANCE_INVALID"
        if expected[:3] != expected[3:] + (dataset_version,):
            # Keep the three source identities explicit and compare independently.
            if (model_version != calibration.model_version
                    or strategy_version != calibration.strategy_version
                    or dataset_version != calibration.dataset_version):
                return "CALIBRATION_PROVENANCE_MISMATCH"
        return None

    def calculate(self, *, confidence, calibration, now_ms,
                  model_version, strategy_version, dataset_version):
        """Return an auditable leverage decision; invalid inputs always reject."""
        try:
            probability = _decimal(confidence, "confidence")
        except ValueError:
            return LeverageDecision(False, "CONFIDENCE_INVALID")

        if probability < self.confidence_floor or probability > self.confidence_ceiling:
            return LeverageDecision(False, "CONFIDENCE_OUT_OF_DOMAIN")

        reason = self._validate_calibration(
            calibration, now_ms=now_ms, model_version=model_version,
            strategy_version=strategy_version, dataset_version=dataset_version,
        )
        if reason:
            return LeverageDecision(False, reason)

        fraction = (
            (probability - self.confidence_floor)
            / (self.confidence_ceiling - self.confidence_floor)
        )
        leverage = self.min_leverage + (
            (self.max_leverage - self.min_leverage) * fraction
        )
        if (not leverage.is_finite()
                or leverage < self.min_leverage
                or leverage > self.max_leverage):
            return LeverageDecision(False, "LEVERAGE_OUT_OF_BOUNDS")

        return LeverageDecision(
            True, "CALIBRATED_LINEAR_LEVERAGE",
            leverage=leverage,
            model_version=calibration.model_version,
            report_sha256=calibration.report_sha256,
            protocol_sha256=calibration.protocol_sha256,
        )
