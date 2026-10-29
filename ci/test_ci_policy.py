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
        for name in ("android-chart-pro-release", "signal-scan", "telegram-command", "dashboard-backtest", "local-data-lake-smoke"):
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

    def test_data_lake_requires_real_postgres_and_feather_dependencies(self):
        workflow = self.workflows["data-lake-postgres"]
        self.assertIn("push", workflow["triggering"]["events"])
        commands = "\n".join(item["script"] for item in workflow["scripts"])
        self.assertIn("requirements-data-lake.txt", commands)
        self.assertIn("requirements-data-lake-export.txt", commands)
        self.assertIn("ci/test-data-lake.sh", commands)
        self.assertIn("postgres-server.log", workflow["artifacts"])
        runner = (ROOT / "ci/test-data-lake.sh").read_text()
        for gate in ("import psycopg, pyarrow, pandas", "initdb", "DATA_LAKE_REQUIRE_POSTGRES=1",
                     "market_data.test_postgres", "-s data_lake", "trap cleanup_lake_postgres EXIT",
                     "postgres-server.log", "Data-lake CI failed during:"):
            with self.subTest(gate=gate):
                self.assertIn(gate, runner)

    def test_local_trial_branch_keeps_postgres_and_regression_jobs(self):
        for name in ("canonical-market-data", "data-lake-postgres"):
            with self.subTest(name=name):
                workflow = self.workflows[name]
                self.assertIn(
                    {"pattern": "feature/local-data-lake", "include": True, "source": True},
                    workflow["triggering"]["branch_patterns"],
                )
                self.assertIn("deploy/data-lake/", workflow["when"]["changeset"]["includes"])
                self.assertIn(".dockerignore", workflow["when"]["changeset"]["includes"])

    def test_docker_smoke_is_manual_and_preserves_trial_boundaries(self):
        workflow = self.workflows["local-data-lake-smoke"]
        self.assertEqual(workflow["instance_type"], "linux_x2")
        self.assertLessEqual(workflow["max_build_duration"], 30)
        self.assertIn("local-smoke-tests.log", workflow["artifacts"])
        self.assertFalse(any(".env" in name or "secret" in name.lower() for name in workflow["artifacts"]))
        runner = (ROOT / "ci/test-local-data-lake.sh").read_text()
        for gate in ("python3 -m data_lake.local_trial", "--project-name chart-lake-smoke",
                     "--wait-seconds 120", "report['api']['freshData'] is False",
                     "report['dataRequested'] is False", "report['ok'] is True",
                     "'collector' not in services", "error.code == 401", "down --remove-orphans",
                     "export DOCKER_HOST=unix:///var/run/docker.sock", 'docker --host "$DOCKER_HOST" compose',
                     "unset DOCKER_CONTEXT DOCKER_TLS DOCKER_TLS_VERIFY DOCKER_CERT_PATH COMPOSE_PROFILES",
                     "[ -f .data/local-lake.env ] && [ ! -L .data/local-lake.env ]"):
            with self.subTest(gate=gate):
                self.assertIn(gate, runner)
        self.assertNotIn("--profile collector", runner)
        self.assertNotIn("--load-candles", runner)
        self.assertNotIn("down -v", runner)

    def test_shell_scripts_parse_and_no_unsupported_python_version_key(self):
        for path in (ROOT / "ci").glob("*.sh"):
            subprocess.run(["bash", "-n", str(path)], check=True)
        for name, workflow in self.workflows.items():
            with self.subTest(name=name):
                self.assertNotIn("python", workflow.get("environment", {}))


if __name__ == "__main__":
    unittest.main()
