"""Pure deterministic replay orchestration and equity reconciliation."""

from decimal import Decimal, DecimalException

from paper_execution.account_history import (
    STRATEGIES,
    _replay_decimal,
    _replay_text,
    replay_ledger_events,
)


def _amount(value, code, *, positive=False, nonnegative=False, signed=False):
    return _replay_decimal(
        value, code, positive=positive, nonnegative=nonnegative, signed=signed
    )


def _sum(values):
    return sum(values, Decimal(0))


def reconcile_daily_equity_replay(inputs):
    """Replay each ledger independently and reconcile cutover and boundary equity.

    This function is pure: it never reads or writes a database and never mutates
    the loader-owned input object.
    """
    if not isinstance(inputs, dict):
        raise ValueError("ACCOUNT_HISTORY_REPLAY_INPUT_INVALID")
    boundary = inputs.get("utc_day_ms")
    cutover_at = inputs.get("cutover_snapshot_at_ms")
    if type(boundary) is not int or boundary % 86_400_000:
        raise ValueError("ACCOUNT_HISTORY_UTC_DAY_INVALID")
    if type(cutover_at) is not int or not 0 <= cutover_at < boundary:
        raise ValueError("ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID")

    ledgers = inputs.get("ledgers")
    if not isinstance(ledgers, dict) or set(ledgers) != STRATEGIES:
        raise ValueError("ACCOUNT_HISTORY_CUTOVER_LEDGER_SET_INVALID")
    cutover = inputs.get("cutover")
    mark = inputs.get("market_mark")
    if not isinstance(cutover, dict) or not isinstance(mark, dict):
        raise ValueError("ACCOUNT_HISTORY_REPLAY_INPUT_INVALID")

    cutover_mark = _amount(
        cutover.get("mark_price"), "ACCOUNT_EQUITY_CUTOVER_RECONCILIATION_MISMATCH",
        positive=True,
    )
    cutover_candle = cutover.get("mark_candle_close_ms")
    cutover_observed = cutover.get("mark_observed_at_ms")
    if (type(cutover_candle) is not int or cutover_candle > cutover_at
            or type(cutover_observed) is not int or cutover_observed < cutover_candle):
        raise ValueError("ACCOUNT_EQUITY_CUTOVER_RECONCILIATION_MISMATCH")

    boundary_mark_at = mark.get("effective_at_ms")
    boundary_candle = mark.get("candle_close_ms")
    if (boundary_mark_at != boundary or boundary_candle != boundary
            or mark.get("quality_status") != "VERIFIED"):
        raise ValueError("ACCOUNT_HISTORY_BOUNDARY_MARK_INVALID")
    boundary_mark = _amount(
        mark.get("mark_price"), "ACCOUNT_HISTORY_BOUNDARY_MARK_INVALID", positive=True
    )

    initial_capital = _amount(
        cutover.get("initial_capital_quote"),
        "ACCOUNT_EQUITY_CUTOVER_RECONCILIATION_MISMATCH", positive=True,
    )
    cutover_equity = _amount(
        cutover.get("account_equity_quote"),
        "ACCOUNT_EQUITY_CUTOVER_RECONCILIATION_MISMATCH", positive=True,
    )
    expected_cutover_equity = _amount(
        cutover.get("expected_account_equity_quote"),
        "ACCOUNT_EQUITY_CUTOVER_RECONCILIATION_MISMATCH", positive=True,
    )
    declared_realized = _amount(
        cutover.get("reconciled_realized_pnl_quote"),
        "ACCOUNT_EQUITY_CUTOVER_RECONCILIATION_MISMATCH", signed=True,
    )
    declared_fees = _amount(
        cutover.get("reconciled_fees_quote"),
        "ACCOUNT_EQUITY_CUTOVER_RECONCILIATION_MISMATCH", nonnegative=True,
    )
    declared_funding = _amount(
        cutover.get("reconciled_funding_quote"),
        "ACCOUNT_EQUITY_CUTOVER_RECONCILIATION_MISMATCH", signed=True,
    )

    cutover_realized = []
    cutover_fees = []
    cutover_funding = []
    cutover_unrealized = []
    for strategy_id in sorted(STRATEGIES):
        entry = ledgers[strategy_id]
        if not isinstance(entry, dict) or not isinstance(entry.get("snapshot"), dict):
            raise ValueError("ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID")
        snapshot = entry["snapshot"]
        if snapshot.get("snapshot_at_ms") != cutover_at:
            raise ValueError("ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID")
        position = _amount(
            snapshot.get("position_base"), "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID",
            signed=True,
        )
        average = _amount(
            snapshot.get("average_entry_price"),
            "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID", nonnegative=True,
        )
        if (position == 0 and average != 0) or (position != 0 and average <= 0):
            raise ValueError("ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID")
        realized = _amount(
            snapshot.get("realized_pnl_quote"),
            "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID", signed=True,
        )
        fees = _amount(
            snapshot.get("fees_quote"),
            "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID", nonnegative=True,
        )
        funding = _amount(
            snapshot.get("funding_quote"),
            "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID", signed=True,
        )
        cutover_realized.append(realized)
        cutover_fees.append(fees)
        cutover_funding.append(funding)
        cutover_unrealized.append(position * (cutover_mark - average))

    if (_sum(cutover_realized) != declared_realized
            or _sum(cutover_fees) != declared_fees
            or _sum(cutover_funding) != declared_funding):
        raise ValueError("ACCOUNT_EQUITY_CUTOVER_RECONCILIATION_MISMATCH")
    calculated_cutover_equity = (
        initial_capital + _sum(cutover_realized) + _sum(cutover_unrealized)
        - _sum(cutover_fees) - _sum(cutover_funding)
    )
    if calculated_cutover_equity != cutover_equity or cutover_equity != expected_cutover_equity:
        raise ValueError("ACCOUNT_EQUITY_CUTOVER_RECONCILIATION_MISMATCH")

    replayed = {}
    realized_values = []
    unrealized_values = []
    fee_values = []
    funding_values = []
    for strategy_id in sorted(STRATEGIES):
        entry = ledgers[strategy_id]
        execution_watermark = entry.get("coverage_watermark_at_ms")
        funding_watermark = inputs.get("funding_coverage_watermark_at_ms")
        if type(execution_watermark) is not int or type(funding_watermark) is not int:
            raise ValueError("ACCOUNT_HISTORY_COVERAGE_WATERMARK_INVALID")
        watermark = min(execution_watermark, funding_watermark)
        result = replay_ledger_events(
            entry["snapshot"],
            entry.get("execution_events"),
            entry.get("funding_events"),
            boundary_ms=boundary,
            coverage_watermark_at_ms=watermark,
        )
        position = Decimal(result["position_base"])
        average = Decimal(result["average_entry_price"])
        realized = Decimal(result["realized_pnl_quote"])
        fees = Decimal(result["fees_quote"])
        funding = Decimal(result["funding_quote"])
        unrealized = position * (boundary_mark - average)
        replayed[strategy_id] = {
            **result,
            "unrealized_pnl_quote": _replay_text(unrealized),
        }
        realized_values.append(realized)
        unrealized_values.append(unrealized)
        fee_values.append(fees)
        funding_values.append(funding)

    realized_total = _sum(realized_values)
    unrealized_total = _sum(unrealized_values)
    fees_total = _sum(fee_values)
    funding_total = _sum(funding_values)
    equity = (
        initial_capital + realized_total + unrealized_total
        - fees_total - funding_total
    )
    if equity <= 0:
        raise ValueError("ACCOUNT_HISTORY_REPLAY_EQUITY_INVALID")

    return {
        "cutover_id": cutover_id if (cutover_id := inputs.get("cutover_id")) else
            (_ for _ in ()).throw(ValueError("ACCOUNT_EQUITY_CUTOVER_REQUIRED")),
        "boundary_ms": boundary,
        "boundary_mark_id": mark.get("mark_id"),
        "boundary_mark_price": _replay_text(boundary_mark),
        "ledgers": replayed,
        "initial_capital_quote": _replay_text(initial_capital),
        "realized_pnl_quote": _replay_text(realized_total),
        "unrealized_pnl_quote": _replay_text(unrealized_total),
        "fees_quote": _replay_text(fees_total),
        "funding_quote": _replay_text(funding_total),
        "equity_quote": _replay_text(equity),
    }
