"""Production composition and process entrypoint for the canonical T0 feeder.

Run with: python -m market_data.feeder_service
This process only ingests closed BTCUSDT USD-M candles; it never places orders.
"""
import os
import signal
import socket
import threading
import time

from market_data.feeder import (
    FeederConfig,
    FeederRuntime,
    FeederScheduler,
    LeaseStore,
    RecoveryCoordinator,
    RetryPolicy,
)
from market_data.storage import create_store_from_env
from market_data.sync import sync_window
from market_data.store import INTERVAL_MS


class RecoveryAdapter:
    """Adapt per-timeframe RecoveryCoordinator contracts to FeederRuntime.recover_all()."""

    def __init__(self, coordinators, clock=None, lookback_candles=2000,
                 close_grace_seconds=5):
        if not isinstance(coordinators, dict) or not coordinators:
            raise ValueError("coordinators must be a non-empty timeframe mapping")
        if any(frame not in INTERVAL_MS for frame in coordinators):
            raise ValueError("unsupported recovery timeframe")
        if not callable(clock) and clock is not None:
            raise TypeError("clock must be callable")
        if type(lookback_candles) is not int or not 1 <= lookback_candles <= 2000:
            raise ValueError("lookback_candles must be between 1 and 2000")
        if type(close_grace_seconds) is not int or close_grace_seconds < 0:
            raise ValueError("close_grace_seconds must be nonnegative")
        self.coordinators = dict(coordinators)
        self.clock = clock if clock is not None else (lambda: time.time_ns() // 1_000_000)
        self.lookback_candles = lookback_candles
        self.close_grace_seconds = close_grace_seconds

    def recover_all(self):
        now_ms = self.clock()
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("recovery clock must return nonnegative epoch milliseconds")
        eligible = now_ms - self.close_grace_seconds * 1000
        for timeframe, coordinator in self.coordinators.items():
            interval = INTERVAL_MS[timeframe]
            end_ms = eligible - (eligible % interval)
            start_ms = max(0, end_ms - self.lookback_candles * interval)
            result = coordinator.recover(timeframe, start_ms, end_ms)
            if getattr(result, "complete", None) is not True:
                return False
        return True


def build_runtime(*, config, owner_id, exchange, store, lease_store, clock=None,
                  health=None, event_sink=None, recovery_lookback_candles=2000):
    """Compose the existing canonical sync path into the tested FeederRuntime."""
    if not isinstance(config, FeederConfig):
        raise TypeError("config must be FeederConfig")
    if not callable(clock) and clock is not None:
        raise TypeError("clock must be callable")
    clock_fn = clock if clock is not None else (lambda: time.time_ns() // 1_000_000)

    # Initialize the existing selected store without changing schema or backend.
    store.insert([])

    def canonical_sync(timeframe, start_ms, end_ms):
        return sync_window(exchange, store, timeframe, start_ms, end_ms, now_ms=clock_fn)

    retry = RetryPolicy(
        max_attempts=config.retry_max_attempts,
        base_delay_seconds=config.retry_base_delay_seconds,
        max_delay_seconds=config.retry_max_delay_seconds,
        jitter_ratio=config.retry_jitter_ratio,
    )
    coordinators = {}
    for timeframe in config.timeframes:
        coordinators[timeframe] = RecoveryCoordinator(
            sync_callback=lambda frame, start, end: retry.execute(
                lambda: canonical_sync(frame, start, end)
            ),
            coverage_reader=lambda frame, start, end: store.read_window(
                "BTCUSDT", frame, start, end
            ),
        )
    recovery = RecoveryAdapter(
        coordinators=coordinators,
        clock=clock_fn,
        lookback_candles=recovery_lookback_candles,
        close_grace_seconds=config.close_grace_seconds,
    )
    scheduler = FeederScheduler(
        config=config,
        clock=clock_fn,
        sync_callback=canonical_sync,
    )
    runtime = FeederRuntime(
        config=config,
        scheduler=scheduler,
        lease_store=lease_store,
        owner_id=owner_id,
        recovery=recovery,
        health=health,
        event_sink=event_sink,
        clock=clock_fn,
        retry_policy=retry,
    )

    # Startup recovery is also a canonical writer. Refresh and verify the
    # runtime's lease before every recovery attempt; atomic write fencing is a
    # separate storage-layer change and is intentionally not implied here.
    def guarded_recovery_sync(timeframe, start_ms, end_ms):
        def attempt():
            generation = runtime.lease_generation
            heartbeat = getattr(lease_store, "heartbeat", None)
            if (generation is None or not callable(heartbeat)
                    or heartbeat(
                        owner_id,
                        generation,
                        now_ms=clock_fn(),
                        ttl_seconds=config.lease_ttl_seconds,
                    ) is not True):
                raise PermissionError("Recovery blocked: feeder lease is not current")
            return canonical_sync(timeframe, start_ms, end_ms)
        return retry.execute(attempt)

    for coordinator in coordinators.values():
        coordinator.sync_callback = guarded_recovery_sync
    return runtime


def build_production_runtime(environ=None):
    """Build concrete Binance USD-M + selected canonical store + SQLite lease."""
    values = os.environ if environ is None else environ
    try:
        import ccxt
    except ImportError as exc:
        raise RuntimeError("Install requirements-market-data.txt to run the T0 feeder") from exc

    backend = values.get("MARKET_DATA_BACKEND", "sqlite").strip().lower()
    store = create_store_from_env(values)
    lease_path = values.get("T0_FEEDER_LEASE_DB", "").strip()
    if not lease_path:
        if backend != "sqlite" or not values.get("MARKET_DATA_DB", "").strip():
            raise ValueError(
                "T0_FEEDER_LEASE_DB is required unless SQLite MARKET_DATA_DB is configured"
            )
        lease_path = values["MARKET_DATA_DB"]
    owner_id = values.get("T0_FEEDER_OWNER_ID", "").strip()
    if not owner_id:
        owner_id = f"{socket.gethostname()}:{os.getpid()}"

    config = FeederConfig(
        poll_interval_seconds=int(values.get("T0_FEEDER_POLL_SECONDS", "5")),
        close_grace_seconds=int(values.get("T0_FEEDER_CLOSE_GRACE_SECONDS", "5")),
        retry_max_attempts=int(values.get("T0_FEEDER_RETRY_ATTEMPTS", "5")),
        lease_ttl_seconds=int(values.get("T0_FEEDER_LEASE_TTL_SECONDS", "60")),
        lease_heartbeat_seconds=int(values.get("T0_FEEDER_LEASE_HEARTBEAT_SECONDS", "15")),
        timeframes=("15m", "1h"),
    )
    exchange = ccxt.binanceusdm({"enableRateLimit": True, "timeout": 15_000})
    lease_store = LeaseStore(lease_path)
    return build_runtime(
        config=config,
        owner_id=owner_id,
        exchange=exchange,
        store=store,
        lease_store=lease_store,
        recovery_lookback_candles=int(values.get("T0_FEEDER_RECOVERY_CANDLES", "2000")),
    )


def run_service(runtime, stop_event=None):
    """Start once, block until SIGINT/SIGTERM, and always perform graceful drain."""
    requested_stop = stop_event if stop_event is not None else threading.Event()
    if runtime.start() is not True:
        return 2
    try:
        while not requested_stop.wait(1):
            if runtime.state in ("LEASE_LOST", "FAILED"):
                return 3
    finally:
        runtime.stop(timeout=30)
    return 0


def main():
    runtime = build_production_runtime()
    stop_event = threading.Event()
    previous_handlers = {}

    def request_stop(_signum, _frame):
        stop_event.set()

    for signum in (signal.SIGINT, signal.SIGTERM):
        previous_handlers[signum] = signal.signal(signum, request_stop)
    try:
        return run_service(runtime, stop_event=stop_event)
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)


if __name__ == "__main__":
    raise SystemExit(main())
