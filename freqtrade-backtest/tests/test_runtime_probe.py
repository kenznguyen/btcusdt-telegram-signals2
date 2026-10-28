import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_probe import probe


class RuntimeProbeTest(unittest.TestCase):
    @patch("runtime_probe.shutil.which", return_value=None)
    def test_missing_executable_never_verified(self, _):
        result = probe()
        self.assertFalse(result["actual_runtime_invoked"])
        self.assertFalse(result["runtime_available"])
        self.assertFalse(result["verified"])
        self.assertFalse(result["event_parity_verified"])

    @patch("runtime_probe.subprocess.run")
    @patch("runtime_probe.shutil.which", return_value="/usr/bin/freqtrade")
    def test_real_version_is_not_strategy_parity(self, _, run):
        def response(*args, **kwargs):
            class Result:
                returncode = 0
                stdout = "freqtrade 2026.1\n"
                stderr = ""
            return Result()
        run.side_effect = response
        result = probe()
        self.assertTrue(result["runtime_available"])
        self.assertTrue(result["actual_runtime_invoked"])
        self.assertFalse(result["backtesting_executed"])
        self.assertFalse(result["same_ohlcv_data_compared"])
        self.assertFalse(result["verified"])
        self.assertFalse(result["strategy_entry_exit_ported"])


if __name__ == "__main__":
    unittest.main()
