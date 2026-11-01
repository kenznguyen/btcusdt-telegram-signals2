"""Centralized T0 feeder scheduling and retry primitives.

The scheduler never fetches exchange data or writes candles itself. Its injected
callback is the only hand-off to the existing sync_window() ingestion path.
"""
from dataclasses import dataclass
import math
import random
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
