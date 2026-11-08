"""RED-only architecture contracts for the T2 HTTP candle consumer.

These tests intentionally describe the approved target boundary. They do not
implement an HTTP client or change the existing consumer/runtime.
"""
import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "freqai_bridge"


class T2HttpConsumerRedTest(unittest.TestCase):
    def test_http_adapter_module_exists(self):
        self.assertTrue(
            (BRIDGE / "http_candles.py").is_file(),
            "T2 HTTP adapter is not implemented",
        )

    def test_context_does_not_import_t0_store(self):
        source = (BRIDGE / "context.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = [
            node for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        forbidden = [
            node for node in imports
            if isinstance(node, ast.ImportFrom)
            and node.module == "market_data.store"
        ]
        self.assertEqual(forbidden, [], "T2 context still imports market_data.store")

    def test_context_does_not_call_t0_read_window(self):
        source = (BRIDGE / "context.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "read_window"
        ]
        self.assertEqual(calls, [], "T2 context still calls direct SQLite read_window")

    def test_strategy_does_not_accept_canonical_db_path(self):
        source = (BRIDGE / "ChartProFreqaiResearch.py").read_text(encoding="utf-8")
        self.assertNotIn(
            "canonical_db_path",
            source,
            "FreqAI strategy still passes a T0 database path to the consumer",
        )

    def test_strategy_does_not_pass_database_to_canonical_context(self):
        source = (BRIDGE / "ChartProFreqaiResearch.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "canonical_context"
        ]
        self.assertEqual(
            calls, [],
            "Strategy must migrate from the legacy DB-argument call to the HTTP context contract",
        )

    def test_approved_freshness_formula_is_present_in_contract_plan(self):
        plan = (
            ROOT / "docs/architecture/"
            "T2_HTTP_CANDLE_CONSUMER_CONTRACT_AND_TEST_PLAN_2026-11-08.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "latestAvailableAtMs - latestCloseTimeMs",
            plan,
        )
        self.assertIn("closeLagMs - observationAgeMs", plan)
        self.assertIn("120000 ms", plan)

    def test_transport_limits_are_recorded_in_contract_plan(self):
        plan = (
            ROOT / "docs/architecture/"
            "T2_HTTP_CANDLE_CONSUMER_CONTRACT_AND_TEST_PLAN_2026-11-08.md"
        ).read_text(encoding="utf-8")
        for required in (
            "connect timeout 3 s",
            "read timeout 5 s",
            "3 total attempts",
            "250 ms then 500 ms",
            "256 KiB",
            "do not automatically follow redirects",
        ):
            with self.subTest(required=required):
                self.assertIn(required, plan)


if __name__ == "__main__":
    unittest.main()
