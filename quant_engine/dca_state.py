"""Crash-safe DCA reservation ledger; no orders are sent from this module.

Reservation deliberately remains consumed after a crash. Reconciliation against
the exchange/paper fill journal is required before advancing position state.
"""
import sqlite3
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


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
            self.db.execute("""CREATE TABLE IF NOT EXISTS dca_intent_binding (
                symbol TEXT NOT NULL, trade_id TEXT NOT NULL,
                intent_id TEXT NOT NULL UNIQUE, side TEXT NOT NULL
                    CHECK(side IN ('LONG','SHORT')),
                PRIMARY KEY(symbol,trade_id),
                FOREIGN KEY(symbol,trade_id) REFERENCES dca_state(symbol,trade_id)
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

    def bind_paper_intent(self, symbol, trade_id, intent_id, side):
        """Persist the intent identity BEFORE submitting a paper order.

        The caller must use the exact same intent ID for an idempotent retry.
        An unbound DCA can never be acknowledged by reconciliation.
        """
        for label, value in (("symbol", symbol), ("trade_id", trade_id),
                             ("intent_id", intent_id)):
            _required(value, label)
        if side not in ("LONG", "SHORT"):
            raise ValueError("invalid position side")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            reservation = self.read(symbol, trade_id)
            if reservation is None or reservation["status"] != "RESERVED":
                raise StateConflict("DCA reservation missing or already filled")
            current = self.db.execute(
                "SELECT intent_id,side FROM dca_intent_binding WHERE symbol=? AND trade_id=?",
                (symbol, trade_id)).fetchone()
            if current:
                if current != (intent_id, side):
                    raise StateConflict("DCA intent cannot be rebound")
                self.db.execute("COMMIT")
                return False
            self.db.execute(
                "INSERT INTO dca_intent_binding VALUES (?,?,?,?)",
                (symbol, trade_id, intent_id, side))
            self.db.execute("COMMIT")
            return True
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def reconcile_paper_fill(self, symbol, trade_id, journal_path):
        """Confirm only an exact terminal FILLED order in PaperLedger's own DB.

        A missing/OPEN/PARTIALLY_FILLED/REJECTED order is unresolved.
        Never retry its DCA reservation automatically after a restart.
        """
        _required(symbol, "symbol")
        _required(trade_id, "trade_id")
        bound = self.db.execute(
            "SELECT intent_id,side FROM dca_intent_binding WHERE symbol=? AND trade_id=?",
            (symbol, trade_id)).fetchone()
        if bound is None or self.read(symbol, trade_id) is None:
            raise StateConflict("unbound or missing DCA reservation")
        intent_id, side = bound
        path = Path(journal_path).resolve()
        if not path.is_file():
            raise StateConflict("paper journal unavailable")
        try:
            with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as ledger:
                ledger.execute("PRAGMA query_only=ON")
                rows = ledger.execute(
                    "SELECT intent_id,order_id,status,document FROM paper_orders WHERE intent_id=?",
                    (intent_id,)).fetchall()
        except sqlite3.Error as error:
            raise StateConflict("unreadable paper journal") from error
        if not rows:
            return False
        if len(rows) != 1:
            raise StateConflict("ambiguous paper order")
        persisted_intent, persisted_order, persisted_status, raw = rows[0]
        try:
            doc = json.loads(raw)
            if not isinstance(doc, dict):
                raise ValueError("invalid paper order")
            if (persisted_intent != intent_id or doc.get("intentId") != intent_id or
                doc.get("orderId") != persisted_order or
                doc.get("status") != persisted_status or doc.get("mode") != "PAPER" or
                doc.get("side") != ("BUY" if side == "LONG" else "SELL")):
                raise ValueError("paper order identity mismatch")
            if persisted_status != "FILLED":
                if persisted_status in ("OPEN","PARTIALLY_FILLED","REJECTED","CANCELED"):
                    return False
                raise ValueError("invalid terminal status")
            filled = Decimal(str(doc["filledBase"]))
            remaining = Decimal(str(doc["remainingBase"]))
            price = Decimal(str(doc["averagePrice"]))
            fee = Decimal(str(doc["feeQuote"]))
            if (not all(x.is_finite() for x in (filled,remaining,price,fee)) or
                filled <= 0 or remaining != 0 or price <= 0 or fee < 0):
                raise ValueError("invalid paper fill accounting")
        except (ValueError, TypeError, KeyError, InvalidOperation) as error:
            raise StateConflict("invalid paper fill record") from error
        return self.confirm_fill(symbol, trade_id, persisted_order)

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
