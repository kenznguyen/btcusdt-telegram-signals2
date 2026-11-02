"""Read-only audit of canonical T0 candle integrity and continuity.

The audit opens SQLite in read-only/query-only mode. It never repairs, inserts,
updates, deletes, vacuums, checkpoints, or migrates canonical data.
"""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sqlite3
import sys
import time


INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000}
CANONICAL = ("binance", "USDT_PERPETUAL", "BTCUSDT")
REQUIRED_COLUMNS = {
    "exchange", "market_type", "symbol", "timeframe", "open_time_ms",
    "open", "high", "low", "close", "volume", "available_at_ms",
}
PRICE_COLUMNS = ("open", "high", "low", "close", "volume")


def _decimal(value, *, allow_zero=False):
    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        raise ValueError("decimal must be a bounded text value")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("decimal is invalid") from error
    if not number.is_finite() or len(number.as_tuple().digits) > 40:
        raise ValueError("decimal must be finite and bounded")
    if not -30 <= number.as_tuple().exponent <= 30 or number.adjusted() > 30:
        raise ValueError("decimal precision is outside supported bounds")
    if number < 0 or (not allow_zero and number == 0):
        raise ValueError("price must be positive and volume nonnegative")
    return number


def audit_database(db_path, *, as_of_ms=None):
    """Return a deterministic integrity report without mutating the database."""
    path = Path(db_path).expanduser().resolve()
    now = time.time_ns() // 1_000_000 if as_of_ms is None else as_of_ms
    if type(now) is not int or now < 0:
        raise ValueError("as_of_ms must be a nonnegative integer")

    report = {
        "schema_version": 1,
        "database": str(path),
        "as_of_ms": now,
        "result": "FAIL",
        "timeframes": {
            timeframe: {
                "rows": 0, "unique_rows": 0, "ordered_by_open_time_ms": True,
                "first_open_time_ms": None, "last_open_time_ms": None,
                "expected_between_first_last": 0, "missing_candles": 0, "gaps": [],
            }
            for timeframe in INTERVAL_MS
        },
        "issues": [],
        "read_only": True,
    }

    def issue(code, detail):
        report["issues"].append({"code": code, "detail": detail})

    if not path.is_file():
        issue("database_unavailable", "Canonical SQLite database file does not exist.")
        return report

    try:
        uri = path.as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=5) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only=ON")
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                issue("sqlite_integrity_check_failed", str(integrity))

            table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='candles'"
            ).fetchone()
            if table is None:
                issue("canonical_table_missing", "SQLite table 'candles' does not exist.")
                return report

            table_info = connection.execute("PRAGMA table_info(candles)").fetchall()
            columns = {row["name"] for row in table_info}
            missing_columns = sorted(REQUIRED_COLUMNS - columns)
            if missing_columns:
                issue("canonical_schema_invalid", "Missing columns: " + ", ".join(missing_columns))
                return report

            identity_columns = ("exchange", "market_type", "symbol", "timeframe", "open_time_ms")
            primary_key = tuple(
                row["name"] for row in sorted(table_info, key=lambda item: item["pk"]) if row["pk"]
            )
            unique_keys = []
            for index in connection.execute("PRAGMA index_list(candles)").fetchall():
                if index["unique"]:
                    index_columns = tuple(
                        item["name"] for item in connection.execute(
                            f'PRAGMA index_info("{index["name"]}")'
                        ).fetchall()
                    )
                    unique_keys.append(index_columns)
            if primary_key != identity_columns and identity_columns not in unique_keys:
                issue(
                    "identity_constraint_missing",
                    "Canonical schema must enforce uniqueness on exchange/market_type/symbol/timeframe/open_time_ms.",
                )

            selected = ", ".join(f'"{name}"' for name in sorted(REQUIRED_COLUMNS))
            rows = connection.execute(
                f"SELECT rowid AS audit_rowid, {selected} FROM candles "
                "ORDER BY timeframe, open_time_ms, rowid"
            ).fetchall()
    except sqlite3.Error as error:
        issue("database_read_failed", f"{type(error).__name__}: {error}")
        return report

    if not rows:
        issue("canonical_store_empty", "No canonical candle rows were found.")

    identities = Counter()
    valid_by_timeframe = defaultdict(list)
    read_order_by_timeframe = defaultdict(list)

    for row in rows:
        values = dict(row)
        timeframe = values["timeframe"]
        symbol = values["symbol"]
        opened = values["open_time_ms"]
        identity = (
            values["exchange"], values["market_type"], symbol, timeframe, opened
        )
        identities[identity] += 1

        if (values["exchange"], values["market_type"], symbol) != CANONICAL:
            issue(
                "noncanonical_market_identity",
                f"rowid={values['audit_rowid']} has market identity "
                f"{values['exchange']}/{values['market_type']}/{symbol}.",
            )

        interval = INTERVAL_MS.get(timeframe) if isinstance(timeframe, str) else None
        if interval is None:
            issue(
                "unsupported_timeframe",
                f"rowid={values['audit_rowid']} has unsupported timeframe {timeframe!r}.",
            )
            continue

        if type(opened) is not int or opened < 0:
            issue("invalid_open_timestamp", f"rowid={values['audit_rowid']} has invalid open_time_ms.")
            continue
        if opened % interval:
            issue(
                "timestamp_not_aligned",
                f"rowid={values['audit_rowid']} open_time_ms={opened} is not aligned to {timeframe}.",
            )
            continue

        available = values["available_at_ms"]
        if type(available) is not int or available < 0:
            issue("invalid_available_timestamp", f"rowid={values['audit_rowid']} has invalid available_at_ms.")
        elif available < opened + interval or opened + interval > now:
            issue(
                "candle_not_closed",
                f"rowid={values['audit_rowid']} was observed before close or is not closed as of audit time.",
            )

        valid_by_timeframe[timeframe].append(opened)
        read_order_by_timeframe[timeframe].append(opened)

        try:
            numbers = {
                name: _decimal(values[name], allow_zero=(name == "volume"))
                for name in PRICE_COLUMNS
            }
            if (
                numbers["low"] > numbers["high"]
                or not numbers["low"] <= numbers["open"] <= numbers["high"]
                or not numbers["low"] <= numbers["close"] <= numbers["high"]
            ):
                raise ValueError("OHLC values violate low <= open/close <= high")
        except (ValueError, TypeError) as error:
            issue("invalid_ohlcv", f"rowid={values['audit_rowid']}: {error}")

    for identity, count in identities.items():
        if count > 1:
            issue(
                "duplicate_candle_identity",
                f"{identity!r} occurs {count} times; key must be unique by exchange/market/symbol/timeframe/open time.",
            )

    for timeframe, interval in INTERVAL_MS.items():
        timestamps = sorted(set(valid_by_timeframe[timeframe]))
        summary = report["timeframes"][timeframe]
        summary["rows"] = len(valid_by_timeframe[timeframe])
        summary["unique_rows"] = len(timestamps)
        summary["ordered_by_open_time_ms"] = (
            read_order_by_timeframe[timeframe]
            == sorted(read_order_by_timeframe[timeframe])
        )
        if not timestamps:
            continue
        summary["first_open_time_ms"] = timestamps[0]
        summary["last_open_time_ms"] = timestamps[-1]
        expected = ((timestamps[-1] - timestamps[0]) // interval) + 1
        summary["expected_between_first_last"] = expected
        summary["missing_candles"] = max(0, expected - len(timestamps))

        for previous, current in zip(timestamps, timestamps[1:]):
            delta = current - previous
            if delta > interval and delta % interval == 0:
                missing = delta // interval - 1
                gap = {
                    "after_open_time_ms": previous,
                    "before_open_time_ms": current,
                    "missing_candles": missing,
                    "missing_duration_ms": missing * interval,
                }
                summary["gaps"].append(gap)
                issue(
                    "candle_gap",
                    f"{timeframe}: {missing} missing candle(s) between {previous} and {current}.",
                )

    report["result"] = "PASS" if not report["issues"] else "FAIL"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only T0 canonical candle integrity audit")
    parser.add_argument("--db", default=None, help="Canonical SQLite database path")
    parser.add_argument("--as-of-ms", type=int, default=None, help="Optional deterministic UTC epoch-ms audit time")
    args = parser.parse_args(argv)
    db_path = args.db or __import__("os").environ.get("MARKET_DATA_DB", "")
    if not db_path:
        parser.error("provide --db or set MARKET_DATA_DB")
    report = audit_database(db_path, as_of_ms=args.as_of_ms)
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    print(f"T0_DATA_INTEGRITY_CANDLE_CONTINUITY_GATE={report['result']}")
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
