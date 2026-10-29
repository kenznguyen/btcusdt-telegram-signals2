"""Exact primitive decisions from Android StrategyEngine.kt; parity research only.

This module does not simulate a complete trade lifecycle or place orders.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class StrategyParameters:
    leverage: float = 13.0
    rsi_length: int = 14
    dmi_length: int = 14
    adx_smoothing: int = 14
    h1_adx_entry: float = 20.0
    long_rsi_entry: float = 30.0
    short_rsi_entry: float = 70.0
    long_rsi_tp: float = 76.0
    short_rsi_tp: float = 24.0
    tp_roe: float = 5.0
    dca_roe: float = -20.0
    dca_adx: float = 45.0
    short_dca_rsi: float = 80.0
    long_dca_rsi: float = 20.0
    soft_sl_roe: float = -35.0
    emergency_sl_roe: float = -90.0
    soft_sl_adx: float = 35.0
    entry_margin_pct: float = 0.50
    dca_margin_ratio: float = 1.00
    fee_rate: float = 0.0005
    slippage_bps: float = 5.0


class StrategyRules:
    def __init__(self, params=None):
        self.p = params or StrategyParameters()

    def long_entry(self, previous_rsi, rsi, h1_plus, h1_minus, h1_adx):
        return h1_plus > h1_minus and h1_adx > self.p.h1_adx_entry and previous_rsi <= self.p.long_rsi_entry and rsi > self.p.long_rsi_entry

    def short_entry(self, previous_rsi, rsi, h1_plus, h1_minus, h1_adx):
        return h1_minus > h1_plus and h1_adx > self.p.h1_adx_entry and previous_rsi >= self.p.short_rsi_entry and rsi < self.p.short_rsi_entry

    def dca(self, side, roe, adx, rsi, previous_rsi):
        return (roe <= self.p.dca_roe and adx > self.p.dca_adx and
                ((rsi > self.p.long_dca_rsi and rsi > previous_rsi) if side == "LONG" else
                 (rsi < self.p.short_dca_rsi and rsi < previous_rsi)))

    def tp(self, side, rsi, roe):
        return ((rsi >= self.p.long_rsi_tp) if side == "LONG" else (rsi <= self.p.short_rsi_tp)) and roe >= self.p.tp_roe

    def roe(self, side, average, price):
        return ((price - average) if side == "LONG" else (average - price)) / average * self.p.leverage * 100

    def threshold_price(self, side, average, absolute_roe):
        move = abs(absolute_roe) / (100 * self.p.leverage)
        return average * (1 - move if side == "LONG" else 1 + move)

    def emergency(self, side, low, high, average):
        stop = self.threshold_price(side, average, abs(self.p.emergency_sl_roe))
        return low <= stop if side == "LONG" else high >= stop

    def soft(self, side, low, high, candle_open, close, prev_open, prev_close,
             h1_plus, h1_minus, h1_adx, average):
        stop = self.threshold_price(side, average, abs(self.p.soft_sl_roe))
        reversal = (h1_minus > h1_plus if side == "LONG" else h1_plus > h1_minus) and h1_adx > self.p.soft_sl_adx
        return ((low <= stop and reversal and candle_open > close and prev_close < prev_open)
                if side == "LONG" else
                (high >= stop and reversal and close > candle_open and prev_close > prev_open))

    @staticmethod
    def exit_priority(emergency, soft, tp):
        return "EMERGENCY SL" if emergency else "SOFT SL" if soft else "TAKE PROFIT" if tp else None

    def execution_fill(self, price, action):
        slip = max(0.0, self.p.slippage_bps) / 10000
        return price * (1 + slip if action.upper() == "BUY" else 1 - slip)

    def stop_fill(self, side, stop, opened):
        reference = min(opened, stop) if side == "LONG" else max(opened, stop)
        return self.execution_fill(reference, "SELL" if side == "LONG" else "BUY")


def compare_event_traces(kotlin_trace, python_trace, dataset_sha256):
    """No green result for absent traces, absent dataset hash or mismatched events."""
    if not isinstance(dataset_sha256, str) or not __import__("re").fullmatch(r"sha256:[0-9a-f]{64}", dataset_sha256):
        return {"parity_verified": False, "reason": "MISSING_DATASET_CHECKSUM"}
    if not isinstance(kotlin_trace, list) or not isinstance(python_trace, list):
        return {"parity_verified": False, "reason": "MISSING_TRACE"}
    if not kotlin_trace or not python_trace:
        return {"parity_verified": False, "reason": "EMPTY_TRACE"}
    for trace in (kotlin_trace, python_trace):
        if not all(isinstance(row, dict) and "kind" in row and "candleTime" in row for row in trace):
            return {"parity_verified": False, "reason": "INVALID_TRACE"}
    if kotlin_trace != python_trace:
        return {"parity_verified": False, "reason": "EVENT_MISMATCH"}
    return {"parity_verified": True, "reason": "EVENT_TRACE_MATCH"}
