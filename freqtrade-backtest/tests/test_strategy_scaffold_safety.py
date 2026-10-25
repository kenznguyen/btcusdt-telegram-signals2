"""Safety contract for the deliberately non-trading Freqtrade scaffold.

These tests use AST rather than importing Freqtrade, so they run in offline CI
without an exchange, credentials or an installed trading engine.
"""
import ast
from pathlib import Path
import unittest

STRATEGY = Path(__file__).resolve().parents[1] / "strategies" / "BtcM15H1ParityGate.py"


class FreqtradeScaffoldSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(STRATEGY.read_text(encoding="utf-8"))
        cls.strategy = next(
            node for node in cls.tree.body
            if isinstance(node, ast.ClassDef) and node.name == "BtcM15H1ParityGate"
        )

    def test_entry_and_exit_are_explicitly_disabled(self):
        expected = {
            "populate_entry_trend": {"enter_long": 0, "enter_short": 0},
            "populate_exit_trend": {"exit_long": 0, "exit_short": 0},
        }
        for method_name, columns in expected.items():
            method = next(
                node for node in self.strategy.body
                if isinstance(node, ast.FunctionDef) and node.name == method_name
            )
            assigned = {}
            for node in ast.walk(method):
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target = node.targets[0]
                    if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == "dataframe":
                        if isinstance(target.slice, ast.Constant) and isinstance(node.value, ast.Constant):
                            assigned[target.slice.value] = node.value.value
            for column, value in columns.items():
                self.assertEqual(value, assigned.get(column), f"{method_name}.{column} must remain disabled")

    def test_no_order_placement_or_network_calls(self):
        forbidden = {"requests", "httpx", "ccxt", "socket", "subprocess", "websocket"}
        imported = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertFalse(forbidden & imported)


if __name__ == "__main__":
    unittest.main()
