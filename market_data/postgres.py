"""PostgreSQL/TimescaleDB adapter ported from PR #63's PostgresCandleStore."""

from contextlib import contextmanager
from decimal import Decimal
import hashlib
import json

from market_data.store import Candle, EXCHANGE, MARKET_TYPE, PRICE_FIELDS, INTERVAL_MS, MAX_CANDLES, MAX_TIMESTAMP


class StoreUnavailable(RuntimeError):
    pass


@contextmanager
def connection(location, *, read_only=False):
    try:
        import psycopg
    except ImportError:
        raise StoreUnavailable("PostgreSQL driver is unavailable") from None
    try:
        with psycopg.connect(location, connect_timeout=5, autocommit=True) as database:
            database.execute("SET statement_timeout = 5000")
            database.execute("SET lock_timeout = 5000")
            with database.transaction():
                if read_only:
                    database.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                yield database
    except psycopg.Error:
        raise StoreUnavailable("PostgreSQL storage is unavailable") from None


def _validate_window(symbol, timeframe, start_ms, end_ms, as_of_ms):
    if symbol != "BTCUSDT" or timeframe not in INTERVAL_MS:
        raise ValueError("Unsupported market or timeframe")
    if type(start_ms) is not int or type(end_ms) is not int or not 0 <= start_ms <= MAX_TIMESTAMP or not 0 <= end_ms <= MAX_TIMESTAMP:
        raise ValueError("Invalid window timestamps")
    step = INTERVAL_MS[timeframe]
    if start_ms % step or end_ms % step or not 0 < end_ms - start_ms <= MAX_CANDLES * step:
        raise ValueError("Window must be aligned, nonempty and bounded")
    if as_of_ms is not None and (type(as_of_ms) is not int or not 0 <= as_of_ms <= MAX_TIMESTAMP):
        raise ValueError("Invalid as-of timestamp")
    return start_ms, end_ms, step


def _render_window(symbol, timeframe, start, end, as_of_ms, candles):
    step = INTERVAL_MS[timeframe]
    gaps, cursor = [], start
    for candle in candles:
        if candle["openTimeMs"] > cursor:
            gaps.append({"startMs": cursor, "endMs": candle["openTimeMs"]})
        cursor = candle["closeTimeMs"]
    if cursor < end:
        gaps.append({"startMs": cursor, "endMs": end})
    result = {"exchange": EXCHANGE, "marketType": MARKET_TYPE, "symbol": symbol,
              "timeframe": timeframe, "startMs": start, "endMs": end,
              "asOfMs": as_of_ms, "candles": candles}
    digest = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    result["datasetVersion"] = "sha256:" + digest
    result["coverage"] = {"expected": (end-start)//step, "returned": len(candles),
                          "complete": not gaps, "gaps": gaps}
    return result


class PostgresCandleStore:
    """Read-only adapter; canonical writes are deliberately disabled."""

    canonical_writes_disabled = True

    def __init__(self, location):
        self.location = location

def read_window(location, symbol, timeframe, start_ms, end_ms, as_of_ms=None):
    start, end, _ = _validate_window(symbol, timeframe, start_ms, end_ms, as_of_ms)
    with connection(location, read_only=True) as database:
        rows = database.execute("""SELECT timeframe,open_time_ms,open,high,low,close,
                volume,available_at_ms,symbol FROM market_data.candles
            WHERE exchange=%s AND market_type=%s AND symbol=%s AND timeframe=%s
                AND open_time_ms>=%s AND open_time_ms<%s
                AND (%s::bigint IS NULL OR available_at_ms<=%s::bigint) ORDER BY open_time_ms""",
            (EXCHANGE, MARKET_TYPE, symbol, timeframe, start, end, as_of_ms, as_of_ms)).fetchall()
        candles = [Candle(row[0], row[1], *(format(value, "f") for value in row[2:7]), row[7], row[8]).as_dict()
                   for row in rows]
    return _render_window(symbol, timeframe, start, end, as_of_ms, candles)
