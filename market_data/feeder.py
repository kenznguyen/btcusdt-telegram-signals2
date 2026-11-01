"""Centralized T0 feeder scheduling and retry primitives.

The scheduler never fetches exchange data or writes candles itself. Its injected
callback is the only hand-off to the existing sync_window() ingestion path.
"""
from dataclasses import dataclass
import math
import random
import sqlite3
import threading
import time

from market_data.store import INTERVAL_MS, MAX_CANDLES


@dataclass(frozen=True)
class FeederConfig:
    poll_interval_seconds: int = 5
    close_grace_seconds: int = 5
    retry_max_attempts: int = 5
    retry_base_delay_seconds: float = 1.0
    retry_max_delay_seconds: float = 300.0
    retry_jitter_ratio: float = 0.2
    lease_ttl_seconds: int = 60
    lease_heartbeat_seconds: int = 15
    timeframes: tuple = ("15m", "1h")

    def __post_init__(self):
        if type(self.poll_interval_seconds) is not int or self.poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be a positive integer")
        if type(self.close_grace_seconds) is not int or self.close_grace_seconds < 0:
            raise ValueError("close_grace_seconds must be a nonnegative integer")
        if type(self.retry_max_attempts) is not int or self.retry_max_attempts < 1:
            raise ValueError("retry_max_attempts must be a positive integer")
        if (not isinstance(self.retry_base_delay_seconds, (int, float))
                or not math.isfinite(self.retry_base_delay_seconds)
                or self.retry_base_delay_seconds <= 0):
            raise ValueError("retry_base_delay_seconds must be positive and finite")
        if (not isinstance(self.retry_max_delay_seconds, (int, float))
                or not math.isfinite(self.retry_max_delay_seconds)
                or self.retry_max_delay_seconds < self.retry_base_delay_seconds):
            raise ValueError("retry_max_delay_seconds must be finite and at least the base delay")
        if (not isinstance(self.retry_jitter_ratio, (int, float))
                or not math.isfinite(self.retry_jitter_ratio)
                or not 0 <= self.retry_jitter_ratio <= 1):
            raise ValueError("retry_jitter_ratio must be between zero and one")
        if type(self.lease_ttl_seconds) is not int or self.lease_ttl_seconds <= 0:
            raise ValueError("lease_ttl_seconds must be a positive integer")
        if type(self.lease_heartbeat_seconds) is not int or not 0 < self.lease_heartbeat_seconds < self.lease_ttl_seconds:
            raise ValueError("lease_heartbeat_seconds must be positive and less than lease TTL")
        if (not isinstance(self.timeframes, tuple) or not self.timeframes
                or len(set(self.timeframes)) != len(self.timeframes)
                or any(frame not in INTERVAL_MS for frame in self.timeframes)):
            raise ValueError("timeframes must be a unique tuple of supported intervals")


class RetryPolicy:
    """Retry transient transport/rate-limit failures with bounded exponential delay."""

    def __init__(self, max_attempts=5, base_delay_seconds=1.0,
                 max_delay_seconds=300.0, jitter_ratio=0.2,
                 random_fn=None, sleep=None):
        if type(max_attempts) is not int or max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer")
        if (not isinstance(base_delay_seconds, (int, float))
                or not math.isfinite(base_delay_seconds) or base_delay_seconds <= 0):
            raise ValueError("base_delay_seconds must be positive and finite")
        if (not isinstance(max_delay_seconds, (int, float))
                or not math.isfinite(max_delay_seconds)
                or max_delay_seconds < base_delay_seconds):
            raise ValueError("max_delay_seconds must be finite and at least the base delay")
        if (not isinstance(jitter_ratio, (int, float))
                or not math.isfinite(jitter_ratio) or not 0 <= jitter_ratio <= 1):
            raise ValueError("jitter_ratio must be between zero and one")
        self.max_attempts = max_attempts
        self.base_delay_seconds = float(base_delay_seconds)
        self.max_delay_seconds = float(max_delay_seconds)
        self.jitter_ratio = float(jitter_ratio)
        self.random_fn = random_fn if random_fn is not None else random.random
        self.sleep = sleep if sleep is not None else time.sleep
        if not callable(self.random_fn) or not callable(self.sleep):
            raise TypeError("random_fn and sleep must be callable")

    @staticmethod
    def _retry_after(error):
        value = getattr(error, "retry_after_seconds", None)
        if value is None:
            value = getattr(error, "retry_after", None)
        if value is None:
            headers = getattr(error, "headers", None)
            if isinstance(headers, dict):
                value = headers.get("Retry-After", headers.get("retry-after"))
        if value is None:
            return None
        if isinstance(value, str):
            try:
                value = float(value.strip())
            except ValueError as exc:
                raise ValueError("Retry-After must be a numeric number of seconds") from exc
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError("Retry-After must be a nonnegative finite number of seconds")
        return float(value)

    @classmethod
    def _is_transient(cls, error):
        if isinstance(error, (TimeoutError, ConnectionError)):
            return True
        status = getattr(error, "status_code", getattr(error, "status", None))
        if type(status) is int and (status in (408, 425, 429) or 500 <= status <= 599):
            return True
        # CCXT and other adapters may expose a parsed Retry-After value.
        return (getattr(error, "retry_after_seconds", None) is not None
                or getattr(error, "retry_after", None) is not None)

    def _delay(self, failed_attempt, retry_after):
        exponential = min(
            self.max_delay_seconds,
            self.base_delay_seconds * (2 ** (failed_attempt - 1)),
        )
        sample = self.random_fn()
        if isinstance(sample, bool) or not isinstance(sample, (int, float)) or not math.isfinite(sample) or not 0 <= sample <= 1:
            raise ValueError("random_fn must return a finite value between zero and one")
        jittered = exponential * (1 + ((2 * sample) - 1) * self.jitter_ratio)
        local_delay = min(self.max_delay_seconds, max(0.0, jittered))
        # Server Retry-After is authoritative even when it exceeds our local cap.
        return max(local_delay, retry_after or 0.0)

    def execute(self, operation):
        if not callable(operation):
            raise TypeError("operation must be callable")
        for attempt in range(1, self.max_attempts + 1):
            try:
                return operation()
            except Exception as error:
                if not self._is_transient(error) or attempt >= self.max_attempts:
                    raise
                retry_after = self._retry_after(error)
                self.sleep(self._delay(attempt, retry_after))
        raise AssertionError("unreachable")


class SchedulerExecutionError(RuntimeError):
    """One or more timeframe syncs failed; successful timeframes remain committed."""

    def __init__(self, failures, completed):
        self.failures = dict(failures)
        self.completed = dict(completed)
        failed = ", ".join(sorted(self.failures))
        super().__init__(f"Feeder sync failed for timeframe(s): {failed}")


class FeederScheduler:
    """UTC close-boundary scheduler with independent per-timeframe watermarks."""

    def __init__(self, config, clock=None, sync_callback=None):
        if not isinstance(config, FeederConfig):
            raise TypeError("config must be FeederConfig")
        if not callable(sync_callback):
            raise TypeError("sync_callback must be callable")
        self.config = config
        self.clock = clock if clock is not None else (lambda: time.time_ns() // 1_000_000)
        if not callable(self.clock):
            raise TypeError("clock must be callable")
        initial_now = self._now_ms()
        self._lock = threading.RLock()
        self._last_completed_end_ms = {
            frame: initial_now - (initial_now % INTERVAL_MS[frame])
            for frame in config.timeframes
        }
        self._running = set()
        self.sync_callback = sync_callback

    def _now_ms(self):
        value = self.clock()
        if type(value) is not int or value < 0:
            raise ValueError("scheduler clock must return nonnegative integer epoch milliseconds")
        return value

    @property
    def last_completed_end_ms(self):
        with self._lock:
            return dict(self._last_completed_end_ms)

    @property
    def running_timeframes(self):
        with self._lock:
            return frozenset(self._running)

    def _validate_timeframe(self, timeframe):
        if timeframe not in self.config.timeframes:
            raise ValueError(f"Unsupported feeder timeframe: {timeframe}")

    def _eligible_end_ms(self, timeframe, now_ms=None):
        interval = INTERVAL_MS[timeframe]
        now = self._now_ms() if now_ms is None else now_ms
        eligible = now - self.config.close_grace_seconds * 1000
        return eligible - (eligible % interval)

    def due_timeframes(self):
        now = self._now_ms()
        due = []
        with self._lock:
            for timeframe in self.config.timeframes:
                eligible_end = self._eligible_end_ms(timeframe, now)
                if (eligible_end > self._last_completed_end_ms[timeframe]
                        and timeframe not in self._running):
                    due.append(timeframe)
        return tuple(due)

    def window_for(self, timeframe):
        self._validate_timeframe(timeframe)
        interval = INTERVAL_MS[timeframe]
        now = self._now_ms()
        end_ms = self._eligible_end_ms(timeframe, now)
        with self._lock:
            start_ms = self._last_completed_end_ms[timeframe]
        if end_ms <= start_ms:
            raise ValueError(f"No closed candle window is due for {timeframe}")
        end_ms = min(end_ms, start_ms + MAX_CANDLES * interval)
        return start_ms, end_ms

    def mark_running(self, timeframe):
        self._validate_timeframe(timeframe)
        with self._lock:
            if timeframe in self._running:
                return False
            self._running.add(timeframe)
            return True

    def mark_completed(self, timeframe, close_boundary_ms):
        self._validate_timeframe(timeframe)
        interval = INTERVAL_MS[timeframe]
        if type(close_boundary_ms) is not int or close_boundary_ms < 0 or close_boundary_ms % interval:
            raise ValueError("completion boundary must be an aligned UTC millisecond timestamp")
        eligible_end = self._eligible_end_ms(timeframe)
        with self._lock:
            previous = self._last_completed_end_ms[timeframe]
            if timeframe not in self._running:
                raise ValueError("timeframe must be running before it can be marked complete")
            if close_boundary_ms <= previous or close_boundary_ms > eligible_end:
                raise ValueError("completion boundary is not a newly closed candle boundary")
            self._last_completed_end_ms[timeframe] = close_boundary_ms
            self._running.discard(timeframe)

    def mark_failed(self, timeframe):
        self._validate_timeframe(timeframe)
        with self._lock:
            self._running.discard(timeframe)

    def run_due(self):
        """Run due timeframes independently; a failure never suppresses another frame."""
        completed, failures = {}, {}
        for timeframe in self.due_timeframes():
            if not self.mark_running(timeframe):
                continue
            try:
                start_ms, end_ms = self.window_for(timeframe)
                result = self.sync_callback(timeframe, start_ms, end_ms)
                self.mark_completed(timeframe, end_ms)
                completed[timeframe] = result
            except Exception as error:
                self.mark_failed(timeframe)
                failures[timeframe] = error
        if failures:
            raise SchedulerExecutionError(failures, completed) from next(iter(failures.values()))
        return completed

    def run_forever(self, stop_event):
        """Poll on the configured cadence until stopped or an unhandled sync error occurs."""
        if not callable(getattr(stop_event, "is_set", None)) or not callable(getattr(stop_event, "wait", None)):
            raise TypeError("stop_event must provide is_set() and wait(timeout)")
        while not stop_event.is_set():
            self.run_due()
            if stop_event.wait(self.config.poll_interval_seconds):
                break


@dataclass(frozen=True)
class RecoveryResult:
    """Verified result of a bounded canonical-store recovery pass."""

    complete: bool
    recovered_windows: tuple
    coverage: dict


class RecoveryIncompleteError(RuntimeError):
    """Raised when canonical storage still contains gaps after recovery."""


class RecoveryPlanner:
    """Validate store-reported gaps and return chronological half-open windows."""

    def plan(self, timeframe, coverage):
        if timeframe not in INTERVAL_MS:
            raise ValueError(f"Unsupported recovery timeframe: {timeframe}")
        if not isinstance(coverage, dict):
            raise ValueError("coverage must be a mapping")
        interval = INTERVAL_MS[timeframe]
        start = coverage.get("startMs")
        end = coverage.get("endMs")
        if (type(start) is not int or type(end) is not int
                or start < 0 or end <= start
                or start % interval or end % interval):
            raise ValueError("coverage bounds must be valid aligned UTC millisecond timestamps")
        details = coverage.get("coverage")
        if not isinstance(details, dict):
            raise ValueError("coverage details are required")
        gaps = details.get("gaps")
        if not isinstance(gaps, list):
            raise ValueError("coverage gaps must be a list")

        windows = []
        for gap in gaps:
            if not isinstance(gap, dict):
                raise ValueError("each coverage gap must be a mapping")
            gap_start, gap_end = gap.get("startMs"), gap.get("endMs")
            if (type(gap_start) is not int or type(gap_end) is not int
                    or gap_start < start or gap_end > end
                    or gap_start % interval or gap_end % interval
                    or gap_end <= gap_start):
                raise ValueError("gap must be nonempty, aligned, and within requested coverage")
            windows.append((gap_start, gap_end))

        windows.sort()
        previous_end = None
        for gap_start, gap_end in windows:
            if previous_end is not None and gap_start < previous_end:
                raise ValueError("coverage gaps must not overlap")
            previous_end = gap_end
        return windows


class RecoveryCoordinator:
    """Recover reported gaps only through the injected canonical sync callback."""

    def __init__(self, sync_callback, coverage_reader):
        if not callable(sync_callback):
            raise TypeError("sync_callback must be callable")
        if not callable(coverage_reader):
            raise TypeError("coverage_reader must be callable")
        self.sync_callback = sync_callback
        self.coverage_reader = coverage_reader
        self.planner = RecoveryPlanner()

    def recover(self, timeframe, start_ms, end_ms):
        if timeframe not in INTERVAL_MS:
            raise ValueError(f"Unsupported recovery timeframe: {timeframe}")
        interval = INTERVAL_MS[timeframe]
        if (type(start_ms) is not int or type(end_ms) is not int
                or start_ms < 0 or end_ms <= start_ms
                or start_ms % interval or end_ms % interval):
            raise ValueError("recovery bounds must be valid aligned UTC millisecond timestamps")

        initial = self.coverage_reader(timeframe, start_ms, end_ms)
        windows = self.planner.plan(timeframe, initial)
        if not windows:
            return RecoveryResult(True, (), initial)

        for gap_start, gap_end in windows:
            # This callback must be the existing sync_window() path; recovery
            # does not introduce an exchange client or an alternate writer.
            self.sync_callback(timeframe, gap_start, gap_end)

        verified = self.coverage_reader(timeframe, start_ms, end_ms)
        remaining = self.planner.plan(timeframe, verified)
        if remaining:
            raise RecoveryIncompleteError(
                f"Recovery left {len(remaining)} gap(s) for {timeframe}"
            )
        return RecoveryResult(True, tuple(windows), verified)


@dataclass(frozen=True)
class Lease:
    """A fencing generation granted to one feeder process."""

    owner: str
    generation: int
    expires_at_ms: int


class LeaseStore:
    """SQLite-backed singleton lease with monotonic fencing generations.

    Every state transition uses BEGIN IMMEDIATE so concurrent processes cannot
    both acquire or renew ownership. Storage errors propagate; callers must
    treat them as loss of ownership (fail closed).
    """

    def __init__(self, db_path, lease_name="binance-btcusdt-canonical"):
        if not isinstance(db_path, (str, bytes)) or not db_path:
            raise ValueError("db_path must be a non-empty filesystem path")
        if not isinstance(lease_name, str) or not lease_name.strip():
            raise ValueError("lease_name must be a non-empty string")
        self.db_path = str(db_path)
        self.lease_name = lease_name

    @staticmethod
    def _validate(owner, generation=None, now_ms=None, ttl_seconds=None):
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError("owner must be a non-empty string")
        if generation is not None and (type(generation) is not int or generation < 1):
            raise ValueError("generation must be a positive integer")
        if now_ms is not None and (type(now_ms) is not int or now_ms < 0):
            raise ValueError("now_ms must be a nonnegative integer")
        if ttl_seconds is not None and (type(ttl_seconds) is not int or ttl_seconds <= 0):
            raise ValueError("ttl_seconds must be a positive integer")

    def _transaction(self, operation):
        connection = sqlite3.connect(self.db_path, timeout=5, isolation_level=None)
        try:
            connection.execute("PRAGMA busy_timeout=5000")
            connection.execute("""CREATE TABLE IF NOT EXISTS feeder_leases (
                lease_name TEXT PRIMARY KEY,
                owner TEXT,
                generation INTEGER NOT NULL CHECK(generation >= 0),
                expires_at_ms INTEGER NOT NULL CHECK(expires_at_ms >= 0)
            )""")
            connection.execute("BEGIN IMMEDIATE")
            result = operation(connection)
            connection.commit()
            return result
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def acquire(self, owner, now_ms, ttl_seconds=60):
        self._validate(owner, now_ms=now_ms, ttl_seconds=ttl_seconds)
        expires = now_ms + ttl_seconds * 1000

        def operation(connection):
            row = connection.execute(
                "SELECT owner, generation, expires_at_ms FROM feeder_leases WHERE lease_name=?",
                (self.lease_name,),
            ).fetchone()
            if row is None:
                generation = 1
                connection.execute(
                    "INSERT INTO feeder_leases VALUES (?, ?, ?, ?)",
                    (self.lease_name, owner, generation, expires),
                )
                return Lease(owner, generation, expires)
            current_owner, generation, current_expiry = row
            if current_owner is not None and current_expiry > now_ms:
                if current_owner == owner:
                    return Lease(owner, generation, current_expiry)
                return None
            generation += 1
            connection.execute(
                "UPDATE feeder_leases SET owner=?, generation=?, expires_at_ms=? WHERE lease_name=?",
                (owner, generation, expires, self.lease_name),
            )
            return Lease(owner, generation, expires)

        return self._transaction(operation)

    def heartbeat(self, owner, generation, now_ms, ttl_seconds=60):
        self._validate(owner, generation, now_ms, ttl_seconds)
        expires = now_ms + ttl_seconds * 1000

        def operation(connection):
            cursor = connection.execute(
                """UPDATE feeder_leases SET expires_at_ms=?
                   WHERE lease_name=? AND owner=? AND generation=? AND expires_at_ms>?""",
                (expires, self.lease_name, owner, generation, now_ms),
            )
            return cursor.rowcount == 1

        return self._transaction(operation)

    def is_current(self, owner, generation, now_ms):
        self._validate(owner, generation, now_ms)

        def operation(connection):
            row = connection.execute(
                """SELECT 1 FROM feeder_leases
                   WHERE lease_name=? AND owner=? AND generation=? AND expires_at_ms>?""",
                (self.lease_name, owner, generation, now_ms),
            ).fetchone()
            return row is not None

        return self._transaction(operation)

    def authorize_write(self, owner, generation, now_ms):
        # The check is an authoritative lease check. Writers must invoke it
        # immediately before each canonical write; a stale generation fails.
        return self.is_current(owner, generation, now_ms)

    def release(self, owner, generation):
        self._validate(owner, generation)

        def operation(connection):
            cursor = connection.execute(
                """UPDATE feeder_leases SET owner=NULL, expires_at_ms=0
                   WHERE lease_name=? AND owner=? AND generation=?""",
                (self.lease_name, owner, generation),
            )
            return cursor.rowcount == 1

        return self._transaction(operation)

@dataclass(frozen=True)
class TimeframeHealth:
    """Freshness assessment for one canonical candle timeframe."""

    state: str
    latest_closed_candle_close_ms: int | None
    last_successful_sync_ms: int | None
    unresolved_gap_count: int
    sync_error: str | None
    age_ms: int | None


@dataclass(frozen=True)
class HealthResult:
    """Combined process, dependency and market-data health assessment."""

    state: str
    live: bool
    ready: bool
    timeframes: dict


class HealthEvaluator:
    """Evaluate liveness, readiness and independent M15/H1 data freshness.

    Candle close timestamps are compared against the supplied clock. One full
    interval of lag is DEGRADED; two intervals is STALE. Missing or malformed
    snapshot data fails closed and never produces readiness.
    """

    _PRIORITY = {
        "STARTING": 0,
        "HEALTHY": 1,
        "DEGRADED": 2,
        "STALE": 3,
        "FAILED": 4,
        "STOPPED": 5,
    }

    def __init__(self, config=None):
        self.config = config if config is not None else FeederConfig()
        if not isinstance(self.config, FeederConfig):
            raise TypeError("config must be FeederConfig")

    @classmethod
    def _worst_state(cls, states):
        return max(states, key=lambda state: cls._PRIORITY[state])

    @staticmethod
    def _valid_timestamp(value):
        return type(value) is int and value >= 0

    def _timeframe_health(self, snapshot, timeframe, now_ms):
        interval = INTERVAL_MS[timeframe]
        data = snapshot.get("m15" if timeframe == "15m" else "1h")
        if not isinstance(data, dict):
            return TimeframeHealth("FAILED", None, None, 0, "INVALID_SNAPSHOT", None)

        latest = data.get("latest_closed_candle_close_ms")
        last_sync = data.get("last_successful_sync_ms")
        gaps = data.get("unresolved_gap_count", 0)
        sync_error = data.get("sync_error")

        if latest is None:
            return TimeframeHealth("STARTING", None, last_sync, gaps if type(gaps) is int else 0,
                                   sync_error, None)
        if (not self._valid_timestamp(latest)
                or not self._valid_timestamp(last_sync)
                or type(gaps) is not int or gaps < 0
                or latest > now_ms):
            return TimeframeHealth("FAILED", None, None, 0, "INVALID_SNAPSHOT", None)

        age_ms = now_ms - latest
        if age_ms >= 2 * interval:
            state = "STALE"
        elif age_ms >= interval or gaps > 0 or sync_error:
            state = "DEGRADED"
        else:
            state = "HEALTHY"
        return TimeframeHealth(state, latest, last_sync, gaps, sync_error, age_ms)

    def evaluate(self, snapshot, now_ms=None):
        if now_ms is None:
            now_ms = time.time_ns() // 1_000_000
        if not self._valid_timestamp(now_ms):
            raise ValueError("now_ms must be a nonnegative integer epoch timestamp")
        if not isinstance(snapshot, dict):
            snapshot = {}

        process_running = snapshot.get("process_running") is True
        live = process_running
        if not process_running:
            return HealthResult("STOPPED", False, False, {})

        if (snapshot.get("fatal_error") is True
                or snapshot.get("storage_readable") is not True
                or snapshot.get("storage_writable") is not True):
            return HealthResult("FAILED", live, False, {
                frame: self._timeframe_health(snapshot, frame, now_ms)
                for frame in self.config.timeframes
            })

        timeframes = {
            frame: self._timeframe_health(snapshot, frame, now_ms)
            for frame in self.config.timeframes
        }
        states = [item.state for item in timeframes.values()]
        if snapshot.get("startup_complete") is not True:
            states.append("STARTING")
        if snapshot.get("lease_valid") is not True:
            states.append("DEGRADED")

        state = self._worst_state(states)
        # An otherwise healthy process is still STARTING until initialization
        # has completed. More severe data/dependency failures retain priority.
        if snapshot.get("startup_complete") is not True and state == "HEALTHY":
            state = "STARTING"
        ready = (
            snapshot.get("startup_complete") is True
            and snapshot.get("storage_readable") is True
            and snapshot.get("storage_writable") is True
            and snapshot.get("lease_valid") is True
            and snapshot.get("fatal_error") is not True
            and all(item.state == "HEALTHY" for item in timeframes.values())
        )
        return HealthResult(state, live, ready, timeframes)
