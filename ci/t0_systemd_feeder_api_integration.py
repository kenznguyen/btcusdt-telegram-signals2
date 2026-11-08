#!/usr/bin/env python3
"""Disposable systemd integration test for the T0 Feeder and read-only Candle API.

This harness creates synthetic SQLite data and transient units on a CI runner only.
It never constructs a production Feeder composition or contacts an exchange.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from wsgiref.simple_server import make_server

from market_data.api import application
from market_data.feeder import FeederConfig, FeederRuntime, LeaseStore
from market_data.feeder_service import run_service
from market_data.store import CandleStore, INTERVAL_MS
from market_data.write_gateway import SQLiteWalKeeper


PORT = 18788
TOKEN = "ci-disposable-token-only"
TIMEFRAME = "15m"
OPEN_MS = 1_800_000_000_000 // INTERVAL_MS[TIMEFRAME] * INTERVAL_MS[TIMEFRAME]


def event(path, name):
    record = f"{time.monotonic_ns()} {name}\n".encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, record)
    finally:
        os.close(fd)


class DeterministicScheduler:
    def start(self):
        return True

    def run_due(self):
        return {}

    def stop(self):
        return True

    def wait_for_idle(self, timeout=None):
        return True


class StartupBarrier:
    def __init__(self, delay=3.0):
        self.delay = delay

    def recover_all(self):
        time.sleep(self.delay)
        return True


def seed_database(path):
    CandleStore(path)
    LeaseStore(str(path))
    with sqlite3.connect(path) as db:
        db.execute(
            """INSERT INTO candles (
                exchange, market_type, symbol, timeframe, open_time_ms,
                open, high, low, close, volume, available_at_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("binance", "USDT_PERPETUAL", "BTCUSDT", TIMEFRAME, OPEN_MS,
             "100.0", "101.0", "99.0", "100.5", "1.25",
             OPEN_MS + INTERVAL_MS[TIMEFRAME]),
        )
        db.commit()


def feeder_process(db_path, event_path):
    event(event_path, "FEEDER_PROCESS_STARTING")
    runtime = FeederRuntime(
        config=FeederConfig(
            poll_interval_seconds=1,
            lease_ttl_seconds=8,
            lease_heartbeat_seconds=2,
            timeframes=(TIMEFRAME,),
        ),
        scheduler=DeterministicScheduler(),
        lease_store=LeaseStore(db_path),
        owner_id=f"ci-systemd-{os.getpid()}",
        recovery=StartupBarrier(),
        wal_keeper=SQLiteWalKeeper(db_path),
    )
    stop_event = __import__("threading").Event()

    def request_stop(_signum, _frame):
        event(event_path, "FEEDER_SIGTERM")
        stop_event.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    result = run_service(runtime, stop_event=stop_event)
    event(event_path, f"FEEDER_EXIT_{result}")
    return result


def api_process(event_path):
    event(event_path, "API_PROCESS_STARTING")

    def request_stop(_signum, _frame):
        event(event_path, "API_SIGTERM")
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    with make_server("127.0.0.1", PORT, application) as server:
        event(event_path, "API_LISTENING")
        server.serve_forever()
    return 0


def run(command, check=True, capture=True):
    result = subprocess.run(
        command, check=False, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if check and result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def unit_state(unit):
    result = run(
        ["sudo", "systemctl", "show", "--property=ActiveState", "--value", unit],
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "not-found"


def wait_for(predicate, description, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.1)
    raise AssertionError(f"timed out waiting for {description}")


def start_feeder(script, unit, db_path, event_path, repo_root):
    run([
        "sudo", "systemd-run", "--quiet", "--no-block", f"--unit={unit}",
        "--property=Type=notify", "--property=NotifyAccess=all",
        "--property=TimeoutStartSec=15s", "--property=KillMode=control-group",
        f"--setenv=PYTHONPATH={repo_root}",
        sys.executable, script, "feeder", "--db", db_path, "--events", event_path,
    ])


def start_api(script, unit, feeder_unit, db_path, event_path, repo_root):
    run([
        "sudo", "systemd-run", "--quiet", "--no-block", f"--unit={unit}",
        "--property=Type=simple", f"--property=Requires={feeder_unit}.service",
        f"--property=After={feeder_unit}.service",
        f"--property=BindsTo={feeder_unit}.service",
        f"--property=ReadOnlyPaths={Path(db_path).parent}",
        "--property=KillMode=control-group",
        f"--setenv=PYTHONPATH={repo_root}",
        f"--setenv=MARKET_DATA_DB={db_path}",
        f"--setenv=MARKET_DATA_TOKEN={TOKEN}",
        sys.executable, script, "api", "--events", event_path,
    ])


def candle_request(token):
    query = (
        f"symbol=BTCUSDT&timeframe={TIMEFRAME}"
        f"&startMs={OPEN_MS}&endMs={OPEN_MS + INTERVAL_MS[TIMEFRAME]}"
    )
    request = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/v1/candles?{query}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def wait_api_ready():
    def ready():
        if unit_state("t0-int-api-a.service") != "active":
            return False
        try:
            status, body = candle_request(TOKEN)
            return status == 200 and len(body.get("candles", [])) == 1
        except (OSError, ValueError):
            return False
    wait_for(ready, "authenticated API candle read")


def assert_api_unavailable():
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=1)
    except (OSError, urllib.error.URLError):
        return
    raise AssertionError("API remained reachable after Feeder dependency loss")


def read_events(path):
    if not Path(path).exists():
        return []
    return [line.split() for line in Path(path).read_text().splitlines() if line.strip()]


def stop_units(*units):
    for unit in units:
        run(["sudo", "systemctl", "stop", unit], check=False)
        run(["sudo", "systemctl", "reset-failed", unit], check=False)


def integration(db_path, event_path):
    script = str(Path(__file__).resolve())
    repo_root = str(Path(__file__).resolve().parents[1])
    seed_database(db_path)

    # Pair A: readiness gating, authenticated read, then Feeder SIGKILL propagation.
    feeder_a, api_a = "t0-int-feeder-a", "t0-int-api-a"
    start_feeder(script, feeder_a, db_path, event_path, repo_root)
    wait_for(lambda: unit_state(f"{feeder_a}.service") == "activating",
             "Feeder startup barrier")
    start_api(script, api_a, feeder_a, db_path, event_path, repo_root)
    time.sleep(0.5)
    if unit_state(f"{api_a}.service") == "active":
        raise AssertionError("API became active before Feeder READY")
    wait_for(lambda: unit_state(f"{feeder_a}.service") == "active",
             "Feeder systemd READY")
    wait_for(lambda: unit_state(f"{api_a}.service") == "active",
             "dependent API activation")
    status, body = candle_request(TOKEN)
    assert status == 200 and len(body.get("candles", [])) == 1, (status, body)
    unauthenticated = candle_request("")
    assert unauthenticated[0] == 401, unauthenticated
    event(event_path, "API_AUTHENTICATED_CANDLE_READ_PASS")

    run(["sudo", "systemctl", "kill", "--signal=SIGKILL", f"{feeder_a}.service"])
    wait_for(lambda: unit_state(f"{api_a}.service") in ("inactive", "failed"),
             "BindsTo API stop after Feeder SIGKILL")
    wait_for(lambda: unit_state(f"{feeder_a}.service") in ("failed", "inactive"),
             "Feeder SIGKILL exit")
    assert_api_unavailable()
    event(event_path, "FEEDER_SIGKILL_PROPAGATION_PASS")
    stop_units(f"{api_a}.service", f"{feeder_a}.service")

    # Wait for the killed process's short disposable lease TTL to expire.
    time.sleep(9)

    # Pair B: fresh Feeder generation, API read, and reverse-order graceful shutdown.
    feeder_b, api_b = "t0-int-feeder-b", "t0-int-api-b"
    start_feeder(script, feeder_b, db_path, event_path, repo_root)
    wait_for(lambda: unit_state(f"{feeder_b}.service") == "active",
             "restarted Feeder READY")
    start_api(script, api_b, feeder_b, db_path, event_path, repo_root)
    wait_for(lambda: unit_state(f"{api_b}.service") == "active",
             "restarted dependent API")
    status, body = candle_request(TOKEN)
    assert status == 200 and len(body.get("candles", [])) == 1, (status, body)
    event(event_path, "FEEDER_API_RESTART_READ_PASS")

    run(["sudo", "systemctl", "stop", f"{feeder_b}.service"])
    wait_for(lambda: unit_state(f"{api_b}.service") in ("inactive", "failed"),
             "API shutdown before Feeder drain")
    wait_for(lambda: unit_state(f"{feeder_b}.service") in ("inactive", "failed"),
             "orderly Feeder shutdown")

    records = read_events(event_path)
    api_stop = [int(row[0]) for row in records if row[1] == "API_SIGTERM"]
    feeder_stop = [int(row[0]) for row in records if row[1] == "FEEDER_SIGTERM"]
    assert api_stop and feeder_stop and api_stop[-1] < feeder_stop[-1], records
    event(event_path, "ORDERLY_REVERSE_SHUTDOWN_PASS")
    event(event_path, "T0_SYSTEMD_FEEDER_API_INTEGRATION=PASS")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("feeder", "api", "integration"):
        child = sub.add_parser(mode)
        child.add_argument("--events", required=True)
        if mode in ("feeder", "integration"):
            child.add_argument("--db", required=True)
    args = parser.parse_args()

    if args.mode == "feeder":
        return feeder_process(args.db, args.events)
    if args.mode == "api":
        return api_process(args.events)
    if args.mode == "integration":
        integration(args.db, args.events)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
