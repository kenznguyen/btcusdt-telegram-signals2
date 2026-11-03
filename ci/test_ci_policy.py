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
            "p5-4-10-backup-restore-fixture.yml",
            "android-release-pair.yml",
        }

        self.assertIn("p5-3-10-4-g1-red-execution.yml", actual)
        self.assertIn("p5-3-11-5-g2-red-validation.yml", actual)
        self.assertLessEqual(actual, approved)
        self.assertTrue((ROOT / "ci/archive/github-actions/market-data-ci.yml").exists())

    def test_p5_4_1_orchestrator_is_allowlisted_and_fail_closed(self):
        path = ROOT / ".github/workflows/p5-4-1-post-merge-validation.yml"
        self.assertTrue(path.is_file())
        workflow = yaml.safe_load(path.read_text())
        self.assertEqual(set(workflow["on"]), {"push", "workflow_dispatch"})
        self.assertEqual(
            workflow["on"]["push"]["branches"],
            ["feature/p5-4-1-post-merge-validation-20261103"],
        )
        self.assertTrue({
            "market_data/**", "ci/**", "pipeline/**", "freqai_bridge/**",
            "app.py", "requirements*.txt", ".github/workflows/**",
        }.issubset(set(workflow["on"]["push"]["paths"])))
        self.assertNotIn("pull_request", workflow["on"])
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


    def test_p5_4_10_backup_restore_workflow_is_allowlisted_and_fixture_only(self):
        path = ROOT / ".github/workflows/p5-4-10-backup-restore-fixture.yml"
        self.assertTrue(path.is_file())
        workflow = yaml.safe_load(path.read_text())
        self.assertIn("push", workflow["on"])
        self.assertIn("workflow_dispatch", workflow["on"])
        self.assertEqual(workflow["permissions"]["contents"], "read")
        self.assertEqual(set(workflow["jobs"]), {"fixture-only"})
        job = workflow["jobs"]["fixture-only"]
        env = job["env"]
        self.assertEqual(env["AI_EXECUTION_ENABLED"], "false")
        for key in ("MARKET_DATA_DB", "T0_FEEDER_LEASE_DB", "PAPER_DB",
                    "PAPER_TRADING_DB", "BINANCE_API_KEY", "BINANCE_API_SECRET",
                    "OKX_API_KEY", "OKX_API_SECRET", "MARKET_DATA_POSTGRES_DSN",
                    "MARKET_DATA_TOKEN", "MARKET_DATA_BACKEND"):
            with self.subTest(environment_key=key):
                self.assertEqual(env[key], "")
        steps = job["steps"]
        checkout = next(step for step in steps if step.get("name") == "Checkout exact event commit")
        self.assertEqual(checkout["with"]["ref"], "${{ github.sha }}")
        self.assertFalse(checkout["with"]["persist-credentials"])
        guard = next(step for step in steps if step.get("name") == "Verify source identity and execution boundary")
        self.assertIn('test "$actual" = "$GITHUB_SHA"', guard["run"])
        self.assertIn("AI_EXECUTION_ENABLED", guard["run"])
        runner = next(step for step in steps if step.get("name") == "Run fixture-only Backup and Restore tests")
        self.assertIn("ci/run_backup_restore_tests.py", runner["run"])
        upload = next(step for step in steps if step.get("name") == "Upload test logs and machine-readable evidence")
        self.assertTrue(upload["if"].startswith("always()"))
        self.assertIn("backup-restore-evidence/**", upload["with"]["path"])

    def test_g2_red_contract_is_not_configured_in_codemagic(self):
        self.assertNotIn("p5-3-11-5-g2-red-tests", self.workflows)


    def test_g2_acceptance_is_github_actions_only_and_historical_red_is_manual(self):
        green = (ROOT / ".github/workflows/p5-3-11-g2-integration-green.yml").read_text()
        red = (ROOT / ".github/workflows/p5-3-11-g2-integration-red.yml").read_text()
        self.assertIn("permissions:\n  contents: read", green)
        self.assertIn("ref: ${{ github.event.pull_request.head.sha || github.sha }}", green)
        self.assertIn("persist-credentials: false", green)
        green_workflow = yaml.safe_load(green)
        green_triggers = green_workflow.get("on", green_workflow.get(True, {}))
        self.assertIn("workflow_call", green_triggers)
        self.assertIn("workflow_dispatch", green_triggers)
        self.assertNotIn("push", green_triggers)
        self.assertNotIn("pull_request", green_triggers)
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
        self.assertIn("workflow_call", workflow["on"])
        self.assertIn("push", workflow["on"])
        self.assertEqual(
            workflow["on"]["push"]["branches"],
            [
                "feature/t0-operational-contract-release-gate-20261102",
                "feature/p5-4-1-post-merge-validation-20261103",
            ],
        )
        self.assertNotIn("pull_request", workflow["on"])
        self.assertIn("ci/**", workflow["on"]["push"]["paths"])
        self.assertIn(".github/workflows/t0-validation.yml", workflow["on"]["push"]["paths"])
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

    def test_manual_stateful_tasks_never_start_on_push(self):
        for name in ("signal-scan", "telegram-command", "dashboard-backtest"):
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

    def test_obsolete_android_apk_build_workflows_are_retired(self):
        self.assertNotIn("android-chart-pro-debug", self.workflows)
        self.assertNotIn("android-chart-pro-release", self.workflows)
        serialized = (ROOT / "codemagic.yaml").read_text()
        for retired in ("android-chart-pro-debug:", "android-chart-pro-release:",
                        ":app:assembleDebug", ":app:assembleParallel", "ci/release-android.sh"):
            with self.subTest(retired=retired):
                self.assertNotIn(retired, serialized)

    def test_github_actions_never_build_or_publish_android_apks(self):
        workflows = ROOT / ".github/workflows"
        forbidden = (
            ":app:assembleDebug",
            ":app:assembleRelease",
            ":app:assembleParallel",
            "ci/setup-android.sh",
            "ci/release-android.sh",
            "android-app/app/build/outputs/apk",
            "artifacts/BTC-5-Tang-Paper-*.apk",
        )
        for path in sorted((*workflows.glob("*.yml"), *workflows.glob("*.yaml"))):
            if path.name == "android-release-pair.yml":
                continue
            content = path.read_text()
            for token in forbidden:
                with self.subTest(workflow=path.name, token=token):
                    self.assertNotIn(token, content)

    def test_android_release_pair_is_manual_pinned_and_release_signed(self):
        workflow_path = ROOT / ".github/workflows/android-release-pair.yml"
        self.assertTrue(workflow_path.is_file())
        workflow = yaml.safe_load(workflow_path.read_text())
        triggers = workflow.get("on", workflow.get(True, {}))
        self.assertEqual(set(triggers), {"workflow_dispatch"})
        source_input = triggers["workflow_dispatch"]["inputs"]["source_sha"]
        self.assertTrue(source_input["required"])
        self.assertEqual(source_input["type"], "string")
        self.assertEqual(workflow["permissions"]["contents"], "read")
        self.assertEqual(set(workflow["jobs"]), {"release-pair"})
        job = workflow["jobs"]["release-pair"]
        self.assertEqual(job["env"]["AI_EXECUTION_ENABLED"], "false")
        checkout = next(step for step in job["steps"] if step.get("name") == "Checkout exact selected commit")
        self.assertEqual(checkout["with"]["ref"], "${{ github.sha }}")
        self.assertFalse(checkout["with"]["persist-credentials"])
        guard = next(step for step in job["steps"] if step.get("name", "").startswith("Enforce branch"))
        self.assertIn('test "$INPUT_SOURCE_SHA" = "$GITHUB_SHA"', guard["run"])
        self.assertIn('test "$ANDROID_KEY_ALIAS" = "btc-chart-release"', guard["run"])
        for secret in ("ANDROID_KEYSTORE_BASE64", "ANDROID_KEYSTORE_PASSWORD", "ANDROID_KEY_ALIAS", "ANDROID_KEY_PASSWORD"):
            self.assertIn(secret, job["env"])
            self.assertIn(secret, guard["run"])
        build = next(step for step in job["steps"] if step.get("name", "").startswith("Build regular release"))
        self.assertIn(":app:assembleRelease", build["run"])
        self.assertIn(":app:assembleParallel", build["run"])
        verify = next(step for step in job["steps"] if step.get("name", "").startswith("Verify both APK"))
        self.assertIn("ci/verify-android-release-pair.py", verify["run"])
        upload = next(step for step in job["steps"] if step.get("name", "").startswith("Upload paired"))
        self.assertIn("app-release.apk", upload["with"]["path"])
        self.assertIn("app-parallel.apk", upload["with"]["path"])
        self.assertIn("android-release-pair.json", upload["with"]["path"])
        gradle = (ROOT / "android-app/app/build.gradle.kts").read_text()
        parallel = gradle.split('create("parallel") {', 1)[1].split("\n        }", 1)[0]
        self.assertIn('signingConfig = signingConfigs.getByName("release")', parallel)

    def test_shell_scripts_parse_and_no_unsupported_python_version_key(self):
        for path in (ROOT / "ci").glob("*.sh"):
            subprocess.run(["bash", "-n", str(path)], check=True)
        for name, workflow in self.workflows.items():
            with self.subTest(name=name):
                self.assertNotIn("python", workflow.get("environment", {}))


if __name__ == "__main__":
    unittest.main()
