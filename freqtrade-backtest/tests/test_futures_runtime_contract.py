"""Offline contract for futures-only Freqtrade strategy, without installing Freqtrade."""
import ast
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "strategies" / "BtcM15H1FuturesRuntime.py"
CONFIG = ROOT / "config.runtime-futures.json"
sys.path.insert(0, str(ROOT))
from android_signal_predicates import exit_reason, roe_for


def load_exit_evaluator():
    # Evaluate only the isolated pure function; do not import Freqtrade objects.
    tree = ast.parse(PATH.read_text(encoding="utf-8"))
    fun = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
               and n.name == "evaluate_exit")
    module = ast.Module(body=[fun], type_ignores=[])
    ns = {"exit_reason": exit_reason, "roe_for": roe_for}
    exec(compile(ast.fix_missing_locations(module), str(PATH), "exec"), ns)
    return ns["evaluate_exit"]


class FuturesRuntimeContractTest(unittest.TestCase):
    def test_config_requires_isolated_futures_without_keys(self):
        c = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(c["trading_mode"], "futures")
        self.assertEqual(c["margin_mode"], "isolated")
        self.assertEqual(c["exchange"]["name"], "okx")
        self.assertEqual(c["exchange"]["pair_whitelist"], ["BTC/USDT:USDT"])
        self.assertEqual(c["exchange"]["key"], "")
        self.assertEqual(c["exchange"]["secret"], "")
        self.assertTrue(c["dry_run"])

    def test_all_required_callbacks_present(self):
        tree = ast.parse(PATH.read_text(encoding="utf-8"))
        strategy = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                        and n.name == "BtcM15H1FuturesRuntime")
        methods = {n.name for n in strategy.body if isinstance(n, ast.FunctionDef)}
        self.assertTrue({
            "bot_start", "populate_indicators", "populate_entry_trend",
            "populate_exit_trend", "leverage", "custom_stake_amount",
            "custom_exit", "adjust_trade_position",
        }.issubset(methods))
        src = PATH.read_text(encoding="utf-8")
        self.assertIn("RunMode.BACKTEST", src)
        self.assertIn('can_short = True', src)
        self.assertIn('max_entry_position_adjustment = 1', src)
        self.assertIn("return 13.0", src)

    def test_emergency_wins_over_soft_and_tp(self):
        run = load_exit_evaluator()
        candle = {
            "low": 92.0, "high": 101.0, "open": 100.0, "close": 99.0,
            "android_rsi": 80.0, "android_h1_plus_di": 10.0,
            "android_h1_minus_di": 30.0, "android_h1_adx": 40.0,
        }
        previous = {"open": 101.0, "close": 100.0}
        self.assertEqual("EMERGENCY_SL", run("LONG", candle, previous, 100.0))

    def test_soft_stop_precedes_tp_and_is_conditional(self):
        run = load_exit_evaluator()
        candle = {
            "low": 97.0, "high": 101.0, "open": 100.0, "close": 99.0,
            "android_rsi": 80.0, "android_h1_plus_di": 10.0,
            "android_h1_minus_di": 30.0, "android_h1_adx": 40.0,
        }
        self.assertEqual("SOFT_SL", run("LONG", candle, {"open": 101.0, "close": 100.0}, 100.0))
        self.assertIsNone(run("LONG", candle, {"open": 100.0, "close": 101.0}, 100.0))

    def test_tp_when_rsi_and_roe_both_pass(self):
        run = load_exit_evaluator()
        candle = {
            "low": 100.0, "high": 103.0, "open": 100.0, "close": 101.0,
            "android_rsi": 80.0, "android_h1_plus_di": 40.0,
            "android_h1_minus_di": 10.0, "android_h1_adx": 40.0,
        }
        self.assertEqual("TP", run("LONG", candle, {"open": 100.0, "close": 100.0}, 100.0))

    def test_short_emergency(self):
        run = load_exit_evaluator()
        candle = {
            "low": 99.0, "high": 110.0, "open": 100.0, "close": 101.0,
            "android_rsi": 20.0, "android_h1_plus_di": 40.0,
            "android_h1_minus_di": 10.0, "android_h1_adx": 40.0,
        }
        self.assertEqual("EMERGENCY_SL", run("SHORT", candle, {"open": 99, "close": 100}, 100.0))


if __name__ == "__main__":
    unittest.main()
