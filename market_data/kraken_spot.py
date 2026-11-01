"""Read-only Kraken BTC/USDT spot adapter.

This adapter emits source-typed candles only. It does not persist data, mutate
the Binance canonical store, provide failover, or place orders.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import time

INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000}
MAX_CANDLES = 2000
MAX_TIMESTAMP = 2**63 - 1
EXCHANGE_ID = "kraken"
MARKET_TYPE = "SPOT"
SYMBOL = "BTC/USDT"


def _timestamp(value, label):
    if type(value) is not int or not 0 <= value <= MAX_TIMESTAMP:
        raise ValueError(f"{label} must be a nonnegative 64-bit integer")
    return value


def _decimal_text(value, *, allow_zero=False):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Invalid OHLCV decimal") from exc
    if not number.is_finite() or number < 0 or (not allow_zero and number == 0):
        raise ValueError("OHLC prices must be positive and volume nonnegative")
    if len(number.as_tuple().digits) > 40 or not -30 <= number.as_tuple().exponent <= 30:
        raise ValueError("OHLCV decimal is outside supported precision")
    normalized = format(number, "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized or "0"


@dataclass(frozen=True)
class InstrumentIdentity:
    exchange: str
    market_type: str
    native_market_id: str
    canonical_symbol: str


@dataclass(frozen=True)
class SourceCandle:
    instrument: InstrumentIdentity
    timeframe: str
    open_time_ms: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    available_at_ms: int

    def __post_init__(self):
        interval = INTERVAL_MS.get(self.timeframe)
        if interval is None:
            raise ValueError("Unsupported source candle timeframe")
        opened = _timestamp(self.open_time_ms, "Candle open time")
        available = _timestamp(self.available_at_ms, "Availability time")
        if opened % interval or available < opened + interval:
            raise ValueError("Candle must be aligned, closed, and observed")
        values = {}
        for field in ("open", "high", "low", "close", "volume"):
            values[field] = _decimal_text(
                getattr(self, field), allow_zero=field == "volume"
            )
            object.__setattr__(self, field, values[field])
        low, high = Decimal(values["low"]), Decimal(values["high"])
        if (
            low > high
            or not low <= Decimal(values["open"]) <= high
            or not low <= Decimal(values["close"]) <= high
        ):
            raise ValueError("Inconsistent source candle OHLC bounds")

    def as_dict(self):
        interval = INTERVAL_MS[self.timeframe]
        return {
            "exchange": self.instrument.exchange,
            "marketType": self.instrument.market_type,
            "nativeMarketId": self.instrument.native_market_id,
            "symbol": self.instrument.canonical_symbol,
            "timeframe": self.timeframe,
            "openTimeMs": self.open_time_ms,
            "closeTimeMs": self.open_time_ms + interval,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "isClosed": True,
            "availableAtMs": self.available_at_ms,
            "availabilityKind": "FIRST_OBSERVED",
            "quality": "VALIDATED",
            "source": "ccxt.kraken",
        }


class KrakenSpotAdapter:
    """Fetch validated, closed BTC/USDT spot candles from Kraken via CCXT."""

    def __init__(self, exchange):
        self.exchange = exchange

    def validate_market(self):
        if getattr(self.exchange, "id", None) != EXCHANGE_ID:
            raise ValueError("Kraken spot adapter requires the Kraken exchange")
        market = self.exchange.load_markets().get(SYMBOL)
        if not isinstance(market, dict):
            raise ValueError("Kraken BTC/USDT spot market is unavailable")
        if any(
            market.get(key) != value
            for key, value in {
                "symbol": SYMBOL,
                "base": "BTC",
                "quote": "USDT",
                "active": True,
                "spot": True,
            }.items()
        ) or market.get("swap") is True:
            raise ValueError("Market is not active Kraken BTC/USDT spot")
        native_market_id = market.get("id")
        if not isinstance(native_market_id, str) or not native_market_id.strip():
            raise ValueError("Kraken market has no valid native market identifier")
        return InstrumentIdentity(
            exchange=EXCHANGE_ID,
            market_type=MARKET_TYPE,
            native_market_id=native_market_id,
            canonical_symbol=SYMBOL,
        )

    def fetch_closed_window(self, timeframe, start_ms, end_ms, *, now_ms=None):
        interval = INTERVAL_MS.get(timeframe)
        start = _timestamp(start_ms, "Window start")
        end = _timestamp(end_ms, "Window end")
        if interval is None or start % interval or end % interval or not start < end:
            raise ValueError("Use a supported timeframe and aligned nonempty window")
        expected = (end - start) // interval
        if expected > MAX_CANDLES:
            raise ValueError("Window exceeds the candle limit")

        instrument = self.validate_market()
        server_time = _timestamp(self.exchange.fetch_time(), "Kraken server time")
        rows = self.exchange.fetch_ohlcv(
            SYMBOL, timeframe=timeframe, since=start, limit=expected
        )
        observed_at = (
            _timestamp(now_ms, "Observation time")
            if now_ms is not None
            else _timestamp(time.time_ns() // 1_000_000, "Observation time")
        )
        closed_through = min(server_time, observed_at)
        if not isinstance(rows, (list, tuple)) or len(rows) > expected:
            raise ValueError("Invalid Kraken OHLCV page")

        candles, previous = [], None
        for row in rows:
            if not isinstance(row, (list, tuple)) or len(row) != 6:
                raise ValueError("Invalid Kraken OHLCV row")
            opened = _timestamp(row[0], "Candle open time")
            if opened % interval:
                raise ValueError("Kraken candle timestamp is not timeframe-aligned")
            if previous is not None and opened <= previous:
                raise ValueError("Kraken candles are duplicated or out of order")
            previous = opened
            if not start <= opened < end or opened + interval > closed_through:
                continue
            values = [
                _decimal_text(row[1]),
                _decimal_text(row[2]),
                _decimal_text(row[3]),
                _decimal_text(row[4]),
                _decimal_text(row[5], allow_zero=True),
            ]
            candles.append(SourceCandle(
                instrument=instrument,
                timeframe=timeframe,
                open_time_ms=opened,
                open=values[0],
                high=values[1],
                low=values[2],
                close=values[3],
                volume=values[4],
                available_at_ms=observed_at,
            ))
        return candles
