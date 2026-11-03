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
            "t0-manual-validation.yml",
            "p5-3-11-g2-integration-red.yml",
            "p5-3-11-g2-integration-green.yml",
            "p5-4-1-post-merge-validation.yml",
        }

        self.assertIn("p5-3-10-4-g1-red-execution.yml", actual)
        self.assertIn("p5-3-11-5-g2-red-validation.yml", actual)
        self.assertLessEqual(actual, approved)
        self.assertTrue((ROOT / "ci/archive/github-actions/market-data-ci.yml").exists())

    def test_p5_4_1_orchestrator_is_allowlisted_and_fail_closed(self):
        path = ROOT / ".github/workflows/p5-4-1-post-merge-validation.yml"
        self.assertTrue(path.is_file())
        workflow = yaml.safe_load(path.read_text())
        self.assertIn("workflow_dispatch", workflow["on"])
        self.assertIn("pull_request", workflow["on"])
        self.assertIn("push", workflow["on"])
        self.assertIn("feature/p5-2-5-green-contracts-20261102", workflow["on"]["push"]["branches"])
        self.assertIn("ci/test_ci_policy.py", workflow["on"]["pull_request"]["paths"])
        self.assertEqual(workflow["permissions"]["contents"], "read")
        jobs = workflow["jobs"]
        self.assertEqual(set(jobs), {"preflight", "t0", "g1", "g2", "publish"})
        self.assertEqual(jobs["t0"]["uses"], "./.github/workflows/t0-validation.yml")
        self.assertEqual(jobs["g1"]["uses"], "./.github/workflows/p5-3-10-5-g1-green-validation.yml")
        self.assertEqual(jobs["g2"]["uses"], "./.github/workflows/p5-3-11-g2-integration-green.yml")
        preflight = jobs["preflight"]["steps"]
        source_guard = next(step for step in preflight if step.get("name") == "Enforce exact SHA and no-runtime boundary")
        self.assertIn("EXPECTED_SHA", source_guard["env"])
        self.assertIn("AI_EXECUTION_ENABLED", source_guard["run"])
        self.assertIn("test \"$AI_EXECUTION_ENABLED\" = \"false\"", source_guard["run"])
        publish = jobs["publish"]
        self.assertEqual(set(publish["needs"]), {"preflight", "t0", "g1", "g2"})
        publish_run = next(step["run"] for step in publish["steps"] if step.get("name") == "Verify all suites and source identities")
        self.assertIn("T0_RESULT", publish_run)
        self.assertIn("G1_RESULT", publish_run)
        self.assertIn("G2_RESULT", publish_run)
        self.assertIn("test \"$actual\" = \"$EXPECTED_SHA\"", publish_run)

    def test_g2_red_contract_is_not_configured_in_codemagic(self):
        self.assertNotIn("p5-3-11-5-g2-red-tests", self.workflows)


    def test_g2_acceptance_is_github_actions_only_and_historical_red_is_manual(self):
        green = (ROOT / ".github/workflows/p5-3-11-g2-integration-green.yml").read_text()
        red = (ROOT / ".github/workflows/p5-3-11-g2-integration-red.yml").read_text()
        self.assertIn("permissions:\n  contents: read", green)
        self.assertIn("ref: ${{ github.event.pull_request.head.sha || github.sha }}", green)
        self.assertIn("persist-credentials: false", green)
        self.assertIn("integration/p5-3-11-g2-gateway-green-20261103", green)
        self.assertIn(
            "branches:\n      - feature/p5-3-11-5-g2-red-tests-20261103\n      - integration/p5-3-11-g2-gateway-green-20261103",
            green,
        )
        self.assertIn("workflow_dispatch:", green)
        self.assertIn("market_data.test_g2_writer_routing", green)
        self.assertIn("market_data.test_feeder_lease", green)
        self.assertIn("market_data.test_feeder_atomic_fencing", green)
        self.assertIn("market_data.test_feeder_lifecycle", green)
        self.assertIn("g2-feeder-routing-tests.log", green)
        self.assertNotIn("p5-3-11-g2-gateway-green-acceptance", self.workflows)

        data = self.workflows["canonical-market-data"]
        branch_patterns = {item["pattern"] for item in data["triggering"]["branch_patterns"]}
        self.assertNotIn("integration/p5-3-11-g2-gateway-green-20261103", branch_patterns)
        commands = "\n".join(item["script"] for item in data["scripts"])
        self.assertNotIn("market_data.test_g2_writer_routing", commands)
        self.assertNotIn("g2-feeder-routing-tests.log", commands)
        self.assertNotIn("g2-feeder-routing-tests.log", data["artifacts"])

        readme = (ROOT / "market_data/README.md").read_text()
        self.assertIn("GitHub Actions là cổng CI/acceptance duy nhất", readme)
        self.assertIn("Codemagic không được dùng để chạy, chạy lại hoặc nghiệm thu PR #125/G2", readme)
        self.assertNotIn("Codemagic là gate CI/acceptance mặc định", readme)
        self.assertIn("workflow_dispatch:", red)
        self.assertNotIn("  push:", red)



    def test_t0_ci_is_migrated_to_github_actions(self):
        workflow_path = ROOT / ".github/workflows/t0-validation.yml"
        manual_path = ROOT / ".github/workflows/t0-manual-validation.yml"
        self.assertTrue(workflow_path.is_file())
        self.assertTrue(manual_path.is_file())
        workflow = yaml.safe_load(workflow_path.read_text())
        manual = yaml.safe_load(manual_path.read_text())
        self.assertEqual(set(workflow["jobs"]), {"t0-validation"})
        self.assertIn("push", workflow["on"])
        self.assertIn("pull_request", workflow["on"])
        self.assertIn("integration/p5-3-11-g2-gateway-green-20261103",
                      workflow["on"]["pull_request"]["branches"])
        atomic_step = next(
            step for step in workflow["jobs"]["t0-validation"]["steps"]
            if step.get("name") == "Run atomic fencing and prior T0 contracts"
        )
        self.assertIn('grep -q "Ran 100 tests"', atomic_step.get("run", ""))
        self.assertNotIn('grep -q "Ran 99 tests"', atomic_step.get("run", ""))
        audit_source = (ROOT / "ci/t0_operational_contract.py").read_text()
        health_step = next(
            step for step in workflow["jobs"]["t0-validation"]["steps"]
            if step.get("name") == "Run runtime health API and T0 regression contracts"
        )
        self.assertIn('grep -q "Ran 107 tests"', health_step.get("run", ""))
        self.assertNotIn('grep -q "Ran 106 tests"', health_step.get("run", ""))
        self.assertIn('health_runtime_api_count": \'grep -q "Ran 107 tests"\'', audit_source)
        sigkill_step = next(
            step for step in workflow["jobs"]["t0-validation"]["steps"]
            if step.get("name") == "Run isolated SQLite SIGKILL recovery contracts"
        )
        self.assertIn('grep -q "Ran 101 tests"', sigkill_step.get("run", ""))
        self.assertNotIn('grep -q "Ran 100 tests"', sigkill_step.get("run", ""))
        self.assertIn('sigkill_recovery_count": \'grep -q "Ran 101 tests"\'', audit_source)
        audit_source = (ROOT / "ci/t0_operational_contract.py").read_text()
        self.assertIn('atomic_fencing_count": \'grep -q "Ran 100 tests"\'', audit_source)
        self.assertIn("workflow_dispatch", manual["on"])
        self.assertEqual(manual["permissions"]["contents"], "read")
        self.assertNotIn("MARKET_DATA_TEST_DATABASE_URL", manual["jobs"]["manual-gate"].get("env", {}))
        timescale_step = next(
            step for step in manual["jobs"]["manual-gate"]["steps"]
            if step.get("name") == "Run disposable TimescaleDB integration tests"
        )
        self.assertIn("MARKET_DATA_TEST_DATABASE_URL", timescale_step.get("env", {}))
        self.assertIn("github.event.pull_request.head.sha || github.sha",
                      workflow["jobs"]["t0-validation"]["steps"][0]["with"]["ref"])
        isolated_env = workflow["jobs"]["t0-validation"]["env"]
        for key in ("MARKET_DATA_DB", "T0_FEEDER_LEASE_DB", "PAPER_DB",
                    "BINANCE_API_KEY", "BINANCE_API_SECRET", "OKX_API_KEY", "OKX_API_SECRET"):
            with self.subTest(environment_key=key):
                self.assertEqual(isolated_env[key], "")
        commands = "\n".join(step.get("run", "") for step in workflow["jobs"]["t0-validation"]["steps"])
        required = ("market_data.test_store", "market_data.test_storage", "market_data.test_sync",
                    "market_data.test_api", "market_data.test_gateway_runtime", "market_data.test_feeder_lease",
                    "market_data.test_feeder_health", "market_data.test_feeder_lifecycle",
                    "market_data.test_feeder_atomic_fencing", "market_data.test_feeder_health_runtime_api",
                    "market_data.test_feeder_sigkill_recovery", "ci.test_t0_operational_contract",
                    "ci.test_t0_data_integrity")
        for module in required:
            with self.subTest(module=module):
                self.assertIn(module, commands)
        options = manual["on"]["workflow_dispatch"]["inputs"]["gate"]["options"]
        for gate in ("final-runtime-config", "component-tests-p3", "kraken-adapter",
                     "kraken-spot-sqlite", "kraken-spot-read-api", "timescaledb-integration"):
            with self.subTest(gate=gate):
                self.assertIn(gate, options)

    def test_timescaledb_runner_is_provider_neutral(self):
        script = (ROOT / "ci/test-timescaledb.sh").read_text()
        self.assertIn("MARKET_DATA_TEST_DATABASE_URL", script)
        self.assertIn("CI_PYTHON", script)
        self.assertNotIn("CM_BUILD_DIR", script)
        self.assertNotIn("CODEMAGIC", script)

    def test_t0_executable_workflows_are_removed_from_codemagic(self):
        retired = {
            "market-data-timescaledb", "market-data-kraken-adapter-tests",
            "market-data-kraken-spot-sqlite-tests", "market-data-kraken-spot-read-api",
            "t0-feeder-scheduler", "t0-feeder-health", "t0-feeder-lifecycle",
            "t0-feeder-atomic-fencing", "t0-health-runtime-api", "t0-feeder-sigkill-recovery",
            "t0-operational-contract-release-gate", "t0-data-integrity-candle-continuity-gate",
            "t0-final-runtime-configuration-check", "t0-component-tests-p3",
            "t0-feeder-lifecycle-red", "t0-feeder-atomic-fencing-red",
            "p5-2-4-shadow-migration-red", "p5-2-5-runtime-red-validation", "p5-3-11-5-g2-red-tests",
        }
        self.assertTrue(retired.isdisjoint(set(self.workflows)))
        commands = "\n".join(item["script"] for item in self.workflows["canonical-market-data"]["scripts"])
        for module in ("market_data.test_store", "market_data.test_storage", "market_data.test_sync",
                       "market_data.test_api", "market_data.test_gateway_runtime"):
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
                     "-s integrations", "ci.test_legacy_runner"):
            with self.subTest(gate=gate):
                self.assertIn(gate, commands)
        for t0_only in ("import ccxt", "import app", "market_data.sync --help", "compileall -q market_data"):
            self.assertNotIn(t0_only, commands)
        t0_workflow = yaml.safe_load((ROOT / ".github/workflows/t0-validation.yml").read_text())
        t0_commands = "\n".join(step.get("run", "") for step in t0_workflow["jobs"]["t0-validation"]["steps"])
        for module in ("market_data.test_store", "market_data.test_storage", "market_data.test_sync",
                       "market_data.test_api", "market_data.test_gateway_runtime"):
            self.assertIn(module, t0_commands)
        for t0_command in ("import ccxt", "import app", "market_data.sync --help", "compileall -q market_data"):
            self.assertIn(t0_command, t0_commands)

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
