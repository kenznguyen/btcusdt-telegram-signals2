import ast
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "strategies" / "BtcM15H1ParityGate.py"


class ParityGateTest(unittest.TestCase):
    def test_entry_and_exit_are_explicitly_disabled(self):
        tree = ast.parse(PATH.read_text(encoding="utf-8"))
        methods = {node.name: node for cls in tree.body if isinstance(cls, ast.ClassDef)
                   for node in cls.body if isinstance(node, ast.FunctionDef)}
        for method, fields in (("populate_entry_trend", ("enter_long", "enter_short")),
                               ("populate_exit_trend", ("exit_long", "exit_short"))):
            assignments = {}
            for node in ast.walk(methods[method]):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                    for target in node.targets:
                        if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant):
                            assignments[target.slice.value] = node.value.value
            for field in fields:
                self.assertEqual(assignments.get(field), 0, field)


if __name__ == "__main__":
    unittest.main()
