"""Read-only Bybit V5 BTCUSDT linear perpetual shadow-data adapter.

Uses public REST only. It never calls the Binance canonical store or any
strategy, backtest, paper-execution, or order-submission interface.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000}
BYBIT_INTERVAL = {"15m": "15", "1h": "60"}
MAX_CANDLES = 1000
BASE_URL = "https://api.bybit.com"
EXCHANGE = "bybit"
MARKET_TYPE = "LINEAR_PERPETUAL"
SYMBOL = "BTCUSDT"


def _integer(value, label):
    if type(value) is not int or not 0 <= value < 2**63:
        raise ValueError(f"{label} must be a nonnegative 64-bit integer")
    return value


def _decimal(value, *, zero=False):
    if not isinstance(value, str) or not value or len(value) > 80:
        raise ValueError("Bybit OHLCV values must be decimal strings")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Invalid Bybit OHLCV decimal") from exc
    if not number.is_finite() or number < 0 or (not zero and number == 0):
        raise ValueError("Prices must be positive and volume/turnover nonnegative")
    if len(number.as_tuple().digits) > 40 or not -30 <= number.as_tuple().exponent <= 30:
        raise ValueError("Bybit decimal is outside supported precision")
    return format(number, "f")


@dataclass(frozen=True)
class BybitLinearCandle:
    timeframe: str
    open_time_ms: int
    open: str
    high: str
    low: str
    close: str
    volume_btc: str
    turnover_usdt: str
    available_at_ms: int

    def __post_init__(self):
        interval = INTERVAL_MS.get(self.timeframe)
        if interval is None:
            raise ValueError("Unsupported Bybit timeframe")
        opened = _integer(self.open_time_ms, "Candle open time")
        available = _integer(self.available_at_ms, "Availability time")
        if opened % interval or available < opened + interval:
            raise ValueError("Bybit candle must be aligned, closed and observed")
        for name in ("open", "high", "low", "close"):
            object.__setattr__(self, name, _decimal(getattr(self, name)))
        object.__setattr__(self, "volume_btc", _decimal(self.volume_btc, zero=True))
        object.__setattr__(self, "turnover_usdt", _decimal(self.turnover_usdt, zero=True))
        low, high = Decimal(self.low), Decimal(self.high)
        if not low <= Decimal(self.open) <= high or not low <= Decimal(self.close) <= high or low > high:
            raise ValueError("Inconsistent Bybit OHLC bounds")

    def as_dict(self):
        return {
            "exchange": EXCHANGE,
            "marketType": MARKET_TYPE,
            "category": "linear",
            "symbol": SYMBOL,
            "timeframe": self.timeframe,
            "openTimeMs": self.open_time_ms,
            "closeTimeMs": self.open_time_ms + INTERVAL_MS[self.timeframe],
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volumeBtc": self.volume_btc,
            "turnoverUsdt": self.turnover_usdt,
            "isClosed": True,
            "availableAtMs": self.available_at_ms,
            "availabilityKind": "FIRST_OBSERVED",
            "source": "bybit.v5.market.kline",
        }


class BybitLinearAdapter:
    def __init__(self, request_json=None, *, base_url=BASE_URL):
        self.request_json = request_json or self._request_json
        self.base_url = base_url.rstrip("/")

    def _request_json(self, path, params):
        url = self.base_url + path + "?" + urlencode(params)
        request = Request(url, headers={"User-Agent": "btc-shadow-market-data/1.0"})
        try:
            with urlopen(request, timeout=15) as response:
                if response.status != 200:
                    raise RuntimeError(f"Bybit HTTP status {response.status} for {path}")
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            # Preserve a short, non-secret response hint for diagnosing regional
            # denials, WAF responses and API-level HTTP failures in CI logs.
            raw_detail = exc.read(512).decode("utf-8", errors="replace").strip()
            detail = ""
            if raw_detail:
                try:
                    body = json.loads(raw_detail)
                    if isinstance(body, dict):
                        code = body.get("retCode")
                        message = body.get("retMsg")
                        detail = f" retCode={code!r} retMsg={message!r}"
                except (ValueError, TypeError):
                    detail = " response=" + " ".join(raw_detail.split())[:240]
            raise RuntimeError(
                f"Bybit HTTP {exc.code} {exc.reason} for {path}.{detail}"
            ) from exc
        if not isinstance(payload, dict) or payload.get("retCode") != 0:
            raise ValueError("Bybit API returned an unsuccessful response")
        return payload.get("result", {})

    def validate_instrument(self):
        result = self.request_json("/v5/market/instruments-info", {
            "category": "linear", "symbol": SYMBOL,
        })
        items = result.get("list") if isinstance(result, dict) else None
        if not isinstance(items, list) or len(items) != 1:
            raise ValueError("Bybit BTCUSDT linear instrument is unavailable")
        item = items[0]
        expected = {
            "symbol": SYMBOL, "contractType": "LinearPerpetual",
            "status": "Trading", "baseCoin": "BTC", "quoteCoin": "USDT",
        }
        if not isinstance(item, dict) or any(item.get(k) != v for k, v in expected.items()):
            raise ValueError("Instrument is not active BTCUSDT linear perpetual")
        return item

    def server_time_ms(self):
        result = self.request_json("/v5/market/time", {})
        if not isinstance(result, dict):
            raise ValueError("Invalid Bybit server time response")
        if "timeNano" in result:
            value = result["timeNano"]
            if not isinstance(value, str) or not value.isdigit():
                raise ValueError("Invalid Bybit nanosecond server time")
            return int(value) // 1_000_000
        if "timeSecond" in result:
            value = result["timeSecond"]
            if not isinstance(value, str) or not value.isdigit():
                raise ValueError("Invalid Bybit server time")
            return int(value) * 1000
        raise ValueError("Bybit server time is missing")

    def fetch_closed_window(self, timeframe, start_ms, end_ms, *, now_ms=None):
        interval = INTERVAL_MS.get(timeframe)
        start, end = _integer(start_ms, "Window start"), _integer(end_ms, "Window end")
        if interval is None or start % interval or end % interval or not start < end:
            raise ValueError("Use an aligned, nonempty 15m or 1h window")
        expected = (end - start) // interval
        if expected > MAX_CANDLES:
            raise ValueError("Window exceeds Bybit V5 page limit")
        self.validate_instrument()
        server_ms = self.server_time_ms()
        observed = _integer(now_ms, "Observation time") if now_ms is not None else time.time_ns() // 1_000_000
        closed_through = min(server_ms, observed)
        result = self.request_json("/v5/market/kline", {
            "category": "linear", "symbol": SYMBOL,
            "interval": BYBIT_INTERVAL[timeframe],
            "start": str(start), "end": str(end - 1), "limit": str(expected),
        })
        rows = result.get("list") if isinstance(result, dict) else None
        if not isinstance(rows, list) or len(rows) > expected:
            raise ValueError("Invalid Bybit kline page")
        candles, seen = [], set()
        for row in reversed(rows):
            if not isinstance(row, list) or len(row) != 7:
                raise ValueError("Malformed Bybit kline row")
            if not isinstance(row[0], str) or not row[0].isdigit():
                raise ValueError("Invalid Bybit candle timestamp")
            opened = int(row[0])
            if opened in seen:
                raise ValueError("Duplicate Bybit candle")
            seen.add(opened)
            if opened % interval or not start <= opened < end:
                raise ValueError("Bybit candle timestamp is unaligned or out of range")
            if opened + interval > closed_through:
                continue
            candles.append(BybitLinearCandle(
                timeframe, opened, row[1], row[2], row[3], row[4],
                row[5], row[6], observed,
            ))
        return candles
