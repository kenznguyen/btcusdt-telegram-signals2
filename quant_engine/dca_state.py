"""Crash-safe DCA reservation ledger; no orders are sent from this module.

Reservation deliberately remains consumed after a crash. Reconciliation against
the exchange/paper fill journal is required before advancing position state.
"""
import sqlite3


class StateConflict(RuntimeError):
    pass


def _required(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


class DcaStore:
    def __init__(self, path):
        _required(path, "path")
        self.db = sqlite3.connect(path, timeout=10, isolation_level=None)
        try:
            self.db.execute("PRAGMA busy_timeout=10000")
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("""CREATE TABLE IF NOT EXISTS dca_state (
                symbol TEXT NOT NULL, trade_id TEXT NOT NULL,
                candle_id TEXT NOT NULL, status TEXT NOT NULL,
                fill_id TEXT,
                PRIMARY KEY(symbol, trade_id)
            )""")
        except BaseException:
            self.db.close()
            raise

    def reserve_once(self, symbol, trade_id, candle_id):
        for label, value in (("symbol", symbol), ("trade_id", trade_id), ("candle_id", candle_id)):
            _required(value, label)
        # Primary key enforces one attempt per trade across restarts and processes.
        cursor = self.db.execute(
            "INSERT OR IGNORE INTO dca_state(symbol, trade_id, candle_id, status) VALUES (?, ?, ?, 'RESERVED')",
            (symbol, trade_id, candle_id))
        return cursor.rowcount == 1

    def read(self, symbol, trade_id):
        _required(symbol, "symbol")
        _required(trade_id, "trade_id")
        row = self.db.execute(
            "SELECT candle_id, status, fill_id FROM dca_state WHERE symbol=? AND trade_id=?",
            (symbol, trade_id)).fetchone()
        return None if row is None else dict(zip(("candle_id", "status", "fill_id"), row))

    def confirm_fill(self, symbol, trade_id, fill_id):
        for label, value in (("symbol", symbol), ("trade_id", trade_id), ("fill_id", fill_id)):
            _required(value, label)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT status, fill_id FROM dca_state WHERE symbol=? AND trade_id=?",
                (symbol, trade_id)).fetchone()
            if row is None or row[0] not in ("RESERVED", "FILLED"):
                raise StateConflict("missing or invalid DCA reservation")
            if row[0] == "FILLED":
                if row[1] != fill_id:
                    raise StateConflict("conflicting DCA fill ID")
                self.db.execute("COMMIT")
                return False
            self.db.execute(
                "UPDATE dca_state SET status='FILLED', fill_id=? WHERE symbol=? AND trade_id=?",
                (fill_id, symbol, trade_id))
            self.db.execute("COMMIT")
            return True
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
