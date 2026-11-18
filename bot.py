"""Reusable RSI/ADX/Smart-DCA strategy rules; no Telegram, dashboard or runtime entrypoint."""

import os

import numpy as np
import pandas as pd

LEVERAGE = float(os.getenv("LEVERAGE", "13"))
RSI_LEN = int(os.getenv("RSI_LENGTH", "14"))
DMI_LEN = int(os.getenv("DMI_LENGTH", "14"))
ADX_SMOOTH = int(os.getenv("ADX_SMOOTHING", "14"))
H1_ADX_ENTRY = float(os.getenv("H1_ADX_ENTRY", "20"))
LONG_RSI_ENTRY = float(os.getenv("LONG_RSI_ENTRY", "30"))
SHORT_RSI_ENTRY = float(os.getenv("SHORT_RSI_ENTRY", "70"))
LONG_RSI_TP = float(os.getenv("LONG_RSI_TP", "76"))
SHORT_RSI_TP = float(os.getenv("SHORT_RSI_TP", "24"))
TP_ROE = float(os.getenv("TP_ROE", "5"))
DCA_ROE = float(os.getenv("DCA_ROE", "-20"))
DCA_ADX = float(os.getenv("DCA_ADX", "45"))
SHORT_DCA_RSI = float(os.getenv("SHORT_DCA_RSI", "80"))
LONG_DCA_RSI = float(os.getenv("LONG_DCA_RSI", "20"))
SOFT_SL_ROE = float(os.getenv("SOFT_SL_ROE", "-35"))
EMERGENCY_SL_ROE = float(os.getenv("EMERGENCY_SL_ROE", "-90"))
SOFT_SL_ADX = float(os.getenv("SOFT_SL_ADX", "35"))
SLIPPAGE_BPS = float(os.getenv("SLIPPAGE_BPS", "5"))

def rma(series, length):
    """Wilder RMA with an SMA seed, close to Pine ta.rma()."""
    x = pd.Series(series, dtype="float64")
    out = pd.Series(np.nan, index=x.index, dtype="float64")
    valid = x.dropna()
    if len(valid) < length:
        return out
    first_pos = valid.index[length - 1]
    seed = x.loc[valid.index[:length]].mean()
    out.loc[first_pos] = seed
    alpha = 1.0 / length
    started = False
    prev = np.nan
    for idx in x.index:
        val = x.loc[idx]
        if idx == first_pos:
            prev = seed
            started = True
        elif started:
            if pd.isna(val):
                out.loc[idx] = prev
            else:
                prev = (prev * (length - 1) + val) / length
                out.loc[idx] = prev
    return out

def add_indicators(df):
    d = df.copy()
    close = d["close"]
    prev_close = close.shift(1)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = rma(gain, RSI_LEN)
    avg_loss = rma(loss, RSI_LEN)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    d["rsi"] = 100 - (100 / (1 + rs))
    d.loc[(avg_loss == 0) & (avg_gain > 0), "rsi"] = 100
    d.loc[(avg_loss == 0) & (avg_gain == 0), "rsi"] = 50

    high, low = d["high"], d["low"]
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=d.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=d.index)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    atr = rma(tr, DMI_LEN)
    plus_di = 100 * rma(plus_dm, DMI_LEN) / atr.replace(0, np.nan)
    minus_di = 100 * rma(minus_dm, DMI_LEN) / atr.replace(0, np.nan)
    denom = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / denom
    d["plus_di"] = plus_di
    d["minus_di"] = minus_di
    d["adx"] = rma(dx, ADX_SMOOTH)
    return d

def roe_for(side, avg_entry, close):
    if not side or avg_entry <= 0:
        return None
    if side == "LONG":
        return ((close - avg_entry) / avg_entry) * LEVERAGE * 100
    return ((avg_entry - close) / avg_entry) * LEVERAGE * 100

def entry_signals(previous_rsi, rsi, h1_plus_di, h1_minus_di, h1_adx):
    """Canonical M15 RSI-cross entry rules with the last fully closed H1 trend."""
    h1_bull = h1_plus_di > h1_minus_di and h1_adx > H1_ADX_ENTRY
    h1_bear = h1_minus_di > h1_plus_di and h1_adx > H1_ADX_ENTRY
    return (
        h1_bull and previous_rsi <= LONG_RSI_ENTRY and rsi > LONG_RSI_ENTRY,
        h1_bear and previous_rsi >= SHORT_RSI_ENTRY and rsi < SHORT_RSI_ENTRY,
    )

def take_profit_signal(side, rsi, roe):
    return ((side == "LONG" and rsi >= LONG_RSI_TP) or
            (side == "SHORT" and rsi <= SHORT_RSI_TP)) and roe is not None and roe >= TP_ROE

def dca_signal(side, roe, adx, rsi, previous_rsi):
    if roe > DCA_ROE or adx <= DCA_ADX:
        return False
    if side == "LONG":
        return rsi > LONG_DCA_RSI and rsi > previous_rsi
    if side == "SHORT":
        return rsi < SHORT_DCA_RSI and rsi < previous_rsi
    return False

def emergency_stop_triggered(side, low, high, avg_entry):
    threshold = threshold_price(side, avg_entry, abs(EMERGENCY_SL_ROE))
    return (low <= threshold) if side == "LONG" else (high >= threshold)

def soft_stop_triggered(side, low, high, candle_open, candle_close,
                        previous_open, previous_close, h1_plus_di, h1_minus_di,
                        h1_adx, avg_entry):
    threshold = threshold_price(side, avg_entry, abs(SOFT_SL_ROE))
    reversal = ((h1_minus_di > h1_plus_di) if side == "LONG" else
                (h1_plus_di > h1_minus_di)) and h1_adx > SOFT_SL_ADX
    two_bear = candle_open > candle_close and previous_close < previous_open
    two_bull = candle_close > candle_open and previous_close > previous_open
    return ((low <= threshold and reversal and two_bear) if side == "LONG" else
            (high >= threshold and reversal and two_bull))

def threshold_price(side, avg_entry, abs_roe):
    move = abs(abs_roe) / (100.0 * LEVERAGE)
    return avg_entry * (1.0 - move) if side == "LONG" else avg_entry * (1.0 + move)

def execution_fill_price(reference_price, action):
    """Estimated market fill after adverse slippage; not an exchange-confirmed fill."""
    slip = max(0.0, SLIPPAGE_BPS) / 10000.0
    return float(reference_price) * (1.0 + slip if action.upper() == "BUY" else 1.0 - slip)

def stop_fill_price(side, stop_price, candle_open):
    """Conservative stop-market estimate: gap-through fills at open, otherwise at stop; then adverse slippage."""
    side = str(side).upper()
    stop_price = float(stop_price)
    candle_open = float(candle_open)
    if side == "LONG":
        reference = candle_open if candle_open <= stop_price else stop_price
        return execution_fill_price(reference, "SELL")
    if side == "SHORT":
        reference = candle_open if candle_open >= stop_price else stop_price
        return execution_fill_price(reference, "BUY")
    raise ValueError(f"Unsupported position side: {side}")
