"""Build a deterministic legacy combined SQLite fixture for P5.2.4.

The fixture is disposable and never reads environment-selected/canonical paths.
"""
import json
import sqlite3
from pathlib import Path

from market_data.feeder import LeaseStore
from market_data.feeder_status import FeederRuntimeStatusStore
from market_data.store import Candle, CandleStore
from paper_execution.ledger import PaperLedger


FIXED_NOW_MS = 1_800_000_000_000
LEASE_NAME = "binance-btcusdt-canonical"
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


def _candles(timeframe, count, start, interval):
    return [
        Candle(
            timeframe=timeframe, open_time_ms=start + index * interval,
            open="60000", high="60100", low="59900", close="60050",
            volume="1.25", available_at_ms=start + (index + 1) * interval + 5_000,
        )
        for index in range(count)
    ]


def _insert_candles(db, rows):
    for candle in rows:
        c = candle.as_dict()
        db.execute(
            """INSERT INTO candles VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (c["exchange"], c["marketType"], c["symbol"], c["timeframe"],
             c["openTimeMs"], c["open"], c["high"], c["low"], c["close"],
             c["volume"], c["availableAtMs"]),
        )


def build_legacy_fixture(path):
    """Create the source fixture using real repository schema constructors."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    risk_limits = {
        "maxDrawdownPct": PAPER_CONFIG["max_drawdown_pct"],
        "maxDailyLossUsdt": PAPER_CONFIG["max_daily_loss_usdt"],
        "maxExposureUsdt": PAPER_CONFIG["max_exposure_usdt"],
    }
    ledger = PaperLedger(
        path,
        max_position_base=PAPER_CONFIG["max_position_base"],
        fee_rate=PAPER_CONFIG["fee_rate"],
        max_spread_bps=PAPER_CONFIG["max_spread_bps"],
        risk_limits=risk_limits,
        require_risk_limits=PAPER_CONFIG["require_risk_limits"],
        leverage=PAPER_CONFIG["leverage"],
    )
    CandleStore(path).initialize_schema()

    m15_start = FIXED_NOW_MS - 12 * 900_000
    h1_start = FIXED_NOW_MS - 6 * 3_600_000
    mutation_gap_open_time_ms = m15_start + 6 * 900_000
    with sqlite3.connect(path) as db:
        # Both source time series are contiguous before any fault injection.
        _insert_candles(db, _candles("15m", 12, m15_start, 900_000))
        _insert_candles(db, _candles("1h", 6, h1_start, 3_600_000))
        db.commit()

        # LeaseStore's public constructor deliberately accepts str/bytes paths,
        # unlike the other schema helpers which normalize PathLike values.
        lease_store = LeaseStore(str(path), lease_name=LEASE_NAME)
        lease = lease_store.acquire("fixture-owner-A", now_ms=FIXED_NOW_MS, ttl_seconds=60)
        if lease is None:
            raise RuntimeError("Unable to acquire disposable fixture lease")
        # Advance through six expired-owner takeovers so the final owner is generation 7.
        for generation in range(2, 8):
            next_owner = "fixture-owner-B" if generation % 2 == 0 else "fixture-owner-A"
            lease = lease_store.acquire(
                next_owner,
                now_ms=FIXED_NOW_MS + (generation - 1) * 60_001,
                ttl_seconds=60,
            )
            if lease is None or lease.generation != generation:
                raise RuntimeError("Unable to seed deterministic lease generation")
        if lease.owner != "fixture-owner-A":
            raise RuntimeError("Fixture lease owner/generation mismatch")

        # Runtime status schema and fenced publication use the production store.
        status_store = FeederRuntimeStatusStore(path, lease_name=LEASE_NAME)
        status_time = FIXED_NOW_MS + 6 * 60_001
        if not status_store.publish(
            "fixture-owner-A", 7, "RUNNING",
            now_ms=status_time, recovery_complete=True,
        ):
            raise RuntimeError("Unable to publish disposable fixture runtime status")

        # One open position, one filled order and representative non-open statuses.
        db.execute(
            "UPDATE paper_state SET position='0.001',average='60000',"
            "realized='1.25',fees='0.03',paused=0 WHERE id=1"
        )
        db.execute(
            "UPDATE paper_strategy_state SET owner='STRATEGY_CORE',"
            "dca_used=1,initial_margin_quote='4.615384615384615' WHERE id=1"
        )
        db.execute(
            "UPDATE paper_risk_control SET paused=0,killed=1,"
            "reason='FIXTURE_KILL_SWITCH',updated_at_ms=? WHERE id=1",
            (FIXED_NOW_MS,),
        )
        order_docs = [
            ("fixture-filled", "FILLED"),
            ("fixture-open", "OPEN"),
            ("fixture-cancelled", "CANCELED"),
            ("fixture-rejected", "REJECTED"),
        ]
        for index, (order_id, status) in enumerate(order_docs, 1):
            document = {
                "orderId": order_id, "intentId": order_id,
                "status": status, "side": "BUY",
                "filledBase": "0.001" if status == "FILLED" else "0",
                "feeQuote": "0.03" if status == "FILLED" else "0",
            }
            db.execute(
                """INSERT INTO paper_orders
                (intent_id,payload_hash,order_id,status,document)
                VALUES (?,?,?,?,?)""",
                (order_id, "sha256:" + str(index) * 64, order_id,
                 status, json.dumps(document, sort_keys=True)),
            )
        db.execute("INSERT INTO paper_books VALUES (?,?)",
                   ("fixture-book-hash", FIXED_NOW_MS))
        for index, kind in enumerate(("SUBMIT", "FILL", "CANCEL", "PAUSE", "KILL"), 1):
            db.execute(
                "INSERT INTO paper_audit(at_ms,kind,document) VALUES (?,?,?)",
                (FIXED_NOW_MS + index, kind,
                 json.dumps({"fixtureEvent": index}, sort_keys=True)),
            )
        db.execute(
            """INSERT INTO paper_equity_history
            (snapshot_hash,candle_close_ms,observed_at_ms,mark_price,position_base,
             average_entry_price,realized_pnl,fees,unrealized_pnl,equity,
             high_water_mark,drawdown_usdt,drawdown_pct,exposure_usdt,dataset_version)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("fixture-equity-1", FIXED_NOW_MS, FIXED_NOW_MS + 5_000,
             "60050", "0.001", "60000", "1.25", "0.03", "0.05",
             "101.27", "102", "0.73", "0.715686", "60.05",
             "sha256:" + "a" * 64),
        )
        for day in (FIXED_NOW_MS - 86_400_000, FIXED_NOW_MS):
            db.execute("INSERT INTO paper_daily_baselines VALUES (?,?,?,?)",
                       (day, day + 1_000, "100", "FIRST_OBSERVED_UTC_DAY"))
        db.execute("INSERT INTO paper_account_config VALUES (1,'100')")
        db.execute(
            "CREATE TABLE IF NOT EXISTS paper_control_budget "
            "(minute INTEGER PRIMARY KEY, used INTEGER NOT NULL)"
        )
        db.executemany(
            "INSERT INTO paper_control_budget VALUES (?,?)",
            ((FIXED_NOW_MS // 60_000, 12),
             (FIXED_NOW_MS // 60_000 + 1, 30)),
        )
        db.commit()

    effective_config = {
        "initial_capital": PAPER_CONFIG["initial_capital"],
        "max_position_base": str(ledger.maximum),
        "fee_rate": str(ledger.fee_rate),
        "max_spread_bps": str(ledger.spread),
        "max_drawdown_pct": risk_limits["maxDrawdownPct"],
        "max_daily_loss_usdt": risk_limits["maxDailyLossUsdt"],
        "max_exposure_usdt": risk_limits["maxExposureUsdt"],
        "leverage": str(ledger.leverage),
        "require_risk_limits": ledger.require_risk_limits,
    }
    if effective_config != PAPER_CONFIG:
        raise RuntimeError("PaperLedger effective configuration differs from fixture manifest")

    return {
        "source_db": str(path),
        "paper_tables": list(PAPER_TABLES),
        "paper_config": effective_config,
        "fixed_now_ms": FIXED_NOW_MS,
        "m15_gap_mutation_open_time_ms": mutation_gap_open_time_ms,
    }
