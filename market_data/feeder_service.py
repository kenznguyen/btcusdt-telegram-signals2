"""Production composition and process entrypoint for the canonical T0 feeder.

Run with: python -m market_data.feeder_service
This process only ingests closed BTCUSDT USD-M candles; it never places orders.
"""
import os
import signal
from pathlib import Path
import secrets
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
from market_data.storage import PostgresStore, create_store_from_env
from market_data.postgres import PostgresLeaseStore, PostgresWriteGateway
from market_data.sync import sync_window
from market_data.store import INTERVAL_MS
from market_data.write_gateway import SQLiteWriteGateway


POSTGRES_CANONICAL_LEASE_NAME = "binance-btcusdt-canonical"


class PostgresRuntimeLeaseAdapter:
    """Adapt DB-clock PostgreSQL leases to FeederRuntime's legacy clock API."""

    def __init__(self, backend):
        required = ("acquire", "heartbeat", "is_current", "release")
        if any(not callable(getattr(backend, name, None)) for name in required):
            raise TypeError("backend must provide PostgreSQL lease operations")
        self.backend = backend

    def acquire(self, owner, now_ms=None, ttl_seconds=60):
        return self.backend.acquire(owner, ttl_seconds=ttl_seconds)

    def heartbeat(self, owner, generation, now_ms=None, ttl_seconds=60):
        return self.backend.heartbeat(owner, generation, ttl_seconds=ttl_seconds)

    def is_current(self, owner, generation, now_ms=None):
        return self.backend.is_current(owner, generation)

    def authorize_write(self, owner, generation, now_ms=None):
        return self.backend.is_current(owner, generation)

    def release(self, owner, generation):
        return self.backend.release(owner, generation)


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

    # Select one atomic writer/lease authority pair. PostgreSQL must use one
    # DSN for candles, leases and the transactionally fenced write gateway.
    if isinstance(store, PostgresStore):
        if not isinstance(lease_store, PostgresLeaseStore):
            raise ValueError("PostgreSQL store and lease must both use PostgreSQL")
        if store.dsn != lease_store.location:
            raise ValueError("PostgreSQL candle store and feeder lease must share the same DSN")
        initialize_store = getattr(store, "initialize", None)
        if callable(initialize_store):
            initialize_store()
        runtime = None
        runtime_lease_store = PostgresRuntimeLeaseAdapter(lease_store)
        write_gateway = PostgresWriteGateway(
            store.dsn,
            lease_name=lease_store.lease_name,
            owner_id=owner_id,
            generation_provider=lambda: runtime.lease_generation,
        )
    else:
        # Preserve the existing SQLite path and its same-database invariant.
        store_path = getattr(store, "path", None)
        lease_path = getattr(lease_store, "db_path", None)
        if store_path is None or lease_path is None:
            raise ValueError("Feeder requires a same-database SQLite store and lease")
        if Path(store_path).resolve() != Path(lease_path).resolve():
            raise ValueError("Candle store and feeder lease must share the same SQLite database")
        # Runtime composition must never provision canonical storage.
        # The SQLite database and schema must already exist before startup.
        runtime = None
        runtime_lease_store = lease_store
        write_gateway = SQLiteWriteGateway(
            store=store,
            lease_store=lease_store,
            owner_id=owner_id,
            generation_provider=lambda: runtime.lease_generation,
            clock=clock_fn,
        )

    def canonical_sync(timeframe, start_ms, end_ms):
        return sync_window(exchange, write_gateway, timeframe, start_ms, end_ms, now_ms=clock_fn)

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
        lease_store=runtime_lease_store,
        owner_id=owner_id,
        recovery=recovery,
        health=health,
        event_sink=event_sink,
        clock=clock_fn,
        retry_policy=retry,
    )
    runtime.canonical_write_gateway = write_gateway

    # Startup recovery is also a canonical writer. Refresh the lease before
    # recovery; every resulting page is independently fenced inside the same
    # SQLite transaction that commits its candles.
    def guarded_recovery_sync(timeframe, start_ms, end_ms):
        def attempt():
            generation = runtime.lease_generation
            heartbeat = getattr(runtime_lease_store, "heartbeat", None)
            try:
                lease_current = (
                    generation is not None
                    and callable(heartbeat)
                    and heartbeat(
                        owner_id,
                        generation,
                        now_ms=clock_fn(),
                        ttl_seconds=config.lease_ttl_seconds,
                    ) is True
                )
            except Exception:
                lease_current = False
            if not lease_current:
                # A failed renewal is authoritative lease loss. Stop admission
                # immediately; the startup exception path drains before it
                # attempts an exact owner/generation release.
                runtime.on_lease_lost()
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
    if backend == "postgres":
        if values.get("T0_FEEDER_LEASE_DB", "").strip():
            raise ValueError("T0_FEEDER_LEASE_DB is not allowed with PostgreSQL backend")
        requested_lease_name = values.get(
            "T0_FEEDER_LEASE_NAME", POSTGRES_CANONICAL_LEASE_NAME
        ).strip()
        if requested_lease_name != POSTGRES_CANONICAL_LEASE_NAME:
            raise ValueError(
                "PostgreSQL canonical candles require the fixed canonical lease identity"
            )
        lease_store = PostgresLeaseStore(
            store.dsn, lease_name=POSTGRES_CANONICAL_LEASE_NAME
        )
    else:
        lease_path = values.get("T0_FEEDER_LEASE_DB", "").strip()
        if not lease_path:
            if backend != "sqlite" or not values.get("MARKET_DATA_DB", "").strip():
                raise ValueError(
                    "T0_FEEDER_LEASE_DB is required unless SQLite MARKET_DATA_DB is configured"
                )
            lease_path = values["MARKET_DATA_DB"]
        lease_store = LeaseStore(lease_path)
    # The owner ID is an opaque fencing capability. Generate a fresh,
    # high-entropy value per process unless an operator supplies a secret.
    owner_id = values.get("T0_FEEDER_OWNER_ID", "").strip()
    if not owner_id:
        owner_id = secrets.token_urlsafe(32)

    config = FeederConfig(
        poll_interval_seconds=int(values.get("T0_FEEDER_POLL_SECONDS", "5")),
        close_grace_seconds=int(values.get("T0_FEEDER_CLOSE_GRACE_SECONDS", "5")),
        retry_max_attempts=int(values.get("T0_FEEDER_RETRY_ATTEMPTS", "5")),
        lease_ttl_seconds=int(values.get("T0_FEEDER_LEASE_TTL_SECONDS", "60")),
        lease_heartbeat_seconds=int(values.get("T0_FEEDER_LEASE_HEARTBEAT_SECONDS", "15")),
        timeframes=("15m", "1h"),
    )
    exchange = ccxt.binanceusdm({"enableRateLimit": True, "timeout": 15_000})
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
