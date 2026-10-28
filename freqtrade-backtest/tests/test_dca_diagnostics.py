"""Pure tests for why Futures runtime did not propose DCA."""
import ast
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from android_signal_predicates import exit_reason, roe_for, dca_signal

PATH = ROOT / "strategies" / "BtcM15H1FuturesRuntime.py"


def load_function():
    tree = ast.parse(PATH.read_text(encoding="utf-8"))
    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name in ("evaluate_exit", "dca_diagnosis")]
    module = ast.fix_missing_locations(ast.Module(body=funcs, type_ignores=[]))
    scope = {"exit_reason": exit_reason, "roe_for": roe_for, "dca_signal": dca_signal, "math": math}
    exec(compile(module, str(PATH), "exec"), scope)
    return scope["dca_diagnosis"]


class DcaDiagnosticsTest(unittest.TestCase):
    def setUp(self):
        self.diagnose = load_function()
        self.candle = {
            "open": 100.0, "high": 100.1, "low": 98.0, "close": 98.1,
            "android_rsi": 35.0, "android_prev_rsi": 30.0, "android_adx": 46.0,
            "android_h1_plus_di": None, "android_h1_minus_di": None,
            "android_h1_adx": None,
        }
        self.previous = {"open": 100.0, "close": 99.9}

    def test_qualifying_long_dca(self):
        result = self.diagnose("LONG", self.candle, self.previous, 100, 1, False, 50, 50)
        self.assertEqual("dca_proposed", result["reason"])
        self.assertTrue(result["dca_candidate"])

    def test_not_enough_margin(self):
        result = self.diagnose("LONG", self.candle, self.previous, 100, 1, False, 50, 40)
        self.assertEqual("insufficient_free_stake", result["reason"])

    def test_rsi_filter_rejected(self):
        c = {**self.candle, "android_rsi": 24.0, "android_prev_rsi": 30.0}
        result = self.diagnose("LONG", c, self.previous, 100, 1, False, 50, 50)
        self.assertEqual("rsi_direction_filter_not_met", result["reason"])

    def test_entry_limit(self):
        result = self.diagnose("LONG", self.candle, self.previous, 100, 2, False, 50, 50)
        self.assertEqual("position_already_adjusted_or_open_order", result["reason"])

    def test_exit_priority(self):
        c = {**self.candle, "low": 92.0}
        result = self.diagnose("LONG", c, self.previous, 100, 1, False, 50, 50)
        self.assertEqual("exit_has_priority", result["reason"])

    def test_not_below_roe_threshold(self):
        c = {**self.candle, "low": 99.5, "close": 100.0}
        result = self.diagnose("LONG", c, self.previous, 100, 1, False, 50, 50)
        self.assertEqual("roe_not_below_minus_20", result["reason"])


if __name__ == "__main__":
    unittest.main()
