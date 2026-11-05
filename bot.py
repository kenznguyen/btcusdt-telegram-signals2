import os
import json
import time
from datetime import datetime, timezone

import requests
import numpy as np
import pandas as pd

# Signal-only bot. No Binance trading API keys or order endpoints are used.
SYMBOL = "BTCUSDT"
INTERVAL = "15m"
H1_INTERVAL = "1h"
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
INITIAL_CAPITAL = float(os.getenv("BACKTEST_INITIAL_CAPITAL", "100"))
ENTRY_MARGIN_PCT = float(os.getenv("ENTRY_MARGIN_PCT", "0.50"))
DCA_MARGIN_RATIO = float(os.getenv("DCA_MARGIN_RATIO", "1.00"))
FEE_RATE = float(os.getenv("TAKER_FEE_RATE", "0.0005"))
SLIPPAGE_BPS = float(os.getenv("SLIPPAGE_BPS", "5"))
STATE_FILE = "state.json"
FAPI = "https://fapi.binance.com"

def utc_now():
    return datetime.now(timezone.utc)

def get_klines(interval, limit=500):
    url = "https://www.okx.com/api/v5/market/history-candles"

    bar_map = {
        "15m": "15m",
        "1h": "1H",
        "1d": "1Dutc",
        "1w": "1Wutc",
    }

    bar = bar_map.get(interval)
    if bar is None:
        raise ValueError(f"Unsupported interval: {interval}")

    rows = []
    after = None

    # OKX trả tối đa 300 nến mỗi lần gọi
    while len(rows) < limit:
        params = {
            "instId": "BTC-USDT-SWAP",
            "bar": bar,
            "limit": str(min(300, limit - len(rows))),
        }

        if after is not None:
            params["after"] = after

        response = requests.get(url, params=params, timeout=20)

        if not response.ok:
            print("OKX HTTP status:", response.status_code)
            print("OKX response:", response.text[:1000])
            response.raise_for_status()

        payload = response.json()

        if payload.get("code") != "0":
            raise RuntimeError(
                f"OKX API error: {payload.get('msg')}"
            )

        batch = payload.get("data", [])
        if not batch:
            break

        rows.extend(batch)

        # Dữ liệu trả về từ mới đến cũ.
        # Lấy timestamp của nến cũ nhất để truy vấn tiếp.
        oldest_ts = batch[-1][0]

        if len(batch) < 2 or len(rows) >= limit:
            break

        after = oldest_ts

    if not rows:
        raise RuntimeError("OKX returned no candle data")

    # Loại nến trùng và sắp xếp thời gian tăng dần
    unique_rows = {row[0]: row for row in rows}
    rows = sorted(unique_rows.values(), key=lambda row: int(row[0]))

    df = pd.DataFrame(
        rows,
        columns=[
            "open_time", "open", "high", "low", "close",
            "volume_contracts", "volume", "quote_volume", "confirm"
        ],
    )

    for c in ["open", "high", "low", "close", "volume", "quote_volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["open_time"] = pd.to_datetime(
        pd.to_numeric(df["open_time"]),
        unit="ms",
        utc=True,
    )

    duration_map = {
        "15m": pd.Timedelta(minutes=15),
        "1h": pd.Timedelta(hours=1),
        "1d": pd.Timedelta(days=1),
        "1w": pd.Timedelta(weeks=1),
    }

    df["close_time"] = (
        df["open_time"] + duration_map[interval]
    )

    # Chỉ dùng nến đã đóng theo cờ xác nhận của OKX
    # và thời gian đóng nến.
    now = pd.Timestamp.now(tz="UTC")
    df = df.loc[
        (df["confirm"].astype(str) == "1")
        & (df["close_time"] <= now)
    ].copy()

    return df.tail(limit).reset_index(drop=True)
    

    

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

def load_state():
    default = {
        "last_processed_open": None,
        "side": None,
        "qty": 0.0,
        "avg_entry": 0.0,
        "dca_used": False,
        "entry_time": None,
        "last_event": None,
        "last_closed": None,
        "account_balance": INITIAL_CAPITAL
    }
    if not os.path.exists(STATE_FILE):
        return default
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        default.update(saved)
        if "account_balance" not in saved:
            default["account_balance"] = INITIAL_CAPITAL
        return default
    except Exception:
        return default

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def fmt_price(x):
    return f"{x:,.2f}"

def roe_for(side, avg_entry, close):
    if not side or avg_entry <= 0:
        return None
    if side == "LONG":
        return ((close - avg_entry) / avg_entry) * LEVERAGE * 100
    return ((avg_entry - close) / avg_entry) * LEVERAGE * 100


def build_status_report(state, price, candle_time, m15_row=None, h1_row=None):
    side = state.get("side") or "FLAT"
    last_closed = state.get("last_closed")
    lines = [
        "📊 BTCUSDT — BÁO CÁO TRẠNG THÁI",
        f"🕒 Thời gian nến: {candle_time.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"💰 Giá tham chiếu: {fmt_price(price)}",
    ]

    if m15_row is not None:
        rsi = float(m15_row["rsi"]) if pd.notna(m15_row["rsi"]) else None
        adx = float(m15_row["adx"]) if pd.notna(m15_row["adx"]) else None
        lines.append(f"📈 M15: RSI {rsi:.2f} | ADX {adx:.2f}" if rsi is not None and adx is not None else "📈 M15: Chưa đủ dữ liệu chỉ báo")
    if h1_row is not None:
        h1_adx = float(h1_row["adx"]) if pd.notna(h1_row["adx"]) else None
        plus_di = float(h1_row["plus_di"]) if pd.notna(h1_row["plus_di"]) else None
        minus_di = float(h1_row["minus_di"]) if pd.notna(h1_row["minus_di"]) else None
        if h1_adx is not None and plus_di is not None and minus_di is not None:
            trend = "TĂNG" if plus_di > minus_di else "GIẢM" if minus_di > plus_di else "TRUNG TÍNH"
            lines.append(f"🧭 H1: {trend} | +DI {plus_di:.2f} / -DI {minus_di:.2f} | ADX {h1_adx:.2f}")
        else:
            lines.append("🧭 H1: Chưa đủ dữ liệu chỉ báo")
    lines.append("")

    if side in ("LONG", "SHORT"):
        avg_entry = float(state.get("avg_entry") or 0)
        qty = float(state.get("qty") or 0)
        dca_used = bool(state.get("dca_used", False))
        margin_used = float(state.get("initial_margin") or 0.0) + float(state.get("dca_margin") or 0.0)
        if avg_entry > 0 and qty > 0:
            pnl = (price - avg_entry) * qty if side == "LONG" else (avg_entry - price) * qty
            roe = pnl / margin_used * 100 if margin_used > 0 else 0
            lines.extend([
                f"📌 Vị thế mô phỏng: {side}",
                f"Giá vào trung bình: {fmt_price(avg_entry)}",
                f"Khối lượng: {qty:.8f} BTC",
                f"PnL chưa thực hiện (ước tính): {pnl:+.4f} USDT",
                f"ROE trên margin mô phỏng: {roe:+.2f}%",
                f"Margin mô phỏng: {margin_used:.2f} USDT",
                f"DCA đã dùng: {'Có' if dca_used else 'Chưa'}",
                "TP: đang theo dõi điều kiện RSI và ROE; chưa xác nhận kích hoạt.",
                "Soft SL: đang theo dõi ROE, ADX H1 và xác nhận 2 nến; chưa xác nhận kích hoạt.",
                "Emergency SL: đang giám sát ngưỡng bảo vệ; chưa xác nhận kích hoạt.",
            ])
        else:
            lines.extend([f"📌 Vị thế mô phỏng: {side}", "⚠️ Thiếu giá vào hoặc khối lượng hợp lệ; chưa tính được PnL."])
    else:
        lines.extend(["📌 Vị thế mô phỏng: FLAT", "Hiện không có vị thế mở trong state.json."])

    lines.extend(["", "🧾 VỊ THẾ ĐÃ ĐÓNG GẦN NHẤT"])
    if isinstance(last_closed, dict) and last_closed:
        closed_side = last_closed.get("side", "N/A")
        reason = last_closed.get("reason", "N/A")
        entry = last_closed.get("avg_entry")
        exit_price = last_closed.get("exit_price")
        pnl = last_closed.get("pnl_usd")
        closed_roe = last_closed.get("roe_pct")
        exit_time = last_closed.get("exit_time", "N/A")
        lines.extend([
            f"Hướng: {closed_side}",
            f"Lý do đóng: {reason}",
            f"Giá vào TB: {fmt_price(float(entry)) if entry is not None else 'N/A'}",
            f"Giá đóng: {fmt_price(float(exit_price)) if exit_price is not None else 'N/A'}",
            f"PnL đã đóng: {float(pnl):+.4f} USDT" if pnl is not None else "PnL đã đóng: N/A",
            f"ROE khi đóng: {float(closed_roe):+.2f}%" if closed_roe is not None else "ROE khi đóng: N/A",
            f"Thời gian đóng: {exit_time}",
        ])
    else:
        lines.append("Chưa có dữ liệu vị thế đã đóng.")
    lines.append("ℹ️ Tín hiệu mô phỏng; bot không đặt lệnh Futures.")
    return "\n".join(lines)


def build_signal_report(m15, h1):
    row = m15.iloc[-1]
    prev = m15.iloc[-2]
    h = h1.iloc[-1]
    rsi = float(row["rsi"])
    prev_rsi = float(prev["rsi"])
    adx = float(row["adx"])
    h1_adx = float(h["adx"])
    plus_di = float(h["plus_di"])
    minus_di = float(h["minus_di"])
    h1_bull = plus_di > minus_di and h1_adx > H1_ADX_ENTRY
    h1_bear = minus_di > plus_di and h1_adx > H1_ADX_ENTRY
    long_ready = h1_bull and prev_rsi <= LONG_RSI_ENTRY and rsi > LONG_RSI_ENTRY
    short_ready = h1_bear and prev_rsi >= SHORT_RSI_ENTRY and rsi < SHORT_RSI_ENTRY
    trend = "TĂNG" if plus_di > minus_di else "GIẢM" if minus_di > plus_di else "TRUNG TÍNH"
    signal = "LONG ENTRY ĐỦ ĐIỀU KIỆN" if long_ready else "SHORT ENTRY ĐỦ ĐIỀU KIỆN" if short_ready else "Chưa có tín hiệu vào lệnh mới"
    return "\n".join([
        "🔎 BTCUSDT — KIỂM TRA TÍN HIỆU",
        f"🕒 {row['open_time'].strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Giá đóng M15: {fmt_price(float(row['close']))}",
        f"RSI M15: {rsi:.2f} (nến trước {prev_rsi:.2f}) | ADX M15: {adx:.2f}",
        f"Xu hướng H1: {trend} | ADX H1: {h1_adx:.2f}",
        f"Điều kiện LONG: {'ĐẠT' if long_ready else 'Chưa đạt'}",
        f"Điều kiện SHORT: {'ĐẠT' if short_ready else 'Chưa đạt'}",
        f"Kết luận: {signal}",
        "ℹ️ Đây là phân tích mô phỏng, không phải lệnh giao dịch."
    ])



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

    
          
