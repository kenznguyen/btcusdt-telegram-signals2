"""Controlled synthetic OHLCV scenarios are tests, never evidence of market performance."""
import tempfile
import unittest
from pathlib import Path
from quant_engine.scenario_runner import write_scenarios, replay_scenarios

class ControlledScenarioTests(unittest.TestCase):
    def test_each_unobserved_core_branch_is_exercised_by_actual_python_indicators(self):
        with tempfile.TemporaryDirectory() as tmp:
            scenarios=Path(tmp)/"scenarios"
            write_scenarios(scenarios)
            report=replay_scenarios(scenarios)
            self.assertEqual(set(report),{"DCA","SOFT SL","EMERGENCY SL"})
            for name,item in report.items():
                self.assertEqual(item["events"],[name])
                self.assertTrue((scenarios/name/"python-trace.json").is_file())
                self.assertEqual(item["data_class"],"CONTROLLED_SYNTHETIC")
            self.assertEqual(report["DCA"]["dca_used"],True)

    def test_missing_required_initial_state_is_not_silently_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            scenarios=Path(tmp)/"scenarios"
            write_scenarios(scenarios)
            (scenarios/"DCA"/"initial-state.json").unlink()
            with self.assertRaises((FileNotFoundError,ValueError)):
                replay_scenarios(scenarios)

if __name__=="__main__":
    unittest.main()
