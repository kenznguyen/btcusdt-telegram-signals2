from pathlib import Path
import subprocess
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class CiPolicyTest(unittest.TestCase):
    def setUp(self):
        self.workflows = yaml.safe_load((ROOT / "codemagic.yaml").read_text())["workflows"]

    def test_github_has_no_active_actions_workflows(self):
        workflows = ROOT / ".github/workflows"
        self.assertFalse(list(workflows.glob("*.yml")) + list(workflows.glob("*.yaml")))
        self.assertTrue((ROOT / "ci/archive/github-actions/market-data-ci.yml").exists())

    def test_manual_stateful_and_release_tasks_never_start_on_push(self):
        for name in ("android-chart-pro-release", "signal-scan", "telegram-command", "dashboard-backtest"):
            with self.subTest(name=name):
                self.assertNotIn("triggering", self.workflows[name])

    def test_data_checks_keep_dependency_import_tests_and_cli_gates(self):
        data = self.workflows["canonical-market-data"]
        self.assertIn("push", data["triggering"]["events"])
        commands = "\n".join(item["script"] for item in data["scripts"])
        for gate in ("requirements-market-data.txt", "requirements-web.txt", "requirements-ci.txt",
                     "import ccxt", "import app", "market_data.test_store", "market_data.test_sync",
                     "market_data.test_api", "-s integrations", "-s ci", "market_data.sync --help"):
            with self.subTest(gate=gate):
                self.assertIn(gate, commands)

    def test_android_debug_keeps_unit_tests_and_apk_gate(self):
        workflow = self.workflows["android-chart-pro-debug"]
        self.assertIn("push", workflow["triggering"]["events"])
        self.assertIn(
            {"pattern": "feature/android-five-layer-control", "include": True, "source": True},
            workflow["triggering"]["branch_patterns"],
        )
        self.assertIn("android-app/", workflow["when"]["changeset"]["includes"])
        commands = "\n".join(item["script"] for item in workflow["scripts"])
        self.assertIn(":app:testDebugUnitTest", commands)
        self.assertIn(":app:assembleDebug", commands)
        self.assertIn(":app:testParallelUnitTest", commands)
        self.assertIn(":app:assembleParallel", commands)
        self.assertIn("ci.test_android_apks", commands)
        self.assertIn("ci/verify-android-apks.py", commands)
        self.assertIn("ci/setup-android.sh", commands)
        self.assertIn("android-source-sha.txt", workflow["artifacts"])
        self.assertIn("android-apks.json", workflow["artifacts"])
        self.assertIn("artifacts/BTC-5-Tang-Paper-*.apk", workflow["artifacts"])

    def test_shell_scripts_parse_and_no_unsupported_python_version_key(self):
        for path in (ROOT / "ci").glob("*.sh"):
            subprocess.run(["bash", "-n", str(path)], check=True)
        for name, workflow in self.workflows.items():
            with self.subTest(name=name):
                self.assertNotIn("python", workflow.get("environment", {}))


if __name__ == "__main__":
    unittest.main()
