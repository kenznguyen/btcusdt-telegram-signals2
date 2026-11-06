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


def read_snapshot(db_path, strategy_id=None):
    """Read an existing paper ledger without creating a database or initializing tables."""
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError("Paper ledger is unavailable")
    with closing(sqlite3.connect(path.as_uri()+"?mode=ro", uri=True, timeout=10)) as connection, connection, localcontext() as context:
        context.prec = 80
        connection.execute("BEGIN")
        risk = risk_control.snapshot(connection)
        if strategy_id in DUAL_STRATEGIES:
            migration = connection.execute(
                "SELECT 1 FROM paper_schema_migrations WHERE version=? AND status='APPLIED'",
                (MIGRATION_VERSION,),
            ).fetchone()
            if not migration:
                raise sqlite3.DatabaseError("DUAL_LEDGER_MIGRATION_NOT_APPLIED")
            row = connection.execute(
                """SELECT position_base,average_entry_price,realized_pnl_quote,fees_quote,
                          funding_quote,dca_used,initial_margin_quote
                   FROM paper_strategy_ledgers WHERE account_id=1 AND strategy_id=?""",
                (strategy_id,),
            ).fetchone()
            if row is None:
                raise sqlite3.DatabaseError("DUAL_LEDGER_STRATEGY_STATE_MISSING")
            try:
                position, average, realized, fees, funding, margin = (
                    Decimal(row[0]), Decimal(row[1]), Decimal(row[2]),
                    Decimal(row[3]), Decimal(row[4]), Decimal(row[6])
                )
                if any(not value.is_finite() for value in
                       (position, average, realized, fees, funding, margin)):
                    raise ValueError
                if (position == 0 and average != 0) or (position != 0 and average <= 0):
                    raise ValueError
                if fees < 0 or margin < 0 or type(row[5]) is not int or row[5] not in (0, 1):
                    raise ValueError
            except (DecimalException, TypeError, ValueError):
                raise sqlite3.DatabaseError("DUAL_LEDGER_STRATEGY_STATE_CORRUPT") from None
            orders = [json.loads(item[0]) for item in connection.execute(
                "SELECT document FROM paper_orders WHERE strategy_id=? ORDER BY rowid DESC LIMIT 100",
                (strategy_id,),
            )]
            return {
                "mode": "PAPER", "liveTradingSupported": False, "paused": risk["paused"],
                "riskControl": risk,
                "strategyState": {"owner": strategy_id, "strategyId": strategy_id,
                                  "dcaUsed": bool(row[5]), "initialMarginQuote": row[6]},
                "positionBase": text(position), "averageEntryPrice": text(average),
                "realizedPnlQuote": text(realized), "feesQuote": text(fees),
                "fundingQuote": text(funding), "netRealizedPnlQuote": text(realized-fees-funding),
                "orders": orders, "simulationModel": "VISIBLE_DEPTH_LIMIT_SNAPSHOT",
            }
        position, average, realized, fees, paused = stored_state(connection)
        strategy = connection.execute(
            "SELECT owner,dca_used,initial_margin_quote FROM paper_strategy_state WHERE id=1"
        ).fetchone() if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_strategy_state'"
        ).fetchone() else (None, 0, "0")
        orders = [json.loads(row[0]) for row in connection.execute(
            "SELECT document FROM paper_orders ORDER BY rowid DESC LIMIT 100"
        )]
        return {"mode": "PAPER", "liveTradingSupported": False, "paused": bool(paused),
                "riskControl": risk, "strategyState": {"owner": strategy[0],
                "dcaUsed": bool(strategy[1]), "initialMarginQuote": strategy[2]},
                "positionBase": text(position), "averageEntryPrice": text(average),
                "realizedPnlQuote": text(realized), "feesQuote": text(fees),
                "netRealizedPnlQuote": text(realized-fees), "orders": orders,
                "simulationModel": "VISIBLE_DEPTH_LIMIT_SNAPSHOT"}


DUAL_STRATEGIES = {"STRATEGY_CORE", "AI_FREQAI"}
MIGRATION_VERSION = 1
MIGRATION_CHECKSUM = hashlib.sha256(
    b"dual-ledger-v1.1:additive-account-strategy-ledgers-risk-reservations-funding-remaining"
).hexdigest()
LEGACY_BOOK_MIGRATION_VERSION = 2
LEGACY_BOOK_MIGRATION_CHECKSUM = hashlib.sha256(
    b"dual-ledger-v2:legacy-book-depth-consumption-reconciliation-evidence"
).hexdigest()


def read_account_risk_snapshot(db_path, *, now_ms):
    """Read a reconciled account-wide PAPER risk snapshot without writing state."""
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError("Paper ledger is unavailable")
    now = stamp(now_ms)

    def dec(raw, field, nonnegative=False):
        if not isinstance(raw, str) or not 1 <= len(raw) <= 256:
            raise sqlite3.DatabaseError(f"ACCOUNT_RISK_{field}_INVALID")
        try:
            value = Decimal(raw)
        except (DecimalException, TypeError, ValueError):
            raise sqlite3.DatabaseError(f"ACCOUNT_RISK_{field}_INVALID") from None
        if (not value.is_finite() or not -200 <= value.as_tuple().exponent <= 200
                or value.adjusted() > 200 or (nonnegative and value < 0)):
            raise sqlite3.DatabaseError(f"ACCOUNT_RISK_{field}_INVALID")
        return value

    uri = path.as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, timeout=10)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        migration = db.execute(
            "SELECT checksum FROM paper_schema_migrations WHERE version=? AND status='APPLIED'",
            (MIGRATION_VERSION,),
        ).fetchone()
        if migration is None or migration["checksum"] != MIGRATION_CHECKSUM:
            raise sqlite3.DatabaseError("DUAL_LEDGER_MIGRATION_NOT_APPLIED")

        account = db.execute(
            "SELECT initial_capital FROM paper_accounts WHERE account_id=1"
        ).fetchone()
        risk = db.execute(
            """SELECT high_water_mark_quote,daily_baseline_utc_day_ms,
                      daily_baseline_equity_quote,last_equity_quote,last_mark_price,
                      mark_observed_at_ms,mark_candle_close_ms,dataset_version,
                      risk_ready,unavailable_reason
               FROM paper_account_risk_state WHERE account_id=1"""
        ).fetchone()
        if account is None or risk is None or type(risk["risk_ready"]) is not int or risk["risk_ready"] not in (0, 1):
            raise sqlite3.DatabaseError("ACCOUNT_RISK_STATE_MISSING_OR_CORRUPT")

        capital = dec(account["initial_capital"], "INITIAL_CAPITAL", True)
        mark = dec(risk["last_mark_price"], "MARK_PRICE", True)
        hwm = dec(risk["high_water_mark_quote"], "HIGH_WATER_MARK", True)
        baseline = dec(risk["daily_baseline_equity_quote"], "DAILY_BASELINE", True)
        recorded_equity = dec(risk["last_equity_quote"], "LAST_EQUITY")
        observed, candle = stamp(risk["mark_observed_at_ms"]), stamp(risk["mark_candle_close_ms"])
        if capital <= 0 or mark <= 0 or hwm <= 0 or baseline <= 0:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_REQUIRED_AMOUNT_INVALID")
        if observed > now or now - observed > 30 * 60_000 or candle > observed or observed - candle > 30 * 60_000:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_MARK_STALE_OR_INVALID")
        if not isinstance(risk["dataset_version"], str) or not risk["dataset_version"].strip():
            raise sqlite3.DatabaseError("ACCOUNT_RISK_DATASET_VERSION_MISSING")

        rows = db.execute(
            """SELECT strategy_id,position_base,average_entry_price,realized_pnl_quote,
                      fees_quote,funding_quote,initial_margin_quote
               FROM paper_strategy_ledgers WHERE account_id=1"""
        ).fetchall()
        ledgers = {r["strategy_id"]: r for r in rows}
        required = {"STRATEGY_CORE", "AI_FREQAI", "LEGACY_UNATTRIBUTED"}
        if set(ledgers) != required:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_LEDGER_SET_INVALID")

        realized = fees = funding = unrealized = filled = Decimal(0)
        positions = {}
        for sid, row in ledgers.items():
            qty = dec(row["position_base"], sid + "_POSITION")
            avg = dec(row["average_entry_price"], sid + "_AVERAGE", True)
            rpnl = dec(row["realized_pnl_quote"], sid + "_REALIZED")
            fee = dec(row["fees_quote"], sid + "_FEES", True)
            fund = dec(row["funding_quote"], sid + "_FUNDING")
            margin = dec(row["initial_margin_quote"], sid + "_MARGIN", True)
            if (qty == 0 and avg != 0) or (qty != 0 and avg <= 0):
                raise sqlite3.DatabaseError("ACCOUNT_RISK_POSITION_INCONSISTENT")
            upnl = qty * (mark - avg) if qty else Decimal(0)
            realized += rpnl
            fees += fee
            funding += fund
            unrealized += upnl
            filled += abs(qty) * mark
            positions[sid] = {
                "positionBase": text(qty), "averageEntryPrice": text(avg),
                "realizedPnlQuote": text(rpnl), "feesQuote": text(fee),
                "fundingQuote": text(fund), "initialMarginQuote": text(margin),
                "unrealizedPnlQuote": text(upnl),
            }

        legacy_pnl = legacy_fees = Decimal(0)
        adjustments = db.execute(
            """SELECT adjustment_type,amount_quote FROM paper_account_adjustments
               WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'"""
        )
        for row in adjustments:
            value = dec(row["amount_quote"], "LEGACY_ADJUSTMENT")
            if row["adjustment_type"] == "LEGACY_REALIZED_PNL":
                legacy_pnl += value
            elif row["adjustment_type"] == "LEGACY_FEES" and value >= 0:
                legacy_fees += value
            else:
                raise sqlite3.DatabaseError("ACCOUNT_RISK_LEGACY_ADJUSTMENT_INVALID")

        equity = capital + realized + legacy_pnl - fees - legacy_fees - funding + unrealized
        if equity <= 0 or equity != recorded_equity:
            raise sqlite3.DatabaseError("ACCOUNT_EQUITY_RECONCILIATION_MISMATCH")

        reserved_notional = reserved_margin = Decimal(0)
        reservations = db.execute(
            """SELECT status,remaining_notional_quote,remaining_margin_quote,
                      reserved_notional_quote,reserved_margin_quote
               FROM paper_risk_reservations WHERE account_id=1"""
        )
        for row in reservations:
            rn = dec(row["remaining_notional_quote"], "RESERVATION_NOTIONAL", True)
            rm = dec(row["remaining_margin_quote"], "RESERVATION_MARGIN", True)
            on = dec(row["reserved_notional_quote"], "RESERVATION_ORIGINAL_NOTIONAL", True)
            om = dec(row["reserved_margin_quote"], "RESERVATION_ORIGINAL_MARGIN", True)
            if rn > on or rm > om:
                raise sqlite3.DatabaseError("ACCOUNT_RISK_RESERVATION_EXCEEDS_ORIGINAL")
            if row["status"] in ("ACTIVE", "PARTIAL"):
                reserved_notional += rn
                reserved_margin += rm
            elif row["status"] not in ("RELEASED", "CONSUMED", "EXPIRED"):
                raise sqlite3.DatabaseError("ACCOUNT_RISK_RESERVATION_STATUS_INVALID")

        day = now // 86_400_000 * 86_400_000
        if risk["daily_baseline_utc_day_ms"] != day:
            raise sqlite3.DatabaseError("ACCOUNT_RISK_DAILY_BASELINE_UNAVAILABLE")
        daily_pnl = equity - baseline
        drawdown = max(Decimal(0), hwm - equity)
        return {
            "mode": "PAPER", "liveTradingSupported": False, "available": True,
            "riskReady": bool(risk["risk_ready"]), "unavailableReason": risk["unavailable_reason"],
            "accountEquityQuote": text(equity),
            "grossExposureQuote": text(filled + reserved_notional),
            "filledExposureQuote": text(filled), "reservedNotionalQuote": text(reserved_notional),
            "reservedMarginQuote": text(reserved_margin),
            "maxDrawdownUsdt": text(drawdown), "maxDrawdownPct": text(drawdown / hwm * 100),
            "dailyPnlUsdt": text(daily_pnl), "dailyLossUsdt": text(max(Decimal(0), -daily_pnl)),
            "highWaterMarkQuote": text(hwm), "dailyBaselineUtcDayMs": day,
            "markPrice": text(mark), "markObservedAtMs": observed,
            "datasetVersion": risk["dataset_version"],
            "killSwitch": risk_control.snapshot(db), "positions": positions,
            "updatedAtMs": observed,
        }


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
        remaining_margin_quote TEXT NOT NULL,
        reserved_notional_quote TEXT NOT NULL,
        remaining_notional_quote TEXT NOT NULL,
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
    strategy_metadata = {
        strategy: (0, "0") for strategy in positions
    }
    legacy_qty, legacy_avg = Decimal(legacy_position), Decimal(legacy_average)
    legacy_dca = owner_row[1]
    try:
        legacy_margin = number(str(owner_row[2]))
    except (DecimalException, TypeError, ValueError):
        raise sqlite3.DatabaseError("DUAL_LEDGER_LEGACY_STRATEGY_STATE_CORRUPT") from None
    if type(legacy_dca) is not int or legacy_dca not in (0, 1) or legacy_margin < 0:
        raise sqlite3.DatabaseError("DUAL_LEDGER_LEGACY_STRATEGY_STATE_CORRUPT")
    if not legacy_qty and (legacy_dca or legacy_margin):
        raise sqlite3.DatabaseError("DUAL_LEDGER_LEGACY_STRATEGY_STATE_INCONSISTENT")
    if legacy_qty:
        target_owner = owner if owner in DUAL_STRATEGIES else "LEGACY_UNATTRIBUTED"
        positions[target_owner] = (text(legacy_qty), text(legacy_avg))
        strategy_metadata[target_owner] = (legacy_dca, text(legacy_margin))

    for strategy_id, (quantity, average) in positions.items():
        dca_used, initial_margin = strategy_metadata[strategy_id]
        connection.execute(
            """INSERT INTO paper_strategy_ledgers
               (account_id,strategy_id,position_base,average_entry_price,realized_pnl_quote,
                fees_quote,funding_quote,dca_used,initial_margin_quote,updated_at_ms,version)
               VALUES (1,?,?,?,'0','0','0',?,?,?,1)""",
            (strategy_id, quantity, average, dca_used, initial_margin, applied_at),
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


def migrate_legacy_book_depth(connection, source_sha):
    """Add an independent, append-only consumption ledger for legacy reductions."""
    if not isinstance(source_sha, str) or len(source_sha) != 40 or any(
        character not in "0123456789abcdef" for character in source_sha.lower()
    ):
        raise ValueError("DUAL_LEDGER_SOURCE_SHA_REQUIRED")

    base = connection.execute(
        "SELECT checksum,status FROM paper_schema_migrations WHERE version=?",
        (MIGRATION_VERSION,),
    ).fetchone()
    if base is None or base[0] != MIGRATION_CHECKSUM or base[1] != "APPLIED":
        raise sqlite3.DatabaseError("DUAL_LEDGER_V1_REQUIRED_FOR_LEGACY_BOOK_V2")

    applied = connection.execute(
        "SELECT checksum,status FROM paper_schema_migrations WHERE version=?",
        (LEGACY_BOOK_MIGRATION_VERSION,),
    ).fetchone()
    if applied:
        if (applied[0] != LEGACY_BOOK_MIGRATION_CHECKSUM
                or applied[1] != "APPLIED"):
            raise sqlite3.DatabaseError("LEGACY_BOOK_MIGRATION_CHECKSUM_MISMATCH")
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_legacy_book_consumptions'"
        ).fetchone()
        if not table:
            raise sqlite3.DatabaseError("LEGACY_BOOK_MIGRATION_SCHEMA_MISSING")
        return

    existing_table = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_legacy_book_consumptions'"
    ).fetchone()
    if existing_table:
        raise sqlite3.DatabaseError("LEGACY_BOOK_SCHEMA_WITHOUT_MIGRATION_RECORD")

    connection.execute("""CREATE TABLE paper_legacy_book_consumptions (
        consumption_id TEXT PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id),
        intent_id TEXT NOT NULL REFERENCES paper_orders(intent_id),
        book_id TEXT NOT NULL CHECK(length(book_id)>0),
        side TEXT NOT NULL CHECK(side IN ('BUY','SELL')),
        price TEXT NOT NULL,
        consumed_quantity TEXT NOT NULL,
        reconciliation_id TEXT NOT NULL CHECK(length(trim(reconciliation_id))>0),
        evidence_hash TEXT NOT NULL CHECK(
            length(evidence_hash)=71 AND substr(evidence_hash,1,7)='sha256:'
        ),
        created_at_ms INTEGER NOT NULL,
        UNIQUE(intent_id,book_id,side,price)
    )""")
    connection.execute(
        "CREATE INDEX paper_legacy_book_depth_active "
        "ON paper_legacy_book_consumptions(book_id,side,price)"
    )
    applied_at_row = connection.execute(
        "SELECT updated_at_ms FROM paper_account_risk_state WHERE account_id=1"
    ).fetchone()
    applied_at = applied_at_row[0] if applied_at_row else 0
    connection.execute(
        """INSERT INTO paper_schema_migrations
           (version,name,checksum,applied_at_ms,source_sha,status)
           VALUES (?,?,?,?,?,'APPLIED')""",
        (LEGACY_BOOK_MIGRATION_VERSION, "legacy_book_depth_v2",
         LEGACY_BOOK_MIGRATION_CHECKSUM, applied_at, source_sha.lower()),
    )


def reduce_legacy_unattributed(
    db_path, raw, book, now_ms, *, reconciliation_id, evidence_hash,
    fee_rate="0.001", max_spread_bps="50",
):
    """PAPER-only close/flatten path for unattributed legacy exposure; never opens risk."""
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError("Paper ledger is unavailable")
    intent, now = intent_value(raw), stamp(now_ms)
    if (not isinstance(reconciliation_id, str) or not reconciliation_id.strip()
            or len(reconciliation_id) > 256 or not reconciliation_id.isprintable()):
        raise ValueError("LEGACY_RECONCILIATION_ID_REQUIRED")
    if (not isinstance(evidence_hash, str) or len(evidence_hash) != 71
            or not evidence_hash.startswith("sha256:")
            or any(character not in "0123456789abcdef" for character in evidence_hash[7:])):
        raise ValueError("LEGACY_EVIDENCE_HASH_REQUIRED")
    fee = number(fee_rate)
    spread_limit = number(max_spread_bps)
    if fee < 0 or fee > 1 or spread_limit <= 0:
        raise ValueError("LEGACY_REDUCTION_CONFIGURATION_INVALID")

    strategy_id = "LEGACY_UNATTRIBUTED"
    event = "LEGACY_REDUCTION"
    digest = identity("payload:", {
        **intent, "strategyId": strategy_id, "strategyEvent": event,
        "reconciliationId": reconciliation_id, "evidenceHash": evidence_hash,
    })

    with closing(sqlite3.connect(path, timeout=10)) as connection, connection, localcontext() as context:
        context.prec = 80
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("BEGIN IMMEDIATE")

        migration = connection.execute(
            "SELECT checksum,status FROM paper_schema_migrations WHERE version=?",
            (LEGACY_BOOK_MIGRATION_VERSION,),
        ).fetchone()
        if (migration is None or migration[0] != LEGACY_BOOK_MIGRATION_CHECKSUM
                or migration[1] != "APPLIED"):
            raise sqlite3.DatabaseError("LEGACY_BOOK_MIGRATION_NOT_APPLIED")

        previous = connection.execute(
            "SELECT payload_hash,document FROM paper_orders WHERE intent_id=?",
            (intent["intentId"],),
        ).fetchone()
        if previous:
            if previous[0] != digest:
                raise ValueError("Intent ID was reused with a different payload")
            return json.loads(previous[1])

        row = connection.execute(
            """SELECT position_base,average_entry_price,realized_pnl_quote,fees_quote,
                      funding_quote,dca_used,initial_margin_quote
               FROM paper_strategy_ledgers
               WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'"""
        ).fetchone()
        if row is None:
            raise sqlite3.DatabaseError("DUAL_LEDGER_LEGACY_STRATEGY_STATE_MISSING")
        try:
            position, average, realized, fees, funding, margin = (
                Decimal(row[0]), Decimal(row[1]), Decimal(row[2]),
                Decimal(row[3]), Decimal(row[4]), Decimal(row[6])
            )
            if any(not value.is_finite() for value in
                   (position, average, realized, fees, funding, margin)):
                raise ValueError
            if ((position == 0 and average != 0) or (position != 0 and average <= 0)
                    or fees < 0 or margin < 0 or type(row[5]) is not int
                    or row[5] not in (0, 1)):
                raise ValueError
        except (DecimalException, TypeError, ValueError):
            raise sqlite3.DatabaseError("DUAL_LEDGER_LEGACY_STRATEGY_STATE_CORRUPT") from None

        target = Decimal(intent["targetPositionBase"])
        delta = target - position
        quantity = abs(delta)
        side = "BUY" if delta > 0 else "SELL" if delta < 0 else "NONE"
        reducing = (
            position != 0 and target * position >= 0
            and abs(target) < abs(position)
        )
        reason = None if reducing else "LEGACY_REDUCTION_ONLY"
        bids = asks = None
        book_id = None
        if reason is None and not intent["decisionAtMs"] <= now <= intent["validUntilMs"]:
            reason = "EXPIRED_INTENT"
        if reason is None:
            try:
                bids, asks, spread, book_id = book_value(book, now)
            except (ValueError, TypeError):
                reason = "INVALID_BOOK"
            else:
                if spread > spread_limit:
                    reason = "SPREAD_LIMIT"

        filled = quote = fee_quote = ZERO
        next_position, next_average = position, average
        next_realized, next_fees = realized, fees
        used_levels = []
        if reason is None and quantity:
            levels = asks if delta > 0 else bids
            for price, visible in levels:
                if (delta > 0 and price > Decimal(intent["limitPrice"])) or (
                    delta < 0 and price < Decimal(intent["limitPrice"])
                ):
                    break
                core_ai_rows = connection.execute(
                    """SELECT reserved_quantity FROM paper_book_level_reservations
                       WHERE book_id=? AND side=? AND price=?
                         AND status IN ('ACTIVE','CONSUMED')""",
                    (book_id, side, text(price)),
                ).fetchall()
                legacy_rows = connection.execute(
                    """SELECT consumed_quantity FROM paper_legacy_book_consumptions
                       WHERE book_id=? AND side=? AND price=?""",
                    (book_id, side, text(price)),
                ).fetchall()
                already_used = (
                    sum((Decimal(item[0]) for item in core_ai_rows), ZERO)
                    + sum((Decimal(item[0]) for item in legacy_rows), ZERO)
                )
                available = max(ZERO, visible - already_used)
                take = min(quantity - filled, available)
                if take <= 0:
                    continue
                filled += take
                quote += take * price
                signed_fill = take if delta > 0 else -take
                new_position = next_position + signed_fill
                if next_position == 0 or next_position * signed_fill > 0:
                    next_average = (
                        abs(next_position) * next_average + take * price
                    ) / abs(new_position)
                else:
                    next_realized += min(abs(next_position), take) * (
                        price - next_average
                    ) * (1 if next_position > 0 else -1)
                    if new_position == 0:
                        next_average = ZERO
                next_position = new_position
                used_levels.append((side, text(price), text(take)))
                if filled == quantity:
                    break
            if filled:
                fee_quote = quote * fee
                next_fees += fee_quote

        status = "REJECTED" if reason else (
            "FILLED" if filled == quantity else
            "PARTIALLY_FILLED" if filled else "OPEN"
        )
        order = {
            "orderId": identity("paper:", intent["intentId"]),
            "intentId": intent["intentId"],
            "strategyId": strategy_id,
            "strategyEvent": event,
            "reservationId": None,
            "status": status,
            "side": side,
            "quantityBase": text(quantity),
            "filledBase": text(filled),
            "remainingBase": text(quantity - filled),
            "averagePrice": text(quote / filled) if filled else None,
            "feeQuote": text(fee_quote),
            "createdAtMs": now,
            "updatedAtMs": now,
            "mode": "PAPER",
            "reason": reason or (
                "VISIBLE_DEPTH_SIMULATION" if filled else "NO_VISIBLE_DEPTH"
            ),
            "reconciliationId": reconciliation_id,
            "evidenceHash": evidence_hash,
        }
        connection.execute(
            """INSERT INTO paper_orders
               (intent_id,payload_hash,order_id,status,document,account_id,strategy_id,
                strategy_event,reservation_id,created_schema_version)
               VALUES (?,?,?,?,?,1,?,?,NULL,?)""",
            (intent["intentId"], digest, order["orderId"], status,
             json.dumps(order, allow_nan=False), strategy_id, event,
             LEGACY_BOOK_MIGRATION_VERSION),
        )

        if filled:
            next_margin = (
                margin * abs(next_position) / abs(position)
                if next_position else ZERO
            )
            next_dca = row[5] if next_position else 0
            connection.execute(
                """UPDATE paper_strategy_ledgers
                   SET position_base=?,average_entry_price=?,realized_pnl_quote=?,
                       fees_quote=?,dca_used=?,initial_margin_quote=?,
                       updated_at_ms=?,version=version+1
                   WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'""",
                (text(next_position), text(next_average), text(next_realized),
                 text(next_fees), next_dca, text(next_margin), now),
            )
            for level_side, price_text, quantity_text in used_levels:
                consumption_id = identity("legacy-book-consumption:", {
                    "intentId": intent["intentId"], "bookId": book_id,
                    "side": level_side, "price": price_text,
                })
                connection.execute(
                    """INSERT INTO paper_legacy_book_consumptions
                       (consumption_id,account_id,intent_id,book_id,side,price,
                        consumed_quantity,reconciliation_id,evidence_hash,created_at_ms)
                       VALUES (?,1,?,?,?,?,?,?,?,?)""",
                    (consumption_id, intent["intentId"], book_id, level_side,
                     price_text, quantity_text, reconciliation_id, evidence_hash, now),
                )

            risk = connection.execute(
                """SELECT high_water_mark_quote,last_mark_price,risk_ready
                   FROM paper_account_risk_state WHERE account_id=1"""
            ).fetchone()
            if risk and risk[2]:
                try:
                    mark = Decimal(risk[1])
                    hwm = Decimal(risk[0])
                    capital_row = connection.execute(
                        "SELECT initial_capital FROM paper_accounts WHERE account_id=1"
                    ).fetchone()
                    if capital_row is None or not mark.is_finite() or mark <= 0 or not hwm.is_finite() or hwm <= 0:
                        raise ValueError
                    ledger_rows = connection.execute(
                        """SELECT position_base,average_entry_price,realized_pnl_quote,
                                  fees_quote,funding_quote
                           FROM paper_strategy_ledgers WHERE account_id=1"""
                    ).fetchall()
                    adjustment_rows = connection.execute(
                        """SELECT adjustment_type,amount_quote FROM paper_account_adjustments
                           WHERE account_id=1"""
                    ).fetchall()
                    aggregate_realized = aggregate_fees = aggregate_funding = unrealized = ZERO
                    for ledger_row in ledger_rows:
                        qty, avg, rpnl, ledger_fees, funding_total = map(Decimal, ledger_row)
                        if any(not value.is_finite() for value in
                               (qty, avg, rpnl, ledger_fees, funding_total)):
                            raise ValueError
                        aggregate_realized += rpnl
                        aggregate_fees += ledger_fees
                        aggregate_funding += funding_total
                        if qty:
                            unrealized += qty * (mark - avg)
                    adjustment_realized = sum(
                        (Decimal(amount) for kind, amount in adjustment_rows
                         if kind == "LEGACY_REALIZED_PNL"), ZERO
                    )
                    adjustment_fees = sum(
                        (Decimal(amount) for kind, amount in adjustment_rows
                         if kind == "LEGACY_FEES"), ZERO
                    )
                    equity_after = (
                        Decimal(capital_row[0]) + adjustment_realized
                        + aggregate_realized + unrealized
                        - adjustment_fees - aggregate_fees - aggregate_funding
                    )
                    if not equity_after.is_finite() or equity_after <= 0:
                        raise ValueError
                    connection.execute(
                        """UPDATE paper_account_risk_state
                           SET last_equity_quote=?,high_water_mark_quote=?,
                               updated_at_ms=?,version=version+1
                           WHERE account_id=1""",
                        (text(equity_after), text(max(hwm, equity_after)), now),
                    )
                except (DecimalException, TypeError, ValueError):
                    connection.execute(
                        """UPDATE paper_account_risk_state
                           SET risk_ready=0,
                               unavailable_reason='LEGACY_REDUCTION_EQUITY_RECONCILIATION_FAILED',
                               updated_at_ms=?,version=version+1
                           WHERE account_id=1""",
                        (now,),
                    )

        audit = {
            **order,
            "bookId": book_id,
            "consumedLevels": [
                {"side": item[0], "price": item[1], "quantity": item[2]}
                for item in used_levels
            ],
        }
        connection.execute(
            "INSERT INTO paper_audit(at_ms,kind,document) VALUES (?,?,?)",
            (now, event, json.dumps(audit, allow_nan=False)),
        )
        return order


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
                migrate_legacy_book_depth(connection, self.source_sha)

    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @staticmethod
    def audit(connection, at_ms, kind, value):
        connection.execute("INSERT INTO paper_audit(at_ms,kind,document) VALUES (?,?,?)",
                           (at_ms, kind, json.dumps(value, allow_nan=False)))


    def _submit_scoped(self, intent, book, now, strategy_event):
        strategy_id = self.strategy_id
        if strategy_event not in (None, "ENTRY", "DCA", "EXIT"):
            raise ValueError("Invalid strategy event")
        with closing(self.connect()) as connection, connection, localcontext() as context:
            context.prec = 80
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """SELECT position_base,average_entry_price,realized_pnl_quote,fees_quote,
                          funding_quote,dca_used,initial_margin_quote
                   FROM paper_strategy_ledgers WHERE account_id=1 AND strategy_id=?""",
                (strategy_id,),
            ).fetchone()
            if row is None:
                raise sqlite3.DatabaseError("DUAL_LEDGER_STRATEGY_STATE_MISSING")
            try:
                position, average, realized, fees, funding, margin = (
                    Decimal(row[0]), Decimal(row[1]), Decimal(row[2]),
                    Decimal(row[3]), Decimal(row[4]), Decimal(row[6])
                )
                if any(not value.is_finite() for value in
                       (position, average, realized, fees, funding, margin)):
                    raise ValueError
                if (position == 0 and average != 0) or (position != 0 and average <= 0):
                    raise ValueError
                if fees < 0 or margin < 0 or type(row[5]) is not int or row[5] not in (0, 1):
                    raise ValueError
            except (DecimalException, TypeError, ValueError):
                raise sqlite3.DatabaseError("DUAL_LEDGER_STRATEGY_STATE_CORRUPT") from None

            digest = identity("payload:", {
                **intent, "strategyId": strategy_id, "strategyEvent": strategy_event,
            })
            previous = connection.execute(
                "SELECT payload_hash,document FROM paper_orders WHERE intent_id=?",
                (intent["intentId"],),
            ).fetchone()
            if previous:
                if previous[0] != digest:
                    raise ValueError("Intent ID was reused with a different payload")
                return json.loads(previous[1])

            target = Decimal(intent["targetPositionBase"])
            limit = Decimal(intent["limitPrice"])
            delta = target - position
            quantity = abs(delta)
            side = "BUY" if delta > 0 else "SELL" if delta < 0 else "NONE"
            reducing = position != 0 and target * position >= 0 and abs(target) < abs(position)
            reversing = position != 0 and target * position < 0
            increase_quantity = (
                abs(target) if reversing else
                max(ZERO, abs(target) - abs(position)) if position * target > 0 else
                abs(target) if position == 0 else ZERO
            )
            event = strategy_event or (
                "ENTRY" if position == 0 or reversing else
                "DCA" if increase_quantity > 0 else "EXIT"
            )
            if event == "EXIT" and increase_quantity > 0:
                reason = "EXIT_CANNOT_INCREASE_EXPOSURE"
            elif increase_quantity > 0 and event == "DCA" and bool(row[5]):
                reason = "DCA_ALREADY_USED"
            elif increase_quantity > 0 and event == "DCA" and position == 0:
                reason = "DCA_REQUIRES_EXISTING_POSITION"
            elif increase_quantity > 0 and event == "ENTRY" and position != 0 and not reversing:
                reason = "ENTRY_REQUIRES_FLAT_OR_REVERSAL"
            elif increase_quantity == 0 and event == "DCA":
                reason = "DCA_WITHOUT_EXPOSURE_INCREASE"
            else:
                reason = None

            pending = connection.execute(
                """SELECT 1 FROM paper_orders
                   WHERE strategy_id=? AND status IN ('OPEN','PARTIALLY_FILLED') LIMIT 1""",
                (strategy_id,),
            ).fetchone()
            if reason is None and pending:
                reason = "PENDING_ORDER"

            risk_row = connection.execute(
                """SELECT high_water_mark_quote,daily_baseline_utc_day_ms,
                          daily_baseline_equity_quote,last_equity_quote,last_mark_price,
                          mark_observed_at_ms,mark_candle_close_ms,dataset_version,
                          risk_ready,unavailable_reason
                   FROM paper_account_risk_state WHERE account_id=1"""
            ).fetchone()
            account = connection.execute(
                "SELECT initial_capital FROM paper_accounts WHERE account_id=1"
            ).fetchone()
            adjustment_rows = connection.execute(
                "SELECT adjustment_type,amount_quote FROM paper_account_adjustments WHERE account_id=1"
            ).fetchall()
            mark = mark_observed = mark_candle = None
            equity = None
            if increase_quantity > 0 and reason is None:
                legacy_row = connection.execute(
                    """SELECT position_base FROM paper_strategy_ledgers
                       WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'"""
                ).fetchone()
                try:
                    legacy_quantity = Decimal(legacy_row[0]) if legacy_row else ZERO
                    if not legacy_quantity.is_finite():
                        raise ValueError
                except (DecimalException, TypeError, ValueError):
                    reason = "LEGACY_UNATTRIBUTED_STATE_CORRUPT"
                if reason is None and legacy_quantity != 0:
                    reason = "LEGACY_UNATTRIBUTED_EXPOSURE"
                if reason is None and (self.risk_limits is None or not all(
                    key in self.risk_limits for key in
                    ("maxDrawdownPct", "maxDailyLossUsdt", "maxExposureUsdt")
                )):
                    reason = "RISK_LIMITS_UNCONFIGURED"
                if reason is None and (risk_row is None or account is None or not risk_row[8]):
                    reason = "RISK_INPUTS_UNAVAILABLE"
                elif reason is None:
                    try:
                        mark = Decimal(risk_row[4])
                        mark_observed = stamp(risk_row[5])
                        mark_candle = stamp(risk_row[6])
                        hwm = Decimal(risk_row[0])
                        daily_baseline = Decimal(risk_row[2])
                        if (
                            mark <= 0 or hwm <= 0 or daily_baseline <= 0 or
                            mark_observed > now or now-mark_observed > 30*60_000 or
                            mark_candle > now or now-mark_candle > 30*60_000 or
                            not risk_row[7] or
                            risk_row[1] != now//86_400_000*86_400_000
                        ):
                            raise ValueError
                    except (DecimalException, TypeError, ValueError):
                        reason = "RISK_INPUTS_STALE_OR_CORRUPT"
                    else:
                        ledgers = connection.execute(
                            """SELECT position_base,average_entry_price,realized_pnl_quote,
                                      fees_quote,funding_quote
                               FROM paper_strategy_ledgers WHERE account_id=1"""
                        ).fetchall()
                        adjustment_realized = sum(
                            (Decimal(amount) for kind, amount in adjustment_rows
                             if kind == "LEGACY_REALIZED_PNL"), ZERO
                        )
                        adjustment_fees = sum(
                            (Decimal(amount) for kind, amount in adjustment_rows
                             if kind == "LEGACY_FEES"), ZERO
                        )
                        aggregate_realized = aggregate_fees = aggregate_funding = unrealized = gross = ZERO
                        for ledger_row in ledgers:
                            qty, avg, rpnl, fee_total, funding_total = map(Decimal, ledger_row)
                            aggregate_realized += rpnl
                            aggregate_fees += fee_total
                            aggregate_funding += funding_total
                            if qty:
                                unrealized += qty * (mark-avg)
                                gross += abs(qty) * mark
                        equity = (
                            Decimal(account[0]) + adjustment_realized + aggregate_realized +
                            unrealized - adjustment_fees - aggregate_fees - aggregate_funding
                        )
                        if equity <= 0:
                            reason = "ACCOUNT_EQUITY_NON_POSITIVE"
                        else:
                            drawdown_pct = max(ZERO, hwm-equity) / hwm * Decimal(100)
                            daily_loss = max(ZERO, daily_baseline-equity)
                            if drawdown_pct >= Decimal(str(self.risk_limits["maxDrawdownPct"])):
                                reason = "MAX_DRAWDOWN_LIMIT"
                                risk_control.set_kill(connection, True, now, reason)
                            elif daily_loss >= Decimal(str(self.risk_limits["maxDailyLossUsdt"])):
                                reason = "DAILY_LOSS_LIMIT"
                                risk_control.set_kill(connection, True, now, reason)
                            else:
                                active_reservations = connection.execute(
                                    """SELECT remaining_notional_quote FROM paper_risk_reservations
                                       WHERE account_id=1 AND status IN ('ACTIVE','PARTIAL')"""
                                ).fetchall()
                                reserved = sum((Decimal(item[0]) for item in active_reservations), ZERO)
                                projected_gross = gross + reserved
                                if reversing:
                                    projected_gross -= abs(position)*mark
                                    projected_gross += abs(target)*mark
                                else:
                                    projected_gross += increase_quantity*mark
                                if projected_gross > Decimal(str(self.risk_limits["maxExposureUsdt"])):
                                    reason = "MAX_EXPOSURE_LIMIT"
                                else:
                                    admission_margin = equity * Decimal("0.01")
                                    admission_notional = admission_margin * self.leverage
                                    requested_notional = increase_quantity * limit
                                    if requested_notional > admission_notional:
                                        reason = "MARGIN_RESERVATION_EXCEEDED"

            if reason is None:
                latch_reason = risk_control.risk_block_reason(connection)
                if latch_reason and (increase_quantity > 0 or not reducing):
                    # A kill/pause blocks every increase, but does not block a valid reduction.
                    reason = latch_reason
            if reason is None and not intent["decisionAtMs"] <= now <= intent["validUntilMs"]:
                reason = "EXPIRED_INTENT"

            bids = asks = None
            book_id = None
            if reason is None and quantity:
                try:
                    bids, asks, spread, book_id = book_value(book, now)
                except (ValueError, TypeError):
                    reason = "INVALID_BOOK"
                else:
                    if spread > self.spread:
                        reason = "SPREAD_LIMIT"

            filled = quote = fee = ZERO
            next_position, next_average, next_realized, next_fees = position, average, realized, fees
            used_levels = []
            if reason is None and quantity:
                levels = asks if delta > 0 else bids
                for price, visible in levels:
                    if (delta > 0 and price > limit) or (delta < 0 and price < limit):
                        break
                    consumed_rows = connection.execute(
                        """SELECT reserved_quantity FROM paper_book_level_reservations
                           WHERE book_id=? AND side=? AND price=? AND status IN ('ACTIVE','CONSUMED')""",
                        (book_id, side, text(price)),
                    ).fetchall()
                    legacy_consumed_rows = connection.execute(
                        """SELECT consumed_quantity FROM paper_legacy_book_consumptions
                           WHERE book_id=? AND side=? AND price=?""",
                        (book_id, side, text(price)),
                    ).fetchall()
                    consumed = (
                        sum((Decimal(item[0]) for item in consumed_rows), ZERO)
                        + sum((Decimal(item[0]) for item in legacy_consumed_rows), ZERO)
                    )
                    available = max(ZERO, visible-consumed)
                    take = min(quantity-filled, available)
                    if take <= 0:
                        continue
                    filled += take
                    quote += take*price
                    signed_fill = take if delta > 0 else -take
                    new_position = next_position+signed_fill
                    if next_position == 0 or next_position*signed_fill > 0:
                        next_average = (
                            abs(next_position)*next_average+take*price
                        )/abs(new_position)
                    else:
                        next_realized += min(abs(next_position), take) * (
                            price-next_average
                        ) * (1 if next_position > 0 else -1)
                        if new_position == 0:
                            next_average = ZERO
                        elif next_position*new_position < 0:
                            next_average = price
                    next_position = new_position
                    used_levels.append((side, text(price), text(take)))
                    if filled == quantity:
                        break
                if filled:
                    fee = quote*self.fee_rate
                    next_fees += fee

            status = "REJECTED" if reason else (
                "FILLED" if filled == quantity else
                "PARTIALLY_FILLED" if filled else "OPEN"
            )
            reservation_id = identity("reservation:", {
                "intentId": intent["intentId"], "strategyId": strategy_id,
            }) if reason is None and quantity else None
            order = {
                "orderId": identity("paper:", intent["intentId"]),
                "intentId": intent["intentId"], "strategyId": strategy_id,
                "strategyEvent": event, "reservationId": reservation_id,
                "status": status, "side": side, "quantityBase": text(quantity),
                "filledBase": text(filled), "remainingBase": text(quantity-filled),
                "averagePrice": text(quote/filled) if filled else None,
                "feeQuote": text(fee), "createdAtMs": now, "updatedAtMs": now,
                "mode": "PAPER",
                "reason": reason or ("TARGET_ALREADY_REACHED" if quantity == 0 else "VISIBLE_DEPTH_SIMULATION"),
            }
            connection.execute(
                """INSERT INTO paper_orders
                   (intent_id,payload_hash,order_id,status,document,account_id,strategy_id,
                    strategy_event,reservation_id,created_schema_version)
                   VALUES (?,?,?,?,?,1,?,?,?,?)""",
                (intent["intentId"], digest, order["orderId"], status,
                 json.dumps(order, allow_nan=False), strategy_id, event,
                 reservation_id, MIGRATION_VERSION),
            )

            if reservation_id:
                if increase_quantity > 0:
                    reserved_margin = admission_margin
                    reserved_notional = admission_notional
                    opening_filled = (
                        max(ZERO, filled-abs(position)) if reversing else
                        min(filled, increase_quantity)
                    )
                    remaining_open = max(ZERO, increase_quantity-opening_filled)
                    remaining_notional = min(
                        reserved_notional, remaining_open*limit
                    )
                    remaining_margin = remaining_notional/self.leverage
                    reservation_status = (
                        "CONSUMED" if remaining_notional == 0 else
                        "PARTIAL" if filled else "ACTIVE"
                    )
                    reservation_kind = event
                else:
                    reserved_margin = reserved_notional = remaining_margin = remaining_notional = ZERO
                    reservation_status = "CONSUMED"
                    reservation_kind = "BOOK_DEPTH"
                config_version = identity("risk-config:", {
                    "limits": {key: str(value) for key, value in self.risk_limits.items()}
                    if self.risk_limits else None,
                    "leverage": text(self.leverage),
                })
                connection.execute(
                    """INSERT INTO paper_risk_reservations
                       (reservation_id,account_id,intent_id,strategy_id,reservation_kind,status,
                        reserved_margin_quote,remaining_margin_quote,reserved_notional_quote,
                        remaining_notional_quote,leverage,equity_basis_quote,risk_config_version,
                        created_at_ms,updated_at_ms)
                       VALUES (?,1,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (reservation_id, intent["intentId"], strategy_id, reservation_kind,
                     reservation_status, text(reserved_margin), text(remaining_margin),
                     text(reserved_notional), text(remaining_notional), text(self.leverage),
                     text(equity) if equity is not None else "0", config_version, now, now),
                )
                for level_side, price_text, quantity_text in used_levels:
                    connection.execute(
                        """INSERT INTO paper_book_level_reservations
                           (reservation_id,book_id,side,price,reserved_quantity,
                            remaining_quantity,status)
                           VALUES (?,?,?,?,?,'0','CONSUMED')""",
                        (reservation_id, book_id, level_side, price_text, quantity_text),
                    )

            if filled:
                next_margin = abs(next_position)*next_average/self.leverage if next_position else ZERO
                next_dca = 0 if next_position == 0 else (
                    1 if event == "DCA" and increase_quantity > 0 else row[5]
                )
                connection.execute(
                    """UPDATE paper_strategy_ledgers
                       SET position_base=?,average_entry_price=?,realized_pnl_quote=?,
                           fees_quote=?,dca_used=?,initial_margin_quote=?,
                           updated_at_ms=?,version=version+1
                       WHERE account_id=1 AND strategy_id=?""",
                    (text(next_position), text(next_average), text(next_realized),
                     text(next_fees), next_dca, text(next_margin), now, strategy_id),
                )
                if risk_row and risk_row[8]:
                    mark_for_update = Decimal(risk_row[4])
                    updated_rows = connection.execute(
                        """SELECT position_base,average_entry_price,realized_pnl_quote,
                                  fees_quote,funding_quote
                           FROM paper_strategy_ledgers WHERE account_id=1"""
                    ).fetchall()
                    unrealized_after = sum(
                        (Decimal(qty)*(mark_for_update-Decimal(avg)) if Decimal(qty) else ZERO)
                        for qty, avg, _, _, _ in updated_rows
                    )
                    realized_after = sum((Decimal(item[2]) for item in updated_rows), ZERO)
                    fees_after = sum((Decimal(item[3]) for item in updated_rows), ZERO)
                    funding_after = sum((Decimal(item[4]) for item in updated_rows), ZERO)
                    adjustment_realized_after = sum(
                        (Decimal(amount) for kind, amount in adjustment_rows
                         if kind == "LEGACY_REALIZED_PNL"), ZERO
                    )
                    adjustment_fees_after = sum(
                        (Decimal(amount) for kind, amount in adjustment_rows
                         if kind == "LEGACY_FEES"), ZERO
                    )
                    capital_after = Decimal(account[0]) if account else ZERO
                    equity_after = (
                        capital_after+adjustment_realized_after+realized_after+
                        unrealized_after-adjustment_fees_after-fees_after-funding_after
                    )
                    hwm_after = max(Decimal(risk_row[0]), equity_after)
                    connection.execute(
                        """UPDATE paper_account_risk_state
                           SET last_equity_quote=?,high_water_mark_quote=?,updated_at_ms=?,
                               version=version+1 WHERE account_id=1""",
                        (text(equity_after), text(hwm_after), now),
                    )
            self.audit(connection, now, "SUBMIT", order)
            return order

    def submit(self, raw, book, now_ms, *, strategy_id=None, strategy_event=None):
        intent, now = intent_value(raw), stamp(now_ms)
        strategy_id = self.strategy_id if strategy_id is None else strategy_id
        if self.strategy_id in DUAL_STRATEGIES and strategy_id != self.strategy_id:
            raise ValueError("PAPER_LEDGER_STRATEGY_SCOPE_MISMATCH")
        if self.strategy_id in DUAL_STRATEGIES:
            return self._submit_scoped(intent, book, now, strategy_event)
        with closing(self.connect()) as check_connection:
            migrated = check_connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_schema_migrations'"
            ).fetchone()
        if migrated:
            raise ValueError("DUAL_LEDGER_MIGRATION_ACTIVE_MANUAL_WRITE_BLOCKED")
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
        return read_snapshot(self.path, self.strategy_id)

    def strategy_state(self):
        return self.snapshot().get("strategyState", {"owner": None, "dcaUsed": False, "initialMarginQuote": "0"})

    def record_equity(self, mark_price, candle_close_ms, observed_at_ms, dataset_version, initial_capital="100"):
        if self.strategy_id in DUAL_STRATEGIES:
            raise ValueError("DUAL_LEDGER_ACCOUNT_EQUITY_REQUIRES_SHARED_RECONCILIATION")
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
            if self.strategy_id in DUAL_STRATEGIES:
                row = connection.execute(
                    "SELECT document,strategy_id FROM paper_orders WHERE order_id=?",
                    (order_id,),
                ).fetchone()
                if row is None:
                    raise ValueError("Unknown paper order")
                if row[1] != self.strategy_id:
                    raise ValueError("PAPER_ORDER_STRATEGY_SCOPE_MISMATCH")
                order = json.loads(row[0])
            else:
                # Pre-dual-ledger MANUAL databases have no strategy_id column.
                # Keep that compatibility path read-only with respect to schema,
                # while refusing to cancel an explicitly strategy-owned order.
                row = connection.execute(
                    "SELECT document FROM paper_orders WHERE order_id=?",
                    (order_id,),
                ).fetchone()
                if row is None:
                    raise ValueError("Unknown paper order")
                order = json.loads(row[0])
                if order.get("strategyId") not in (None, "MANUAL"):
                    raise ValueError("PAPER_ORDER_STRATEGY_SCOPE_MISMATCH")
            if now < order["createdAtMs"]:
                raise ValueError("Cancel time precedes order")
            if order["status"] in ACTIVE:
                order.update(status="CANCELED", updatedAtMs=now, reason="CANCELED_BY_USER")
                connection.execute("UPDATE paper_orders SET status=?,document=? WHERE order_id=?", (order["status"], json.dumps(order), order_id))
                reservation_id = order.get("reservationId")
                if reservation_id:
                    reservation = connection.execute(
                        "SELECT remaining_notional_quote FROM paper_risk_reservations WHERE reservation_id=?",
                        (reservation_id,),
                    ).fetchone()
                    if reservation:
                        next_status = "CONSUMED" if Decimal(order["filledBase"]) > 0 else "RELEASED"
                        connection.execute(
                            """UPDATE paper_risk_reservations
                               SET status=?,remaining_margin_quote='0',
                                   remaining_notional_quote='0',updated_at_ms=?
                               WHERE reservation_id=?""",
                            (next_status, now, reservation_id),
                        )
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
