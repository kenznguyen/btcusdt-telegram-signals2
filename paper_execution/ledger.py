"""Atomic visible-depth limit-order simulation. This module has no network client."""

from contextlib import closing
from decimal import Decimal, DecimalException, localcontext
import json
import hashlib
from pathlib import Path
import sqlite3

from pipeline.values import identity, number, stamp
from paper_execution import risk_control, equity as equity_history

ZERO = Decimal(0)
ACTIVE = {"OPEN", "PARTIALLY_FILLED"}
INTENT_FIELDS = {"intentId", "symbol", "exchange", "marketType", "strategyVersion", "modelVersion",
                 "datasetVersion", "targetPositionBase", "limitPrice", "decisionAtMs", "validUntilMs",
                 "inputSnapshotId", "mode"}


def text(value):
    result = format(value, "f")
    return result.rstrip("0").rstrip(".") if "." in result else result


def intent_value(raw):
    if not isinstance(raw, dict) or set(raw) != INTENT_FIELDS:
        raise ValueError("Invalid intent fields")
    result = dict(raw)
    for key in ("intentId", "strategyVersion", "modelVersion", "datasetVersion", "inputSnapshotId"):
        value = result[key]
        if not isinstance(value, str) or not value.strip() or len(value) > 200 or not value.isprintable():
            raise ValueError("Invalid intent identifier")
    if (result["mode"], result["symbol"], result["exchange"], result["marketType"]) != (
            "PAPER", "BTCUSDT", "binance", "USDT_PERPETUAL"):
        raise ValueError("Only BTCUSDT perpetual PAPER intents are supported")
    result["targetPositionBase"] = text(number(result["targetPositionBase"], signed=True))
    price = number(result["limitPrice"])
    if price <= 0:
        raise ValueError("Limit price must be positive")
    result["limitPrice"] = text(price)
    decision, expiry = stamp(result["decisionAtMs"]), stamp(result["validUntilMs"])
    if not 0 < expiry-decision <= 60_000:
        raise ValueError("Intent lifetime must be at most 60 seconds")
    return result


def book_value(raw, now_ms):
    if not isinstance(raw, dict) or (raw.get("source"), raw.get("connector"), raw.get("symbol")) != (
            "hummingbot", "binance_perpetual", "BTCUSDT"):
        raise ValueError("Invalid book source")
    observed = stamp(raw.get("observedAtMs"))
    if not -5_000 <= now_ms-observed <= 30_000:
        raise ValueError("Invalid book timestamp")
    sides = []
    for side in ("bids", "asks"):
        rows = raw.get(side)
        if not isinstance(rows, list) or not 1 <= len(rows) <= 20:
            raise ValueError("Invalid book depth")
        levels = []
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Invalid book level")
            price, quantity = number(row.get("price")), number(row.get("quantity"))
            if price <= 0 or quantity <= 0:
                raise ValueError("Book levels must be positive")
            levels.append((price, quantity))
        if len({p for p, _ in levels}) != len(levels):
            raise ValueError("Duplicate book price")
        sides.append(sorted(levels, reverse=side == "bids"))
    bids, asks = sides
    if bids[0][0] >= asks[0][0]:
        raise ValueError("Crossed order book")
    canonical = {"observedAtMs": observed, "bids": [[text(p), text(q)] for p, q in bids],
                 "asks": [[text(p), text(q)] for p, q in asks]}
    spread = (asks[0][0]-bids[0][0]) / ((asks[0][0]+bids[0][0])/2) * 10_000
    return bids, asks, spread, identity("book:", canonical)


def stored_state(connection):
    """Validate persisted state before arithmetic or returning a trusted snapshot."""
    row = connection.execute("SELECT position,average,realized,fees,paused FROM paper_state WHERE id=1").fetchone()
    try:
        if row is None or type(row[4]) is not int or row[4] not in (0, 1):
            raise ValueError("Invalid state row")
        if any(not isinstance(value, str) or not 1 <= len(value) <= 256 for value in row[:4]):
            raise ValueError("Invalid state amount")
        values = tuple(Decimal(value) for value in row[:4])
        if any(not value.is_finite() or not -200 <= value.as_tuple().exponent <= 200 or value.adjusted() > 200 for value in values):
            raise ValueError("Invalid state amount")
        position, average, _, fees = values
        if fees < 0 or average < 0 or (position == 0 and average != 0) or (position != 0 and average <= 0):
            raise ValueError("Inconsistent state")
        return (*values, row[4])
    except (DecimalException, TypeError, ValueError):
        raise sqlite3.DatabaseError("Paper ledger state is corrupt or uninitialized") from None


def read_snapshot(db_path):
    """Read existing paper state without creating a database or initializing tables."""
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError("Paper ledger is unavailable")
    with closing(sqlite3.connect(path.as_uri()+"?mode=ro", uri=True, timeout=10)) as connection, connection, localcontext() as context:
        context.prec = 80
        connection.execute("BEGIN")
        position, average, realized, fees, paused = stored_state(connection)
        risk = risk_control.snapshot(connection)
        strategy = connection.execute("SELECT owner,dca_used,initial_margin_quote FROM paper_strategy_state WHERE id=1").fetchone() if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_strategy_state'").fetchone() else (None, 0, "0")
        orders = [json.loads(row[0]) for row in connection.execute("SELECT document FROM paper_orders ORDER BY rowid DESC LIMIT 100")]
        return {"mode": "PAPER", "liveTradingSupported": False, "paused": bool(paused), "riskControl": risk, "strategyState": {"owner": strategy[0], "dcaUsed": bool(strategy[1]), "initialMarginQuote": strategy[2]}, "positionBase": text(position),
                "averageEntryPrice": text(average), "realizedPnlQuote": text(realized), "feesQuote": text(fees),
                "netRealizedPnlQuote": text(realized-fees), "orders": orders,
                "simulationModel": "VISIBLE_DEPTH_LIMIT_SNAPSHOT"}


DUAL_STRATEGIES = {"STRATEGY_CORE", "AI_FREQAI"}
MIGRATION_VERSION = 1
MIGRATION_CHECKSUM = hashlib.sha256(
    b"dual-ledger-v1:additive-account-strategy-ledgers-risk-reservations-funding"
).hexdigest()


def migrate_dual_ledger(connection, source_sha):
    """Atomically add the first dual-ledger schema without rewriting legacy tables."""
    if not isinstance(source_sha, str) or len(source_sha) != 40 or any(
        character not in "0123456789abcdef" for character in source_sha.lower()
    ):
        raise ValueError("DUAL_LEDGER_SOURCE_SHA_REQUIRED")

    migration_table = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_schema_migrations'"
    ).fetchone()
    if migration_table:
        applied = connection.execute(
            "SELECT checksum FROM paper_schema_migrations WHERE version=?",
            (MIGRATION_VERSION,),
        ).fetchone()
        if applied:
            if applied[0] != MIGRATION_CHECKSUM:
                raise sqlite3.DatabaseError("DUAL_LEDGER_MIGRATION_CHECKSUM_MISMATCH")
            return

    legacy_position, legacy_average, legacy_realized, legacy_fees, _ = stored_state(connection)
    owner_row = connection.execute(
        "SELECT owner,dca_used,initial_margin_quote FROM paper_strategy_state WHERE id=1"
    ).fetchone()
    if owner_row is None:
        raise sqlite3.DatabaseError("DUAL_LEDGER_LEGACY_STRATEGY_STATE_MISSING")
    owner = owner_row[0]
    config_exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_account_config'"
    ).fetchone()
    capital_row = connection.execute(
        "SELECT initial_capital FROM paper_account_config WHERE id=1"
    ).fetchone() if config_exists else None
    if capital_row is None:
        raise sqlite3.DatabaseError("DUAL_LEDGER_INITIAL_CAPITAL_UNAVAILABLE")
    try:
        initial_capital = number(str(capital_row[0]))
    except (DecimalException, TypeError, ValueError):
        raise sqlite3.DatabaseError("DUAL_LEDGER_INITIAL_CAPITAL_CORRUPT") from None
    if initial_capital <= 0:
        raise sqlite3.DatabaseError("DUAL_LEDGER_INITIAL_CAPITAL_CORRUPT")

    connection.execute("""CREATE TABLE IF NOT EXISTS paper_schema_migrations (
        version INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        checksum TEXT NOT NULL,
        applied_at_ms INTEGER NOT NULL,
        source_sha TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('APPLIED'))
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS paper_accounts (
        account_id INTEGER PRIMARY KEY CHECK(account_id=1),
        mode TEXT NOT NULL CHECK(mode='PAPER'),
        initial_capital TEXT NOT NULL,
        currency TEXT NOT NULL CHECK(currency='USDT'),
        created_at_ms INTEGER NOT NULL,
        migration_version INTEGER NOT NULL
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS paper_strategy_ledgers (
        account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id),
        strategy_id TEXT NOT NULL CHECK(strategy_id IN
            ('STRATEGY_CORE','AI_FREQAI','LEGACY_UNATTRIBUTED')),
        position_base TEXT NOT NULL,
        average_entry_price TEXT NOT NULL,
        realized_pnl_quote TEXT NOT NULL,
        fees_quote TEXT NOT NULL,
        funding_quote TEXT NOT NULL,
        dca_used INTEGER NOT NULL CHECK(dca_used IN (0,1)),
        initial_margin_quote TEXT NOT NULL,
        updated_at_ms INTEGER NOT NULL,
        version INTEGER NOT NULL,
        PRIMARY KEY(account_id,strategy_id)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS paper_account_adjustments (
        adjustment_id TEXT PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id),
        strategy_id TEXT NOT NULL CHECK(strategy_id='LEGACY_UNATTRIBUTED'),
        adjustment_type TEXT NOT NULL CHECK(adjustment_type IN
            ('LEGACY_REALIZED_PNL','LEGACY_FEES')),
        amount_quote TEXT NOT NULL,
        source_table TEXT NOT NULL,
        source_hash TEXT NOT NULL,
        created_at_ms INTEGER NOT NULL
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS paper_account_risk_state (
        account_id INTEGER PRIMARY KEY REFERENCES paper_accounts(account_id),
        high_water_mark_quote TEXT,
        daily_baseline_utc_day_ms INTEGER,
        daily_baseline_equity_quote TEXT,
        last_equity_quote TEXT,
        last_mark_price TEXT,
        mark_observed_at_ms INTEGER,
        mark_candle_close_ms INTEGER,
        dataset_version TEXT,
        risk_ready INTEGER NOT NULL CHECK(risk_ready IN (0,1)),
        unavailable_reason TEXT,
        updated_at_ms INTEGER NOT NULL,
        version INTEGER NOT NULL
    )""")

    order_columns = {row[1] for row in connection.execute("PRAGMA table_info(paper_orders)")}
    for name, declaration in (
        ("account_id", "INTEGER"),
        ("strategy_id", "TEXT"),
        ("strategy_event", "TEXT"),
        ("reservation_id", "TEXT"),
        ("created_schema_version", "INTEGER"),
    ):
        if name not in order_columns:
            connection.execute(f"ALTER TABLE paper_orders ADD COLUMN {name} {declaration}")
    connection.execute(
        "CREATE INDEX IF NOT EXISTS paper_orders_account_strategy_status "
        "ON paper_orders(account_id,strategy_id,status)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS paper_orders_reservation ON paper_orders(reservation_id)"
    )
    connection.execute("""CREATE TABLE IF NOT EXISTS paper_risk_reservations (
        reservation_id TEXT PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id),
        intent_id TEXT NOT NULL UNIQUE REFERENCES paper_orders(intent_id),
        strategy_id TEXT NOT NULL CHECK(strategy_id IN ('STRATEGY_CORE','AI_FREQAI')),
        reservation_kind TEXT NOT NULL CHECK(reservation_kind IN
            ('ENTRY','DCA','PENDING','BOOK_DEPTH')),
        status TEXT NOT NULL CHECK(status IN
            ('ACTIVE','PARTIAL','RELEASED','CONSUMED','EXPIRED')),
        reserved_margin_quote TEXT NOT NULL,
        reserved_notional_quote TEXT NOT NULL,
        leverage TEXT NOT NULL,
        equity_basis_quote TEXT NOT NULL,
        risk_config_version TEXT NOT NULL,
        created_at_ms INTEGER NOT NULL,
        updated_at_ms INTEGER NOT NULL
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS paper_book_level_reservations (
        reservation_id TEXT NOT NULL REFERENCES paper_risk_reservations(reservation_id),
        book_id TEXT NOT NULL,
        side TEXT NOT NULL CHECK(side IN ('BUY','SELL')),
        price TEXT NOT NULL,
        reserved_quantity TEXT NOT NULL,
        remaining_quantity TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('ACTIVE','RELEASED','CONSUMED')),
        PRIMARY KEY(reservation_id,book_id,side,price)
    )""")
    connection.execute(
        "CREATE INDEX IF NOT EXISTS paper_book_level_active "
        "ON paper_book_level_reservations(book_id,side,price,status)"
    )
    connection.execute("""CREATE TABLE IF NOT EXISTS paper_funding_events (
        funding_event_id TEXT PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id),
        strategy_id TEXT NOT NULL CHECK(strategy_id IN
            ('STRATEGY_CORE','AI_FREQAI','LEGACY_UNATTRIBUTED')),
        amount_quote TEXT NOT NULL,
        event_at_ms INTEGER NOT NULL,
        source_snapshot_id TEXT NOT NULL,
        payload_hash TEXT NOT NULL UNIQUE
    )""")

    latest_mark = connection.execute(
        "SELECT observed_at_ms FROM paper_equity_history ORDER BY observed_at_ms DESC,id DESC LIMIT 1"
    ).fetchone()
    applied_at = latest_mark[0] if latest_mark else 0
    connection.execute(
        "INSERT INTO paper_accounts VALUES (1,'PAPER',?,'USDT',?,?)",
        (str(initial_capital), applied_at, MIGRATION_VERSION),
    )

    positions = {
        "STRATEGY_CORE": ("0", "0"),
        "AI_FREQAI": ("0", "0"),
        "LEGACY_UNATTRIBUTED": ("0", "0"),
    }
    legacy_qty, legacy_avg = Decimal(legacy_position), Decimal(legacy_average)
    if legacy_qty:
        target_owner = owner if owner in DUAL_STRATEGIES else "LEGACY_UNATTRIBUTED"
        positions[target_owner] = (text(legacy_qty), text(legacy_avg))

    for strategy_id, (quantity, average) in positions.items():
        connection.execute(
            """INSERT INTO paper_strategy_ledgers
               (account_id,strategy_id,position_base,average_entry_price,realized_pnl_quote,
                fees_quote,funding_quote,dca_used,initial_margin_quote,updated_at_ms,version)
               VALUES (1,?,?,?,'0','0','0',0,'0',?,1)""",
            (strategy_id, quantity, average, applied_at),
        )

    adjustment_source = json.dumps(
        {"position": str(legacy_position), "average": str(legacy_average),
         "realized": str(legacy_realized), "fees": str(legacy_fees),
         "owner": owner_row[0]},
        sort_keys=True, separators=(",", ":"),
    )
    adjustment_hash = hashlib.sha256(adjustment_source.encode()).hexdigest()
    for adjustment_type, amount in (
        ("LEGACY_REALIZED_PNL", legacy_realized),
        ("LEGACY_FEES", legacy_fees),
    ):
        connection.execute(
            """INSERT INTO paper_account_adjustments
               VALUES (?,?,?,?,?,?,?,?)""",
            (f"legacy-v1:{adjustment_type}", 1, "LEGACY_UNATTRIBUTED",
             adjustment_type, text(Decimal(amount)), "paper_state", adjustment_hash, applied_at),
        )

    # A single-position historical equity curve cannot prove aggregate cutover
    # equity or historical funding. Keep the account explicitly not risk-ready.
    connection.execute(
        """INSERT INTO paper_account_risk_state
           VALUES (1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,
                   'LEGACY_CUTOVER_REQUIRES_EQUITY_AND_FUNDING_RECONCILIATION',?,1)""",
        (applied_at,),
    )
    connection.execute(
        """INSERT INTO paper_schema_migrations
           VALUES (?,?,?,?,?,'APPLIED')""",
        (MIGRATION_VERSION, "dual_ledger_v1", MIGRATION_CHECKSUM, applied_at, source_sha.lower()),
    )


class PaperLedger:
    def __init__(self, db_path, *, max_position_base="0.01", fee_rate="0.0005", max_spread_bps="50", risk_limits=None, require_risk_limits=False, leverage="13", strategy_id="MANUAL", source_sha=None):
        self.path = Path(db_path)
        self.maximum, self.fee_rate, self.spread = number(max_position_base), number(fee_rate), number(max_spread_bps)
        self.risk_limits, self.require_risk_limits = risk_limits, bool(require_risk_limits)
        self.leverage = number(leverage)
        if strategy_id not in {"MANUAL", *DUAL_STRATEGIES}:
            raise ValueError("Invalid paper ledger strategy scope")
        self.strategy_id = strategy_id
        self.source_sha = source_sha
        if self.leverage <= 0:
            raise ValueError("Invalid strategy leverage")
        if self.maximum <= 0 or self.fee_rate > 1 or not 0 < self.spread <= 10_000:
            raise ValueError("Invalid paper risk configuration")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection, connection:
            connection.execute("PRAGMA journal_mode=WAL")
            initialized = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_state'").fetchone()
            connection.execute("""CREATE TABLE IF NOT EXISTS paper_state (
                id INTEGER PRIMARY KEY CHECK(id=1), position TEXT NOT NULL, average TEXT NOT NULL,
                realized TEXT NOT NULL, fees TEXT NOT NULL, paused INTEGER NOT NULL)""")
            if not initialized:
                connection.execute("INSERT INTO paper_state VALUES (1,'0','0','0','0',0)")
            stored_state(connection)
            connection.execute("""CREATE TABLE IF NOT EXISTS paper_orders (
                intent_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, order_id TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL, document TEXT NOT NULL)""")
            connection.execute("CREATE INDEX IF NOT EXISTS paper_order_status ON paper_orders(status)")
            connection.execute("CREATE TABLE IF NOT EXISTS paper_books (book_id TEXT PRIMARY KEY, used_at_ms INTEGER NOT NULL)")
            connection.execute("""CREATE TABLE IF NOT EXISTS paper_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT, at_ms INTEGER NOT NULL, kind TEXT NOT NULL, document TEXT NOT NULL)""")
            risk_control.ensure(connection)
            strategy_table = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_strategy_state'").fetchone()
            connection.execute("""CREATE TABLE IF NOT EXISTS paper_strategy_state (
                id INTEGER PRIMARY KEY CHECK(id=1), owner TEXT, dca_used INTEGER NOT NULL CHECK(dca_used IN (0,1)),
                initial_margin_quote TEXT NOT NULL)""")
            if not strategy_table:
                legacy_position = Decimal(stored_state(connection)[0])
                connection.execute("INSERT OR IGNORE INTO paper_strategy_state VALUES (1,?,?,?)",
                                   ("LEGACY" if legacy_position else None, 0, "0"))
            else:
                existing_strategy = connection.execute("SELECT 1 FROM paper_strategy_state WHERE id=1").fetchone()
                if not existing_strategy:
                    legacy_position = Decimal(stored_state(connection)[0])
                    connection.execute("INSERT INTO paper_strategy_state VALUES (1,?,?,?)",
                                       ("LEGACY" if legacy_position else None, 0, "0"))
            equity_history.ensure(connection)
            if self.strategy_id in DUAL_STRATEGIES:
                migrate_dual_ledger(connection, self.source_sha)

    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @staticmethod
    def audit(connection, at_ms, kind, value):
        connection.execute("INSERT INTO paper_audit(at_ms,kind,document) VALUES (?,?,?)",
                           (at_ms, kind, json.dumps(value, allow_nan=False)))

    def submit(self, raw, book, now_ms, *, strategy_id=None, strategy_event=None):
        intent, now = intent_value(raw), stamp(now_ms)
        strategy_id = self.strategy_id if strategy_id is None else strategy_id
        if self.strategy_id in DUAL_STRATEGIES and strategy_id != self.strategy_id:
            raise ValueError("PAPER_LEDGER_STRATEGY_SCOPE_MISMATCH")
        if strategy_id not in {"MANUAL", "STRATEGY_CORE", "AI_FREQAI"}:
            raise ValueError("Invalid strategy owner")
        if strategy_event not in (None, "ENTRY", "DCA", "EXIT"):
            raise ValueError("Invalid strategy event")
        digest = identity("payload:", {**intent, "strategyId": strategy_id})
        with closing(self.connect()) as connection, connection, localcontext() as context:
            context.prec = 80
            connection.execute("BEGIN IMMEDIATE")
            position, average, realized, fees, paused = stored_state(connection)
            owner_row = connection.execute("SELECT owner,dca_used,initial_margin_quote FROM paper_strategy_state WHERE id=1").fetchone()
            owner, dca_used, initial_margin = owner_row
            previous = connection.execute("SELECT payload_hash,document FROM paper_orders WHERE intent_id=?", (intent["intentId"],)).fetchone()
            if previous:
                if previous[0] != digest:
                    raise ValueError("Intent ID was reused with a different payload")
                return json.loads(previous[1])
            target, limit = Decimal(intent["targetPositionBase"]), Decimal(intent["limitPrice"])
            delta, reason = target-position, None
            side = "BUY" if delta > 0 else "SELL" if delta < 0 else "NONE"
            quantity, filled, quote, fee = abs(delta), ZERO, ZERO, ZERO
            pending = connection.execute("SELECT 1 FROM paper_orders WHERE status IN ('OPEN','PARTIALLY_FILLED') LIMIT 1").fetchone()
            risk_reducing = position != 0 and target * position >= 0 and abs(target) < abs(position)
            risk_reason, auto_kill = equity_history.block_reason(connection, target_position=target,
                current_position=position, limit_price=limit, limits=self.risk_limits,
                require_limits=self.require_risk_limits, now_ms=now)
            if auto_kill:
                risk_control.set_kill(connection, True, now, auto_kill)
                self.audit(connection, now, "RISK_LIMIT_BREACH", {"reason": auto_kill})
            if risk_reason:
                reason = "PAUSED" if risk_reason == "RISK_PAUSED" else risk_reason
            elif not risk_reducing and owner not in (None, strategy_id) and position != 0:
                reason = "POSITION_OWNED_BY_OTHER_STRATEGY"
            elif not risk_reducing and risk_control.risk_block_reason(connection):
                block_reason = risk_control.risk_block_reason(connection)
                reason = "PAUSED" if block_reason == "RISK_PAUSED" else block_reason
            elif paused and not risk_reducing:
                reason = "PAUSED"
            elif not intent["decisionAtMs"] <= now <= intent["validUntilMs"]:
                reason = "EXPIRED_INTENT"
            elif not risk_reducing and abs(target) > self.maximum:
                reason = "POSITION_LIMIT"
            elif pending:
                reason = "PENDING_ORDER"
            else:
                try:
                    bids, asks, spread, book_id = book_value(book, now)
                except (ValueError, TypeError):
                    reason = "INVALID_BOOK"
                else:
                    if spread > self.spread:
                        reason = "SPREAD_LIMIT"
                    elif connection.execute("SELECT 1 FROM paper_books WHERE book_id=?", (book_id,)).fetchone():
                        reason = "SNAPSHOT_ALREADY_USED"
            if reason is None and quantity:
                starting_position = position
                for price, visible in (asks if delta > 0 else bids):
                    if (delta > 0 and price > limit) or (delta < 0 and price < limit):
                        break
                    take = min(quantity-filled, visible)
                    filled, quote = filled+take, quote+take*price
                    # Book levels can straddle the point where an old position is
                    # closed. Account each fill at its own price, not order VWAP.
                    signed_fill = take if delta > 0 else -take
                    new_position = position+signed_fill
                    if position == 0 or position*signed_fill > 0:
                        average = (abs(position)*average+take*price)/abs(new_position)
                    else:
                        realized += min(abs(position), take)*(price-average)*(1 if position > 0 else -1)
                        if new_position == 0:
                            average = ZERO
                        elif position*new_position < 0:
                            average = price
                    position = new_position
                    if filled == quantity:
                        break
                if filled:
                    # ponytail: consume a whole snapshot once; add per-level reservations
                    # only if repeated fills against one paper snapshot are required.
                    connection.execute("INSERT INTO paper_books VALUES (?,?)", (book_id, now))
                    fee = quote*self.fee_rate
                    fees += fee
                    connection.execute("UPDATE paper_state SET position=?,average=?,realized=?,fees=? WHERE id=1",
                                       tuple(map(text, (position, average, realized, fees))))
                    next_owner = owner
                    next_dca_used = dca_used
                    next_initial_margin = initial_margin
                    opened_or_reversed = position != 0 and (
                        owner is None or starting_position == 0 or starting_position * position < 0)
                    if position == 0:
                        next_owner, next_dca_used, next_initial_margin = None, 0, "0"
                    elif opened_or_reversed:
                        next_owner = strategy_id
                        next_dca_used = 1 if strategy_event == "DCA" else 0
                        next_initial_margin = text(abs(position) * average / self.leverage)
                    elif strategy_event == "DCA":
                        next_dca_used = 1
                    connection.execute("UPDATE paper_strategy_state SET owner=?,dca_used=?,initial_margin_quote=? WHERE id=1",
                                       (next_owner, next_dca_used, next_initial_margin))
            status = "REJECTED" if reason else "FILLED" if filled == quantity else "PARTIALLY_FILLED" if filled else "OPEN"
            order = {"orderId": identity("paper:", intent["intentId"]), "intentId": intent["intentId"],
                     "status": status, "side": side, "quantityBase": text(quantity), "filledBase": text(filled),
                     "remainingBase": text(quantity-filled), "averagePrice": text(quote/filled) if filled else None,
                     "feeQuote": text(fee), "createdAtMs": now, "updatedAtMs": now, "mode": "PAPER",
                     "reason": reason or ("TARGET_ALREADY_REACHED" if quantity == 0 else "VISIBLE_DEPTH_SIMULATION")}
            connection.execute("INSERT INTO paper_orders(intent_id,payload_hash,order_id,status,document) VALUES (?,?,?,?,?)",
                               (intent["intentId"], digest, order["orderId"], status, json.dumps(order, allow_nan=False)))
            self.audit(connection, now, "SUBMIT", order)
            return order

    def snapshot(self):
        return read_snapshot(self.path)

    def strategy_state(self):
        return self.snapshot().get("strategyState", {"owner": None, "dcaUsed": False, "initialMarginQuote": "0"})

    def record_equity(self, mark_price, candle_close_ms, observed_at_ms, dataset_version, initial_capital="100"):
        with closing(self.connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            position, average, realized, fees, _ = stored_state(connection)
            return equity_history.record(connection, initial_capital=initial_capital, position=position,
                average=average, realized=realized, fees=fees, mark_price=mark_price,
                candle_close_ms=candle_close_ms, observed_at_ms=observed_at_ms,
                dataset_version=dataset_version)

    def equity_snapshot(self, now_ms):
        with closing(self.connect()) as connection:
            connection.execute("BEGIN")
            return equity_history.snapshot(connection, now_ms)

    def audit_snapshot(self, limit=50, before_id=None):
        return read_audit(self.path, limit=limit, before_id=before_id)

    def set_paused(self, paused, now_ms):
        if type(paused) is not bool:
            raise ValueError("Paused must be a boolean")
        now = stamp(now_ms)
        with closing(self.connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("UPDATE paper_state SET paused=? WHERE id=1", (int(paused),))
            risk_control.set_paused(connection, paused, now)
            self.audit(connection, now, "PAUSE" if paused else "RESUME", {"paused": paused})
        return self.snapshot()

    def set_killed(self, enabled, now_ms, reason="OPERATOR_KILL_SWITCH"):
        now = stamp(now_ms)
        with closing(self.connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            risk_control.set_kill(connection, enabled, now, reason)
            self.audit(connection, now, "KILL_SWITCH", {"enabled": enabled, "reason": reason})
        return self.snapshot()

    def reset_kill(self, acknowledge, ready, now_ms):
        now = stamp(now_ms)
        with closing(self.connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            risk_control.reset_kill(connection, acknowledge, ready, now)
            self.audit(connection, now, "KILL_SWITCH_RESET", {"acknowledge": acknowledge, "ready": ready})
        return self.snapshot()

    def cancel(self, order_id, now_ms):
        now = stamp(now_ms)
        if not isinstance(order_id, str) or not 1 <= len(order_id) <= 200:
            raise ValueError("Invalid order identifier")
        with closing(self.connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT document FROM paper_orders WHERE order_id=?", (order_id,)).fetchone()
            if row is None:
                raise ValueError("Unknown paper order")
            order = json.loads(row[0])
            if now < order["createdAtMs"]:
                raise ValueError("Cancel time precedes order")
            if order["status"] in ACTIVE:
                order.update(status="CANCELED", updatedAtMs=now, reason="CANCELED_BY_USER")
                connection.execute("UPDATE paper_orders SET status=?,document=? WHERE order_id=?", (order["status"], json.dumps(order), order_id))
                self.audit(connection, now, "CANCEL", {"orderId": order_id})
            return order


def read_audit(db_path, *, limit=50, before_id=None):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("Invalid audit limit")
    if before_id is not None and (type(before_id) is not int or before_id <= 0):
        raise ValueError("Invalid audit cursor")
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError("Paper ledger is unavailable")
    with closing(sqlite3.connect(path.as_uri()+"?mode=ro", uri=True, timeout=10)) as connection:
        exists = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_audit'").fetchone()
        if not exists:
            return {"events": [], "nextBeforeId": None}
        if before_id is None:
            rows = connection.execute("SELECT id,at_ms,kind,document FROM paper_audit ORDER BY id DESC LIMIT ?", (limit+1,)).fetchall()
        else:
            rows = connection.execute("SELECT id,at_ms,kind,document FROM paper_audit WHERE id<? ORDER BY id DESC LIMIT ?", (before_id,limit+1)).fetchall()
        more = len(rows) > limit
        rows = rows[:limit]
        return {"events":[{"id":row[0],"atMs":row[1],"kind":row[2],"document":json.loads(row[3])} for row in rows],
                "nextBeforeId": rows[-1][0] if more and rows else None}
