"""Read-only SQLite snapshot for the separately approved T0 G4 runtime gate.

This module never provisions schema, acquires/renews/releases leases, or writes candles.
It is not installed or invoked on the VPS by this change.
"""
import hashlib
import sqlite3
from pathlib import Path
from urllib.parse import quote

from market_data.store import INTERVAL_MS

LEASE_NAME = "binance-btcusdt-canonical"
REQUIRED_CANDLE_COLUMNS = {
    "exchange", "market_type", "symbol", "timeframe", "open_time_ms",
    "available_at_ms",
}
REQUIRED_LEASE_COLUMNS = {
    "lease_name", "owner", "generation", "expires_at_ms",
}


def _table_columns(connection, table):
    return {
        row[1] for row in connection.execute(
            "PRAGMA table_info(" + table + ")"
        ).fetchall()
    }


def inspect_sqlite_read_only(db_path, *, now_ms):
    """Return a sanitized, point-in-time SQLite/lease/watermark snapshot.

    The database must already exist. All SQL is read-only and the connection
    is opened with SQLite URI mode=ro plus PRAGMA query_only=ON.
    """
    if type(now_ms) is not int or now_ms < 0:
        raise ValueError("now_ms must be a nonnegative integer")
    path = Path(db_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError("canonical SQLite database does not exist")

    uri = path.as_uri() + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=5)
    except sqlite3.Error as exc:
        raise RuntimeError("canonical SQLite database is unreadable") from exc

    try:
        connection.execute("PRAGMA query_only=ON")
        if connection.execute("PRAGMA query_only").fetchone()[0] != 1:
            raise RuntimeError("SQLite query_only could not be enforced")

        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise RuntimeError("SQLite integrity check failed")

        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "candles" not in tables:
            raise RuntimeError("required candles table is missing")
        if "feeder_leases" not in tables:
            raise RuntimeError("required feeder_leases table is missing")
        if not REQUIRED_CANDLE_COLUMNS <= _table_columns(connection, "candles"):
            raise RuntimeError("candles table schema is incompatible")
        if not REQUIRED_LEASE_COLUMNS <= _table_columns(connection, "feeder_leases"):
            raise RuntimeError("feeder_leases table schema is incompatible")

        connection.execute("BEGIN")
        lease_rows = connection.execute(
            """SELECT owner, generation, expires_at_ms
               FROM feeder_leases WHERE lease_name=?""",
            (LEASE_NAME,),
        ).fetchall()
        if len(lease_rows) > 1:
            raise RuntimeError("canonical lease identity is not unique")
        if not lease_rows:
            lease = {
                "state": "MISSING",
                "valid": False,
                "generation": None,
                "expires_at_ms": None,
                "owner_fingerprint": None,
            }
        else:
            owner, generation, expires_at_ms = lease_rows[0]
            valid_fields = (
                isinstance(owner, str) and bool(owner.strip())
                and type(generation) is int and generation >= 1
                and type(expires_at_ms) is int and expires_at_ms >= 0
            )
            valid = bool(valid_fields and expires_at_ms > now_ms)
            fingerprint = (
                hashlib.sha256(owner.encode("utf-8")).hexdigest()[:16]
                if isinstance(owner, str) and owner else None
            )
            lease = {
                "state": "VALID" if valid else (
                    "EXPIRED" if valid_fields and expires_at_ms <= now_ms
                    else "INVALID"
                ),
                "valid": valid,
                "generation": generation if type(generation) is int else None,
                "expires_at_ms": expires_at_ms if type(expires_at_ms) is int else None,
                "owner_fingerprint": fingerprint,
            }

        timeframes = {}
        for timeframe, interval_ms in INTERVAL_MS.items():
            row = connection.execute(
                """SELECT open_time_ms, available_at_ms FROM candles
                   WHERE exchange='binance' AND market_type='USDT_PERPETUAL'
                     AND symbol='BTCUSDT' AND timeframe=?
                   ORDER BY open_time_ms DESC LIMIT 1""",
                (timeframe,),
            ).fetchone()
            if row is None:
                timeframes[timeframe] = {
                    "latest_open_time_ms": None,
                    "latest_close_time_ms": None,
                    "latest_available_at_ms": None,
                    "close_lag_ms": None,
                }
                continue
            open_time_ms, available_at_ms = row
            if (type(open_time_ms) is not int or type(available_at_ms) is not int
                    or open_time_ms < 0 or available_at_ms < 0):
                raise RuntimeError("candle watermark contains invalid timestamps")
            close_time_ms = open_time_ms + interval_ms
            timeframes[timeframe] = {
                "latest_open_time_ms": open_time_ms,
                "latest_close_time_ms": close_time_ms,
                "latest_available_at_ms": available_at_ms,
                "close_lag_ms": now_ms - close_time_ms,
            }

        return {
            "integrity": "ok",
            "lease": lease,
            "timeframes": timeframes,
            "observed_at_ms": now_ms,
            "read_only": True,
        }
    except sqlite3.Error as exc:
        raise RuntimeError("read-only SQLite inspection failed") from exc
    finally:
        connection.close()
