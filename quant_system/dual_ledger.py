"""Durable independent paper ledgers and a shared, fail-closed risk gate.

This module is deliberately paper-only. It persists strategy accounting and
returns admission decisions; it never submits exchange orders.
"""
from contextlib import closing
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sqlite3


STRATEGY_IDS = frozenset({"CORE", "AI"})
MARGIN_FRACTION = Decimal("0.01")


def _decimal(value, field, *, positive=False, non_negative=False):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite decimal")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field} must be a finite decimal") from None
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    if positive and result <= 0:
        raise ValueError(f"{field} must be greater than zero")
    if non_negative and result < 0:
        raise ValueError(f"{field} must not be negative")
    return result


@dataclass(frozen=True)
class PositionSnapshot:
    position_id: str
    side: str
    quantity: Decimal
    entry_price: Decimal
    margin_used: Decimal
    dca_count: int

    @property
    def gross_exposure(self):
        return self.quantity * self.entry_price


@dataclass(frozen=True)
class LedgerSnapshot:
    strategy_id: str
    equity: Decimal
    positions: tuple[PositionSnapshot, ...]


@dataclass(frozen=True)
class RiskDecision:
    accepted: bool
    reason: str
    required_margin: Decimal = Decimal("0")
    gross_margin_used: Decimal = Decimal("0")
    gross_exposure: Decimal = Decimal("0")
    reservation_id: str | None = None


class StrategyLedger:
    """One strategy's account and positions, isolated by strategy_id.

    CORE and AI can share a SQLite database file. Every read and write is
    namespaced by strategy_id and every mutation uses an IMMEDIATE transaction.
    """

    def __init__(self, path, *, strategy_id, initial_equity):
        if strategy_id not in STRATEGY_IDS:
            raise ValueError("strategy_id must be CORE or AI")
        if not path or str(path) == ":memory:":
            raise ValueError("A durable SQLite file path is required")
        equity = _decimal(initial_equity, "initial_equity", positive=True)
        self.path = Path(path)
        self.strategy_id = strategy_id
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS strategy_accounts (
                    strategy_id TEXT PRIMARY KEY,
                    equity TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS strategy_positions (
                    strategy_id TEXT NOT NULL,
                    position_id TEXT NOT NULL,
                    side TEXT NOT NULL CHECK (side IN ('LONG', 'SHORT')),
                    quantity TEXT NOT NULL,
                    entry_price TEXT NOT NULL,
                    margin_used TEXT NOT NULL,
                    dca_count INTEGER NOT NULL DEFAULT 0 CHECK (dca_count >= 0),
                    PRIMARY KEY (strategy_id, position_id),
                    FOREIGN KEY (strategy_id) REFERENCES strategy_accounts(strategy_id)
                );
            """)
            db.execute(
                "INSERT OR IGNORE INTO strategy_accounts(strategy_id, equity) VALUES (?, ?)",
                (strategy_id, str(equity)),
            )
            db.commit()

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def snapshot(self):
        with closing(self._connect()) as db:
            account = db.execute(
                "SELECT equity FROM strategy_accounts WHERE strategy_id=?",
                (self.strategy_id,),
            ).fetchone()
            if account is None:
                raise RuntimeError("Strategy account is missing")
            rows = db.execute(
                """SELECT position_id, side, quantity, entry_price, margin_used, dca_count
                   FROM strategy_positions WHERE strategy_id=? ORDER BY position_id""",
                (self.strategy_id,),
            ).fetchall()
        positions = tuple(
            PositionSnapshot(
                position_id=row["position_id"],
                side=row["side"],
                quantity=Decimal(row["quantity"]),
                entry_price=Decimal(row["entry_price"]),
                margin_used=Decimal(row["margin_used"]),
                dca_count=row["dca_count"],
            )
            for row in rows
        )
        return LedgerSnapshot(self.strategy_id, Decimal(account["equity"]), positions)

    def restore_position(self, position_id, *, side, quantity, entry_price, margin_used):
        """Restore a reconciled existing position; not an admission API."""
        if not isinstance(position_id, str) or not position_id.strip():
            raise ValueError("position_id is required")
        if side not in ("LONG", "SHORT"):
            raise ValueError("side must be LONG or SHORT")
        qty = _decimal(quantity, "quantity", positive=True)
        price = _decimal(entry_price, "entry_price", positive=True)
        margin = _decimal(margin_used, "margin_used", positive=True)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute(
                    """INSERT INTO strategy_positions
                       (strategy_id, position_id, side, quantity, entry_price, margin_used, dca_count)
                       VALUES (?, ?, ?, ?, ?, ?, 0)""",
                    (self.strategy_id, position_id, side, str(qty), str(price), str(margin)),
                )
                db.commit()
            except Exception:
                db.rollback()
                raise


    def record_reserved_entry(self, *, reservation_id, position_id, side, quantity, entry_price):
        """Atomically consume a shared ENTRY reservation and persist its position."""
        if not isinstance(position_id, str) or not position_id.strip():
            raise ValueError("position_id is required")
        if side not in ("LONG", "SHORT"):
            raise ValueError("side must be LONG or SHORT")
        qty = _decimal(quantity, "quantity", positive=True)
        price = _decimal(entry_price, "entry_price", positive=True)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                reservation = db.execute(
                    """SELECT strategy_id, position_id, action, required_margin, notional_exposure, status
                       FROM risk_reservations WHERE reservation_id=?""",
                    (reservation_id,),
                ).fetchone()
                if (reservation is None or reservation["status"] != "RESERVED"
                    or reservation["strategy_id"] != self.strategy_id
                    or reservation["position_id"] != position_id
                    or reservation["action"] != "ENTRY"):
                    raise ValueError("Missing, consumed, or mismatched ENTRY reservation")
                if qty * price > Decimal(reservation["notional_exposure"]):
                    raise ValueError("ENTRY exceeds reserved gross exposure")
                db.execute(
                    """INSERT INTO strategy_positions
                       (strategy_id, position_id, side, quantity, entry_price, margin_used, dca_count)
                       VALUES (?, ?, ?, ?, ?, ?, 0)""",
                    (self.strategy_id, position_id, side, str(qty), str(price),
                     reservation["required_margin"]),
                )
                updated = db.execute(
                    """UPDATE risk_reservations SET status='CONSUMED'
                       WHERE reservation_id=? AND status='RESERVED'""",
                    (reservation_id,),
                )
                if updated.rowcount != 1:
                    raise ValueError("ENTRY reservation was already consumed")
                db.commit()
            except Exception:
                db.rollback()
                raise

    def restore_dca(self, position_id, *, quantity, price, margin_used):
        """Restore historical DCA state; new DCA intents require a reservation."""
        qty = _decimal(quantity, "quantity", positive=True)
        dca_price = _decimal(price, "price", positive=True)
        margin = _decimal(margin_used, "margin_used", positive=True)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    """SELECT quantity, entry_price, margin_used, dca_count
                       FROM strategy_positions WHERE strategy_id=? AND position_id=?""",
                    (self.strategy_id, position_id),
                ).fetchone()
                if row is None:
                    raise ValueError("Unknown position for this strategy")
                old_qty = Decimal(row["quantity"])
                old_price = Decimal(row["entry_price"])
                total_qty = old_qty + qty
                average_price = ((old_qty * old_price) + (qty * dca_price)) / total_qty
                total_margin = Decimal(row["margin_used"]) + margin
                db.execute(
                    """UPDATE strategy_positions
                       SET quantity=?, entry_price=?, margin_used=?, dca_count=?
                       WHERE strategy_id=? AND position_id=?""",
                    (str(total_qty), str(average_price), str(total_margin),
                     row["dca_count"] + 1, self.strategy_id, position_id),
                )
                db.commit()
            except Exception:
                db.rollback()
                raise


    def record_reserved_dca(self, *, reservation_id, position_id, quantity, price):
        """Atomically consume a shared DCA reservation and update one position."""
        qty = _decimal(quantity, "quantity", positive=True)
        dca_price = _decimal(price, "price", positive=True)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                reservation = db.execute(
                    """SELECT strategy_id, position_id, action, required_margin, notional_exposure, status
                       FROM risk_reservations WHERE reservation_id=?""",
                    (reservation_id,),
                ).fetchone()
                if (reservation is None or reservation["status"] != "RESERVED"
                    or reservation["strategy_id"] != self.strategy_id
                    or reservation["position_id"] != position_id
                    or reservation["action"] != "DCA"):
                    raise ValueError("Missing, consumed, or mismatched DCA reservation")
                if qty * dca_price > Decimal(reservation["notional_exposure"]):
                    raise ValueError("DCA exceeds reserved gross exposure")
                row = db.execute(
                    """SELECT quantity, entry_price, margin_used, dca_count
                       FROM strategy_positions WHERE strategy_id=? AND position_id=?""",
                    (self.strategy_id, position_id),
                ).fetchone()
                if row is None:
                    raise ValueError("Unknown position for this strategy")
                old_qty = Decimal(row["quantity"])
                old_price = Decimal(row["entry_price"])
                total_qty = old_qty + qty
                average_price = ((old_qty * old_price) + (qty * dca_price)) / total_qty
                total_margin = Decimal(row["margin_used"]) + Decimal(reservation["required_margin"])
                db.execute(
                    """UPDATE strategy_positions
                       SET quantity=?, entry_price=?, margin_used=?, dca_count=?
                       WHERE strategy_id=? AND position_id=?""",
                    (str(total_qty), str(average_price), str(total_margin),
                     row["dca_count"] + 1, self.strategy_id, position_id),
                )
                updated = db.execute(
                    """UPDATE risk_reservations SET status='CONSUMED'
                       WHERE reservation_id=? AND status='RESERVED'""",
                    (reservation_id,),
                )
                if updated.rowcount != 1:
                    raise ValueError("DCA reservation was already consumed")
                db.commit()
            except Exception:
                db.rollback()
                raise


    def record_reduction(self, position_id, *, quantity, realized_pnl, fees):
        """Atomically reduce one strategy position, release proportional margin and book PnL."""
        qty = _decimal(quantity, "quantity", positive=True)
        realized = _decimal(realized_pnl, "realized_pnl")
        fee_amount = _decimal(fees, "fees", non_negative=True)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                position = db.execute(
                    """SELECT quantity, margin_used FROM strategy_positions
                       WHERE strategy_id=? AND position_id=?""",
                    (self.strategy_id, position_id),
                ).fetchone()
                if position is None:
                    raise ValueError("Unknown position for this strategy")
                old_quantity = Decimal(position["quantity"])
                old_margin = Decimal(position["margin_used"])
                if qty > old_quantity:
                    raise ValueError("Reduction quantity exceeds the open position")
                remaining_quantity = old_quantity - qty
                released_margin = old_margin * qty / old_quantity
                remaining_margin = old_margin - released_margin

                account = db.execute(
                    "SELECT equity FROM strategy_accounts WHERE strategy_id=?",
                    (self.strategy_id,),
                ).fetchone()
                if account is None:
                    raise RuntimeError("Strategy account is missing")
                updated_equity = Decimal(account["equity"]) + realized - fee_amount
                if updated_equity <= 0:
                    raise ValueError("Reduction would make strategy equity non-positive")

                if remaining_quantity == 0:
                    db.execute(
                        "DELETE FROM strategy_positions WHERE strategy_id=? AND position_id=?",
                        (self.strategy_id, position_id),
                    )
                else:
                    db.execute(
                        """UPDATE strategy_positions SET quantity=?, margin_used=?
                           WHERE strategy_id=? AND position_id=?""",
                        (str(remaining_quantity), str(remaining_margin),
                         self.strategy_id, position_id),
                    )
                db.execute(
                    "UPDATE strategy_accounts SET equity=? WHERE strategy_id=?",
                    (str(updated_equity), self.strategy_id),
                )
                db.commit()
            except Exception:
                db.rollback()
                raise

    def apply_realized_pnl(self, *, pnl, fees):
        realized = _decimal(pnl, "pnl")
        fee_amount = _decimal(fees, "fees", non_negative=True)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT equity FROM strategy_accounts WHERE strategy_id=?",
                    (self.strategy_id,),
                ).fetchone()
                if row is None:
                    raise RuntimeError("Strategy account is missing")
                updated = Decimal(row["equity"]) + realized - fee_amount
                if updated <= 0:
                    raise ValueError("Realized PnL would make strategy equity non-positive")
                db.execute(
                    "UPDATE strategy_accounts SET equity=? WHERE strategy_id=?",
                    (str(updated), self.strategy_id),
                )
                db.commit()
            except Exception:
                db.rollback()
                raise


class SharedRiskEngine:
    """Shared collateral gate with optional atomic reservations in the ledger DB.

    Stateless admit_* methods support deterministic backtests. For concurrent
    CORE/AI paper admission, use reserve_entry/reserve_dca with the same SQLite
    file as both StrategyLedger instances. BEGIN IMMEDIATE serializes admission,
    and reserved collateral is included until a ledger consumes the reservation.
    """

    def __init__(self, path=None):
        self.path = None
        if path is not None:
            if not path or str(path) == ":memory:":
                raise ValueError("A durable shared reservation database path is required")
            self.path = Path(path)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(self.path, timeout=15)) as db:
                db.execute("PRAGMA journal_mode=WAL")
                db.execute("PRAGMA synchronous=FULL")
                db.execute("""CREATE TABLE IF NOT EXISTS risk_reservations (
                    reservation_id TEXT PRIMARY KEY,
                    strategy_id TEXT NOT NULL CHECK (strategy_id IN ('CORE', 'AI')),
                    position_id TEXT NOT NULL,
                    action TEXT NOT NULL CHECK (action IN ('ENTRY', 'DCA')),
                    required_margin TEXT NOT NULL,
                    notional_exposure TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('RESERVED', 'CONSUMED', 'CANCELLED')),
                    resolution_evidence TEXT
                )""")
                columns = {
                    row[1] for row in db.execute("PRAGMA table_info(risk_reservations)").fetchall()
                }
                if "notional_exposure" not in columns:
                    db.execute("ALTER TABLE risk_reservations ADD COLUMN notional_exposure TEXT")
                if "resolution_evidence" not in columns:
                    db.execute("ALTER TABLE risk_reservations ADD COLUMN resolution_evidence TEXT")
                db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS one_active_position_reservation
                    ON risk_reservations(strategy_id, position_id) WHERE status='RESERVED'""")
                db.commit()

    def _reserve_increase(self, *, reservation_id, strategy_id, position_id,
                          action, account_equity, notional_exposure,
                          data_fresh, state_reconciled, kill_switch):
        if self.path is None:
            return RiskDecision(False, "PERSISTENT_RESERVATION_STORE_REQUIRED")
        if (not isinstance(reservation_id, str) or not reservation_id.strip()
            or strategy_id not in STRATEGY_IDS
            or not isinstance(position_id, str) or not position_id.strip()
            or action not in ("ENTRY", "DCA")
            or type(data_fresh) is not bool
            or type(state_reconciled) is not bool
            or type(kill_switch) is not bool):
            return RiskDecision(False, "INVALID_RISK_STATE")
        try:
            equity = _decimal(account_equity, "account_equity", positive=True)
            exposure = _decimal(notional_exposure, "notional_exposure", positive=True)
        except ValueError:
            return RiskDecision(False, "INVALID_RISK_STATE")
        required = equity * MARGIN_FRACTION
        if kill_switch:
            return RiskDecision(False, "KILL_SWITCH_ACTIVE", required)
        if not data_fresh:
            return RiskDecision(False, "STALE_DATA", required)
        if not state_reconciled:
            return RiskDecision(False, "UNRECONCILED_STATE", required)

        with closing(sqlite3.connect(self.path, timeout=15, isolation_level=None)) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute(
                    "SELECT 1 FROM risk_reservations WHERE reservation_id=?",
                    (reservation_id,),
                ).fetchone():
                    db.rollback()
                    return RiskDecision(False, "DUPLICATE_RESERVATION", required)
                accounts = db.execute(
                    "SELECT COUNT(*) AS count FROM strategy_accounts WHERE strategy_id IN ('CORE', 'AI')"
                ).fetchone()["count"]
                if accounts != 2:
                    db.rollback()
                    return RiskDecision(False, "INVALID_RISK_STATE", required)
                position = db.execute(
                    "SELECT 1 FROM strategy_positions WHERE strategy_id=? AND position_id=?",
                    (strategy_id, position_id),
                ).fetchone()
                if action == "ENTRY" and position is not None:
                    db.rollback()
                    return RiskDecision(False, "POSITION_ALREADY_EXISTS", required)
                if action == "DCA" and position is None:
                    db.rollback()
                    return RiskDecision(False, "POSITION_NOT_FOUND", required)
                active = db.execute(
                    """SELECT 1 FROM risk_reservations
                       WHERE strategy_id=? AND position_id=? AND status='RESERVED'""",
                    (strategy_id, position_id),
                ).fetchone()
                if active:
                    db.rollback()
                    return RiskDecision(False, "POSITION_ALREADY_RESERVED", required)
                position_rows = db.execute(
                    "SELECT quantity, entry_price, margin_used FROM strategy_positions"
                ).fetchall()
                gross_margin = sum(
                    (Decimal(row["margin_used"]) for row in position_rows), Decimal("0")
                )
                gross_exposure = sum(
                    (Decimal(row["quantity"]) * Decimal(row["entry_price"])
                     for row in position_rows), Decimal("0")
                )
                pending_rows = db.execute(
                    """SELECT required_margin, notional_exposure FROM risk_reservations
                       WHERE status='RESERVED'"""
                ).fetchall()
                pending_margin = sum(
                    (Decimal(row["required_margin"]) for row in pending_rows), Decimal("0")
                )
                pending_exposure = sum(
                    (Decimal(row["notional_exposure"]) for row in pending_rows), Decimal("0")
                )
                committed_margin = gross_margin + pending_margin
                committed_exposure = gross_exposure + pending_exposure
                if committed_margin > equity or equity - committed_margin < required:
                    db.rollback()
                    return RiskDecision(
                        False, "INSUFFICIENT_MARGIN", required, committed_margin,
                        committed_exposure,
                    )
                db.execute(
                    """INSERT INTO risk_reservations
                       (reservation_id, strategy_id, position_id, action, required_margin,
                        notional_exposure, status)
                       VALUES (?, ?, ?, ?, ?, ?, 'RESERVED')""",
                    (reservation_id, strategy_id, position_id, action, str(required), str(exposure)),
                )
                db.commit()
                return RiskDecision(
                    True, "RISK_ADMITTED", required, committed_margin,
                    committed_exposure, reservation_id,
                )
            except sqlite3.IntegrityError:
                db.rollback()
                return RiskDecision(False, "POSITION_ALREADY_RESERVED", required)
            except Exception:
                db.rollback()
                raise

    def reserve_entry(self, *, reservation_id, strategy_id, position_id,
                      account_equity, notional_exposure, data_fresh,
                      state_reconciled, kill_switch=False):
        return self._reserve_increase(
            reservation_id=reservation_id, strategy_id=strategy_id,
            position_id=position_id, action="ENTRY", account_equity=account_equity,
            notional_exposure=notional_exposure, data_fresh=data_fresh,
            state_reconciled=state_reconciled,
            kill_switch=kill_switch,
        )

    def reserve_dca(self, *, reservation_id, strategy_id, position_id,
                    account_equity, notional_exposure, data_fresh,
                    state_reconciled, kill_switch=False):
        return self._reserve_increase(
            reservation_id=reservation_id, strategy_id=strategy_id,
            position_id=position_id, action="DCA", account_equity=account_equity,
            notional_exposure=notional_exposure, data_fresh=data_fresh,
            state_reconciled=state_reconciled,
            kill_switch=kill_switch,
        )


    def cancel_reservation(self, reservation_id, *, evidence):
        """Release only an unresolved reservation with explicit reconciliation evidence."""
        if self.path is None:
            raise ValueError("Persistent reservation store is required")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("Reconciliation evidence is required")
        with closing(sqlite3.connect(self.path, timeout=15, isolation_level=None)) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT status FROM risk_reservations WHERE reservation_id=?",
                    (reservation_id,),
                ).fetchone()
                if row is None or row[0] != "RESERVED":
                    raise ValueError("Only an active reservation can be reconciled as cancelled")
                updated = db.execute(
                    """UPDATE risk_reservations
                       SET status='CANCELLED', resolution_evidence=?
                       WHERE reservation_id=? AND status='RESERVED'""",
                    (evidence.strip(), reservation_id),
                )
                if updated.rowcount != 1:
                    raise ValueError("Reservation state changed during reconciliation")
                db.commit()
            except Exception:
                db.rollback()
                raise

    def _gross_margin(self, core_snapshot, ai_snapshot):
        if not isinstance(core_snapshot, LedgerSnapshot) or not isinstance(ai_snapshot, LedgerSnapshot):
            raise ValueError("Both valid ledger snapshots are required")
        if core_snapshot.strategy_id != "CORE" or ai_snapshot.strategy_id != "AI":
            raise ValueError("Snapshots must be supplied in CORE, AI order")
        gross = Decimal("0")
        for snapshot in (core_snapshot, ai_snapshot):
            for position in snapshot.positions:
                margin = _decimal(position.margin_used, "position margin", non_negative=True)
                gross += margin
        return gross

    def _gross_exposure(self, core_snapshot, ai_snapshot):
        if not isinstance(core_snapshot, LedgerSnapshot) or not isinstance(ai_snapshot, LedgerSnapshot):
            raise ValueError("Both valid ledger snapshots are required")
        if core_snapshot.strategy_id != "CORE" or ai_snapshot.strategy_id != "AI":
            raise ValueError("Snapshots must be supplied in CORE, AI order")
        gross = Decimal("0")
        for snapshot in (core_snapshot, ai_snapshot):
            for position in snapshot.positions:
                quantity = _decimal(position.quantity, "position quantity", positive=True)
                price = _decimal(position.entry_price, "position entry price", positive=True)
                gross += quantity * price
        return gross

    def _admit_increase(self, *, account_equity, core_snapshot, ai_snapshot,
                        data_fresh, state_reconciled, kill_switch):
        try:
            equity = _decimal(account_equity, "account_equity", positive=True)
            gross = self._gross_margin(core_snapshot, ai_snapshot)
            gross_exposure = self._gross_exposure(core_snapshot, ai_snapshot)
        except (ValueError, TypeError):
            return RiskDecision(False, "INVALID_RISK_STATE")
        if type(data_fresh) is not bool or type(state_reconciled) is not bool or type(kill_switch) is not bool:
            return RiskDecision(False, "INVALID_RISK_STATE", gross_margin_used=gross,
                                gross_exposure=gross_exposure)
        required = equity * MARGIN_FRACTION
        if kill_switch:
            return RiskDecision(False, "KILL_SWITCH_ACTIVE", required, gross, gross_exposure)
        if not data_fresh:
            return RiskDecision(False, "STALE_DATA", required, gross, gross_exposure)
        if not state_reconciled:
            return RiskDecision(False, "UNRECONCILED_STATE", required, gross, gross_exposure)
        if gross > equity or equity - gross < required:
            return RiskDecision(False, "INSUFFICIENT_MARGIN", required, gross, gross_exposure)
        return RiskDecision(True, "RISK_ADMITTED", required, gross, gross_exposure)

    def admit_entry(self, *, account_equity, core_snapshot, ai_snapshot,
                    data_fresh, state_reconciled, kill_switch=False):
        return self._admit_increase(
            account_equity=account_equity, core_snapshot=core_snapshot,
            ai_snapshot=ai_snapshot, data_fresh=data_fresh,
            state_reconciled=state_reconciled, kill_switch=kill_switch,
        )

    def admit_dca(self, *, account_equity, position_id, core_snapshot, ai_snapshot,
                  data_fresh, state_reconciled, kill_switch=False):
        decision = self._admit_increase(
            account_equity=account_equity, core_snapshot=core_snapshot,
            ai_snapshot=ai_snapshot, data_fresh=data_fresh,
            state_reconciled=state_reconciled, kill_switch=kill_switch,
        )
        if not decision.accepted:
            return decision
        matches = [
            position for snapshot in (core_snapshot, ai_snapshot)
            for position in snapshot.positions if position.position_id == position_id
        ]
        if len(matches) != 1:
            return RiskDecision(False, "POSITION_NOT_UNIQUELY_FOUND",
                                decision.required_margin, decision.gross_margin_used,
                                decision.gross_exposure)
        return decision

    def admit_reduction(self, *, strategy_id, position_id, quantity,
                        core_snapshot, ai_snapshot, kill_switch=False):
        try:
            if strategy_id not in STRATEGY_IDS:
                raise ValueError("Invalid strategy")
            self._gross_margin(core_snapshot, ai_snapshot)
            qty = _decimal(quantity, "quantity", positive=True)
        except (ValueError, TypeError):
            return RiskDecision(False, "INVALID_REDUCTION")
        selected = core_snapshot if strategy_id == "CORE" else ai_snapshot
        matches = [p for p in selected.positions if p.position_id == position_id]
        if len(matches) != 1 or qty > matches[0].quantity:
            return RiskDecision(False, "INVALID_REDUCTION")
        return RiskDecision(
            True, "RISK_REDUCTION_ADMITTED",
            gross_margin_used=self._gross_margin(core_snapshot, ai_snapshot),
            gross_exposure=self._gross_exposure(core_snapshot, ai_snapshot),
        )
