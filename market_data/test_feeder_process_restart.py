"""Process-level T0 restart acceptance using an isolated temporary SQLite database.

A child process commits one fenced candle, opens a second write transaction,
then receives SIGKILL before commit. The parent verifies SQLite rollback,
persistent committed data, lease-generation takeover, stale-writer rejection,
and successful idempotent recovery.
"""
import json
import os
from pathlib import Path
import selectors
import signal
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import unittest

from market_data.feeder import LeaseStore
from market_data.store import (
    Candle,
    CandleStore,
    EXCHANGE,
    INTERVAL_MS,
    MARKET_TYPE,
    read_window,
)
from market_data.write_gateway import SQLiteWriteGateway

NOW = 1_800_000_000_000
STEP = INTERVAL_MS["15m"]
OPEN_TIME = NOW - (NOW % STEP)

CRASH_WORKER = textwrap.dedent('''
    import json
    import sqlite3
    import sys
    import time

    from market_data.feeder import LeaseStore
    from market_data.store import Candle, CandleStore, EXCHANGE, INTERVAL_MS, MARKET_TYPE
    from market_data.write_gateway import SQLiteWriteGateway

    db_path, open_time, now_ms = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    step = INTERVAL_MS["15m"]
    CandleStore(db_path)
    leases = LeaseStore(db_path)
    lease = leases.acquire("crashed-worker", now_ms=now_ms, ttl_seconds=60)
    if lease is None:
        raise RuntimeError("test worker failed to acquire its isolated lease")

    gateway = SQLiteWriteGateway(
        store=CandleStore(db_path),
        lease_store=leases,
        owner_id="crashed-worker",
        generation_provider=lambda: lease.generation,
        clock=lambda: now_ms + 1,
    )
    committed = Candle(
        "15m", open_time, "100", "101", "99", "100.5", "1",
        open_time + step,
    )
    if gateway.write_batch([committed]) != 1:
        raise RuntimeError("first candle was not committed")

    uncommitted_time = open_time + step
    connection = sqlite3.connect(db_path, timeout=5, isolation_level=None)
    connection.execute("PRAGMA busy_timeout=5000")
    connection.execute("BEGIN IMMEDIATE")
    connection.execute(
        """INSERT INTO candles
           (exchange, market_type, symbol, timeframe, open_time_ms,
            open, high, low, close, volume, available_at_ms)
           VALUES (?, ?, 'BTCUSDT', '15m', ?, '100', '101', '99',
                   '100.5', '1', ?)""",
        (EXCHANGE, MARKET_TYPE, uncommitted_time, uncommitted_time + step),
    )
    print(json.dumps({
        "owner": lease.owner,
        "generation": lease.generation,
        "committed_rows": 1,
        "uncommitted_rows": 1,
    }), flush=True)
    time.sleep(120)
''').strip()


def candle(open_time_ms):
    return Candle(
        "15m", open_time_ms, "100", "101", "99", "100.5", "1",
        open_time_ms + STEP,
    )


class FeederProcessRestartTest(unittest.TestCase):
    def test_sigkill_rolls_back_open_transaction_and_restart_fences_old_generation(self):
        with tempfile.TemporaryDirectory(prefix="t0-process-restart-") as directory:
            db_path = str(Path(directory) / "isolated-restart.sqlite3")
            CandleStore(db_path)
            process_env = os.environ.copy()
            for name in (
                "MARKET_DATA_DB", "MARKET_DATA_POSTGRES_DSN",
                "T0_FEEDER_LEASE_DB", "PAPER_DB",
                "BINANCE_API_KEY", "BINANCE_API_SECRET",
                "OKX_API_KEY", "OKX_API_SECRET",
            ):
                process_env.pop(name, None)
            repo_root = str(Path(__file__).resolve().parents[1])
            existing_pythonpath = process_env.get("PYTHONPATH", "")
            process_env["PYTHONPATH"] = os.pathsep.join(
                value for value in (repo_root, existing_pythonpath) if value
            )

            process = subprocess.Popen(
                [
                    sys.executable, "-c", CRASH_WORKER,
                    db_path, str(OPEN_TIME), str(NOW),
                ],
                cwd=repo_root,
                env=process_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ)
                    ready = selector.select(timeout=10)
                self.assertTrue(ready, "child process did not reach its uncommitted transaction")
                line = process.stdout.readline()
                if not line:
                    stderr = process.stderr.read()
                    self.fail(f"child process exited before crash barrier: {stderr}")
                crash_state = json.loads(line)
                self.assertEqual(crash_state["owner"], "crashed-worker")
                self.assertEqual(crash_state["generation"], 1)
                self.assertEqual(crash_state["committed_rows"], 1)
                self.assertEqual(crash_state["uncommitted_rows"], 1)

                process.kill()
                return_code = process.wait(timeout=5)
                self.assertEqual(return_code, -signal.SIGKILL)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)

            before_restart = read_window(
                db_path, "BTCUSDT", "15m", OPEN_TIME, OPEN_TIME + 2 * STEP
            )
            self.assertEqual(before_restart["coverage"]["returned"], 1)
            self.assertEqual(before_restart["coverage"]["gaps"], [{
                "startMs": OPEN_TIME + STEP,
                "endMs": OPEN_TIME + 2 * STEP,
            }])

            leases = LeaseStore(db_path)
            replacement = leases.acquire(
                "restarted-worker", now_ms=NOW + 60_001, ttl_seconds=60
            )
            self.assertIsNotNone(replacement)
            self.assertEqual(replacement.generation, crash_state["generation"] + 1)
            self.assertFalse(leases.release("crashed-worker", crash_state["generation"]))

            stale_gateway = SQLiteWriteGateway(
                store=CandleStore(db_path),
                lease_store=leases,
                owner_id="crashed-worker",
                generation_provider=lambda: crash_state["generation"],
                clock=lambda: NOW + 60_002,
            )
            with self.assertRaisesRegex(PermissionError, "lease is not current"):
                stale_gateway.write_batch([candle(OPEN_TIME + STEP)])

            restarted_gateway = SQLiteWriteGateway(
                store=CandleStore(db_path),
                lease_store=leases,
                owner_id="restarted-worker",
                generation_provider=lambda: replacement.generation,
                clock=lambda: NOW + 60_002,
            )
            self.assertEqual(
                restarted_gateway.write_batch([candle(OPEN_TIME + STEP)]), 1
            )
            self.assertEqual(
                restarted_gateway.write_batch([candle(OPEN_TIME + STEP)]), 0
            )

            after_restart = read_window(
                db_path, "BTCUSDT", "15m", OPEN_TIME, OPEN_TIME + 2 * STEP
            )
            self.assertEqual(after_restart["coverage"]["returned"], 2)
            self.assertTrue(after_restart["coverage"]["complete"])
            self.assertEqual(after_restart["coverage"]["gaps"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
