"""Independent CORE/AI intent routing through the shared paper-risk engine.

This module does not generate signals, infer leverage, choose position sizing,
or submit exchange orders. Callers provide validated StrategyIntents from the
existing CORE and FreqAI signal producers plus explicit order sizing.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from quant_system.dual_ledger import RiskDecision
from quant_system.dual_strategy import CANDLE_MS, Origin, Side, Signal


def _positive_decimal(value, field):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite positive decimal")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field} must be a finite positive decimal") from None
    if not number.is_finite() or number <= 0:
        raise ValueError(f"{field} must be a finite positive decimal")
    return number


@dataclass(frozen=True)
class StrategyIntent:
    """One explicit ENTRY or DCA request from exactly one strategy stream."""

    signal: Signal
    action: str
    position_id: str
    reservation_id: str
    quantity: Decimal | str
    price: Decimal | str
    notional_exposure: Decimal | str


@dataclass(frozen=True)
class IntentResult:
    accepted: bool
    reason: str
    origin: Origin | None = None
    action: str | None = None
    position_id: str | None = None
    reservation_id: str | None = None
    required_margin: Decimal = Decimal("0")


@dataclass(frozen=True)
class CoordinatorResult:
    intents: tuple[IntentResult, ...]


class DualStrategySignalCoordinator:
    """Route each strategy intent independently; never arbitrate signal direction."""

    def __init__(self, *, core_ledger, ai_ledger, risk_engine):
        if getattr(core_ledger, "strategy_id", None) != "CORE":
            raise ValueError("core_ledger must be the CORE StrategyLedger")
        if getattr(ai_ledger, "strategy_id", None) != "AI":
            raise ValueError("ai_ledger must be the AI StrategyLedger")
        core_path = Path(core_ledger.path).resolve()
        ai_path = Path(ai_ledger.path).resolve()
        risk_path = getattr(risk_engine, "path", None)
        if risk_path is None or core_path != ai_path or core_path != Path(risk_path).resolve():
            raise ValueError("Both ledgers and SharedRiskEngine must use the same durable database")
        self.core_ledger = core_ledger
        self.ai_ledger = ai_ledger
        self.risk_engine = risk_engine

    def _ledger(self, origin):
        if origin is Origin.CORE:
            return self.core_ledger
        if origin is Origin.AI:
            return self.ai_ledger
        raise ValueError("Unknown strategy origin")

    @staticmethod
    def _validate_intent(intent):
        if not isinstance(intent, StrategyIntent) or not isinstance(intent.signal, Signal):
            raise ValueError("INVALID_INTENT")
        signal = intent.signal
        if (not isinstance(signal.origin, Origin) or not isinstance(signal.side, Side)
            or type(signal.candle_close_ms) is not int
            or signal.candle_close_ms <= 0 or signal.candle_close_ms % CANDLE_MS
            or not isinstance(signal.signal_id, str) or not signal.signal_id.strip()
            or len(signal.signal_id) > 256):
            raise ValueError("INVALID_SIGNAL")
        if intent.action not in ("ENTRY", "DCA"):
            raise ValueError("INVALID_ACTION")
        for field, value in (("position_id", intent.position_id),
                             ("reservation_id", intent.reservation_id)):
            if not isinstance(value, str) or not value.strip() or len(value) > 256:
                raise ValueError(f"INVALID_{field.upper()}")
        quantity = _positive_decimal(intent.quantity, "quantity")
        price = _positive_decimal(intent.price, "price")
        exposure = _positive_decimal(intent.notional_exposure, "notional_exposure")
        if exposure < quantity * price:
            raise ValueError("NOTIONAL_BELOW_ORDER_VALUE")
        return quantity, price, exposure

    def route(self, intents, *, data_fresh, state_reconciled, kill_switch=False):
        """Admit each supplied intent separately and write it to its own ledger.

        The input order is preserved. Opposing CORE/AI directions are not
        compared or suppressed; shared collateral decides each admission.
        """
        if type(data_fresh) is not bool or type(state_reconciled) is not bool or type(kill_switch) is not bool:
            raise ValueError("Risk-state flags must be booleans")
        results = []
        for intent in intents:
            try:
                quantity, price, exposure = self._validate_intent(intent)
                ledger = self._ledger(intent.signal.origin)
                if intent.action == "DCA":
                    positions = [
                        position for position in ledger.snapshot().positions
                        if position.position_id == intent.position_id
                    ]
                    if len(positions) != 1:
                        results.append(self._rejected(intent, "POSITION_NOT_FOUND"))
                        continue
                    if positions[0].side != intent.signal.side.value:
                        results.append(self._rejected(intent, "DCA_SIDE_MISMATCH"))
                        continue

                portfolio_equity = (
                    self.core_ledger.snapshot().equity + self.ai_ledger.snapshot().equity
                )
                reserve = (
                    self.risk_engine.reserve_entry if intent.action == "ENTRY"
                    else self.risk_engine.reserve_dca
                )
                decision = reserve(
                    reservation_id=intent.reservation_id,
                    strategy_id=intent.signal.origin.value,
                    position_id=intent.position_id,
                    account_equity=portfolio_equity,
                    notional_exposure=exposure,
                    data_fresh=data_fresh,
                    state_reconciled=state_reconciled,
                    kill_switch=kill_switch,
                )
                if not decision.accepted:
                    results.append(self._rejected(intent, decision.reason, decision.required_margin))
                    continue

                try:
                    if intent.action == "ENTRY":
                        ledger.record_reserved_entry(
                            reservation_id=intent.reservation_id,
                            position_id=intent.position_id,
                            side=intent.signal.side.value,
                            quantity=quantity,
                            entry_price=price,
                        )
                    else:
                        ledger.record_reserved_dca(
                            reservation_id=intent.reservation_id,
                            position_id=intent.position_id,
                            quantity=quantity,
                            price=price,
                        )
                except Exception:
                    # Do not silently release a reservation after an uncertain
                    # ledger write; it must remain visible for reconciliation.
                    results.append(self._rejected(
                        intent, "LEDGER_WRITE_FAILED_RECONCILIATION_REQUIRED",
                        decision.required_margin,
                    ))
                    continue
                results.append(IntentResult(
                    True, "RISK_ADMITTED_AND_RECORDED", intent.signal.origin,
                    intent.action, intent.position_id, intent.reservation_id,
                    decision.required_margin,
                ))
            except (ValueError, TypeError, AttributeError) as exc:
                reason = str(exc) if str(exc) else "INVALID_INTENT"
                results.append(self._rejected(intent, reason))
        return CoordinatorResult(tuple(results))

    @staticmethod
    def _rejected(intent, reason, required_margin=Decimal("0")):
        signal = getattr(intent, "signal", None)
        origin = signal.origin if isinstance(signal, Signal) and isinstance(signal.origin, Origin) else None
        action = getattr(intent, "action", None)
        position_id = getattr(intent, "position_id", None)
        reservation_id = getattr(intent, "reservation_id", None)
        return IntentResult(
            False, reason, origin, action, position_id, reservation_id, required_margin
        )

    def reduce(self, *, strategy_id, position_id, quantity, realized_pnl, fees,
               kill_switch=False):
        """Apply an accounting reduction even while Kill Switch blocks increases."""
        if type(kill_switch) is not bool:
            return RiskDecision(False, "INVALID_RISK_STATE")
        core_snapshot = self.core_ledger.snapshot()
        ai_snapshot = self.ai_ledger.snapshot()
        decision = self.risk_engine.admit_reduction(
            strategy_id=strategy_id,
            position_id=position_id,
            quantity=quantity,
            core_snapshot=core_snapshot,
            ai_snapshot=ai_snapshot,
            kill_switch=kill_switch,
        )
        if not decision.accepted:
            return decision
        ledger = self.core_ledger if strategy_id == "CORE" else self.ai_ledger if strategy_id == "AI" else None
        if ledger is None:
            return RiskDecision(False, "INVALID_REDUCTION")
        try:
            ledger.record_reduction(
                position_id, quantity=quantity, realized_pnl=realized_pnl, fees=fees
            )
        except (ValueError, TypeError):
            return RiskDecision(False, "REDUCTION_WRITE_REJECTED")
        return decision
