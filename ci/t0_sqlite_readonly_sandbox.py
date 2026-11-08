"""Disposable Linux proof for T0 SQLite WAL reads inside a systemd read-only sandbox.

This script never opens or modifies the canonical T0 database. It creates a
throwaway database under a temporary directory and uses transient systemd units.
"""
import os
import sqlite3
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from market_data.store import INTERVAL_MS, read_window

STEP = INTERVAL_MS["15m"]
REPOSITORY = Path.cwd().resolve()


def _run_readonly_service(database: Path, expected_rows: int, label: str) -> str:
    child = r"""
import os
import sqlite3
from pathlib import Path
from market_data.store import read_window

database = Path(os.environ["T0_SANDBOX_DB"])
expected = int(os.environ["T0_EXPECTED_ROWS"])
step = 900_000
result = read_window(database, "BTCUSDT", "15m", 0, 2 * step)
assert result["coverage"]["returned"] == expected, result["coverage"]

# The ordinary API read path must work with the whole data directory mounted
# read-only, even while the Feeder-equivalent writer holds a WAL transaction.
uri = database.resolve().as_uri() + "?mode=ro"
with sqlite3.connect(uri, uri=True, timeout=5) as reader:
    try:
        reader.execute("UPDATE candles SET close='999' WHERE open_time_ms=0")
    except sqlite3.OperationalError:
        pass
    else:
        raise AssertionError("mode=ro unexpectedly allowed UPDATE")

# The service identity owns the disposable files; the systemd mount sandbox,
# not Unix ownership, must deny writes from this process.
try:
    (database.parent / "must-not-be-created").write_text("forbidden")
except OSError:
    pass
else:
    raise AssertionError("ReadOnlyPaths allowed a filesystem write")

try:
    with sqlite3.connect(database, timeout=2) as writer:
        writer.execute("UPDATE candles SET close='999' WHERE open_time_ms=0")
except sqlite3.Error:
    pass
else:
    raise AssertionError("ordinary SQLite connection wrote through read-only sandbox")

print("T0_SYSTEMD_READONLY_WAL_READ=PASS")
print("T0_SYSTEMD_READONLY_FILESYSTEM_WRITE=DENIED")
print("T0_SYSTEMD_READONLY_SQLITE_WRITE=DENIED")
print("T0_EXPECTED_ROWS=" + str(expected))
"""
    command = [
        "sudo", "-n", "systemd-run", "--system", "--wait", "--pipe", "--collect",
        f"--unit=t0-sqlite-ro-{label}-{uuid.uuid4().hex[:8]}",
        f"--property=User={os.environ.get('USER', 'runner')}",
        f"--property=ReadOnlyPaths={database.parent}",
        "--property=NoNewPrivileges=yes",
        f"--property=WorkingDirectory={REPOSITORY}",
        f"--setenv=PYTHONPATH={REPOSITORY}",
        f"--setenv=T0_SANDBOX_DB={database}",
        f"--setenv=T0_EXPECTED_ROWS={expected_rows}",
        sys.executable, "-c", child,
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=45)
    output = completed.stdout + completed.stderr
    if completed.returncode:
        raise RuntimeError(
            f"systemd read-only sandbox failed ({label}, exit={completed.returncode}):\n{output}"
        )
    for marker in (
        "T0_SYSTEMD_READONLY_WAL_READ=PASS",
        "T0_SYSTEMD_READONLY_FILESYSTEM_WRITE=DENIED",
        "T0_SYSTEMD_READONLY_SQLITE_WRITE=DENIED",
        f"T0_EXPECTED_ROWS={expected_rows}",
    ):
        if marker not in output:
            raise AssertionError(f"Missing sandbox evidence {marker!r}:\n{output}")
    print(output, end="")
    return output


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="t0-sqlite-readonly-") as temporary:
        directory = Path(temporary)
        database = directory / "disposable.sqlite3"
        with sqlite3.connect(database) as setup:
            mode = setup.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower()
            assert mode == "wal", mode
            setup.execute(
                """CREATE TABLE candles (
                    exchange TEXT NOT NULL, market_type TEXT NOT NULL,
                    symbol TEXT NOT NULL, timeframe TEXT NOT NULL,
                    open_time_ms INTEGER NOT NULL, open TEXT NOT NULL,
                    high TEXT NOT NULL, low TEXT NOT NULL, close TEXT NOT NULL,
                    volume TEXT NOT NULL, available_at_ms INTEGER NOT NULL,
                    PRIMARY KEY(exchange, market_type, symbol, timeframe, open_time_ms)
                )"""
            )
            setup.execute(
                "INSERT INTO candles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("binance", "USDT_PERPETUAL", "BTCUSDT", "15m", 0,
                 "100", "102", "99", "101", "5", STEP + 100),
            )

        # Keep a writer connection and an uncommitted row alive so both WAL
        # and SHM files exist while the systemd sandbox attempts a read.
        writer = sqlite3.connect(database, timeout=5, isolation_level=None)
        try:
            writer.execute("PRAGMA journal_mode=WAL")
            writer.execute("BEGIN IMMEDIATE")
            writer.execute(
                "INSERT INTO candles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("binance", "USDT_PERPETUAL", "BTCUSDT", "15m", STEP,
                 "101", "103", "100", "102", "6", 2 * STEP + 100),
            )
            assert Path(str(database) + "-wal").is_file()
            assert Path(str(database) + "-shm").is_file()

            _run_readonly_service(database, 1, "uncommitted")
            writer.execute("COMMIT")
            _run_readonly_service(database, 2, "committed")

            # Prove the sandbox reader did not disrupt the writer's ability
            # to commit or alter the canonical logical dataset.
            after = read_window(database, "BTCUSDT", "15m", 0, 2 * STEP)
            assert after["coverage"]["returned"] == 2
            assert [row["close"] for row in after["candles"]] == ["101", "102"]
        finally:
            writer.close()

    print("T0_SYSTEMD_READONLY_WAL_SANDBOX=PASS")
    print("T0_DISPOSABLE_ONLY=PASS")


if __name__ == "__main__":
    main()
