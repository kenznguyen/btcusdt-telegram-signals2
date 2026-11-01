"""P1.2 contract tests: bounded transient retry, jitter and Retry-After."""
import unittest
from unittest.mock import Mock

from market_data.feeder import RetryPolicy


class RateLimitError(Exception):
    def __init__(self, retry_after_seconds):
        super().__init__("rate limited")
        self.retry_after_seconds = retry_after_seconds


class RetryContractTest(unittest.TestCase):
    def policy(self, sleep, **overrides):
        values = dict(
            max_attempts=5,
            base_delay_seconds=1,
            max_delay_seconds=300,
            jitter_ratio=0,
            random_fn=lambda: 0.5,
            sleep=sleep,
        )
        values.update(overrides)
        return RetryPolicy(**values)

    def test_retries_timeout_then_returns_first_success(self):
        sleep = Mock()
        operation = Mock(side_effect=[TimeoutError(), ConnectionError(), "ok"])
        self.assertEqual(self.policy(sleep).execute(operation), "ok")
        self.assertEqual(operation.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])

    def test_five_attempt_limit_propagates_last_transient_error(self):
        sleep = Mock()
        operation = Mock(side_effect=TimeoutError("offline"))
        with self.assertRaisesRegex(TimeoutError, "offline"):
            self.policy(sleep).execute(operation)
        self.assertEqual(operation.call_count, 5)
        self.assertEqual(sleep.call_count, 4)

    def test_exponential_backoff_is_capped_at_five_minutes(self):
        delays = []
        # Five total attempts means four failures/retries before the success.
        operation = Mock(side_effect=[TimeoutError()] * 4 + ["ok"])
        policy = self.policy(delays.append, base_delay_seconds=100)
        self.assertEqual(policy.execute(operation), "ok")
        self.assertEqual(delays, [100, 200, 300, 300])
        self.assertEqual(operation.call_count, 5)

    def test_jitter_is_applied_within_the_configured_ratio(self):
        delays = []
        operation = Mock(side_effect=[TimeoutError(), "ok"])
        policy = self.policy(delays.append, base_delay_seconds=10,
                             jitter_ratio=0.2, random_fn=lambda: 1.0)
        self.assertEqual(policy.execute(operation), "ok")
        self.assertEqual(delays, [12])

    def test_retry_after_is_not_shortened_by_local_backoff_cap(self):
        delays = []
        operation = Mock(side_effect=[RateLimitError(420), "ok"])
        policy = self.policy(delays.append)
        self.assertEqual(policy.execute(operation), "ok")
        self.assertEqual(delays, [420])

    def test_retry_after_shorter_than_backoff_does_not_reduce_backoff(self):
        delays = []
        operation = Mock(side_effect=[RateLimitError(2), "ok"])
        policy = self.policy(delays.append, base_delay_seconds=10)
        self.assertEqual(policy.execute(operation), "ok")
        self.assertEqual(delays, [10])

    def test_non_transient_validation_error_is_not_retried(self):
        sleep = Mock()
        operation = Mock(side_effect=ValueError("invalid candle"))
        with self.assertRaisesRegex(ValueError, "invalid candle"):
            self.policy(sleep).execute(operation)
        self.assertEqual(operation.call_count, 1)
        sleep.assert_not_called()

    def test_retry_after_must_be_nonnegative_and_finite(self):
        for retry_after in (-1, float("inf")):
            with self.subTest(retry_after=retry_after):
                operation = Mock(side_effect=[RateLimitError(retry_after), "ok"])
                sleep = Mock()
                with self.assertRaises(ValueError):
                    self.policy(sleep).execute(operation)

    def test_http_429_and_5xx_are_transient(self):
        class HttpError(Exception):
            def __init__(self, status_code):
                self.status_code = status_code

        for status in (429, 500, 503):
            with self.subTest(status=status):
                delays = []
                operation = Mock(side_effect=[HttpError(status), "ok"])
                self.assertEqual(self.policy(delays.append).execute(operation), "ok")
                self.assertEqual(operation.call_count, 2)
                self.assertEqual(delays, [1])

    def test_non_retryable_http_client_error_is_not_retried(self):
        class HttpError(Exception):
            status_code = 400

        operation = Mock(side_effect=HttpError("bad request"))
        sleep = Mock()
        with self.assertRaises(HttpError):
            self.policy(sleep).execute(operation)
        self.assertEqual(operation.call_count, 1)
        sleep.assert_not_called()

    def test_retry_after_header_is_honored(self):
        class HttpError(Exception):
            status_code = 429
            headers = {"Retry-After": "7.5"}

        delays = []
        operation = Mock(side_effect=[HttpError(), "ok"])
        self.assertEqual(self.policy(delays.append).execute(operation), "ok")
        self.assertEqual(delays, [7.5])

    def test_local_jitter_never_exceeds_configured_backoff_cap(self):
        delays = []
        operation = Mock(side_effect=[TimeoutError(), "ok"])
        policy = self.policy(delays.append, base_delay_seconds=290,
                             max_delay_seconds=300, jitter_ratio=0.2,
                             random_fn=lambda: 1.0)
        self.assertEqual(policy.execute(operation), "ok")
        self.assertEqual(delays, [300])


if __name__ == "__main__":
    unittest.main()
