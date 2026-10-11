import os
import sys
import traceback

import pandas as pd
import bot

COMMAND = (
    sys.argv[1] if len(sys.argv) > 1
    else os.getenv("COMMAND", "help")
).strip().lower().lstrip("/")


def utc_text(value):
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.strftime("%Y-%m-%d %H:%M:%S UTC")


def snapshot():
    m15_raw = bot.get_klines("15m", 500)
    h1_raw = bot.get_klines("1h", 500)
    if len(m15_raw) < 50 or len(h1_raw) < 50:
        raise RuntimeError("Chưa đủ nến đã đóng để tính chỉ báo.")
    m15 = bot.add_indicators(m15_raw).reset_index(drop=True)
    h1 = bot.add_indicators(h1_raw).reset_index(drop=True)
    latest = m15.iloc[-1]
    previous = m15.iloc[-2]
    hour_bucket = latest["open_time"].floor("h")
    candidates = h1[h1["open_time"] < hour_bucket]
    if candidates.empty:
        h1row = h1.iloc[-1]
    else:
        h1row = candidates.iloc[-1]
    return m15, h1, latest, previous, h1row


def position_lines(state, price):
    side = state.get("side") or "FLAT"
    lines = [f"📌 Vị thế mô phỏng: {side}"]
    if side not in ("LONG", "SHORT"):
        lines.append("Hiện không có vị thế mở trong state.json.")
    else:
        avg = float(state.get("avg_entry") or 0)
        qty = float(state.get("qty") or 0)
        dca_used = bool(state.get("dca_used", False))
        margin = float(state.get("initial_margin") or 0.0) + float(state.get("dca_margin") or 0.0)
        pnl = ((price - avg) if side == "LONG" else (avg - price)) * qty
        roe = pnl / margin * 100 if margin > 0 else 0.0
        lines.extend([
            f"Giá vào trung bình: {bot.fmt_price(avg)}",
            f"Giá tham chiếu: {bot.fmt_price(price)}",
            f"Khối lượng mô phỏng: {qty:.8f} BTC",
            f"PnL chưa thực hiện (ước tính): {pnl:+.4f} USDT",
            f"ROE trên margin mô phỏng: {roe:+.2f}%",
            f"DCA đã dùng: {'Có' if dca_used else 'Chưa'}",
            f"Margin mô phỏng: {margin:.2f} USDT",
            f"Số dư mô phỏng: {float(state.get('account_balance', bot.INITIAL_CAPITAL)):.2f} USDT",
        ])
    last_closed = state.get("last_closed")
    if isinstance(last_closed, dict) and last_closed:
        lines.extend([
            "",
            "🧾 LỆNH ĐÃ ĐÓNG GẦN NHẤT",
            f"Hướng: {last_closed.get('side', 'N/A')}",
            f"Lý do: {last_closed.get('reason', 'N/A')}",
            f"PnL đã đóng: {float(last_closed['pnl_usd']):+.4f} USDT" if last_closed.get("pnl_usd") is not None else "PnL đã đóng: N/A",
            f"ROE khi đóng: {float(last_closed['roe_pct']):+.2f}%" if last_closed.get("roe_pct") is not None else "ROE khi đóng: N/A",
            f"Thời gian đóng: {last_closed.get('exit_time', 'N/A')}",
        ])
    return lines


def build_status(m15, h1, latest, h1row, state):
    price = float(latest["close"])
    side = state.get("side") or "FLAT"
    lines = [
        "📊 BTCUSDT — BÁO CÁO TRẠNG THÁI",
        f"🕒 Nến M15: {utc_text(latest['open_time'])}",
        f"💰 Giá tham chiếu: {bot.fmt_price(price)}",
        f"RSI M15: {float(latest['rsi']):.2f} | ADX M15: {float(latest['adx']):.2f}",
        f"DI+ H1: {float(h1row['plus_di']):.2f} | DI− H1: {float(h1row['minus_di']):.2f} | ADX H1: {float(h1row['adx']):.2f}",
        f"Xu hướng H1: {'TĂNG' if h1row['plus_di'] > h1row['minus_di'] else 'GIẢM' if h1row['minus_di'] > h1row['plus_di'] else 'TRUNG TÍNH'}",
        "",
    ]
    lines.extend(position_lines(state, price))
    lines.extend(["", "Chế độ: TÍN HIỆU MÔ PHỎNG — BOT KHÔNG ĐẶT LỆNH."])
    return "\n".join(lines)


def build_signal(latest, previous, h1row):
    rsi = float(latest["rsi"])
    prev_rsi = float(previous["rsi"])
    adx_m15 = float(latest["adx"])
    plus_di = float(h1row["plus_di"])
    minus_di = float(h1row["minus_di"])
    adx_h1 = float(h1row["adx"])
    h1_bull = plus_di > minus_di and adx_h1 > bot.H1_ADX_ENTRY
    h1_bear = minus_di > plus_di and adx_h1 > bot.H1_ADX_ENTRY
    long_cross = h1_bull and prev_rsi <= bot.LONG_RSI_ENTRY and rsi > bot.LONG_RSI_ENTRY
    short_cross = h1_bear and prev_rsi >= bot.SHORT_RSI_ENTRY and rsi < bot.SHORT_RSI_ENTRY
    ready = "LONG ENTRY" if long_cross else "SHORT ENTRY" if short_cross else "CHƯA CÓ ENTRY MỚI"
    return "\n".join([
        "🔎 BTCUSDT — KIỂM TRA TÍN HIỆU",
        f"🕒 Nến M15: {utc_text(latest['open_time'])}",
        f"Giá đóng nến: {bot.fmt_price(float(latest['close']))}",
        f"RSI M15: {rsi:.2f} (nến trước {prev_rsi:.2f})",
        f"ADX M15: {adx_m15:.2f}",
        f"DI+ H1: {plus_di:.2f} | DI− H1: {minus_di:.2f} | ADX H1: {adx_h1:.2f}",
        f"Điều kiện xu hướng H1 LONG: {'ĐẠT' if h1_bull else 'CHƯA ĐẠT'}",
        f"Điều kiện xu hướng H1 SHORT: {'ĐẠT' if h1_bear else 'CHƯA ĐẠT'}",
        f"Kết luận: {ready}",
        "Lưu ý: kiểm tra điều kiện tại nến đã đóng; đây không phải lệnh giao dịch.",
    ])


def main():
    if COMMAND == "help":
        bot.telegram_send(
            "🤖 LỆNH BOT BTCUSDT\n"
            "/status — Báo cáo thị trường và vị thế\n"
            "/position — Vị thế hiện tại và lệnh đã đóng gần nhất\n"
            "/signal — RSI, ADX, xu hướng H1 và điều kiện entry\n"
            "/backtest — Backtest lịch sử 90 ngày\n"
            "/btstatus — Trạng thái backtest gần nhất\n"
            "/btresult — Báo cáo backtest gần nhất\n"
            "/help — Danh sách lệnh\n\n"
            "Bot chỉ phát tín hiệu mô phỏng, không đặt lệnh Futures."
        )
        print("Sent help response")
        return

    if COMMAND == "backtest":
        from backtest import run_backtest, format_report
        try:
            report = run_backtest(days=int(os.getenv("BACKTEST_DAYS", "90")))
            bot.telegram_send(format_report(report))
        except Exception as exc:
            bot.telegram_send(f"⚠️ Backtest thất bại: {str(exc)[:250]}")
            traceback.print_exc()
        return

    if COMMAND == "btstatus":
        from backtest import get_backtest_status
        bot.telegram_send(get_backtest_status())
        return

    if COMMAND == "btresult":
        from backtest import get_last_report, format_report
        report = get_last_report()
        bot.telegram_send(format_report(report) if report else "Chưa có kết quả. Gửi /backtest để chạy.")
        return

    if COMMAND not in {"status", "position", "signal"}:
        raise ValueError("Unsupported command")

    try:
        m15, h1, latest, previous, h1row = snapshot()
        state = bot.load_state()
        if COMMAND == "signal":
            message = build_signal(latest, previous, h1row)
        elif COMMAND == "position":
            message = "📌 BTCUSDT — VỊ THẾ\n🕒 " + utc_text(latest["open_time"]) + "\n" + "\n".join(position_lines(state, float(latest["close"])))
            message += "\n\nChế độ: TÍN HIỆU MÔ PHỎNG — BOT KHÔNG ĐẶT LỆNH."
        else:
            message = build_status(m15, h1, latest, h1row, state)
        bot.telegram_send(message)
        print(f"Sent command response: {COMMAND}")
    except Exception as exc:
        # Send a concise user-facing error; traceback remains in GitHub Actions logs.
        bot.telegram_send(
            f"⚠️ Không thể hoàn tất /{COMMAND}. Lỗi: {str(exc)[:250]}\n"
            "Hãy mở GitHub Actions để xem log chi tiết."
        )
        traceback.print_exc()


if __name__ == "__main__":
    main()
