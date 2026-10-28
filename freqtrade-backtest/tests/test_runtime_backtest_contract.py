"""Fail-closed guardrails for the real Freqtrade diagnostic backtest path."""
import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "strategies" / "BtcM15H1EntryRuntime.py"
CONFIG = ROOT / "config.runtime-entry.json"


class RuntimeBacktestContractTest(unittest.TestCase):
    def test_config_is_spot_keyless_and_dry_run(self):
        c = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertTrue(c["dry_run"])
        self.assertEqual("spot", c["trading_mode"])
        self.assertEqual("", c["exchange"]["key"])
        self.assertEqual("", c["exchange"]["secret"])
        self.assertEqual(["BTC/USDT"], c["exchange"]["pair_whitelist"])

    def test_adapter_is_long_only_and_explicitly_backtest_gated(self):
        text = ADAPTER.read_text(encoding="utf-8")
        tree = ast.parse(text)
        strategy = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                        and n.name == "BtcM15H1EntryRuntime")
        assignments = {t.id: n.value.value for n in strategy.body
                       if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
                       for t in n.targets if isinstance(t, ast.Name)}
        self.assertIs(assignments["can_short"], False)
        self.assertIs(assignments["use_exit_signal"], False)
        methods = {m.name: m for m in strategy.body if isinstance(m, ast.FunctionDef)}
        self.assertIn("bot_start", methods)
        self.assertIn("RunMode.BACKTEST", text)
        self.assertIn("entry_diagnostics(dataframe, h1)", text)

    def test_diagnostic_adapter_has_no_order_placement_or_http_clients(self):
        tree = ast.parse(ADAPTER.read_text(encoding="utf-8"))
        forbidden = {"ccxt", "requests", "httpx", "socket", "websocket"}
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        self.assertFalse(names & forbidden)


if __name__ == "__main__":
    unittest.main()
