"""Durable SQLite lifecycle status shared by the T0 feeder and HTTP health API.

Status writes are fenced by the canonical feeder lease generation. API reads are
read-only and independently verify that the published owner still holds a live
lease, so a dead/stale process cannot remain READY.
"""
import sqlite3
from contextlib import closing
from pathlib import Path

from market_data.store import EXCHANGE, MARKET_TYPE, SYMBOL, INTERVAL_MS

_STATES = {"STARTING", "RUNNING", "LEASE_LOST", "FAILED", "STOPPED"}


class FeederRuntimeStatusStore:
    def __init__(self, db_path, lease_name="binance-btcusdt-canonical"):
        if not db_path:
            raise ValueError("db_path is required")
        self.db_path = str(Path(db_path))
        self.lease_name = lease_name

    def _connect(self):
        connection = sqlite3.connect(self.db_path, timeout=5, isolation_level=None)
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _ensure_table(self, connection):
        connection.execute("""CREATE TABLE IF NOT EXISTS feeder_runtime_status (
            lease_name TEXT PRIMARY KEY,
            owner TEXT NOT NULL,
            generation INTEGER NOT NULL CHECK(generation >= 1),
            state TEXT NOT NULL,
            recovery_complete INTEGER NOT NULL CHECK(recovery_complete IN (0,1)),
            updated_at_ms INTEGER NOT NULL
        )""")

    def publish(self, owner, generation, state, *, now_ms, recovery_complete):
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError("owner must be a non-empty string")
        if type(generation) is not int or generation < 1:
            raise ValueError("generation must be positive")
        if state not in _STATES:
            raise ValueError("unsupported feeder runtime state")
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("now_ms must be nonnegative")
        if type(recovery_complete) is not bool:
            raise ValueError("recovery_complete must be bool")
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._ensure_table(connection)
                lease = connection.execute(
                    "SELECT owner,generation,expires_at_ms FROM feeder_leases WHERE lease_name=?",
                    (self.lease_name,),
                ).fetchone()
                if lease is None or lease[1] != generation:
                    connection.rollback()
                    return False
                lease_owner, _, expires = lease
                if state == "STOPPED":
                    authorized = lease_owner in (owner, None)
                else:
                    authorized = lease_owner == owner and expires > now_ms
                if not authorized:
                    connection.rollback()
                    return False
                current = connection.execute(
                    "SELECT generation,updated_at_ms FROM feeder_runtime_status WHERE lease_name=?",
                    (self.lease_name,),
                ).fetchone()
                if current is not None and current[0] > generation:
                    connection.rollback()
                    return False
                if current is not None and current[0] == generation and current[1] > now_ms:
                    connection.rollback()
                    return False
                connection.execute("""INSERT INTO feeder_runtime_status
                    (lease_name,owner,generation,state,recovery_complete,updated_at_ms)
                    VALUES (?,?,?,?,?,?)
                    ON CONFLICT(lease_name) DO UPDATE SET owner=excluded.owner,
                    generation=excluded.generation,state=excluded.state,
                    recovery_complete=excluded.recovery_complete,
                    updated_at_ms=excluded.updated_at_ms""",
                    (self.lease_name, owner, generation, state,
                     int(recovery_complete), now_ms))
                connection.commit()
                return True
            except Exception:
                connection.rollback()
                raise

    def snapshot(self, now_ms):
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("now_ms must be nonnegative")
        path = Path(self.db_path).resolve()
        if not path.is_file():
            raise FileNotFoundError("T0 feeder database is unavailable")
        uri = path.as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, timeout=5)) as connection:
            connection.row_factory = sqlite3.Row
            status = connection.execute("""SELECT owner,generation,state,
                recovery_complete,updated_at_ms FROM feeder_runtime_status
                WHERE lease_name=?""", (self.lease_name,)).fetchone()
            if status is None:
                return None
            lease = connection.execute("""SELECT owner,generation,expires_at_ms
                FROM feeder_leases WHERE lease_name=?""", (self.lease_name,)).fetchone()
            lease_valid = bool(
                lease and lease["owner"] == status["owner"]
                and lease["generation"] == status["generation"]
                and lease["expires_at_ms"] > now_ms
            )
            state = status["state"]
            if (state in ("STARTING", "RUNNING") and lease is not None
                    and lease["generation"] > status["generation"]):
                # A replacement generation has acquired the singleton lease;
                # its own STARTING publication may not have committed yet.
                state = "STARTING"
            elif state in ("STARTING", "RUNNING") and not lease_valid and lease is not None:
                state = "LEASE_LOST"
            if state == "RUNNING" and not status["recovery_complete"]:
                state = "STARTING"
            if state in ("STARTING", "RUNNING", "LEASE_LOST", "FAILED"):
                process_running = True
            else:
                process_running = False
            result = {
                "process_running": process_running,
                "startup_complete": state == "RUNNING" and bool(status["recovery_complete"]),
                "storage_readable": True,
                "storage_writable": True,
                "lease_valid": lease_valid,
                "fatal_error": state == "FAILED",
                "runtime_state": state,
            }
            for timeframe in ("15m", "1h"):
                row = connection.execute("""SELECT open_time_ms,available_at_ms FROM candles
                    WHERE exchange=? AND market_type=? AND symbol=? AND timeframe=?
                    ORDER BY open_time_ms DESC LIMIT 1""",
                    (EXCHANGE, MARKET_TYPE, SYMBOL, timeframe)).fetchone()
                if row is None:
                    result["m15" if timeframe == "15m" else "1h"] = {
                        "latest_closed_candle_close_ms": None,
                        "last_successful_sync_ms": None,
                        "unresolved_gap_count": 0,
                        "sync_error": None,
                    }
                else:
                    close_ms = row["open_time_ms"] + INTERVAL_MS[timeframe]
                    result["m15" if timeframe == "15m" else "1h"] = {
                        "latest_closed_candle_close_ms": close_ms,
                        "last_successful_sync_ms": row["available_at_ms"],
                        "unresolved_gap_count": 0,
                        "sync_error": None,
                    }
            return result
