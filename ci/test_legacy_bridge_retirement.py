from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]

RETIRED_PATHS = (
    "app.py",
    "telegram_commands.py",
    "integrations/codemagic_client.py",
    "integrations/test_codemagic_client.py",
    "dashboard/index.html",
    ".github/backtest-trigger.txt",
    "ci/archive/github-actions/signal-scan.yml",
    "ci/archive/github-actions/telegram-command.yml",
    "ci/archive/github-actions/dashboard-backtest.yml",
    "docs/market-data-timescaledb-codemagic.md",
)


class LegacyBridgeRetirementTest(unittest.TestCase):
    def test_legacy_runtime_and_dispatch_files_are_removed(self):
        present = [path for path in RETIRED_PATHS if (ROOT / path).exists()]
        self.assertEqual([], present, f"Retired legacy files remain: {present}")

    def test_strategy_research_library_is_preserved_without_messaging(self):
        strategy = (ROOT / "bot.py").read_text()
        backtest = (ROOT / "backtest.py").read_text()
        for symbol in ("def add_indicators(", "def entry_signals(", "def dca_signal(", "def roe_for("):
            self.assertIn(symbol, strategy)
        self.assertNotIn("telegram", strategy.lower())
        self.assertNotIn("telegram", backtest.lower())
        self.assertNotIn("codemagic", backtest.lower())
        self.assertNotIn("dashboard", backtest.lower())

    def test_five_layer_api_and_t4_rebuild_target_are_preserved(self):
        for path in (
            "market_data/api.py",
            "pipeline/api.py",
            "integrations/hummingbot_bridge.py",
            "integrations/test_hummingbot_bridge.py",
            "control_dashboard/package.json",
            "control_dashboard/package-lock.json",
            "control_dashboard/src/App.jsx",
        ):
            self.assertTrue((ROOT / path).is_file(), f"Five-layer component missing: {path}")

    def test_no_codm_or_telegram_runtime_dependency_in_current_server_docs(self):
        for path in (
            "README.md",
            "docs/REPOSITORY_MAINTENANCE.md",
            "docs/market-data-timescaledb-test.md",
            "integrations/README.md",
            "ci/archive/github-actions/README.md",
        ):
            content = (ROOT / path).read_text().lower()
            self.assertNotIn("codemagic", content, f"Stale Codemagic reference in {path}")
            self.assertNotIn("telegram webhook", content, f"Stale webhook reference in {path}")

    def test_old_flask_dependencies_are_not_required(self):
        requirements = (ROOT / "requirements.txt").read_text().lower()
        web_requirements = (ROOT / "requirements-web.txt").read_text().lower()
        self.assertNotIn("flask", requirements)
        self.assertNotIn("flask", web_requirements)
        self.assertIn("gunicorn", web_requirements)


if __name__ == "__main__":
    unittest.main()
