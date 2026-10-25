"""Independent, offline signal predicates transcribed from Android StrategyEngine.

This module deliberately does not place orders or claim Freqtrade parity.
The stateful replay (candle alignment, DCA accounting and fills) remains pending.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class AndroidSignalThresholds:
    h1_adx_entry: float = 20.0
    long_rsi_entry: float = 30.0
    short_rsi_entry: float = 70.0


def entry_side(previous_rsi, current_rsi, h1_plus_di, h1_minus_di, h1_adx,
               config=AndroidSignalThresholds()):
    """Exactly the Android longEntrySignal/shortEntrySignal comparisons."""
    if any(value is None for value in (
        previous_rsi, current_rsi, h1_plus_di, h1_minus_di, h1_adx
    )):
        return None
    if (h1_plus_di > h1_minus_di and h1_adx > config.h1_adx_entry
            and previous_rsi <= config.long_rsi_entry
            and current_rsi > config.long_rsi_entry):
        return "LONG"
    if (h1_minus_di > h1_plus_di and h1_adx > config.h1_adx_entry
            and previous_rsi >= config.short_rsi_entry
            and current_rsi < config.short_rsi_entry):
        return "SHORT"
    return None


@dataclass(frozen=True)
class AndroidExitThresholds:
    long_rsi_tp: float = 76.0
    short_rsi_tp: float = 24.0
    tp_roe: float = 5.0
    dca_roe: float = -20.0
    dca_adx: float = 45.0
    long_dca_rsi: float = 20.0
    short_dca_rsi: float = 80.0
    soft_sl_roe: float = -35.0
    emergency_sl_roe: float = -90.0
    soft_sl_adx: float = 35.0
    leverage: float = 13.0


def take_profit_signal(side, rsi, roe_pct, config=AndroidExitThresholds()):
    if side not in ("LONG", "SHORT"):
        raise ValueError("Invalid side")
    return (rsi >= config.long_rsi_tp if side == "LONG" else
            rsi <= config.short_rsi_tp) and roe_pct >= config.tp_roe


def dca_signal(side, roe_pct, adx, rsi, previous_rsi,
               config=AndroidExitThresholds()):
    if side not in ("LONG", "SHORT"):
        raise ValueError("Invalid side")
    return (roe_pct <= config.dca_roe and adx > config.dca_adx and
            (rsi > config.long_dca_rsi and rsi > previous_rsi if side == "LONG"
             else rsi < config.short_dca_rsi and rsi < previous_rsi))


def threshold_price(side, avg_entry, abs_roe, config=AndroidExitThresholds()):
    if side not in ("LONG", "SHORT"):
        raise ValueError("Invalid side")
    move = abs(abs_roe) / (100.0 * config.leverage)
    return avg_entry * (1.0 - move if side == "LONG" else 1.0 + move)


def emergency_stop_triggered(side, low, high, avg_entry,
                             config=AndroidExitThresholds()):
    threshold = threshold_price(side, avg_entry, config.emergency_sl_roe, config)
    return low <= threshold if side == "LONG" else high >= threshold


def soft_stop_triggered(side, low, high, candle_open, candle_close,
                        previous_open, previous_close, h1_plus_di, h1_minus_di,
                        h1_adx, avg_entry, config=AndroidExitThresholds()):
    threshold = threshold_price(side, avg_entry, config.soft_sl_roe, config)
    reversal = ((h1_minus_di > h1_plus_di if side == "LONG"
                 else h1_plus_di > h1_minus_di) and h1_adx > config.soft_sl_adx)
    if side == "LONG":
        return (low <= threshold and reversal and candle_open > candle_close
                and previous_close < previous_open)
    return (high >= threshold and reversal and candle_close > candle_open
            and previous_close > previous_open)


@dataclass(frozen=True)
class AndroidExecutionConfig:
    leverage: float = 13.0
    slippage_bps: float = 5.0
    fee_rate: float = 0.0005


def roe_for(side, avg_entry, price, config=AndroidExecutionConfig()):
    if side not in ("LONG", "SHORT"):
        raise ValueError("Invalid side")
    if avg_entry <= 0:
        raise ValueError("Invalid entry price")
    return ((price - avg_entry) if side == "LONG" else
            (avg_entry - price)) / avg_entry * config.leverage * 100.0


def execution_fill_price(price, action, config=AndroidExecutionConfig()):
    if price <= 0:
        raise ValueError("Invalid price")
    if action.upper() not in ("BUY", "SELL"):
        raise ValueError("Invalid action")
    slip = max(0.0, config.slippage_bps) / 10000.0
    return price * (1.0 + slip if action.upper() == "BUY" else 1.0 - slip)


def stop_fill_price(side, stop, candle_open, config=AndroidExecutionConfig()):
    if side not in ("LONG", "SHORT"):
        raise ValueError("Invalid side")
    reference = min(candle_open, stop) if side == "LONG" else max(candle_open, stop)
    return execution_fill_price(reference, "SELL" if side == "LONG" else "BUY", config)


def closed_trade_accounting(side, quantity, avg_entry, entry_notional,
                            exit_price, config=AndroidExecutionConfig()):
    """Same gross, round-trip fee and net PnL formulas as StrategyEngine."""
    if side not in ("LONG", "SHORT"):
        raise ValueError("Invalid side")
    if quantity <= 0 or avg_entry <= 0 or entry_notional <= 0 or exit_price <= 0:
        raise ValueError("Invalid trade accounting")
    gross = ((exit_price - avg_entry) if side == "LONG" else
             (avg_entry - exit_price)) * quantity
    fees = (entry_notional + exit_price * quantity) * config.fee_rate
    return {"gross": gross, "fees": fees, "net_pnl": gross - fees}
