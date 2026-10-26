"""Exact RSI/DMI/ADX smoothing rules copied from Android StrategyEngine.

No third-party TA implementation: Android seeds Wilder RMA from the first
N non-null observations, then carries its value through missing observations.
"""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class IndicatorConfig:
    rsi_length: int = 14
    dmi_length: int = 14
    adx_smoothing: int = 14


def rma(values, length):
    if length < 1:
        raise ValueError("RMA length must be positive")
    result = [None] * len(values)
    valid = [i for i, value in enumerate(values) if value is not None]
    if len(valid) < length:
        return result
    first = valid[length - 1]
    previous = sum(values[i] for i in valid[:length]) / length
    result[first] = previous
    for i in range(first + 1, len(values)):
        if values[i] is not None:
            previous = (previous * (length - 1) + values[i]) / length
        result[i] = previous
    return result


def indicator_series(candles, config=IndicatorConfig()):
    if not candles:
        return []
    if any(n < 1 for n in (config.rsi_length, config.dmi_length, config.adx_smoothing)):
        raise ValueError("Indicator lengths must be positive")
    for candle in candles:
        if any(not isfinite(candle[key]) for key in ("high", "low", "close")):
            raise ValueError("Non-finite OHLC")
        if candle["high"] < candle["low"]:
            raise ValueError("Invalid OHLC range")
    n = len(candles)
    delta = [None] + [candles[i]["close"] - candles[i-1]["close"] for i in range(1, n)]
    gains = [None if d is None else max(d, 0.0) for d in delta]
    losses = [None if d is None else max(-d, 0.0) for d in delta]
    avg_gain = rma(gains, config.rsi_length)
    avg_loss = rma(losses, config.rsi_length)
    rsi = []
    for gain, loss in zip(avg_gain, avg_loss):
        if gain is None or loss is None:
            rsi.append(None)
        elif loss == 0 and gain > 0:
            rsi.append(100.0)
        elif loss == 0 and gain == 0:
            rsi.append(50.0)
        else:
            rsi.append(100.0 - 100.0 / (1.0 + gain / loss))
    tr, plus_dm, minus_dm = [], [], []
    for i, candle in enumerate(candles):
        if i == 0:
            tr.append(candle["high"] - candle["low"])
            plus_dm.append(0.0)
            minus_dm.append(0.0)
            continue
        previous = candles[i - 1]
        tr.append(max(candle["high"] - candle["low"],
                      abs(candle["high"] - previous["close"]),
                      abs(candle["low"] - previous["close"])))
        up = candle["high"] - previous["high"]
        down = previous["low"] - candle["low"]
        plus_dm.append(up if up > down and up > 0 else 0.0)
        minus_dm.append(down if down > up and down > 0 else 0.0)
    atr = rma(tr, config.dmi_length)
    smooth_plus = rma(plus_dm, config.dmi_length)
    smooth_minus = rma(minus_dm, config.dmi_length)
    plus_di = [None if a is None or p is None or a == 0 else 100.0 * p / a
               for a, p in zip(atr, smooth_plus)]
    minus_di = [None if a is None or m is None or a == 0 else 100.0 * m / a
                for a, m in zip(atr, smooth_minus)]
    dx = [None if p is None or m is None or p + m == 0 else
          100.0 * abs(p - m) / (p + m) for p, m in zip(plus_di, minus_di)]
    adx = rma(dx, config.adx_smoothing)
    return [{"rsi": rsi[i], "adx": adx[i],
             "plus_di": plus_di[i], "minus_di": minus_di[i]} for i in range(n)]
