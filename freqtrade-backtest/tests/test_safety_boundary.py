"""Guard against accidental live-trading capabilities in analytics-only sources."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXCLUDED = {"test_safety_boundary.py"}
FORBIDDEN = ("create_order(", "place_order(", "cancel_order(", "api_key =", "secret_key =")


class SafetyBoundaryTest(unittest.TestCase):
    def test_no_trading_calls_in_analytics_python(self):
        for path in ROOT.rglob("*.py"):
            if path.name in EXCLUDED or "tests" in path.parts:
                continue
            source = path.read_text(encoding="utf-8").lower()
            for token in FORBIDDEN:
                with self.subTest(path=str(path), token=token):
                    self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
