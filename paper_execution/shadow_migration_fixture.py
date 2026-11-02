"""Build a deterministic legacy combined SQLite fixture for P5.2.4.

The fixture is disposable and never reads environment-selected/canonical paths.
"""
import json
import sqlite3
from pathlib import Path

from market_data.store import Candle, CandleStore
from paper_execution.ledger import PaperLedger


FIXED_NOW_MS = 1_800_000_000_000
PAPER_TABLES = (
    "paper_state", "paper_orders", "paper_books", "paper_audit",
    "paper_strategy_state", "paper_risk_control", "paper_equity_history",
    "paper_daily_baselines", "paper_account_config",
)
PAPER_CONFIG = {
    "initial_capital": "100",
    "max_position_base": "0.01",
    "fee_rate": "0.0005",
    "max_spread_bps": "50",
    "max_drawdown_pct": "20",
    "max_daily_loss_usdt": "5",
    "max_exposure_usdt": "10",
    "leverage": "13",
    "require_risk_limits": True,
}


def _candles(timeframe, count, start, interval, *, gap_at=None):
    rows = []
    for index in range(count):
        if gap_at is not None and index >= gap_at:
            opening = start + (index + 1) * interval
        else:
            opening = start + index * interval
        rows.append(Candle(
            timeframe=timeframe, open_time_ms=opening,
            open="60000", high="60100", low="59900", close="60050",
            volume="1.25", available_at_ms=opening + interval + 5_000,
        ))
    return rows


def build_legacy_fixture(path):
    """Create the source fixture using real repository schema constructors."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    PaperLedger(path, max_position_base="0.01", fee_rate="0.0005",
                max_spread_bps="50", leverage="13")
    CandleStore(path)

    with sqlite3.connect(path) as db:
        # T0 canonical candle data: continuous M15/H1 plus an isolated gap sample.
        m15_start = FIXED_NOW_MS - 12 * 900_000
        h1_start = FIXED_NOW_MS - 6 * 3_600_000
        for candle in _candles("15m", 12, m15_start, 900_000):
            c = candle.as_dict()
            db.execute("""INSERT INTO candles VALUES
                (?,?,?,?,?,?,?,?,?,?,?)""",
                (c["exchange"], c["marketType"], c["symbol"], c["timeframe"],
                 c["openTimeMs"], c["open"], c["high"], c["low"], c["close"],
                 c["volume"], c["availableAtMs"]))
        for candle in _candles("1h", 6, h1_start, 3_600_000):
            c = candle.as_dict()
            db.execute("""INSERT INTO candles VALUES
                (?,?,?,?,?,?,?,?,?,?,?)""",
                (c["exchange"], c["marketType"], c["symbol"], c["timeframe"],
                 c["openTimeMs"], c["open"], c["high"], c["low"], c["close"],
                 c["volume"], c["availableAtMs"]))
        # Separate symbol/timeframe sample records a real missing interval.
        gap_rows = _candles("15m", 3, FIXED_NOW_MS - 10 * 900_000,
                            900_000, gap_at=1)
        for candle in gap_rows:
            c = candle.as_dict()
            db.execute("""INSERT OR IGNORE INTO candles VALUES
                (?,?,?,?,?,?,?,?,?,?,?)""",
                (c["exchange"], c["marketType"], c["symbol"], c["timeframe"],
                 c["openTimeMs"], c["open"], c["high"], c["low"], c["close"],
                 c["volume"], c["availableAtMs"]))

        db.execute("""CREATE TABLE IF NOT EXISTS feeder_leases (
            lease_name TEXT PRIMARY KEY, owner TEXT, generation INTEGER NOT NULL,
            expires_at_ms INTEGER NOT NULL)""")
        db.execute("INSERT OR REPLACE INTO feeder_leases VALUES (?,?,?,?)",
                   ("binance-btcusdt-canonical", "fixture-owner-A", 7,
                    FIXED_NOW_MS + 60_000))
        db.execute("""CREATE TABLE IF NOT EXISTS feeder_runtime_status (
            lease_name TEXT PRIMARY KEY, owner TEXT NOT NULL,
            generation INTEGER NOT NULL, state TEXT NOT NULL,
            recovery_complete INTEGER NOT NULL, updated_at_ms INTEGER NOT NULL)""")
        db.execute("INSERT OR REPLACE INTO feeder_runtime_status VALUES (?,?,?,?,?,?)",
                   ("binance-btcusdt-canonical", "fixture-owner-A", 7,
                    "RUNNING", 1, FIXED_NOW_MS))

        # One open position, one filled order and representative non-open statuses.
        db.execute("UPDATE paper_state SET position='0.001',average='60000',"
                   "realized='1.25',fees='0.03',paused=0 WHERE id=1")
        db.execute("UPDATE paper_strategy_state SET owner='STRATEGY_CORE',"
                   "dca_used=1,initial_margin_quote='4.615384615384615' WHERE id=1")
        db.execute("UPDATE paper_risk_control SET paused=0,killed=1,"
                   "reason='FIXTURE_KILL_SWITCH',updated_at_ms=? WHERE id=1",
                   (FIXED_NOW_MS,))
        order_docs = [
            ("fixture-filled", "FILLED"),
            ("fixture-open", "OPEN"),
            ("fixture-cancelled", "CANCELED"),
            ("fixture-rejected", "REJECTED"),
        ]
        for index, (order_id, status) in enumerate(order_docs, 1):
            document = {"orderId": order_id, "intentId": order_id,
                        "status": status, "side": "BUY",
                        "filledBase": "0.001" if status == "FILLED" else "0",
                        "feeQuote": "0.03" if status == "FILLED" else "0"}
            db.execute("""INSERT INTO paper_orders
                (intent_id,payload_hash,order_id,status,document)
                VALUES (?,?,?,?,?)""",
                (order_id, "sha256:" + str(index) * 64, order_id,
                 status, json.dumps(document, sort_keys=True)))
        db.execute("INSERT INTO paper_books VALUES (?,?)",
                   ("fixture-book-hash", FIXED_NOW_MS))
        for index, kind in enumerate(("SUBMIT", "FILL", "CANCEL", "PAUSE", "KILL"), 1):
            db.execute("INSERT INTO paper_audit(at_ms,kind,document) VALUES (?,?,?)",
                       (FIXED_NOW_MS + index, kind,
                        json.dumps({"fixtureEvent": index}, sort_keys=True)))
        db.execute("""INSERT INTO paper_equity_history
            (snapshot_hash,candle_close_ms,observed_at_ms,mark_price,position_base,
             average_entry_price,realized_pnl,fees,unrealized_pnl,equity,
             high_water_mark,drawdown_usdt,drawdown_pct,exposure_usdt,dataset_version)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("fixture-equity-1", FIXED_NOW_MS, FIXED_NOW_MS + 5_000,
             "60050", "0.001", "60000", "1.25", "0.03", "0.05",
             "101.27", "102", "0.73", "0.715686", "60.05",
             "sha256:" + "a" * 64))
        for day in (FIXED_NOW_MS - 86_400_000, FIXED_NOW_MS):
            db.execute("INSERT INTO paper_daily_baselines VALUES (?,?,?,?)",
                       (day, day + 1_000, "100", "FIRST_OBSERVED_UTC_DAY"))
        db.execute("INSERT INTO paper_account_config VALUES (1,'100')")
        db.execute("CREATE TABLE IF NOT EXISTS paper_control_budget "
                   "(minute INTEGER PRIMARY KEY, used INTEGER NOT NULL)")
        db.executemany("INSERT INTO paper_control_budget VALUES (?,?)",
                       ((FIXED_NOW_MS // 60_000, 12),
                        (FIXED_NOW_MS // 60_000 + 1, 30)))
        db.commit()

    return {
        "source_db": str(path),
        "paper_tables": list(PAPER_TABLES),
        "paper_config": dict(PAPER_CONFIG),
        "fixed_now_ms": FIXED_NOW_MS,
    }
