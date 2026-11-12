"""Account-wide paper equity and reservation reconciliation."""

from contextlib import closing
from decimal import Decimal, localcontext
import sqlite3

from pipeline.values import number, stamp
from paper_execution import equity as equity_history


def _ledger_decimal(raw, *, signed=False):
    """Validate persisted ledger decimals without applying external-input scale limits."""
    if not isinstance(raw, str) or not 1 <= len(raw) <= 256:
        raise ValueError("Invalid persisted ledger amount")
    try:
        value = Decimal(raw)
    except (ArithmeticError, TypeError, ValueError):
        raise ValueError("Invalid persisted ledger amount") from None
    if (
        not value.is_finite()
        or not -200 <= value.as_tuple().exponent <= 200
        or value.adjusted() > 200
        or (not signed and value < 0)
    ):
        raise ValueError("Invalid persisted ledger amount")
    return value


def _account_ledger_totals(connection, mark, text):
    ledgers = connection.execute(
        """SELECT strategy_id,position_base,average_entry_price,realized_pnl_quote,
                  fees_quote,funding_quote FROM paper_strategy_ledgers
           WHERE account_id=1"""
    ).fetchall()
    expected = {"STRATEGY_CORE", "AI_FREQAI", "LEGACY_UNATTRIBUTED"}
    if {row[0] for row in ledgers} != expected:
        raise sqlite3.DatabaseError("ACCOUNT_RISK_LEDGER_SET_INVALID")

    realized = fees = funding = unrealized = Decimal(0)
    positions = {}
    for strategy_id, raw_qty, raw_avg, raw_pnl, raw_fee, raw_funding in ledgers:
        try:
            qty = _ledger_decimal(raw_qty, signed=True)
            average = _ledger_decimal(raw_avg)
            pnl = _ledger_decimal(raw_pnl, signed=True)
            fee = _ledger_decimal(raw_fee)
            fund = _ledger_decimal(raw_funding, signed=True)
        except ValueError:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_LEDGER_VALUE_INVALID") from None
        if (qty == 0 and average != 0) or (qty != 0 and average <= 0) or fee < 0:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_POSITION_INCONSISTENT")
        unrealized_pnl = qty * (mark - average) if qty else Decimal(0)
        realized += pnl
        fees += fee
        funding += fund
        unrealized += unrealized_pnl
        positions[strategy_id] = {
            "positionBase": text(qty), "averageEntryPrice": text(average),
            "unrealizedPnlQuote": text(unrealized_pnl),
        }
        if strategy_id == "LEGACY_UNATTRIBUTED" and qty != 0:
            raise ValueError("LEGACY_UNATTRIBUTED_EXPOSURE")

    legacy_pnl = legacy_fees = Decimal(0)
    for kind, raw_amount in connection.execute(
        """SELECT adjustment_type,amount_quote FROM paper_account_adjustments
           WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'"""
    ):
        try:
            amount = number(raw_amount, signed=True)
        except ValueError:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_LEGACY_ADJUSTMENT_INVALID") from None
        if kind == "LEGACY_REALIZED_PNL":
            legacy_pnl += amount
        elif kind == "LEGACY_FEES" and amount >= 0:
            legacy_fees += amount
        else:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_LEGACY_ADJUSTMENT_INVALID")

    return realized, fees, funding, unrealized, legacy_pnl, legacy_fees, positions


def _active_reservation_totals(connection):
    reserved_notional = reserved_margin = Decimal(0)
    for row in connection.execute(
        """SELECT status,remaining_notional_quote,remaining_margin_quote,
                  reserved_notional_quote,reserved_margin_quote
           FROM paper_risk_reservations WHERE account_id=1"""
    ):
        status, raw_notional, raw_margin, raw_original_notional, raw_original_margin = row
        try:
            remaining_notional = _ledger_decimal(raw_notional)
            remaining_margin = _ledger_decimal(raw_margin)
            original_notional = _ledger_decimal(raw_original_notional)
            original_margin = _ledger_decimal(raw_original_margin)
        except ValueError:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_RESERVATION_INVALID") from None
        if remaining_notional > original_notional or remaining_margin > original_margin:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_RESERVATION_EXCEEDS_ORIGINAL")
        if status in ("ACTIVE", "PARTIAL"):
            reserved_notional += remaining_notional
            reserved_margin += remaining_margin
        elif status not in ("RELEASED", "CONSUMED", "EXPIRED"):
            raise sqlite3.DatabaseError("ACCOUNT_RISK_RESERVATION_STATUS_INVALID")
    return reserved_notional, reserved_margin


def record_account_mark(
    ledger, mark_price, candle_close_ms, observed_at_ms, dataset_version,
    initial_capital="100",
):
    """Atomically reconcile one account-wide mark across all strategy ledgers."""
    # Late import avoids a cycle because PaperLedger delegates to this module.
    from paper_execution.ledger import (
        _dual_ledger_migrations_ready, _funding_provenance_ready,
        read_account_risk_snapshot, stored_state, text,
    )
    if ledger.strategy_id != "MANUAL":
        raise ValueError("ACCOUNT_MARK_REQUIRES_ACCOUNT_SCOPE")
    mark = number(str(mark_price))
    candle_at, observed_at = stamp(candle_close_ms), stamp(observed_at_ms)
    if mark <= 0 or candle_at > observed_at or observed_at-candle_at > 30*60_000:
        raise ValueError("Invalid or stale account mark")
    if not isinstance(dataset_version, str) or not dataset_version.strip():
        raise ValueError("ACCOUNT_MARK_DATASET_VERSION_REQUIRED")

    with closing(ledger.connect()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        if not _dual_ledger_migrations_ready(connection):
            position, average, realized, fees, _ = stored_state(connection)
            return equity_history.record(
                connection, initial_capital=initial_capital, position=position, average=average,
                realized=realized, fees=fees, mark_price=mark,
                candle_close_ms=candle_at, observed_at_ms=observed_at,
                dataset_version=dataset_version,
            )

        risk = connection.execute(
            """SELECT high_water_mark_quote,daily_baseline_utc_day_ms,
                      daily_baseline_equity_quote,last_mark_price,mark_observed_at_ms,
                      risk_ready,unavailable_reason
               FROM paper_account_risk_state WHERE account_id=1"""
        ).fetchone()
        account = connection.execute(
            "SELECT initial_capital FROM paper_accounts WHERE account_id=1"
        ).fetchone()
        cutover = connection.execute(
            """SELECT funding_coverage_start_at_ms,funding_coverage_end_at_ms,
                      mark_observed_at_ms FROM paper_account_equity_cutovers
               WHERE account_id=1 LIMIT 1"""
        ).fetchone()
        if risk is None or account is None:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_STATE_MISSING_OR_CORRUPT")
        if number(account[0]) != number(str(initial_capital)):
            raise ValueError("PAPER_INITIAL_CAPITAL_CHANGED; explicit account migration required")
        previous_mark_at = stamp(risk[4]) if risk[4] is not None else None
        if previous_mark_at is not None and observed_at < previous_mark_at:
            raise ValueError("OUT_OF_ORDER_ACCOUNT_MARK")
        if type(risk[5]) is not int or risk[5] not in (0, 1):
            raise sqlite3.DatabaseError("ACCOUNT_RISK_STATE_MISSING_OR_CORRUPT")
        utc_day = observed_at // 86_400_000 * 86_400_000
        if risk[1] is not None and (
            type(risk[1]) is not int or risk[1] != utc_day
        ):
            raise ValueError("ACCOUNT_RISK_DAILY_BASELINE_UNAVAILABLE")
        if cutover and risk[1] is None:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_DAILY_BASELINE_UNAVAILABLE")

        with localcontext() as context:
            context.prec = 80
            (
                realized, fees, funding, unrealized, legacy_pnl, legacy_fees, positions,
            ) = _account_ledger_totals(connection, mark, text)
            reserved_notional, reserved_margin = _active_reservation_totals(connection)
            equity = (
                number(account[0]) + realized + legacy_pnl + unrealized
                - fees - legacy_fees - funding
            )
        if not equity.is_finite() or equity <= 0:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_EQUITY_INVALID")
        try:
            hwm = equity if risk[0] is None else number(risk[0])
        except ValueError:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_EQUITY_INVALID") from None
        if hwm <= 0:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_EQUITY_INVALID")

        funding_ready = bool(cutover) and _funding_provenance_ready(
            connection, cutover[0], cutover[1], observed_at, observed_at
        )
        risk_ready = (
            bool(risk[5]) and funding_ready and bool(cutover)
            and risk[1] == utc_day and risk[2] is not None
        )
        unavailable = None if risk_ready else risk[6]
        if not risk_ready and not cutover:
            unavailable = "ACCOUNT_EQUITY_CUTOVER_NOT_ESTABLISHED"
        elif not risk_ready and not funding_ready:
            unavailable = "FUNDING_PROVENANCE_INCOMPLETE"
        elif not risk_ready and not unavailable:
            unavailable = "ACCOUNT_RISK_NOT_READY"

        connection.execute(
            """UPDATE paper_account_risk_state
               SET last_equity_quote=?,high_water_mark_quote=?,last_mark_price=?,
                   mark_observed_at_ms=?,mark_candle_close_ms=?,dataset_version=?,
                   risk_ready=?,unavailable_reason=?,updated_at_ms=?,version=version+1
               WHERE account_id=1""",
            (text(equity), text(max(hwm, equity)), text(mark), observed_at,
             candle_at, dataset_version, int(risk_ready), unavailable, observed_at),
        )
        ledger.audit(connection, observed_at, "ACCOUNT_MARK", {
            "markPrice": text(mark), "candleCloseMs": candle_at,
            "datasetVersion": dataset_version, "accountEquityQuote": text(equity),
            "reservedNotionalQuote": text(reserved_notional),
            "reservedMarginQuote": text(reserved_margin), "riskReady": risk_ready,
        })
        if not cutover or risk[1] is None:
            return {
                "mode": "PAPER", "liveTradingSupported": False, "available": True,
                "riskReady": False, "unavailableReason": unavailable,
                "accountEquityQuote": text(equity), "markPrice": text(mark),
                "markObservedAtMs": observed_at, "datasetVersion": dataset_version,
                "positions": positions, "reservedNotionalQuote": text(reserved_notional),
                "reservedMarginQuote": text(reserved_margin), "updatedAtMs": observed_at,
            }
    return read_account_risk_snapshot(ledger.path, now_ms=observed_at)
