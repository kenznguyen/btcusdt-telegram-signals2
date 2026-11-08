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

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))

from market_data.feeder import LeaseStore
from market_data.store import Candle, CandleStore, INTERVAL_MS, read_window
from market_data.write_gateway import SQLiteWriteGateway

STEP = INTERVAL_MS["15m"]


def _run_readonly_service(database: Path, expected_rows: int, label: str, expect_success: bool = True) -> str:
    child = r"""
import os
import sqlite3
from pathlib import Path
from market_data.store import read_window

database = Path(os.environ["T0_SANDBOX_DB"])
expected = int(os.environ["T0_EXPECTED_ROWS"])
step = 900_000
result = read_window(database, "BTCUSDT", "15m", 0, 3 * step)
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
    if expect_success and completed.returncode:
        raise RuntimeError(
            f"systemd read-only sandbox failed ({label}, exit={completed.returncode}):\n{output}"
        )
    if not expect_success:
        if completed.returncode == 0:
            raise AssertionError(
                f"read-only service unexpectedly opened without WAL/SHM ({label}):\n{output}"
            )
        print(f"T0_COLD_START_WITHOUT_WAL_SHM=BLOCKED_AS_EXPECTED ({label})")
        return output
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
        setup.close()

        # A cleanly closed WAL database can have no -wal/-shm sidecars.
        # Prove the sandboxed read-only service fails closed in this state.
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(database) + suffix)
            if sidecar.exists():
                sidecar.unlink()
        assert not Path(str(database) + "-wal").exists()
        assert not Path(str(database) + "-shm").exists()
        _run_readonly_service(database, 1, "cold-no-sidecars", expect_success=False)

        # Feeder startup must open the writer and establish the WAL/SHM
        # lifecycle before the API service is allowed to start.
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
            _run_readonly_service(database, 1, "writer-ready")

            _run_readonly_service(database, 1, "uncommitted")
            writer.execute("COMMIT")
            _run_readonly_service(database, 2, "committed")

            # Prove the sandbox reader did not disrupt the writer's ability
            # to commit or alter the canonical logical dataset.
            after = read_window(database, "BTCUSDT", "15m", 0, 2 * STEP)
            assert after["coverage"]["returned"] == 2
            assert [row["close"] for row in after["candles"]] == ["101", "102"]
            checkpoint = writer.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            assert checkpoint[0] == 0, checkpoint
        finally:
            writer.close()

        # Model an orderly Feeder shutdown/checkpoint. The WAL/SHM files are
        # absent again, so an API restart must remain blocked until writer
        # startup re-establishes the sidecars.
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(database) + suffix)
            if sidecar.exists():
                sidecar.unlink()
        assert not Path(str(database) + "-wal").exists()
        assert not Path(str(database) + "-shm").exists()
        _run_readonly_service(database, 2, "restart-after-clean-checkpoint", expect_success=False)

        # Restart the writer and perform a committed write to recreate sidecars.
        restarted_writer = sqlite3.connect(database, timeout=5, isolation_level=None)
        try:
            restarted_writer.execute("PRAGMA journal_mode=WAL")
            restarted_writer.execute("BEGIN IMMEDIATE")
            restarted_writer.execute(
                "INSERT INTO candles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("binance", "USDT_PERPETUAL", "BTCUSDT", "15m", 2 * STEP,
                 "102", "104", "101", "103", "7", 3 * STEP + 100),
            )
            restarted_writer.execute("COMMIT")
            assert Path(str(database) + "-wal").is_file()
            assert Path(str(database) + "-shm").is_file()
            _run_readonly_service(database, 3, "api-restart-after-writer-ready")
        finally:
            restarted_writer.close()

    # Model the actual production SQLiteWriteGateway lifecycle. Unlike the
    # persistent writer above, write_batch opens and closes its own connection.
    with tempfile.TemporaryDirectory(prefix="t0-real-feeder-writer-") as temporary:
        gateway_db = Path(temporary) / "canonical.sqlite3"
        store = CandleStore(gateway_db)
        leases = LeaseStore(str(gateway_db))
        lease = leases.acquire("feeder-probe", 1_800_000_000_000, 60)
        assert lease is not None
        gateway = SQLiteWriteGateway(
            store=store,
            lease_store=leases,
            owner_id="feeder-probe",
            generation_provider=lambda: lease.generation,
            clock=lambda: 1_800_000_000_001,
        )
        gateway.write_batch([Candle(
            timeframe="15m",
            open_time_ms=0,
            open="100", high="102", low="99", close="101",
            volume="5", available_at_ms=900_000,
        )])
        wal_exists = Path(str(gateway_db) + "-wal").is_file()
        shm_exists = Path(str(gateway_db) + "-shm").is_file()
        print(f"T0_ACTUAL_WRITE_GATEWAY_WAL_EXISTS={wal_exists}")
        print(f"T0_ACTUAL_WRITE_GATEWAY_SHM_EXISTS={shm_exists}")
        _run_readonly_service(
            gateway_db, 1, "actual-write-gateway-after-close",
            expect_success=wal_exists and shm_exists,
        )
        # Lease heartbeat is another short-lived writer connection in the
        # current Feeder implementation. Check the sidecar lifecycle again.
        leases.heartbeat(
            "feeder-probe", lease.generation,
            now_ms=1_800_000_000_002, ttl_seconds=60,
        )
        wal_after_heartbeat = Path(str(gateway_db) + "-wal").is_file()
        shm_after_heartbeat = Path(str(gateway_db) + "-shm").is_file()
        print(f"T0_ACTUAL_FEEDER_HEARTBEAT_WAL_EXISTS={wal_after_heartbeat}")
        print(f"T0_ACTUAL_FEEDER_HEARTBEAT_SHM_EXISTS={shm_after_heartbeat}")
        _run_readonly_service(
            gateway_db, 1, "actual-feeder-after-heartbeat",
            expect_success=wal_after_heartbeat and shm_after_heartbeat,
        )

        # Evaluate a candidate persistent WAL-keeper connection owned by the
        # Feeder process. It must keep the WAL/SHM sidecars available between
        # short-lived write_batch()/lease-heartbeat connections.
        keeper = sqlite3.connect(gateway_db, timeout=5, isolation_level=None)
        try:
            keeper.execute("PRAGMA journal_mode=WAL")
            keeper.execute("SELECT COUNT(*) FROM candles").fetchone()
            wal_keeper = Path(str(gateway_db) + "-wal").is_file()
            shm_keeper = Path(str(gateway_db) + "-shm").is_file()
            print(f"T0_WAL_KEEPER_WAL_EXISTS={wal_keeper}")
            print(f"T0_WAL_KEEPER_SHM_EXISTS={shm_keeper}")
            assert wal_keeper and shm_keeper, "persistent keeper did not establish WAL/SHM sidecars"
            _run_readonly_service(
                gateway_db, 1, "actual-feeder-with-persistent-wal-keeper",
                expect_success=True,
            )
        finally:
            keeper.close()

    print("T0_SYSTEMD_READONLY_WAL_COLD_START_GUARD=PASS")
    print("T0_SYSTEMD_READONLY_WAL_SANDBOX=PASS")
    print("T0_ACTUAL_WRITE_GATEWAY_LIFECYCLE=TESTED")
    print("T0_DISPOSABLE_ONLY=PASS")


if __name__ == "__main__":
    main()
