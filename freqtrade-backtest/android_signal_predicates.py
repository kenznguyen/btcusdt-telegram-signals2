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
