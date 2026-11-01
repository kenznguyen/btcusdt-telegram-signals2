import unittest
from market_data.feeder import HealthEvaluator, FeederConfig

NOW = 1800000000000

class HealthContractTest(unittest.TestCase):
    def test_fresh_m15_and_h1_are_ready(self):
        evaluator = HealthEvaluator(config=FeederConfig())
        state = {'process_running': True, 'storage_readable': True, 'storage_writable': True, 'lease_valid': True, 'fatal_error': False, 'm15': {'latest_closed_candle_close_ms': NOW, 'unresolved_gap_count': 0}, '1h': {'latest_closed_candle_close_ms': NOW, 'unresolved_gap_count': 0}}
        result = evaluator.evaluate(state, now_ms=NOW + 5000)
        self.assertEqual(result.state, 'HEALTHY')
        self.assertTrue(result.ready)
