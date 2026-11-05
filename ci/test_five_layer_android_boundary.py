from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android-app"
PACKAGE = "com/kenznguyen/btclivealerts"
JAVA = ANDROID / "app/src/main/java" / PACKAGE
TESTS = ANDROID / "app/src/test/java" / PACKAGE


CHART_PRO_SOURCES = (
    "AlertDelivery.kt", "AlertHistoryStore.kt", "AlertPolicy.kt",
    "BacktestPanel.kt", "BinanceRestGate.kt", "ChartAnalytics.kt",
    "ChartMarketSession.kt", "CompleteDashboard.kt", "MarketEngine.kt",
    "MultiStreamSignalEngine.kt", "MultiSymbolScanner.kt", "OrderBookEngine.kt",
    "OrderBookPanel.kt", "OrderBookSequence.kt", "ScannerMarketFeed.kt",
    "SnapshotRetryGate.kt", "StrategyMonitorService.kt", "StrategyEngine.kt",
)

CHART_PRO_TESTS = (
    "AlertHistoryCodecTest.kt", "AlertPolicyTest.kt", "BinanceRestGateTest.kt",
    "ChartAnalyticsTest.kt", "ChartMarketSessionTest.kt",
    "MultiStreamSignalEngineTest.kt", "MultiSymbolScannerTest.kt",
    "OrderBookSequenceTest.kt", "SnapshotRetryGateTest.kt", "StrategyEngineTest.kt",
)


class FiveLayerAndroidBoundaryTest(unittest.TestCase):
    def test_chart_pro_sources_are_absent_from_five_layer_android(self):
        present = [name for name in CHART_PRO_SOURCES if (JAVA / name).exists()]
        self.assertEqual([], present, f"Chart Pro sources remain in five-layer app: {present}")

    def test_chart_pro_tests_are_absent_from_five_layer_android(self):
        present = [name for name in CHART_PRO_TESTS if (TESTS / name).exists()]
        self.assertEqual([], present, f"Chart Pro tests remain in five-layer app: {present}")

    def test_launcher_mounts_only_five_layer_dashboard(self):
        source = (JAVA / "MainActivity.kt").read_text()
        self.assertIn("FiveLayerStandaloneDashboard(this)", source)
        for marker in ("CompleteDashboard", "StrategyMonitorService", "BuildConfig.PARALLEL_INSTALL"):
            self.assertNotIn(marker, source)

    def test_manifest_has_no_chart_pro_monitor_or_notification_permissions(self):
        manifest = (ANDROID / "app/src/main/AndroidManifest.xml").read_text()
        for marker in ("StrategyMonitorService", "FOREGROUND_SERVICE", "POST_NOTIFICATIONS", "VIBRATE"):
            self.assertNotIn(marker, manifest)
        self.assertIn("MainActivity", manifest)

    def test_gradle_defines_one_five_layer_application_identity(self):
        gradle = (ANDROID / "app/build.gradle.kts").read_text()
        self.assertIn('applicationId = "com.kenznguyen.btclivealerts.paper"', gradle)
        self.assertNotIn('create("parallel")', gradle)
        self.assertNotIn("ANDROID_KEYSTORE", gradle)
        self.assertNotIn("btc-chart-release", gradle)

    def test_five_layer_client_and_shared_paper_contracts_are_preserved(self):
        for name in (
            "FiveLayerStandaloneDashboard.kt", "FiveLayerPanel.kt", "FiveLayerApi.kt",
            "FiveLayerCandlesCard.kt", "FiveLayerPresentation.kt", "PaperOrderHistory.kt",
            "HummingbotOrderBook.kt", "OrderBookAnalytics.kt",
        ):
            self.assertTrue((JAVA / name).is_file(), f"Missing five-layer component: {name}")

    def test_existing_five_layer_package_and_saved_api_url_are_preserved(self):
        gradle = (ANDROID / "app/build.gradle.kts").read_text()
        panel = (JAVA / "FiveLayerPanel.kt").read_text()
        self.assertIn('applicationId = "com.kenznguyen.btclivealerts.paper"', gradle)
        self.assertIn('getSharedPreferences("strategy_state_v1", Context.MODE_PRIVATE)', panel)
        self.assertNotIn('getSharedPreferences("five_layer_state_v1", Context.MODE_PRIVATE)', panel)

    def test_app_label_is_five_layer_only(self):
        strings = (ANDROID / "app/src/main/res/values/strings.xml").read_text()
        self.assertIn("BTCUSDT Quant System", strings)
        self.assertNotIn("Chart Pro", strings)

    def test_server_strategy_core_and_regressions_are_preserved(self):
        core = (ROOT / "pipeline/core_strategy.py").read_text()
        for contract in (
            'RSI_LEN = int(os.environ.get("RSI_LENGTH", "14"))',
            'DMI_LEN = int(os.environ.get("DMI_LENGTH", "14"))',
            'ADX_SMOOTH = int(os.environ.get("ADX_SMOOTHING", "14"))',
            'H1_ADX_ENTRY = float(os.environ.get("H1_ADX_ENTRY", "20"))',
            'LONG_RSI_ENTRY = float(os.environ.get("LONG_RSI_ENTRY", "30"))',
            'SHORT_RSI_ENTRY = float(os.environ.get("SHORT_RSI_ENTRY", "70"))',
            'LONG_RSI_TP = float(os.environ.get("LONG_RSI_TP", "76"))',
            'SHORT_RSI_TP = float(os.environ.get("SHORT_RSI_TP", "24"))',
            'TP_ROE = float(os.environ.get("TP_ROE", "5"))',
            'DCA_ROE = float(os.environ.get("DCA_ROE", "-20"))',
            'DCA_ADX = float(os.environ.get("DCA_ADX", "45"))',
            'SOFT_SL_ROE = float(os.environ.get("SOFT_SL_ROE", "-35"))',
            'EMERGENCY_SL_ROE = float(os.environ.get("EMERGENCY_SL_ROE", "-90"))',
        ):
            self.assertIn(contract, core)
        self.assertTrue((ROOT / "pipeline/test_core_strategy.py").is_file())
        self.assertTrue((ROOT / "pipeline/test_core_signal.py").is_file())

    def test_cleanup_branch_uses_github_actions_for_all_layers(self):
        workflow_path = ROOT / ".github/workflows/five-layer-pr-validation.yml"
        self.assertTrue(workflow_path.is_file(), "GitHub Actions validation workflow is missing")
        workflow = workflow_path.read_text()
        for marker in (
            "pull_request:", "feature/android-five-layer-control", "push:",
            "cleanup/remove-chart-pro-from-five-layer-20261105", "workflow_dispatch:",
            "permissions:", "contents: read", "android-paper:", "backend-regression:",
            "dashboard:", 'AI_EXECUTION_ENABLED: "false"',
        ):
            self.assertIn(marker, workflow)
        self.assertFalse((ROOT / "codemagic.yaml").exists(), "Codemagic config must be retired")
        self.assertFalse((ROOT / "docs/CODEMAGIC_SETUP.md").exists(), "Codemagic setup doc must be retired")

    def test_freqai_strategy_is_owned_by_five_layer(self):
        self.assertFalse((ROOT / "freqai_bridge/ChartProFreqaiResearch.py").exists())
        strategy = ROOT / "freqai_bridge/FiveLayerFreqaiResearch.py"
        self.assertTrue(strategy.is_file())
        self.assertIn("class FiveLayerFreqaiResearch", strategy.read_text())


if __name__ == "__main__":
    unittest.main()    def test_cleanup_branch_uses_github_actions_for_all_layers(self):
        workflow_path = ROOT / ".github/workflows/five-layer-pr-validation.yml"
        self.assertTrue(workflow_path.is_file(), "GitHub Actions validation workflow is missing")
        workflow = workflow_path.read_text()
        for marker in (
            "pull_request:", "feature/android-five-layer-control", "push:",
            "cleanup/remove-chart-pro-from-five-layer-20261105", "workflow_dispatch:",
            "permissions:", "contents: read", "android-paper:", "backend-regression:",
            "dashboard:", 'AI_EXECUTION_ENABLED: "false"',
        ):
            self.assertIn(marker, workflow)
        self.assertFalse((ROOT / "codemagic.yaml").exists(), "Codemagic config must be retired")
        self.assertFalse((ROOT / "docs/CODEMAGIC_SETUP.md").exists(), "Codemagic setup doc must be retired")

    def test_freqai_strategy_is_owned_by_five_layer(self):
        self.assertFalse((ROOT / "freqai_bridge/ChartProFreqaiResearch.py").exists())
        strategy = ROOT / "freqai_bridge/FiveLayerFreqaiResearch.py"
        self.assertTrue(strategy.is_file())
        self.assertIn("class FiveLayerFreqaiResearch", strategy.read_text())


if __name__ == "__main__":
    unittest.main()
