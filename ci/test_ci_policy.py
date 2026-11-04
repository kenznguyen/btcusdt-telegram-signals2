from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
APPROVED_WORKFLOWS = {
    "android-release-pair.yml",
    "android-t0-foundation-github-actions.yml",
    "android-t0-foundation.yml",
    "control-dashboard.yml",
    "cross-layer-integration.yml",
    "freqai-strategy-smoke.yml",
    "p5-3-10-4-g1-red-execution.yml",
    "p5-3-10-5-g1-green-validation.yml",
    "p5-3-11-5-g2-red-validation.yml",
    "p5-3-11-g2-integration-green.yml",
    "p5-3-11-g2-integration-red.yml",
    "p5-4-1-post-merge-validation.yml",
    "p5-4-10-backup-restore-fixture.yml",
    "t0-9-art-jni-runtime.yml",
    "t0-health-api-boundary.yml",
    "t0-manual-validation.yml",
    "t0-validation.yml",
}


def load_workflow(name):
    data = yaml.safe_load((WORKFLOWS / name).read_text())
    return data.get("on", data.get(True, {})), data


class CiPolicyTest(unittest.TestCase):
    def test_github_actions_workflows_are_explicitly_allowlisted(self):
        actual = {path.name for path in WORKFLOWS.glob("*.y*ml")}
        self.assertEqual(actual, APPROVED_WORKFLOWS)
        self.assertTrue((ROOT / "ci/archive/github-actions/README.md").is_file())

    def test_legacy_runner_configuration_and_workflows_are_removed(self):
        self.assertFalse((ROOT / "codemagic.yaml").exists())
        self.assertFalse((ROOT / "docs/CODEMAGIC_SETUP.md").exists())
        self.assertFalse((ROOT / "ci/archive/github-actions/dashboard-backtest.yml").exists())
        self.assertFalse((ROOT / "ci/archive/github-actions/telegram-command.yml").exists())
        self.assertTrue((ROOT / "docs/GITHUB_ACTIONS.md").is_file())

    def test_t0_health_api_boundary_is_pr_scoped_and_exact_sha(self):
        triggers, workflow = load_workflow("t0-health-api-boundary.yml")
        self.assertEqual(set(triggers), {"pull_request"})
        self.assertEqual(triggers["pull_request"]["branches"], ["feature/p5-4-1-post-merge-validation-20261103"])
        self.assertEqual(workflow["permissions"]["contents"], "read")
        job = workflow["jobs"]["health-api-contract"]
        self.assertEqual(job["env"]["AI_EXECUTION_ENABLED"], "false")
        checkout = next(step for step in job["steps"] if step.get("name") == "Checkout exact PR source SHA")
        self.assertEqual(checkout["with"]["ref"], "${{ github.event.pull_request.head.sha }}")
        self.assertFalse(checkout["with"]["persist-credentials"])
        test = next(step for step in job["steps"] if step.get("name") == "Run T0 health API and app-surface contracts")
        self.assertIn("market_data.test_app_surface", test["run"])
        self.assertIn("market_data.test_feeder_health_runtime_api", test["run"])

    def test_p5_4_1_orchestrator_requires_t0_g1_g2_and_common_sha(self):
        triggers, workflow = load_workflow("p5-4-1-post-merge-validation.yml")
        self.assertEqual(set(triggers), {"push", "workflow_dispatch"})
        self.assertEqual(set(workflow["jobs"]), {"preflight", "t0", "g1", "g2", "publish"})
        jobs = workflow["jobs"]
        self.assertEqual(jobs["t0"]["uses"], "./.github/workflows/t0-validation.yml")
        self.assertEqual(jobs["g1"]["uses"], "./.github/workflows/p5-3-10-5-g1-green-validation.yml")
        self.assertEqual(jobs["g2"]["uses"], "./.github/workflows/p5-3-11-g2-integration-green.yml")
        self.assertEqual(set(jobs["publish"]["needs"]), {"preflight", "t0", "g1", "g2"})

    def test_dashboard_workflow_pins_toolchain_and_runs_all_gates(self):
        triggers, workflow = load_workflow("control-dashboard.yml")
        self.assertIn("pull_request", triggers)
        self.assertIn("push", triggers)
        job = workflow["jobs"]["dashboard"]
        self.assertEqual(workflow["permissions"]["contents"], "read")
        commands = "
".join(step.get("run", "") for step in job["steps"])
        for command in ("npm@11.9.0", "npm ci --ignore-scripts", "npm test", "npm run build", "npm audit --audit-level=high"):
            self.assertIn(command, commands)
        checkout = next(step for step in job["steps"] if step.get("name") == "Checkout exact source SHA")
        self.assertFalse(checkout["with"]["persist-credentials"])

    def test_cross_layer_workflow_runs_isolated_paper_only_tests(self):
        triggers, workflow = load_workflow("cross-layer-integration.yml")
        self.assertIn("pull_request", triggers)
        job = workflow["jobs"]["isolated-tests"]
        self.assertEqual(job["env"]["AI_EXECUTION_ENABLED"], "false")
        for key in ("MARKET_DATA_DB", "T0_FEEDER_LEASE_DB", "PAPER_DB", "BINANCE_API_KEY", "OKX_API_KEY"):
            self.assertEqual(job["env"][key], "")
        commands = "
".join(step.get("run", "") for step in job["steps"])
        for module in ("integrations", "futures_intelligence.test_import_collector", "pipeline.test_decision",
                       "paper_execution.test_ledger", "freqai_bridge.test_exporter"):
            self.assertIn(module, commands)

    def test_freqai_smoke_is_manual_and_does_not_execute_trades(self):
        triggers, workflow = load_workflow("freqai-strategy-smoke.yml")
        self.assertEqual(set(triggers), {"workflow_dispatch"})
        job = workflow["jobs"]["strategy-load"]
        self.assertEqual(job["env"]["AI_EXECUTION_ENABLED"], "false")
        command = next(step["run"] for step in job["steps"] if step.get("name") == "Verify paper-only strategy load")
        self.assertIn("ci/freqai-smoke.py", command)
        self.assertIn('test "$AI_EXECUTION_ENABLED" = "false"', command)

    def test_legacy_telegram_and_backtest_runtimes_are_absent(self):
        for path in ("bot.py", "backtest.py", "backtest_rsi_percent_b_h1_adx.py",
                     "telegram_commands.py", "dashboard/index.html", "ci/run-legacy.py",
                     "ci/test_legacy_runner.py", "integrations/codemagic_client.py",
                     "integrations/test_codemagic_client.py"):
            with self.subTest(path=path):
                self.assertFalse((ROOT / path).exists())
        app = (ROOT / "app.py").read_text()
        self.assertIn('@app.get("/health/live")', app)
        self.assertIn('@app.get("/health/ready")', app)
        for marker in ("TELEGRAM_BOT_TOKEN", "telegram_webhook", "codemagic_client", "/api/dashboard"):
            self.assertNotIn(marker, app)

    def test_paper_execution_boundary_remains_disabled(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("AI_EXECUTION_ENABLED=false", readme)
        self.assertIn("không có luồng đặt lệnh Futures thật", readme)
        for name in ("t0-validation.yml", "cross-layer-integration.yml", "freqai-strategy-smoke.yml"):
            _, workflow = load_workflow(name)
            for job in workflow["jobs"].values():
                env = job.get("env", {})
                if "AI_EXECUTION_ENABLED" in env:
                    self.assertEqual(env["AI_EXECUTION_ENABLED"], "false")


if __name__ == "__main__":
    unittest.main()
