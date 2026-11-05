from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/five-layer-pr-validation.yml"


class CiPolicyTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(WORKFLOW.is_file(), "Five-layer GitHub Actions workflow is missing")
        self.workflow = WORKFLOW.read_text()

    def test_github_actions_is_the_active_runner(self):
        for marker in (
            "pull_request:",
            "feature/android-five-layer-control",
            "workflow_dispatch:",
            "permissions:",
            "contents: read",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.workflow)
        self.assertFalse((ROOT / "codemagic.yaml").exists())
        self.assertFalse((ROOT / "docs/CODEMAGIC_SETUP.md").exists())

    def test_jobs_checkout_exact_pr_head_and_have_separate_boundaries(self):
        self.assertEqual(3, self.workflow.count("ref: ${{ github.event.pull_request.head.sha || github.sha }}"))
        for job in ("android-paper:", "backend-regression:", "dashboard-boundary:"):
            with self.subTest(job=job):
                self.assertIn(job, self.workflow)

    def test_android_job_runs_tests_build_and_apk_verification(self):
        for gate in (
            "ci.test_five_layer_android_boundary",
            "ci.test_five_layer_android_apk",
            ":app:testDebugUnitTest",
            ":app:assembleDebug",
            "ci/verify-five-layer-android-apk.py",
            "android-apk.json",
            "artifacts/*.apk",
        ):
            with self.subTest(gate=gate):
                self.assertIn(gate, self.workflow)

    def test_backend_job_is_paper_only_and_runs_core_and_risk_regressions(self):
        self.assertIn('AI_EXECUTION_ENABLED: "false"', self.workflow)
        for key in ("MARKET_DATA_DB:", "T0_FEEDER_LEASE_DB:", "PAPER_DB:", "BINANCE_API_KEY:", "OKX_API_KEY:"):
            with self.subTest(key=key):
                self.assertIn(key, self.workflow)
        for gate in (
            "market_data.test_store", "market_data.test_sync", "market_data.test_storage",
            "market_data.test_api", "futures_intelligence.test_import_collector",
            "pipeline.test_core_strategy", "pipeline.test_core_signal",
            "paper_execution.test_risk_control", "paper_execution.test_ledger",
            "integrations.test_hummingbot_bridge",
        ):
            with self.subTest(gate=gate):
                self.assertIn(gate, self.workflow)

    def test_dashboard_is_nonblocking_and_only_checks_its_local_manifest_boundary(self):
        dashboard = self.workflow.split("  dashboard-boundary:", 1)[1]
        self.assertIn("continue-on-error: true", dashboard)
        self.assertIn("test -f control_dashboard/package.json", dashboard)
        self.assertIn("test -f control_dashboard/package-lock.json", dashboard)
        self.assertIn("JSON.parse", dashboard)
        for intensive_gate in ("npm ci", "npm test", "npm run build", "npm audit"):
            with self.subTest(gate=intensive_gate):
                self.assertNotIn(intensive_gate, dashboard)


if __name__ == "__main__":
    unittest.main()
