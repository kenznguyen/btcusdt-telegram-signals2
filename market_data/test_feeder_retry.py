"""P1.2 contract tests: bounded transient retry and backoff."""
import unittest
from unittest.mock import Mock
from market_data.feeder import RetryPolicy


class RetryContractTest(unittest.TestCase):
    def test_retries_timeout_then_returns_success(self):
        sleep = Mock()
        call = Mock(side_effect=[TimeoutError(), ConnectionError(), "ok"])
        policy = RetryPolicy(max_attempts=5, base_delay_seconds=1,
                             max_delay_seconds=300, jitter_ratio=0,
                             random_fn=lambda: 0.5, sleep=sleep)
        self.assertEqual(policy.execute(call), "ok")
        self.assertEqual(call.call_count, 3)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1, 2])

    def test_five_attempt_limit_propagates_last_error(self):
        sleep = Mock()
        call = Mock(side_effect=TimeoutError("offline"))
        policy = RetryPolicy(max_attempts=5, sleep=sleep)
        with self.assertRaisesRegex(TimeoutError, "offline"):
            policy.execute(call)
        self.assertEqual(call.call_count, 5)
        self.assertEqual(sleep.call_count, 4)

    def test_backoff_is_exponential_and_capped(self):
        delays = []
        call = Mock(side_effect=[TimeoutError()] * 5 + ["ok"])
        policy = RetryPolicy(max_attempts=6, base_delay_seconds=100,
                             max_delay_seconds=300, jitter_ratio=0,
                             random_fn=lambda: 0.5, sleep=delays.append)
        self.assertEqual(policy.execute(call), "ok")
        self.assertEqual(delays, [100, 200, 300, 300, 300])

    def test_jitter_is_bounded_and_retry_after_is_honored(self):
        delays = []
        call = Mock(side_effect=[TimeoutError(), "ok"])
        policy = RetryPolicy(max_attempts=2, base_delay_seconds=10,
                             max_delay_seconds=300, jitter_ratio=0.2,
                             random_fn=lambda: 1.0, sleep=delays.append)
        self.assertEqual(policy.execute(call), "ok")
        self.assertEqual(delays, [12])

    def test_non_transient_validation_error_is_not_retried(self):
        call = Mock(side_effect=ValueError("invalid candle"))
        policy = RetryPolicy(sleep=Mock())
        with self.assertRaisesRegex(ValueError, "invalid candle"):
            policy.execute(call)
        self.assertEqual(call.call_count, 1)


if __name__ == "__main__":
    unittest.main()
