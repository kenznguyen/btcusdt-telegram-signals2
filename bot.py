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
TELEGRAM_OUTBOX_FILE = "telegram_outbox.json"
TELEGRAM_SENT_FILE = "telegram_sent_event_ids.json"
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

    # Validate the source batch before indicators/state are allowed to advance.
    # Duplicate timestamps are tolerated across paginated pages but conflicting duplicates are not.
    by_timestamp = {}
    for source_row in rows:
        if len(source_row) < 9:
            raise RuntimeError("OKX candle row is incomplete")
        timestamp = str(source_row[0])
        if timestamp in by_timestamp and by_timestamp[timestamp] != source_row:
            raise RuntimeError(f"Conflicting duplicate OKX candle at {timestamp}")
        by_timestamp[timestamp] = source_row
    rows = sorted(by_timestamp.values(), key=lambda row: int(row[0]))
    interval_ms = {"15m": 15 * 60_000, "1h": 60 * 60_000,
                   "1d": 24 * 60 * 60_000, "1w": 7 * 24 * 60 * 60_000}[interval]
    for previous, current in zip(rows, rows[1:]):
        delta = int(current[0]) - int(previous[0])
        if delta <= 0:
            raise RuntimeError("OKX candles are not strictly chronological")
        if delta % interval_ms != 0:
            raise RuntimeError("OKX candle timestamps are not aligned to interval")
    # Missing intervals are recorded as a warning; do not fabricate candles or indicators.
    gaps = sum(1 for previous, current in zip(rows, rows[1:])
               if int(current[0]) - int(previous[0]) > interval_ms)
    if gaps:
        print(f"WARNING: OKX returned {gaps} candle gap(s) for {interval}; indicators may be less reliable.")

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

    price_cols = ["open", "high", "low", "close", "volume", "quote_volume"]
    numeric = df[price_cols].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise RuntimeError("OKX returned NaN/inf candle values")
    invalid_ohlc = (
        (df["low"] <= 0)
        | (df["high"] < df["low"])
        | (df["high"] < df["open"])
        | (df["high"] < df["close"])
        | (df["low"] > df["open"])
        | (df["low"] > df["close"])
        | (df["open"] <= 0)
        | (df["close"] <= 0)
        | (df["volume"] < 0)
        | (df["quote_volume"] < 0)
    )
    if invalid_ohlc.any():
        raise RuntimeError(f"OKX returned {int(invalid_ohlc.sum())} invalid OHLCV candle(s)")

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

def _atomic_write_json(path, payload):
    """Replace JSON files atomically so a process restart cannot read a partial write."""
    import tempfile
    directory = os.path.dirname(os.path.abspath(path))
    fd, temporary = tempfile.mkstemp(prefix=".state-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

def _read_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

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
        saved = _read_json(STATE_FILE, {})
        if not isinstance(saved, dict):
            raise ValueError("state.json must contain a JSON object")
        default.update(saved)
        if "account_balance" not in saved:
            default["account_balance"] = INITIAL_CAPITAL
        if default.get("side") not in (None, "LONG", "SHORT"):
            raise ValueError("state.json has an unsupported position side")
        for key in ("qty", "avg_entry", "account_balance"):
            value = float(default.get(key) or 0.0)
            if not np.isfinite(value) or value < 0:
                raise ValueError(f"state.json has invalid {key}")
        return default
    except Exception as exc:
        raise RuntimeError(
            f"Cannot safely restore {STATE_FILE}; refusing to reset position state: {exc}"
        ) from exc

def save_state(state):
    _atomic_write_json(STATE_FILE, state)

def telegram_send(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID secret.")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True}, timeout=20)
    r.raise_for_status()
    payload = r.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error: {payload}")

def fmt_price(x):
    return f"{x:,.2f}"

def _event_key(kind, side, candle_time):
    stamp = pd.Timestamp(candle_time)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("UTC")
    else:
        stamp = stamp.tz_convert("UTC")
    return f"{kind}|{side or 'FLAT'}|{stamp.isoformat()}"

def flush_telegram_outbox():
    """Deliver queued alerts; retain failures for the next scheduled run."""
    try:
        queue = _read_json(TELEGRAM_OUTBOX_FILE, [])
        sent = _read_json(TELEGRAM_SENT_FILE, [])
        if not isinstance(queue, list) or not isinstance(sent, list):
            raise ValueError("Telegram outbox/ledger JSON has an invalid shape")
        sent_set = set(str(x) for x in sent)
        remaining = []
        changed = False
        for item in queue:
            key = item.get("key") if isinstance(item, dict) else None
            if not key:
                changed = True
                continue
            if key in sent_set:
                changed = True
                continue
            try:
                telegram_send(item["text"])
            except Exception as exc:
                print(f"Telegram delivery pending for {key}: {exc}")
                remaining.append(item)
                continue
            # Persist the ledger before removing the queue item. Telegram sendMessage has
            # no idempotency key, so a crash after API acceptance but before this write is
            # the one narrow window in which duplicate delivery cannot be ruled out.
            sent.append(key)
            sent_set.add(key)
            sent = sent[-500:]
            _atomic_write_json(TELEGRAM_SENT_FILE, sent)
            changed = True
        if changed or len(remaining) != len(queue):
            _atomic_write_json(TELEGRAM_OUTBOX_FILE, remaining)
        return len(remaining)
    except Exception as exc:
        print(f"Telegram outbox retained for retry: {exc}")
        return -1

def send_event(kind, side, price, candle_time, roe=None, note=""):
    emoji = {"LONG ENTRY":"🟢", "SHORT ENTRY":"🔴", "DCA":"🟠",
             "TAKE PROFIT":"✅", "SOFT SL":"⚠️", "EMERGENCY SL":"🚨"}.get(kind, "ℹ️")
    lines = [
        f"{emoji} BTCUSDT FUTURES — {kind}",
        f"Chiều: {side or 'FLAT'}",
        f"Giá tham chiếu: {fmt_price(float(price))}",
        f"Nến M15 (UTC): {candle_time.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "Chế độ: TÍN HIỆU MÔ PHỎNG — BOT KHÔNG ĐẶT LỆNH"
    ]
    if roe is not None:
        lines.append(f"ROE ước tính tại giá đóng nến: {roe:.2f}%")
    if note:
        lines.append(note)
    lines.append("Người nhận tự xác minh giá và quản lý rủi ro.")
    key = _event_key(kind, side, candle_time)
    try:
        sent = _read_json(TELEGRAM_SENT_FILE, [])
        queue = _read_json(TELEGRAM_OUTBOX_FILE, [])
        if key in sent or any(isinstance(item, dict) and item.get("key") == key for item in queue):
            return
        queue.append({"key": key, "text": "\n".join(lines), "queued_at": utc_now().isoformat()})
        _atomic_write_json(TELEGRAM_OUTBOX_FILE, queue)
        flush_telegram_outbox()
    except Exception as exc:
        # Delivery failures must not stop state persistence; retry the durable outbox later.
        print(f"Could not enqueue Telegram event {key}: {exc}")

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


def send_status_report(state, price, candle_time, m15_row=None, h1_row=None):
    telegram_send(build_status_report(state, price, candle_time, m15_row, h1_row))



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

def main():
    # Retry alerts left by a network outage or process restart before scanning new candles.
    flush_telegram_outbox()
    if os.getenv("TEST_TELEGRAM", "").strip() == "1":
        telegram_send("✅ BTCUSDT Signal Bot: Telegram kết nối thành công!")
        print("Telegram test message sent successfully.")
        return

    m15_raw = get_klines(INTERVAL, 500)
    h1_raw = get_klines(H1_INTERVAL, 500)
    if len(m15_raw) < 100 or len(h1_raw) < 100:
        raise RuntimeError("Not enough closed candles to warm up indicators.")

    m15 = add_indicators(m15_raw).reset_index(drop=True)
    h1 = add_indicators(h1_raw).reset_index(drop=True)
    h1_by_open = {row.open_time: row for row in h1.itertuples(index=False)}
    h1_times = list(h1["open_time"])

    state = load_state()
    last_processed = state.get("last_processed_open")
    if last_processed:
        last_processed = pd.Timestamp(last_processed)
        if last_processed.tzinfo is None:
            last_processed = last_processed.tz_localize("UTC")
        else:
            last_processed = last_processed.tz_convert("UTC")
    else:
        # First deployment: start at the latest closed candle only.
        last_processed = m15.iloc[-2]["open_time"] if len(m15) > 1 else None

    new_rows = (
        m15[m15["open_time"] > last_processed]
        if last_processed is not None
        else m15.tail(1)
    )

    if new_rows.empty:
        # Frequent schedule runs must not spam status reports between closed M15 candles.
        # Telegram commands are handled exclusively by the Render webhook bridge.
        print("No new closed M15 candle; skipped signal scan and status message.")
        return

    events_sent = 0
    for idx, row in new_rows.iterrows():
        # Process only closed M15 rows; use H1 candles closed by this M15 close.
        # Price-based Emergency SL must remain active while indicators warm up.
        closed_at = row["open_time"] + pd.Timedelta(minutes=15)
        prior_h1_candidates = [
            t for t in h1_times if t + pd.Timedelta(hours=1) <= closed_at
        ]
        h1row = h1_by_open[prior_h1_candidates[-1]] if prior_h1_candidates else None
        prev_rsi = m15.loc[idx - 1, "rsi"] if idx > 0 else np.nan

        close = float(row["close"])
        high = float(row["high"])
        low = float(row["low"])
        candle_open = float(row["open"])
        rsi = float(row["rsi"])
        adx = float(row["adx"])
        h1_plus = float(h1row.plus_di) if h1row is not None else np.nan
        h1_minus = float(h1row.minus_di) if h1row is not None else np.nan
        h1_adx = float(h1row.adx) if h1row is not None else np.nan

        h1_bull = h1_plus > h1_minus and h1_adx > H1_ADX_ENTRY
        h1_bear = h1_minus > h1_plus and h1_adx > H1_ADX_ENTRY
        long_signal = (
            h1_bull and prev_rsi <= LONG_RSI_ENTRY and rsi > LONG_RSI_ENTRY
        )
        short_signal = (
            h1_bear and prev_rsi >= SHORT_RSI_ENTRY and rsi < SHORT_RSI_ENTRY
        )

        side = state.get("side")
        avg_entry = float(state.get("avg_entry") or 0.0)
        qty = float(state.get("qty") or 0.0)
        dca_used = bool(state.get("dca_used", False))
        roe = roe_for(side, avg_entry, close)
        exited = False
        close_reason = None

        # Exit priority: emergency SL, soft SL, then TP.
        if side:
            emergency_price = threshold_price(
                side, avg_entry, abs(EMERGENCY_SL_ROE)
            )
            soft_price = threshold_price(side, avg_entry, abs(SOFT_SL_ROE))
            emergency_hit = (
                (side == "LONG" and low <= emergency_price)
                or (side == "SHORT" and high >= emergency_price)
            )

            h1_long_reversal = h1_minus > h1_plus and h1_adx > SOFT_SL_ADX
            h1_short_reversal = h1_plus > h1_minus and h1_adx > SOFT_SL_ADX
            prev_row = m15.loc[idx - 1] if idx > 0 else None
            two_bear = (
                candle_open > close
                and prev_row is not None
                and float(prev_row["close"]) < float(prev_row["open"])
            )
            two_bull = (
                close > candle_open
                and prev_row is not None
                and float(prev_row["close"]) > float(prev_row["open"])
            )
            soft_hit = (
                (
                    side == "LONG"
                    and low <= soft_price
                    and h1_long_reversal
                    and two_bear
                )
                or (
                    side == "SHORT"
                    and high >= soft_price
                    and h1_short_reversal
                    and two_bull
                )
            )
            tp_hit = (
                side == "LONG"
                and rsi >= LONG_RSI_TP
                and roe is not None
                and roe >= TP_ROE
            ) or (
                side == "SHORT"
                and rsi <= SHORT_RSI_TP
                and roe is not None
                and roe >= TP_ROE
            )

            sl_exit_price = None
            if emergency_hit:
                close_reason = "EMERGENCY SL"
                sl_exit_price = stop_fill_price(side, emergency_price, candle_open)
                send_event(
                    close_reason, side, sl_exit_price, row["open_time"], roe,
                    f"Ngưỡng SL: {fmt_price(emergency_price)}; giá khớp SL mô phỏng "
                    f"(xét gap tại open + trượt giá {SLIPPAGE_BPS:g} bps): {fmt_price(sl_exit_price)}",
                )
                events_sent += 1
                exited = True
            elif soft_hit:
                close_reason = "SOFT SL"
                sl_exit_price = stop_fill_price(side, soft_price, candle_open)
                send_event(
                    close_reason, side, sl_exit_price, row["open_time"], roe,
                    f"Ngưỡng SL: {fmt_price(soft_price)}; giá khớp SL mô phỏng "
                    f"(xét gap tại open + trượt giá {SLIPPAGE_BPS:g} bps): {fmt_price(sl_exit_price)}",
                )
                events_sent += 1
                exited = True
            elif tp_hit:
                close_reason = "TAKE PROFIT"
                tp_price = threshold_price(side, avg_entry, TP_ROE)
                exit_fill_price = execution_fill_price(close, "SELL" if side == "LONG" else "BUY")
                tp_rsi = LONG_RSI_TP if side == "LONG" else SHORT_RSI_TP
                send_event(
                    close_reason, side, exit_fill_price, row["open_time"], roe,
                    f"TP kích hoạt khi nến đóng: RSI {'≥' if side == 'LONG' else '≤'} {tp_rsi:g}, "
                    f"ROE ≥ +{TP_ROE:g}%. Giá ngưỡng lý thuyết: {fmt_price(tp_price)}; "
                    f"giá khớp mô phỏng tại close sau trượt giá {SLIPPAGE_BPS:g} bps: {fmt_price(exit_fill_price)}",
                )
                events_sent += 1
                exited = True

            if exited:
                closed_qty = qty
                closed_avg = avg_entry
                closed_margin = float(state.get("initial_margin") or 0.0) + float(state.get("dca_margin") or 0.0)
                actual_exit = (
                    exit_fill_price if close_reason == "TAKE PROFIT"
                    else sl_exit_price if close_reason in ("SOFT SL", "EMERGENCY SL")
                    else close
                )
                entry_notional = float(state.get("entry_notional") or (closed_avg * closed_qty))
                fees = (entry_notional + actual_exit * closed_qty) * FEE_RATE
                gross_pnl = (actual_exit - closed_avg) * closed_qty if side == "LONG" else (closed_avg - actual_exit) * closed_qty
                realized_pnl = gross_pnl - fees
                state["account_balance"] = float(state.get("account_balance", INITIAL_CAPITAL)) + realized_pnl
                closed_roe = (
                    realized_pnl / closed_margin * 100
                    if closed_margin > 0
                    else 0
                )
                state["last_closed"] = {
                    "side": side,
                    "reason": close_reason,
                    "avg_entry": closed_avg,
                    "exit_price": actual_exit,
                    "qty": closed_qty,
                    "pnl_usd": realized_pnl,
                    "gross_pnl_usd": gross_pnl,
                    "fees_usd": fees,
                    "roe_pct": (realized_pnl / closed_margin * 100 if closed_margin > 0 else 0),
                    "account_balance_after": state["account_balance"],
                    "entry_time": state.get("entry_time"),
                    "exit_time": row["open_time"].strftime(
                        "%Y-%m-%d %H:%M UTC"
                    ),
                }
                state.update(
                    {
                        "side": None,
                        "qty": 0.0,
                        "avg_entry": 0.0,
                        "dca_used": False,
                        "entry_time": None,
                        "initial_margin": 0.0,
                        "dca_margin": 0.0,
                        "entry_notional": 0.0,
                    }
                )
                side, avg_entry, qty, dca_used = None, 0.0, 0.0, False

        # Do not open a new position on the same candle that closed one.
        if side is None and not exited:
            if long_signal:
                current_balance = float(state.get("account_balance", INITIAL_CAPITAL))
                entry_margin = current_balance * ENTRY_MARGIN_PCT
                fill_price = execution_fill_price(close, "BUY")
                new_qty = entry_margin * LEVERAGE / fill_price
                state.update(
                    {
                        "side": "LONG",
                        "qty": new_qty,
                        "avg_entry": fill_price,
                        "dca_used": False,
                        "entry_time": row["open_time"].isoformat(),
                        "initial_margin": entry_margin,
                        "dca_margin": 0.0,
                        "entry_notional": new_qty * fill_price,
                    }
                )
                send_event(
                    "LONG ENTRY", "LONG", fill_price, row["open_time"],
                    note=f"Khối lượng mô phỏng: {new_qty:.8f} BTC",
                )
                events_sent += 1
            elif short_signal:
                current_balance = float(state.get("account_balance", INITIAL_CAPITAL))
                entry_margin = current_balance * ENTRY_MARGIN_PCT
                fill_price = execution_fill_price(close, "SELL")
                new_qty = entry_margin * LEVERAGE / fill_price
                state.update(
                    {
                        "side": "SHORT",
                        "qty": new_qty,
                        "avg_entry": fill_price,
                        "dca_used": False,
                        "entry_time": row["open_time"].isoformat(),
                        "initial_margin": entry_margin,
                        "dca_margin": 0.0,
                        "entry_notional": new_qty * fill_price,
                    }
                )
                send_event(
                    "SHORT ENTRY", "SHORT", fill_price, row["open_time"],
                    note=f"Khối lượng mô phỏng: {new_qty:.8f} BTC",
                )
                events_sent += 1

        elif side and not exited and not dca_used:
            current_roe = roe_for(side, avg_entry, close)
            if side == "LONG":
                dca_cond = (
                    current_roe is not None
                    and current_roe <= DCA_ROE
                    and adx > DCA_ADX
                    and rsi > LONG_DCA_RSI
                    and rsi > prev_rsi
                )
            else:
                dca_cond = (
                    current_roe is not None
                    and current_roe <= DCA_ROE
                    and adx > DCA_ADX
                    and rsi < SHORT_DCA_RSI
                    and rsi < prev_rsi
                )

            if dca_cond:
                initial_margin = float(state.get("initial_margin") or 0.0)
                add_margin = initial_margin * DCA_MARGIN_RATIO
                reserved_margin = float(state.get("initial_margin") or 0.0) + float(state.get("dca_margin") or 0.0)
                available_margin = max(0.0, float(state.get("account_balance", INITIAL_CAPITAL)) - reserved_margin)
                action = "BUY" if side == "LONG" else "SELL"
                fill_price = execution_fill_price(close, action)
                add_qty = add_margin * LEVERAGE / fill_price if fill_price > 0 else 0.0
                total_qty = qty + add_qty
                if total_qty > 0 and add_margin > 0 and add_margin <= available_margin + 1e-9:
                    new_avg = (
                        (avg_entry * qty) + (fill_price * add_qty)
                    ) / total_qty
                    state.update(
                        {
                            "qty": total_qty,
                            "avg_entry": new_avg,
                            "dca_used": True,
                            "dca_margin": add_margin,
                            "entry_notional": float(state.get("entry_notional") or (avg_entry * qty)) + fill_price * add_qty,
                        }
                    )
                    send_event(
                        "DCA", side, fill_price, row["open_time"], current_roe,
                        f"Khối lượng DCA mô phỏng: {add_qty:.8f} BTC; "
                        f"giá vốn mô phỏng sau DCA: {fmt_price(new_avg)}",
                    )
                    events_sent += 1

        state["last_processed_open"] = row["open_time"].isoformat()

    save_state(state)
    latest = m15.iloc[-1]
    latest_h1 = h1.iloc[-1]
    send_status_report(state, float(latest["close"]), latest["open_time"], latest, latest_h1)

    print(
        f"Processed {len(new_rows)} candle(s); "
        f"sent {events_sent} Telegram event(s)."
    )
    print(
        f"Status report sent; side={state.get('side')}, "
        f"dca_used={state.get('dca_used')}, "
        f"last={state.get('last_processed_open')}"
    )


if __name__ == "__main__":
    main()
    
          
