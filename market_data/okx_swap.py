"""Read-only OKX BTC-USDT-SWAP linear perpetual shadow adapter."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000}
OKX_BAR = {"15m": "15m", "1h": "1H"}
MAX_CANDLES = 300
BASE_URL = "https://www.okx.com"
EXCHANGE = "okx"
MARKET_TYPE = "LINEAR_PERPETUAL"
SYMBOL = "BTC-USDT-SWAP"


def _integer(value, label):
    if type(value) is not int or not 0 <= value < 2**63:
        raise ValueError(f"{label} must be a nonnegative 64-bit integer")
    return value


def _decimal(value, label, *, zero=False):
    if not isinstance(value, str) or not value or len(value) > 80:
        raise ValueError(f"OKX {label} must be a decimal string")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid OKX {label}") from exc
    if not number.is_finite() or number < 0 or (not zero and number == 0):
        raise ValueError(f"Invalid OKX {label} range")
    if len(number.as_tuple().digits) > 40 or not -30 <= number.as_tuple().exponent <= 30:
        raise ValueError(f"OKX {label} exceeds supported precision")
    return format(number, "f")


@dataclass(frozen=True)
class OkxSwapCandle:
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
            raise ValueError("Unsupported OKX timeframe")
        opened = _integer(self.open_time_ms, "Candle open time")
        available = _integer(self.available_at_ms, "Availability time")
        if opened % interval or available < opened + interval:
            raise ValueError("OKX candle must be aligned, closed and observed")
        for name in ("open", "high", "low", "close"):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))
        object.__setattr__(self, "volume_btc", _decimal(self.volume_btc, "base volume", zero=True))
        object.__setattr__(self, "turnover_usdt", _decimal(self.turnover_usdt, "quote turnover", zero=True))
        low, high = Decimal(self.low), Decimal(self.high)
        if low > high or not low <= Decimal(self.open) <= high or not low <= Decimal(self.close) <= high:
            raise ValueError("Inconsistent OKX OHLC bounds")

    def as_dict(self):
        return {
            "exchange": EXCHANGE, "marketType": MARKET_TYPE, "instType": "SWAP",
            "symbol": SYMBOL, "timeframe": self.timeframe,
            "openTimeMs": self.open_time_ms,
            "closeTimeMs": self.open_time_ms + INTERVAL_MS[self.timeframe],
            "open": self.open, "high": self.high, "low": self.low, "close": self.close,
            "volumeBtc": self.volume_btc, "turnoverUsdt": self.turnover_usdt,
            "isClosed": True, "availableAtMs": self.available_at_ms,
            "availabilityKind": "FIRST_OBSERVED", "source": "okx.api.v5.market.candles",
        }


class OkxSwapAdapter:
    def __init__(self, request_json=None, *, base_url=BASE_URL):
        self.request_json = request_json or self._request_json
        self.base_url = base_url.rstrip("/")

    def _request_json(self, path, params):
        url = self.base_url + path + "?" + urlencode(params)
        request = Request(url, headers={"User-Agent": "btc-shadow-market-data/1.0"})
        try:
            with urlopen(request, timeout=15) as response:
                if response.status != 200:
                    raise RuntimeError(f"OKX HTTP status {response.status} for {path}")
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = " ".join(exc.read(512).decode("utf-8", errors="replace").split())[:240]
            raise RuntimeError(f"OKX HTTP {exc.code} {exc.reason} for {path}. response={detail}") from exc
        if not isinstance(payload, dict) or payload.get("code") != "0" or not isinstance(payload.get("data"), list):
            raise ValueError("OKX API returned an unsuccessful or malformed response")
        return payload["data"]

    def validate_instrument(self):
        rows = self.request_json("/api/v5/public/instruments", {
            "instType": "SWAP", "instId": SYMBOL,
        })
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            raise ValueError("OKX BTC-USDT-SWAP instrument is unavailable")
        item = rows[0]
        expected = {
            "instId": SYMBOL, "instType": "SWAP", "ctType": "linear",
            "state": "live", "baseCcy": "BTC", "quoteCcy": "USDT",
            "settleCcy": "USDT",
        }
        if any(item.get(key) != value for key, value in expected.items()):
            raise ValueError("Instrument is not active BTC-USDT linear USDT-settled swap")
        return item

    def server_time_ms(self):
        rows = self.request_json("/api/v5/public/time", {})
        if len(rows) != 1 or not isinstance(rows[0], dict):
            raise ValueError("Invalid OKX server time response")
        value = rows[0].get("ts")
        if not isinstance(value, str) or not value.isdigit():
            raise ValueError("OKX server time is missing or invalid")
        return int(value)

    def fetch_closed_window(self, timeframe, start_ms, end_ms, *, now_ms=None):
        interval = INTERVAL_MS.get(timeframe)
        start, end = _integer(start_ms, "Window start"), _integer(end_ms, "Window end")
        if interval is None or start % interval or end % interval or not start < end:
            raise ValueError("Use an aligned, nonempty 15m or 1h window")
        expected = (end - start) // interval
        if expected > MAX_CANDLES:
            raise ValueError("Window exceeds OKX candles page limit")
        self.validate_instrument()
        server_ms = self.server_time_ms()
        observed = _integer(now_ms, "Observation time") if now_ms is not None else time.time_ns() // 1_000_000
        closed_through = min(server_ms, observed)
        rows = self.request_json("/api/v5/market/candles", {
            "instId": SYMBOL, "bar": OKX_BAR[timeframe],
            "after": str(end), "limit": str(min(MAX_CANDLES, expected + 5)),
        })
        if not isinstance(rows, list) or len(rows) > MAX_CANDLES:
            raise ValueError("Invalid OKX candles page")
        candles, seen = [], set()
        for row in reversed(rows):
            if not isinstance(row, list) or len(row) != 9:
                raise ValueError("Malformed OKX candle row")
            if not isinstance(row[0], str) or not row[0].isdigit():
                raise ValueError("Invalid OKX candle timestamp")
            opened = int(row[0])
            if opened in seen:
                raise ValueError("Duplicate OKX candle")
            seen.add(opened)
            if opened % interval or not start <= opened < end:
                continue
            if row[8] not in ("0", "1"):
                raise ValueError("Invalid OKX candle confirmation flag")
            if row[8] != "1" or opened + interval > closed_through:
                continue
            # OKX SWAP candle fields: vol=contracts, volCcy=base BTC,
            # volCcyQuote=quote USDT. Never treat contract count as BTC volume.
            candles.append(OkxSwapCandle(
                timeframe, opened, row[1], row[2], row[3], row[4],
                row[6], row[7], observed,
            ))
        return candles
