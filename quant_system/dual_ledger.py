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

    def record_entry(self, position_id, *, side, quantity, entry_price, margin_used):
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

    def record_dca(self, position_id, *, quantity, price, margin_used):
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
    """Aggregate gross collateral across CORE and AI without directional netting.

    Each admission reserves 1% of the supplied portfolio equity. Available
    collateral is the supplied equity less gross margin already recorded in
    both ledgers. There is no position-count limit. Data freshness, reconciled
    state, Kill Switch, and collateral sufficiency are mandatory gates.
    """

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

    def _admit_increase(self, *, account_equity, core_snapshot, ai_snapshot,
                        data_fresh, state_reconciled, kill_switch):
        try:
            equity = _decimal(account_equity, "account_equity", positive=True)
            gross = self._gross_margin(core_snapshot, ai_snapshot)
        except (ValueError, TypeError):
            return RiskDecision(False, "INVALID_RISK_STATE")
        if type(data_fresh) is not bool or type(state_reconciled) is not bool or type(kill_switch) is not bool:
            return RiskDecision(False, "INVALID_RISK_STATE", gross_margin_used=gross)
        required = equity * MARGIN_FRACTION
        if kill_switch:
            return RiskDecision(False, "KILL_SWITCH_ACTIVE", required, gross)
        if not data_fresh:
            return RiskDecision(False, "STALE_DATA", required, gross)
        if not state_reconciled:
            return RiskDecision(False, "UNRECONCILED_STATE", required, gross)
        if gross > equity or equity - gross < required:
            return RiskDecision(False, "INSUFFICIENT_MARGIN", required, gross)
        return RiskDecision(True, "RISK_ADMITTED", required, gross)

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
                                decision.required_margin, decision.gross_margin_used)
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
        return RiskDecision(True, "RISK_REDUCTION_ADMITTED",
                            gross_margin_used=self._gross_margin(core_snapshot, ai_snapshot))
