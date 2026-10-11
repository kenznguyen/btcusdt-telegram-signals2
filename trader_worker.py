"""Continuous BTCUSDT USD-M Futures worker. TESTNET ONLY by design.

Safety properties:
- refuses to start unless BINANCE_TESTNET=true and TRADING_ENABLED=true;
- uses Binance demo/testnet REST API, never the live Futures URL;
- requires one-way position mode and a pre-existing testnet account;
- places a server-side STOP_MARKET closePosition order after every entry/DCA;
- will not open new trades if exchange state or protection is ambiguous.
"""
import hashlib
import hmac
import json
import logging
import os
import signal
import time
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import requests

import bot

LOG = logging.getLogger("btc-trader")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

BASE_URL = "https://demo-fapi.binance.com"
SYMBOL = os.getenv("BINANCE_SYMBOL", "BTCUSDT").upper()
API_KEY = os.getenv("BINANCE_API_KEY", "").strip()
API_SECRET = os.getenv("BINANCE_API_SECRET", "").strip()
TESTNET = os.getenv("BINANCE_TESTNET", "true").strip().lower() == "true"
ENABLED = os.getenv("TRADING_ENABLED", "false").strip().lower() == "true"
LEVERAGE = int(os.getenv("TRADE_LEVERAGE", "3"))
INITIAL_MARGIN = Decimal(os.getenv("INITIAL_MARGIN_USDT", "10"))
DCA_MARGIN = Decimal(os.getenv("DCA_MARGIN_USDT", "10"))
DCA_ROE = Decimal(os.getenv("DCA_ROE_PCT", "-20"))
DCA_ADX = float(os.getenv("DCA_ADX_M15", "45"))
TP_ROE = Decimal(os.getenv("TP_ROE_PCT", "5"))
HARD_SL_ROE = Decimal(os.getenv("EXCHANGE_HARD_SL_ROE_PCT", "-35"))
LOOP_SECONDS = max(3, int(os.getenv("WORKER_LOOP_SECONDS", "10")))
STATE_PATH = Path(os.getenv("TRADER_STATE_PATH", "trader_state.json"))
RECV_WINDOW = 5000
STOP = False
SESSION = requests.Session()
SESSION.headers.update({"X-MBX-APIKEY": API_KEY})


def stop_handler(*_):
    global STOP
    STOP = True


signal.signal(signal.SIGINT, stop_handler)
signal.signal(signal.SIGTERM, stop_handler)


def require_safe_config():
    if not TESTNET:
        raise RuntimeError("Refusing to start: this first version supports Binance demo/testnet only.")
    if BASE_URL != "https://demo-fapi.binance.com":
        raise RuntimeError("Unexpected API base URL; refusing to trade.")
    if not ENABLED:
        raise RuntimeError("Trading is disabled. Set TRADING_ENABLED=true only for a deliberate testnet run.")
    if not API_KEY or not API_SECRET:
        raise RuntimeError("Set BINANCE_API_KEY and BINANCE_API_SECRET as private environment secrets.")
    if INITIAL_MARGIN <= 0 or DCA_MARGIN < 0 or LEVERAGE < 1 or LEVERAGE > 10:
        raise RuntimeError("Unsafe sizing/leverage config: margin must be positive and leverage 1-10 in this test build.")
    if HARD_SL_ROE >= 0 or HARD_SL_ROE < -60:
        raise RuntimeError("EXCHANGE_HARD_SL_ROE_PCT must be negative and no lower than -60% ROE.")
    if DCA_ROE >= 0 or TP_ROE <= 0:
        raise RuntimeError("Invalid DCA/TP thresholds.")


def api(method, path, params=None, signed=False):
    params = dict(params or {})
    if signed:
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = RECV_WINDOW
        query = urlencode(params, doseq=True)
        params["signature"] = hmac.new(
            API_SECRET.encode(), query.encode(), hashlib.sha256
        ).hexdigest()
    response = SESSION.request(
        method, BASE_URL + path, params=params if method.upper() in ("GET", "DELETE") else None,
        data=params if method.upper() not in ("GET", "DELETE") else None,
        timeout=10,
    )
    if not response.ok:
        # Do not log headers, signed query strings, API keys, or signatures.
        raise RuntimeError(f"Binance API {method} {path} returned HTTP {response.status_code}: {response.text[:300]}")
    return response.json()


def public_api(path, params=None):
    response = requests.get(BASE_URL + path, params=params or {}, timeout=10)
    response.raise_for_status()
    return response.json()


def check_account_mode():
    mode = api("GET", "/fapi/v1/positionSide/dual", signed=True)
    if mode.get("dualSidePosition") is True:
        raise RuntimeError("Binance account is in Hedge Mode. Switch testnet account to One-way Mode first.")
    info = public_api("/fapi/v1/exchangeInfo")
    symbol_info = next((x for x in info["symbols"] if x["symbol"] == SYMBOL), None)
    if not symbol_info or symbol_info.get("status") != "TRADING":
        raise RuntimeError(f"{SYMBOL} is not available for trading on this demo endpoint.")
    filters = {x["filterType"]: x for x in symbol_info["filters"]}
    min_notional_filter = filters.get("MIN_NOTIONAL") or filters.get("NOTIONAL")
    min_notional = min_notional_filter.get("notional", min_notional_filter.get("minNotional", "5")) if min_notional_filter else "5"
    return filters["LOT_SIZE"]["stepSize"], filters["PRICE_FILTER"]["tickSize"], min_notional


def floor_step(value, step):
    value, step = Decimal(str(value)), Decimal(str(step))
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def fmt_decimal(value):
    return format(Decimal(str(value)).normalize(), "f")


def position():
    rows = api("GET", "/fapi/v2/positionRisk", {"symbol": SYMBOL}, signed=True)
    row = next((x for x in rows if x.get("symbol") == SYMBOL and x.get("positionSide", "BOTH") == "BOTH"), None)
    if row is None:
        raise RuntimeError("Could not reconcile one-way position from Binance.")
    qty = Decimal(row["positionAmt"])
    return {
        "qty": qty,
        "side": "LONG" if qty > 0 else "SHORT" if qty < 0 else None,
        "entry": Decimal(row["entryPrice"]),
        "mark": Decimal(row["markPrice"]),
        "unrealized": Decimal(row["unRealizedProfit"]),
        "liquidation": Decimal(row.get("liquidationPrice", "0")),
    }


def roe_pct(pos):
    if not pos["side"] or pos["entry"] <= 0:
        return Decimal("0")
    direction = Decimal("1") if pos["side"] == "LONG" else Decimal("-1")
    move = (pos["mark"] - pos["entry"]) / pos["entry"] * direction
    # This is a leverage-based estimate, not the exchange's exact account ROE.
    return move * Decimal(LEVERAGE) * Decimal(100)


def cancel_stops():
    orders = api("GET", "/fapi/v1/openOrders", {"symbol": SYMBOL}, signed=True)
    for order in orders:
        if order.get("type") in ("STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET"):
            api("DELETE", "/fapi/v1/order", {"symbol": SYMBOL, "orderId": order["orderId"]}, signed=True)


def stop_price(pos, tick):
    adverse_move = abs(HARD_SL_ROE) / Decimal(100 * LEVERAGE)
    raw = pos["entry"] * (Decimal(1) - adverse_move if pos["side"] == "LONG" else Decimal(1) + adverse_move)
    rounded = floor_step(raw, tick)
    return rounded


def ensure_exchange_stop(pos, tick):
    """Place a closePosition stop; keep any old stop until the replacement is accepted."""
    if not pos["side"] or pos["qty"] == 0:
        return
    orders = api("GET", "/fapi/v1/openOrders", {"symbol": SYMBOL}, signed=True)
    protective = [o for o in orders if o.get("type") == "STOP_MARKET" and o.get("closePosition") in (True, "true")]
    target = stop_price(pos, tick)
    # Keep a stop if it is already near the current target; avoid churning orders.
    if any(abs(Decimal(o["stopPrice"]) - target) <= Decimal(tick) for o in protective):
        return
    side = "SELL" if pos["side"] == "LONG" else "BUY"
    created = api("POST", "/fapi/v1/order", {
        "symbol": SYMBOL,
        "side": side,
        "type": "STOP_MARKET",
        "stopPrice": fmt_decimal(target),
        "closePosition": "true",
        "workingType": "MARK_PRICE",
        "priceProtect": "TRUE",
        "newOrderRespType": "RESULT",
    }, signed=True)
    if not created.get("orderId"):
        raise RuntimeError("Exchange did not confirm protective stop creation; trading loop will halt.")
    for old in protective:
        if str(old["orderId"]) != str(created["orderId"]):
            try:
                api("DELETE", "/fapi/v1/order", {"symbol": SYMBOL, "orderId": old["orderId"]}, signed=True)
            except Exception:
                LOG.exception("Could not cancel an older protective stop; both may remain open.")


def market_order(side, quantity):
    if quantity <= 0:
        raise RuntimeError("Calculated order quantity is zero.")
    return api("POST", "/fapi/v1/order", {
        "symbol": SYMBOL,
        "side": side,
        "type": "MARKET",
        "quantity": fmt_decimal(quantity),
        "newOrderRespType": "RESULT",
    }, signed=True)


def get_signal():
    m15_raw = bot.get_klines("15m", 500)
    h1_raw = bot.get_klines("1h", 500)
    if len(m15_raw) < 100 or len(h1_raw) < 100:
        raise RuntimeError("Insufficient closed candles for indicators.")
    m15 = bot.add_indicators(m15_raw).reset_index(drop=True)
    h1 = bot.add_indicators(h1_raw).reset_index(drop=True)
    latest, previous = m15.iloc[-1], m15.iloc[-2]
    hour_bucket = latest["open_time"].floor("h")
    prior_h1 = h1[h1["open_time"] < hour_bucket]
    if prior_h1.empty:
        raise RuntimeError("No completed H1 candle available.")
    h = prior_h1.iloc[-1]
    vals = [latest["rsi"], previous["rsi"], latest["adx"], h["adx"], h["plus_di"], h["minus_di"]]
    if any(pd.isna(x) for x in vals):
        raise RuntimeError("Indicator values are not ready.")
    long_signal = (
        h["plus_di"] > h["minus_di"]
        and h["adx"] > bot.H1_ADX_ENTRY
        and previous["rsi"] <= bot.LONG_RSI_ENTRY
        and latest["rsi"] > bot.LONG_RSI_ENTRY
    )
    short_signal = (
        h["minus_di"] > h["plus_di"]
        and h["adx"] > bot.H1_ADX_ENTRY
        and previous["rsi"] >= bot.SHORT_RSI_ENTRY
        and latest["rsi"] < bot.SHORT_RSI_ENTRY
    )
    return {
        "time": latest["open_time"].isoformat(),
        "close": Decimal(str(latest["close"])),
        "rsi": float(latest["rsi"]),
        "adx": float(latest["adx"]),
        "h1_adx": float(h["adx"]),
        "h1_plus": float(h["plus_di"]),
        "h1_minus": float(h["minus_di"]),
        "long": bool(long_signal),
        "short": bool(short_signal),
        "m15": m15,
    }


def load_state():
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception:
        LOG.exception("State file unreadable; fail closed.")
        raise


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE_PATH)


def notify(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        LOG.warning("Telegram not configured; event was logged only.")
        return
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message, "disable_web_page_preview": True},
        timeout=10,
    )
    response.raise_for_status()
    if not response.json().get("ok"):
        raise RuntimeError("Telegram sendMessage failed.")


def order_quantity(margin, price, step, min_notional):
    notional = margin * Decimal(LEVERAGE)
    qty = floor_step(notional / price, step)
    if qty * price < Decimal(str(min_notional)):
        raise RuntimeError("Order notional is below exchange minimum; increase testnet margin or review filters.")
    return qty


def open_new_trade(side, signal, step, tick, min_notional, state):
    mark = Decimal(str(public_api("/fapi/v1/ticker/price", {"symbol": SYMBOL})["price"]))
    qty = order_quantity(INITIAL_MARGIN, mark, step, min_notional)
    api("POST", "/fapi/v1/leverage", {"symbol": SYMBOL, "leverage": LEVERAGE}, signed=True)
    order_side = "BUY" if side == "LONG" else "SELL"
    result = market_order(order_side, qty)
    # Re-read exchange truth; never infer a fill from the request alone.
    pos = position()
    if not pos["side"] or pos["side"] != side:
        raise RuntimeError("Entry order was submitted but exchange position could not be confirmed; halt and inspect testnet.")
    state.update({"side": side, "dca_used": False, "last_entry_signal": signal["time"], "last_action": "ENTRY"})
    save_state(state)
    ensure_exchange_stop(pos, tick)
    notify(f"🧪 TESTNET ENTRY {side} {SYMBOL}\nQty: {fmt_decimal(abs(pos['qty']))}\nEntry: {fmt_decimal(pos['entry'])}\nExchange hard SL: {fmt_decimal(stop_price(pos, tick))}\nOrder ID: {result.get('orderId')}\nĐã xác minh vị thế và lệnh SL phía sàn.")
    LOG.info("Opened %s position qty=%s", side, pos["qty"])


def close_position(pos, reason, tick):
    if not pos["side"] or pos["qty"] == 0:
        return
    # Ensure protective stop exists before requesting a market close.
    ensure_exchange_stop(pos, tick)
    side = "SELL" if pos["qty"] > 0 else "BUY"
    result = api("POST", "/fapi/v1/order", {
        "symbol": SYMBOL,
        "side": side,
        "type": "MARKET",
        "quantity": fmt_decimal(abs(pos["qty"])),
        "reduceOnly": "true",
        "newOrderRespType": "RESULT",
    }, signed=True)
    after = position()
    if after["qty"] != 0:
        raise RuntimeError("Close order returned but position remains open; protective stop retained, manual review required.")
    cancel_stops()
    notify(f"🧪 TESTNET CLOSE {reason}\nOrder ID: {result.get('orderId')}\nVị thế đã được xác minh đóng trên sàn.")
    LOG.warning("Closed position due to %s", reason)


def process_once(step, tick, min_notional):
    state = load_state()
    sig = get_signal()
    pos = position()

    # If restarted while a position exists, assume DCA already used to prevent repeat add-ons.
    if pos["side"] and state.get("side") != pos["side"]:
        state.update({"side": pos["side"], "dca_used": True, "reconciled_after_restart": True})
        save_state(state)
        notify("⚠️ TESTNET: phát hiện vị thế không khớp state cục bộ; tạm khóa DCA, kiểm tra và đồng bộ trạng thái.")
    elif not pos["side"] and state.get("side"):
        state = {"side": None, "dca_used": False, "last_flat_sync": time.time()}
        save_state(state)

    if not pos["side"]:
        if sig["long"] and state.get("last_entry_signal") != sig["time"]:
            open_new_trade("LONG", sig, step, tick, min_notional, state)
        elif sig["short"] and state.get("last_entry_signal") != sig["time"]:
            open_new_trade("SHORT", sig, step, tick, min_notional, state)
        else:
            LOG.info("No entry. candle=%s RSI=%.2f ADX15=%.2f ADX1h=%.2f", sig["time"], sig["rsi"], sig["adx"], sig["h1_adx"])
        return

    # Install/verify server-side protection before evaluating strategy actions.
    ensure_exchange_stop(pos, tick)
    roe = roe_pct(pos)
    LOG.info("Position=%s qty=%s entry=%s mark=%s ROE-est=%.2f%% DCA-used=%s",
             pos["side"], pos["qty"], pos["entry"], pos["mark"], roe, state.get("dca_used", True))

    if roe >= TP_ROE:
        close_position(pos, f"TP ROE {roe:.2f}%", tick)
        return

    # One DCA maximum; require both ROE trigger and M15 ADX threshold.
    if (
        not state.get("dca_used", True)
        and roe <= DCA_ROE
        and sig["adx"] > DCA_ADX
        and DCA_MARGIN > 0
    ):
        add_qty = order_quantity(DCA_MARGIN, pos["mark"], step, min_notional)
        side = "BUY" if pos["side"] == "LONG" else "SELL"
        result = market_order(side, add_qty)
        new_pos = position()
        if new_pos["side"] != pos["side"]:
            raise RuntimeError("DCA submitted but position reconciliation failed; halt and inspect exchange.")
        state.update({"side": pos["side"], "dca_used": True, "last_action": "DCA", "last_dca_order": result.get("orderId")})
        save_state(state)
        ensure_exchange_stop(new_pos, tick)
        notify(f"🧪 TESTNET DCA {pos['side']}\nROE-est trước DCA: {roe:.2f}%\nADX M15: {sig['adx']:.2f}\nQty thêm: {fmt_decimal(add_qty)}\nGiá vào TB mới: {fmt_decimal(new_pos['entry'])}\nĐã xác minh SL phía sàn sau DCA.")
        return

    # Existing signal bot uses 2-candle reversal + H1 trend-strength filter for soft SL.
    m15 = sig["m15"]
    if len(m15) >= 3:
        last, prev = m15.iloc[-1], m15.iloc[-2]
        two_bear = float(last["close"]) < float(last["open"]) and float(prev["close"]) < float(prev["open"])
        two_bull = float(last["close"]) > float(last["open"]) and float(prev["close"]) > float(prev["open"])
        h1_reversal = (
            (pos["side"] == "LONG" and sig["h1_minus"] > sig["h1_plus"])
            or (pos["side"] == "SHORT" and sig["h1_plus"] > sig["h1_minus"])
        ) and sig["h1_adx"] > bot.SOFT_SL_ADX
        adverse_two_candles = (pos["side"] == "LONG" and two_bear) or (pos["side"] == "SHORT" and two_bull)
        if roe <= HARD_SL_ROE and h1_reversal and adverse_two_candles:
            close_position(pos, f"Soft SL confirmed 2 candles; ROE-est {roe:.2f}%", tick)
            return

    # Do not permit an unprotected position: a missing stop causes ensure_exchange_stop to raise and halt.
    save_state({"side": pos["side"], "dca_used": bool(state.get("dca_used", True)), "last_checked": time.time()})


def main():
    require_safe_config()
    step, tick, min_notional = check_account_mode()
    api("POST", "/fapi/v1/leverage", {"symbol": SYMBOL, "leverage": LEVERAGE}, signed=True)
    notify("🧪 BTCUSDT TESTNET worker khởi động. Live trading bị vô hiệu hóa trong phiên bản này.")
    LOG.warning("TESTNET ONLY. Symbol=%s leverage=%sx initial_margin=%s dca_margin=%s", SYMBOL, LEVERAGE, INITIAL_MARGIN, DCA_MARGIN)
    while not STOP:
        try:
            process_once(step, tick, min_notional)
        except Exception:
            LOG.exception("Trading cycle failed. Worker will retry; inspect exchange positions and protective orders.")
            try:
                pos = position()
                if pos["side"]:
                    ensure_exchange_stop(pos, tick)
            except Exception:
                LOG.exception("CRITICAL: could not verify/re-establish exchange-side stop. Manual intervention required.")
                notify("🚨 TESTNET WORKER KHÔNG XÁC MINH ĐƯỢC SL PHÍA SÀN. Kiểm tra Binance Demo ngay; bot không mở thêm lệnh.")
        for _ in range(LOOP_SECONDS):
            if STOP:
                break
            time.sleep(1)
    LOG.warning("Worker stopped.")


if __name__ == "__main__":
    main()
