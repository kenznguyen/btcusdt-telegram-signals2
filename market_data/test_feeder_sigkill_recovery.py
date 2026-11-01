"""Process-level SIGKILL recovery contract for the SQLite T0 feeder."""
import os
from pathlib import Path
import select
import signal
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from market_data.feeder import FeederConfig, LeaseStore
from market_data.feeder_service import build_runtime
from market_data.storage import SQLiteCandleStore
from market_data.store import Candle, CandleStore, INTERVAL_MS, read_window


NOW = 1_800_000_000_000
CLOCK_AFTER_TTL = NOW + 60_001
LOOKBACK = 4


def make_candle(timeframe, opened):
    interval = INTERVAL_MS[timeframe]
    return Candle(
        timeframe=timeframe,
        open_time_ms=opened,
        open="100",
        high="102",
        low="99",
        close="101",
        volume="5",
        available_at_ms=opened + interval + 100,
    )


def ohlcv_row(timeframe, opened):
    return [opened, 100, 102, 99, 101, 5]


class RecoveryExchange:
    """Deterministic Binance USD-M-shaped exchange; no network is used."""

    id = "binanceusdm"

    def __init__(self, rows):
        self.rows = rows
        self.market = {
            "symbol": "BTC/USDT:USDT",
            "id": "BTCUSDT",
            "base": "BTC",
            "quote": "USDT",
            "settle": "USDT",
            "active": True,
            "swap": True,
            "linear": True,
            "spot": False,
        }

    def load_markets(self):
        return {"BTC/USDT:USDT": self.market}

    def fetch_time(self):
        return CLOCK_AFTER_TTL + INTERVAL_MS["1h"]

    def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
        end_exclusive = params["endTime"] + 1
        interval = INTERVAL_MS[timeframe]
        matching = [
            self.rows[(timeframe, opened)]
            for frame, opened in sorted(self.rows, key=lambda item: (item[0], item[1]))
            if frame == timeframe and since <= opened < end_exclusive
        ]
        return matching[:limit]


class SigkillRecoveryTest(unittest.TestCase):
    def test_sigkill_rolls_back_batch_then_generation_two_recovers_m15_and_h1(self):
        audit_lines = ["T0_SIGKILL_RECOVERY_AUDIT=START"]

        def write_audit():
            audit_path = os.environ.get("T0_SIGKILL_AUDIT_PATH")
            if audit_path:
                target = Path(audit_path)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("\n".join(audit_lines + ["RESULT=PASS"]) + "\n")

        self.addCleanup(write_audit)
        with tempfile.TemporaryDirectory(prefix="t0-sigkill-") as directory:
            db_path = Path(directory) / "isolated-canonical.sqlite3"
            writer = CandleStore(db_path)
            leases = LeaseStore(str(db_path))

            # RecoveryAdapter will inspect exactly four closed candles per TF.
            windows = {}
            expected_rows = {}
            for timeframe in ("15m", "1h"):
                interval = INTERVAL_MS[timeframe]
                start, end = NOW - LOOKBACK * interval, NOW
                windows[timeframe] = (start, end)
                missing_indices = {1, 2} if timeframe == "15m" else {2}
                for index in range(LOOKBACK):
                    opened = start + index * interval
                    expected_rows[(timeframe, opened)] = ohlcv_row(timeframe, opened)
                    if index not in missing_indices:
                        writer.insert([make_candle(timeframe, opened)])

            # Process A owns generation 1 and dies after its first uncommitted row.
            lease_a = leases.acquire("process-A", now_ms=NOW, ttl_seconds=60)
            self.assertIsNotNone(lease_a)
            self.assertEqual(lease_a.generation, 1)

            m15_start, _ = windows["15m"]
            uncommitted_batch = [
                make_candle("15m", m15_start + INTERVAL_MS["15m"]),
                make_candle("15m", m15_start + 2 * INTERVAL_MS["15m"]),
            ]

            child_source = r'''
import os
import time
from market_data.store import Candle, CandleStore, INTERVAL_MS

path = os.environ["T0_SIGKILL_DB"]
now = int(os.environ["T0_SIGKILL_NOW"])
step = INTERVAL_MS["15m"]
start = now - 4 * step
batch = [
    Candle("15m", start + step, "100", "102", "99", "101", "5",
           start + 2 * step + 100),
    Candle("15m", start + 2 * step, "100", "102", "99", "101", "5",
           start + 3 * step + 100),
]
original = CandleStore._insert_batch

def insert_one_then_pause(connection, candles):
    inserted = original(connection, candles[:1])
    print("UNCOMMITTED_ROW_INSERTED", flush=True)
    while True:
        time.sleep(1)

CandleStore._insert_batch = staticmethod(insert_one_then_pause)
CandleStore(path).insert_fenced(
    batch,
    owner="process-A",
    generation=1,
    now_ms=lambda: now + 1,
)
'''
            env = dict(os.environ)
            env["T0_SIGKILL_DB"] = str(db_path)
            env["T0_SIGKILL_NOW"] = str(NOW)
            project_root = str(Path(__file__).resolve().parents[1])
            env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
            process = subprocess.Popen(
                [sys.executable, "-c", child_source],
                cwd=project_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            try:
                ready, _, _ = select.select([process.stdout], [], [], 10)
                self.assertTrue(ready, "Process A did not reach the uncommitted insert")
                self.assertEqual(process.stdout.readline().strip(), "UNCOMMITTED_ROW_INSERTED")
                os.kill(process.pid, signal.SIGKILL)
                process_status = process.wait(timeout=10)
                self.assertEqual(process_status, -signal.SIGKILL)
                audit_lines.append("PROCESS_A_EXIT=SIGKILL")
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=10)
                process.stdout.close()
                process.stderr.close()

            # Reopening the WAL database after a hard process death must be safe.
            with sqlite3.connect(db_path, timeout=5) as connection:
                integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
            self.assertEqual(integrity, "ok")
            audit_lines.append("SQLITE_QUICK_CHECK=ok")

            # Neither the inserted prefix nor the remaining row of A's batch survived.
            before_recovery = read_window(
                db_path, "BTCUSDT", "15m", *windows["15m"]
            )
            self.assertEqual(before_recovery["coverage"]["returned"], 2)
            self.assertEqual(
                {row["openTimeMs"] for row in before_recovery["candles"]},
                {
                    windows["15m"][0],
                    windows["15m"][0] + 3 * INTERVAL_MS["15m"],
                },
            )
            audit_lines.append("PROCESS_A_UNCOMMITTED_BATCH_ROWS=0")

            # Simulate the passage of the 60-second TTL without a wall-clock sleep.
            lease_b = leases.acquire(
                "process-B", now_ms=NOW + 60_000, ttl_seconds=60
            )
            self.assertIsNotNone(lease_b)
            self.assertEqual(lease_b.generation, 2)
            audit_lines.extend(["LEASE_A_GENERATION=1", "LEASE_B_GENERATION=2"])

            # A stale generation must remain unable to write after takeover.
            with self.assertRaises(PermissionError):
                writer.insert_fenced(
                    uncommitted_batch,
                    owner="process-A",
                    generation=lease_a.generation,
                    now_ms=lambda: CLOCK_AFTER_TTL,
                )

            store = SQLiteCandleStore(db_path)
            exchange = RecoveryExchange(expected_rows)
            config = FeederConfig(
                lease_ttl_seconds=60,
                lease_heartbeat_seconds=15,
                timeframes=("15m", "1h"),
            )
            runtime = build_runtime(
                config=config,
                owner_id="process-B",
                exchange=exchange,
                store=store,
                lease_store=leases,
                clock=lambda: CLOCK_AFTER_TTL,
                recovery_lookback_candles=LOOKBACK,
            )
            try:
                self.assertTrue(runtime.start())
                self.assertEqual(runtime.lease_generation, 2)
                self.assertEqual(runtime.state, "RUNNING")

                for timeframe in ("15m", "1h"):
                    start, end = windows[timeframe]
                    coverage = store.read_window("BTCUSDT", timeframe, start, end)
                    self.assertEqual(coverage["coverage"]["expected"], LOOKBACK)
                    self.assertEqual(coverage["coverage"]["returned"], LOOKBACK)
                    self.assertTrue(coverage["coverage"]["complete"])
                    self.assertEqual(coverage["coverage"]["gaps"], [])
                    audit_lines.append(
                        f"{timeframe.upper()}_COVERAGE={coverage['coverage']['returned']}/"
                        f"{coverage['coverage']['expected']}"
                    )

                lease_valid_after_recovery = leases.is_current(
                    "process-B", 2, now_ms=CLOCK_AFTER_TTL
                )
                self.assertTrue(lease_valid_after_recovery)
                audit_lines.append(
                    f"LEASE_GENERATION_2_VALID_AFTER_RECOVERY={lease_valid_after_recovery}"
                )
            finally:
                runtime.stop(timeout=5)

            # The only writes after takeover were made through RecoveryAdapter's
            # canonical sync_window -> insert_fenced path under generation 2.


if __name__ == "__main__":
    unittest.main()
