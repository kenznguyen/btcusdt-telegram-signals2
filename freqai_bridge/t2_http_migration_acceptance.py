"""Explicitly invoked acceptance checks for the separately gated T2 SQLite migration.

This module intentionally does not use the unittest discovery filename prefix.
Run it only in the separately authorized direct-DB-removal increment.
"""
import ast
from pathlib import Path
import unittest

BRIDGE = Path(__file__).resolve().parent


class T2HttpMigrationAcceptanceTest(unittest.TestCase):
    def test_context_does_not_import_t0_store(self):
        tree = ast.parse((BRIDGE / "context.py").read_text(encoding="utf-8"))
        imports = [n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "market_data.store"]
        self.assertEqual(imports, [], "T2 context still imports market_data.store")

    def test_context_does_not_call_t0_read_window(self):
        tree = ast.parse((BRIDGE / "context.py").read_text(encoding="utf-8"))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "read_window"]
        self.assertEqual(calls, [], "T2 context still calls direct SQLite read_window")

    def test_strategy_does_not_accept_canonical_db_path(self):
        source = (BRIDGE / "ChartProFreqaiResearch.py").read_text(encoding="utf-8")
        self.assertNotIn("canonical_db_path", source)

    def test_strategy_calls_context_without_database_arguments(self):
        tree = ast.parse((BRIDGE / "ChartProFreqaiResearch.py").read_text(encoding="utf-8"))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "canonical_context"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].args, [], "T2 context must not receive a database path")
        self.assertNotIn("database", {kw.arg for kw in calls[0].keywords})

    def test_http_unavailable_has_no_sqlite_cache_or_venue_fallback(self):
        source = (BRIDGE / "context.py").read_text(encoding="utf-8")
        strategy = (BRIDGE / "ChartProFreqaiResearch.py").read_text(encoding="utf-8")
        self.assertNotIn("market_data.store", source)
        self.assertNotIn("canonical_db_path", strategy)
        self.assertNotIn("sqlite", source.lower())



if __name__ == "__main__":
    unittest.main()
