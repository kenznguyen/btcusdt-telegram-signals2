from pathlib import Path
import subprocess
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class CiPolicyTest(unittest.TestCase):
    def setUp(self):
        self.workflows = yaml.safe_load((ROOT / "codemagic.yaml").read_text())["workflows"]

    def test_github_actions_workflows_are_explicitly_allowlisted(self):
        workflows = ROOT / ".github/workflows"
        actual = {
            path.name
            for pattern in ("*.yml", "*.yaml")
            for path in workflows.glob(pattern)
        }
        approved = {
            "p5-3-10-4-g1-red-execution.yml",
            "p5-3-10-5-g1-green-validation.yml",
            "p5-3-11-5-g2-red-validation.yml",
            "t0-validation.yml",
        }

        self.assertIn("p5-3-10-4-g1-red-execution.yml", actual)
        self.assertIn("p5-3-11-5-g2-red-validation.yml", actual)
        self.assertLessEqual(actual, approved)
        self.assertTrue((ROOT / "ci/archive/github-actions/market-data-ci.yml").exists())

    def test_g2_red_contract_is_not_configured_in_codemagic(self):
        self.assertNotIn("p5-3-11-5-g2-red-tests", self.workflows)


    def test_t0_ci_is_migrated_to_github_actions(self):
        workflow_path = ROOT / ".github/workflows/t0-validation.yml"
        self.assertTrue(workflow_path.is_file())
        workflow = yaml.safe_load(workflow_path.read_text())
        jobs = workflow["jobs"]
        required_jobs = {
            "market-data-core",
            "feeder-scheduler",
            "feeder-health",
            "feeder-lifecycle",
            "atomic-fencing",
            "health-runtime-api",
            "sigkill-recovery",
            "operational-contract",
            "data-integrity",
            "final-runtime-config",
            "component-tests-p3",
            "kraken-adapter",
            "kraken-spot-sqlite",
            "kraken-spot-read-api",
            "timescaledb-integration",
        }
        self.assertLessEqual(required_jobs, set(jobs))
        self.assertIn("workflow_dispatch", workflow["on"])
        self.assertIn("push", workflow["on"])
        self.assertTrue(workflow.get("permissions", {}).get("contents") == "read")

    def test_t0_executable_workflows_are_removed_from_codemagic(self):
        retired = {
            "market-data-timescaledb",
            "market-data-kraken-adapter-tests",
            "market-data-kraken-spot-sqlite-tests",
            "market-data-kraken-spot-read-api",
            "t0-feeder-scheduler",
            "t0-feeder-health",
            "t0-feeder-lifecycle",
            "t0-feeder-atomic-fencing",
            "t0-health-runtime-api",
            "t0-feeder-sigkill-recovery",
            "t0-operational-contract-release-gate",
            "t0-data-integrity-candle-continuity-gate",
            "t0-final-runtime-configuration-check",
            "t0-component-tests-p3",
            "t0-feeder-lifecycle-red",
            "t0-feeder-atomic-fencing-red",
        }
        self.assertTrue(retired.isdisjoint(set(self.workflows)))
        canonical = self.workflows["canonical-market-data"]
        commands = "\\n".join(item["script"] for item in canonical["scripts"])
        for module in (
            "market_data.test_store",
            "market_data.test_storage",
            "market_data.test_sync",
            "market_data.test_api",
            "market_data.test_gateway_runtime",
        ):
            self.assertNotIn(module, commands)

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
