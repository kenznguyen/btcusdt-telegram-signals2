"""Independent BTCUSDT M5 scalping signal scanner with a closed-M15 trend filter.

Signal-only: never places exchange orders. State is stored separately from bot.py.
"""
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests

SYMBOL = "BTC-USDT-SWAP"
LEVERAGE = float(os.getenv("SCALP_LEVERAGE", "13"))
RSI_LENGTH = int(os.getenv("SCALP_RSI_LENGTH", "14"))
DMI_LENGTH = int(os.getenv("SCALP_DMI_LENGTH", "14"))
ADX_SMOOTHING = int(os.getenv("SCALP_ADX_SMOOTHING", "14"))
M15_ADX_MIN = float(os.getenv("SCALP_M15_ADX_MIN", "20"))
M5_ADX_MIN = float(os.getenv("SCALP_M5_ADX_MIN", "18"))
TP_ROE = float(os.getenv("SCALP_TP_ROE", "3"))
SOFT_SL_ROE = float(os.getenv("SCALP_SOFT_SL_ROE", "-35"))
HARD_SL_ROE = float(os.getenv("SCALP_HARD_SL_ROE", "-90"))
FEE_RATE = float(os.getenv("SCALP_TAKER_FEE_RATE", "0.0005"))
STATE_FILE = "scalping_state.json"
API_URL = "https://www.okx.com/api/v5/market/history-candles"


def fetch_closed_candles(bar, limit=300):
    rows = []
    after = None
    duration = pd.Timedelta(minutes=5 if bar == "5m" else 15)
    while len(rows) < limit:
        params = {"instId": SYMBOL, "bar": bar, "limit": str(min(300, limit - len(rows)))}
        if after is not None:
            params["after"] = after
        response = requests.get(API_URL, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != "0":
            raise RuntimeError(f"OKX API error: {payload.get('msg')}")
        batch = payload.get("data", [])
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < 2 or len(rows) >= limit:
            break
        after = batch[-1][0]

    if not rows:
        raise RuntimeError(f"No OKX candles returned for {bar}")
    unique = {str(row[0]): row for row in rows}
    df = pd.DataFrame(sorted(unique.values(), key=lambda x: int(x[0])),
                      columns=["open_time", "open", "high", "low", "close",
                               "volume_contracts", "volume", "quote_volume", "confirm"])
    for col in ("open", "high", "low", "close"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["open_time"] = pd.to_datetime(pd.to_numeric(df["open_time"]), unit="ms", utc=True)
    df["close_time"] = df["open_time"] + duration
    now = pd.Timestamp.now(tz="UTC")
    df = df[(df["confirm"].astype(str) == "1") & (df["close_time"] <= now)].copy()
    return df.tail(limit).reset_index(drop=True)


def rma(series, length):
    x = pd.Series(series, dtype="float64")
    out = pd.Series(np.nan, index=x.index, dtype="float64")
    valid = x.dropna()
    if len(valid) < length:
        return out
    first = valid.index[length - 1]
    seed = x.loc[valid.index[:length]].mean()
    alpha = 1.0 / length
    started, prev = False, np.nan
    for idx in x.index:
        val = x.loc[idx]
        if idx == first:
            prev, started, out.loc[idx] = seed, True, seed
        elif started:
            if pd.notna(val):
                prev = (prev * (length - 1) + val) / length
            out.loc[idx] = prev
    return out


def indicators(df):
    d = df.copy()
    delta = d["close"].diff()
    gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
    avg_gain, avg_loss = rma(gain, RSI_LENGTH), rma(loss, RSI_LENGTH)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    d["rsi"] = 100 - 100 / (1 + rs)
    d.loc[(avg_loss == 0) & (avg_gain > 0), "rsi"] = 100
    d.loc[(avg_loss == 0) & (avg_gain == 0), "rsi"] = 50

    prev_close = d["close"].shift(1)
    up, down = d["high"].diff(), -d["low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=d.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=d.index)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - prev_close).abs(),
                    (d["low"] - prev_close).abs()], axis=1).max(axis=1)
    d["atr"] = rma(tr, DMI_LENGTH)
    d["plus_di"] = 100 * rma(plus_dm, DMI_LENGTH) / d["atr"].replace(0, np.nan)
    d["minus_di"] = 100 * rma(minus_dm, DMI_LENGTH) / d["atr"].replace(0, np.nan)
    denom = (d["plus_di"] + d["minus_di"]).replace(0, np.nan)
    dx = 100 * (d["plus_di"] - d["minus_di"]).abs() / denom
    d["adx"] = rma(dx, ADX_SMOOTHING)
    return d


def telegram_send(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": message, "disable_web_page_preview": True},
                      timeout=20)
    r.raise_for_status()
    if not r.json().get("ok"):
        raise RuntimeError("Telegram sendMessage failed")


def load_state():
    default = {"last_m5_open": None, "side": None, "entry": None,
               "entry_time": None, "last_exit_time": None}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            default.update(json.load(f))
    except (OSError, ValueError):
        pass
    return default


def save_state(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)


def roe(side, entry, price):
    move = (price - entry) / entry if side == "LONG" else (entry - price) / entry
    # Approximate gross ROE; fee impact is shown separately, not assumed to be exact fills.
    return move * LEVERAGE * 100


def main():
    m5_raw = fetch_closed_candles("5m", 300)
    m15_raw = fetch_closed_candles("15m", 200)
    if len(m5_raw) < 60 or len(m15_raw) < 60:
        raise RuntimeError("Insufficient closed candles to warm up indicators.")
    m5, m15 = indicators(m5_raw), indicators(m15_raw)
    row, prev = m5.iloc[-1], m5.iloc[-2]
    trend = m15.iloc[-1]
    candle_key = row["open_time"].isoformat()
    state = load_state()
    if state.get("last_m5_open") == candle_key:
        print("Latest closed M5 candle already processed; skip.")
        return

    price = float(row["close"])
    rsi, adx = float(row["rsi"]), float(row["adx"])
    m15_rsi, m15_adx = float(trend["rsi"]), float(trend["adx"])
    plus15, minus15 = float(trend["plus_di"]), float(trend["minus_di"])
    plus5, minus5 = float(row["plus_di"]), float(row["minus_di"])
    if not all(np.isfinite(x) for x in (rsi, adx, m15_rsi, m15_adx, plus15, minus15, plus5, minus5, float(row["atr"]))):
        raise RuntimeError("Indicator warm-up produced non-finite values; refusing to emit signal.")

    m15_long = m15_adx > M15_ADX_MIN and plus15 > minus15 and m15_rsi > 50
    m15_short = m15_adx > M15_ADX_MIN and minus15 > plus15 and m15_rsi < 50
    m15_reverse = (state.get("side") == "LONG" and m15_short) or (state.get("side") == "SHORT" and m15_long)
    event = None
    side = state.get("side")

    if side in ("LONG", "SHORT"):
        entry = float(state["entry"])
        exit_price = price
        current_roe = roe(side, entry, price)
        # Hard SL is based on intrabar ROE, not ATR.
        adverse_move = abs(HARD_SL_ROE) / (LEVERAGE * 100)
        hard_stop_price = entry * (1 - adverse_move) if side == "LONG" else entry * (1 + adverse_move)
        hard_stop_hit = float(row["low"]) <= hard_stop_price if side == "LONG" else float(row["high"]) >= hard_stop_price
        if hard_stop_hit:
            exit_price = min(float(row["open"]), hard_stop_price) if side == "LONG" else max(float(row["open"]), hard_stop_price)
        exit_roe = roe(side, entry, exit_price)
        opposite_confirm = (side == "LONG" and price < float(prev["low"]) and rsi < 50) or (
            side == "SHORT" and price > float(prev["high"]) and rsi > 50)
        tp_rsi = (side == "LONG" and rsi >= 70) or (side == "SHORT" and rsi <= 30)
        if hard_stop_hit:
            event = ("HARD SL (ROE -90%)", side, exit_roe)
        elif current_roe >= TP_ROE and tp_rsi:
            event = ("TAKE PROFIT", side, current_roe)
        elif current_roe <= SOFT_SL_ROE and m15_reverse and opposite_confirm:
            event = ("SOFT SL (ROE -35% + M15 REVERSAL)", side, current_roe)
        if event:
            telegram_send(
                f"{'✅' if event[0] == 'TAKE PROFIT' else '🚨' if 'HARD SL' in event[0] else '⚠️'} "
                f"BTCUSDT M5 SCALP — {event[0]}\nSide: {side}\n"
                f"Entry: {entry:,.2f}\nExit reference: {exit_price:,.2f}\n"
                f"Gross ROE estimate: {(exit_roe if hard_stop_hit else current_roe):.2f}%\n"
                f"M5 RSI/ADX: {rsi:.2f}/{adx:.2f}\n"
                f"M15 trend: {'LONG' if m15_long else 'SHORT' if m15_short else 'NO TRADE'}\n"
                f"Candle close: {row['close_time'].strftime('%Y-%m-%d %H:%M UTC')}\n"
                "Signal-only simulation; no exchange order was placed."
            )
            state.update({"side": None, "entry": None, "entry_time": None,
                          "last_exit_time": candle_key})
    elif state.get("last_exit_time") != candle_key and adx > M5_ADX_MIN:
        long_entry = (m15_long and 40 <= float(prev["rsi"]) <= 50 and rsi > 50
                      and plus5 > minus5 and price > float(prev["high"]))
        short_entry = (m15_short and 50 <= float(prev["rsi"]) <= 60 and rsi < 50
                       and minus5 > plus5 and price < float(prev["low"]))
        if long_entry or short_entry:
            side = "LONG" if long_entry else "SHORT"
            hard_move = abs(HARD_SL_ROE) / (LEVERAGE * 100)
            hard_stop = price * (1 - hard_move) if side == "LONG" else price * (1 + hard_move)
            state.update({"side": side, "entry": price, "entry_time": candle_key})
            telegram_send(
                f"{'🟢' if side == 'LONG' else '🔴'} BTCUSDT M5 SCALP — {side} ENTRY\n"
                f"Entry reference: {price:,.2f}\nHard SL (-90% ROE) reference: {hard_stop:,.2f}\n"
                f"Soft SL: ROE <= {SOFT_SL_ROE:.1f}% plus confirmed M15 reversal\n"
                f"TP condition: ROE estimate >= {TP_ROE:.1f}% plus M5 RSI "
                f"{' >= 70' if side == 'LONG' else ' <= 30'}\n"
                f"M5 RSI/ADX: {rsi:.2f}/{adx:.2f}\n"
                f"M15 trend: {'LONG' if m15_long else 'SHORT'} | RSI {m15_rsi:.2f} | ADX {m15_adx:.2f}\n"
                f"Candle close: {row['close_time'].strftime('%Y-%m-%d %H:%M UTC')}\n"
                "DCA: disabled. Signal-only simulation; no exchange order was placed."
            )
    state["last_m5_open"] = candle_key
    save_state(state)
    print(f"Processed M5 candle {candle_key}; active_side={state.get('side') or 'FLAT'}")


if __name__ == "__main__":
    main()
