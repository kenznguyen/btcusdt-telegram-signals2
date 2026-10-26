"""Offline, single-candle state transition matching Android StrategyEngine order.

Caller supplies indicators from CLOSED M15 and prior CLOSED H1 only. This is
not a Freqtrade strategy, and does not fetch candles or submit orders.
"""
from dataclasses import dataclass
from android_signal_predicates import (
    entry_side, entry_position, dca_signal, dca_position, roe_for,
    exit_reason, threshold_price, stop_fill_price, execution_fill_price,
    closed_trade_accounting,
)


@dataclass(frozen=True)
class ReplayState:
    balance: float = 100.0
    position: dict | None = None


def step(state, candle, previous_candle, indicators):
    """Return (new_state, event or None); at most one event per closed candle."""
    if not candle["closed"]:
        return state, None
    side = state.position["side"] if state.position else None
    if side is not None:
        pos = state.position
        roe = roe_for(side, pos["avg_entry"], candle["close"])
        reason = exit_reason(
            side, candle["low"], candle["high"], candle["open"], candle["close"],
            previous_candle["open"], previous_candle["close"],
            indicators.get("h1_plus_di"), indicators.get("h1_minus_di"),
            indicators.get("h1_adx"), pos["avg_entry"], indicators.get("rsi"), roe,
        )
        if reason is not None:
            if reason == "EMERGENCY_SL":
                stop = threshold_price(side, pos["avg_entry"], -90)
                fill = stop_fill_price(side, stop, candle["open"])
            elif reason == "SOFT_SL":
                stop = threshold_price(side, pos["avg_entry"], -35)
                fill = stop_fill_price(side, stop, candle["open"])
            else:
                fill = execution_fill_price(candle["close"], "SELL" if side == "LONG" else "BUY")
            accounting = closed_trade_accounting(
                side, pos["qty"], pos["avg_entry"], pos["entry_notional"], fill)
            balance = state.balance + accounting["net_pnl"]
            return ReplayState(balance, None), {
                "kind": reason, "side": side, "price": fill,
                "roe_pct": roe, "balance": balance, **accounting,
            }
        if (not pos["dca_used"] and
                all(indicators.get(key) is not None for key in ("adx", "rsi", "previous_rsi")) and
                dca_signal(side, roe, indicators["adx"], indicators["rsi"], indicators["previous_rsi"])):
            updated = dca_position(pos, state.balance, candle["close"])
            if updated != pos:
                return ReplayState(state.balance, updated), {
                    "kind": "DCA", "side": side, "price": execution_fill_price(
                        candle["close"], "BUY" if side == "LONG" else "SELL"),
                    "roe_pct": roe, "balance": state.balance,
                }
        return state, None

    if state.balance <= 0 or indicators.get("adx") is None:
        return state, None
    candidate = entry_side(
        indicators.get("previous_rsi"), indicators.get("rsi"),
        indicators.get("h1_plus_di"), indicators.get("h1_minus_di"),
        indicators.get("h1_adx"))
    if candidate is None:
        return state, None
    position = entry_position(state.balance, candidate, candle["close"], candle["timestamp_ms"])
    return ReplayState(state.balance, position), {
        "kind": "ENTRY", "side": candidate, "price": position["avg_entry"],
        "roe_pct": 0.0, "balance": state.balance,
    }
