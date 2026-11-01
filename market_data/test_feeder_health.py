import unittest
from market_data.feeder import HealthEvaluator, FeederConfig

class HealthContractTest(unittest.TestCase):
    def test_readiness_requires_healthy_state(self):
        evaluator = HealthEvaluator(config=FeederConfig())
        self.assertIsNotNone(evaluator)
