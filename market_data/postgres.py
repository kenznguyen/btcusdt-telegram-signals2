"""PostgreSQL/TimescaleDB adapter ported from PR #63's PostgresCandleStore."""

from contextlib import contextmanager
from dataclasses import dataclass
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


@dataclass(frozen=True)
class PostgresLease:
    owner: str
    generation: int
    expires_at: object


class PostgresLeaseStore:
    """PostgreSQL singleton lease with DB-clock expiry and monotonic fencing."""

    def __init__(self, location, lease_name="binance-btcusdt-canonical"):
        if not isinstance(location, str) or not location.strip():
            raise ValueError("location must be a non-empty PostgreSQL DSN")
        if not isinstance(lease_name, str) or not lease_name.strip():
            raise ValueError("lease_name must be a non-empty string")
        self.location = location
        self.lease_name = lease_name

    @staticmethod
    def _validate(owner, generation=None, ttl_seconds=None):
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError("owner must be a non-empty string")
        if generation is not None and (type(generation) is not int or generation < 1):
            raise ValueError("generation must be a positive integer")
        if ttl_seconds is not None and (type(ttl_seconds) is not int or ttl_seconds <= 0):
            raise ValueError("ttl_seconds must be a positive integer")

    def acquire(self, owner, ttl_seconds=60):
        self._validate(owner, ttl_seconds=ttl_seconds)
        with connection(self.location) as database:
            database.execute(
                """INSERT INTO market_data.feeder_leases
                   (lease_name, owner_id, generation, expires_at)
                   VALUES (%s, NULL, 0, '1970-01-01 00:00:00+00'::timestamptz)
                   ON CONFLICT (lease_name) DO NOTHING""",
                (self.lease_name,),
            )
            current = database.execute(
                """SELECT owner_id, generation, expires_at
                   FROM market_data.feeder_leases
                   WHERE lease_name=%s
                   FOR UPDATE""",
                (self.lease_name,),
            ).fetchone()
            current_owner, generation, expires_at = current
            # Evaluate expiry only after FOR UPDATE has acquired the row lock.
            # A projection evaluated before a lock wait can otherwise be stale.
            active = database.execute(
                """SELECT expires_at > clock_timestamp()
                   FROM market_data.feeder_leases WHERE lease_name=%s""",
                (self.lease_name,),
            ).fetchone()[0]
            if active:
                if current_owner == owner:
                    return PostgresLease(owner, generation, expires_at)
                return None
            row = database.execute(
                """UPDATE market_data.feeder_leases
                   SET owner_id=%s, generation=generation+1,
                       expires_at=clock_timestamp() + (%s * interval '1 second'),
                       updated_at=clock_timestamp()
                   WHERE lease_name=%s
                   RETURNING generation, expires_at""",
                (owner, ttl_seconds, self.lease_name),
            ).fetchone()
            return PostgresLease(owner, row[0], row[1])

    def heartbeat(self, owner, generation, ttl_seconds=60):
        self._validate(owner, generation, ttl_seconds)
        with connection(self.location) as database:
            row = database.execute(
                """UPDATE market_data.feeder_leases
                   SET expires_at=clock_timestamp() + (%s * interval '1 second'),
                       updated_at=clock_timestamp()
                   WHERE lease_name=%s AND owner_id=%s AND generation=%s
                     AND expires_at > clock_timestamp()
                   RETURNING generation""",
                (ttl_seconds, self.lease_name, owner, generation),
            ).fetchone()
            return row is not None

    def is_current(self, owner, generation):
        self._validate(owner, generation)
        with connection(self.location, read_only=True) as database:
            row = database.execute(
                """SELECT 1 FROM market_data.feeder_leases
                   WHERE lease_name=%s AND owner_id=%s AND generation=%s
                     AND expires_at > clock_timestamp()""",
                (self.lease_name, owner, generation),
            ).fetchone()
            return row is not None

    def release(self, owner, generation):
        self._validate(owner, generation)
        with connection(self.location) as database:
            row = database.execute(
                """UPDATE market_data.feeder_leases
                   SET owner_id=NULL, expires_at='1970-01-01 00:00:00+00'::timestamptz,
                       updated_at=clock_timestamp()
                   WHERE lease_name=%s AND owner_id=%s AND generation=%s
                   RETURNING generation""",
                (self.lease_name, owner, generation),
            ).fetchone()
            return row is not None


class PostgresWriteGateway:
    """Atomic PostgreSQL lease-fenced writer for canonical closed candles."""

    def __init__(self, location, *, lease_name, owner_id, generation_provider):
        if not isinstance(location, str) or not location.strip():
            raise ValueError("location must be a non-empty PostgreSQL DSN")
        if not isinstance(lease_name, str) or not lease_name.strip():
            raise ValueError("lease_name must be a non-empty string")
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise ValueError("owner_id must be a non-empty string")
        if not callable(generation_provider):
            raise TypeError("generation_provider must be callable")
        self.location = location
        self.lease_name = lease_name
        self.owner_id = owner_id
        self.generation_provider = generation_provider

    @staticmethod
    def _validated_batch(candles):
        batch = list(candles)
        validated = []
        for candle in batch:
            if not isinstance(candle, Candle):
                raise ValueError("Expected validated Candle values")
            # Reconstruct to reject mutated/fabricated instances before opening
            # a transaction; the database constraints remain the final guard.
            validated.append(Candle(
                candle.timeframe, candle.open_time_ms, candle.open, candle.high,
                candle.low, candle.close, candle.volume, candle.available_at_ms,
                candle.symbol,
            ))
        return validated

    def write_batch(self, candles):
        batch = self._validated_batch(candles)
        generation = self.generation_provider()
        if type(generation) is not int or generation < 1:
            raise PermissionError("Feeder lease is unavailable; canonical write rejected")

        inserted = 0
        with connection(self.location) as database:
            lease = database.execute(
                """SELECT owner_id, generation
                   FROM market_data.feeder_leases
                   WHERE lease_name=%s
                   FOR UPDATE""",
                (self.lease_name,),
            ).fetchone()
            if (
                lease is None or lease[0] != self.owner_id
                or lease[1] != generation
            ):
                raise PermissionError("Feeder lease is not current; canonical write rejected")
            # Recheck using the database wall clock after the row lock is held.
            active = database.execute(
                """SELECT expires_at > clock_timestamp()
                   FROM market_data.feeder_leases
                   WHERE lease_name=%s AND owner_id=%s AND generation=%s""",
                (self.lease_name, self.owner_id, generation),
            ).fetchone()
            if active is None or not active[0]:
                raise PermissionError("Feeder lease is not current; canonical write rejected")

            for candle in batch:
                key = (
                    EXCHANGE, MARKET_TYPE, candle.symbol,
                    candle.timeframe, candle.open_time_ms,
                )
                values = tuple(Decimal(getattr(candle, name)) for name in PRICE_FIELDS)
                existing = database.execute(
                    """SELECT open, high, low, close, volume
                       FROM market_data.candles
                       WHERE exchange=%s AND market_type=%s AND symbol=%s
                         AND timeframe=%s AND open_time_ms=%s
                       FOR UPDATE""",
                    key,
                ).fetchone()
                if existing is not None:
                    if tuple(existing) != values:
                        raise ValueError("Conflicting closed candle; canonical history was not overwritten")
                    continue

                created = database.execute(
                    """INSERT INTO market_data.candles
                       (exchange, market_type, symbol, timeframe, open_time_ms,
                        open, high, low, close, volume, available_at_ms)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (exchange, market_type, symbol, timeframe, open_time_ms)
                       DO NOTHING
                       RETURNING open_time_ms""",
                    key + values + (candle.available_at_ms,),
                ).fetchone()
                if created is None:
                    existing = database.execute(
                        """SELECT open, high, low, close, volume
                           FROM market_data.candles
                           WHERE exchange=%s AND market_type=%s AND symbol=%s
                             AND timeframe=%s AND open_time_ms=%s""",
                        key,
                    ).fetchone()
                    if existing is None or tuple(existing) != values:
                        raise ValueError("Conflicting closed candle; canonical history was not overwritten")
                else:
                    inserted += 1

            still_current = database.execute(
                """SELECT expires_at > clock_timestamp()
                   FROM market_data.feeder_leases
                   WHERE lease_name=%s AND owner_id=%s AND generation=%s""",
                (self.lease_name, self.owner_id, generation),
            ).fetchone()
            if still_current is None or not still_current[0]:
                raise PermissionError("Feeder lease expired before commit; canonical write rejected")
        return inserted
