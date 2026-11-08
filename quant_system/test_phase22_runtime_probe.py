"""Unit contracts for the R22.2 isolated runtime probe."""
import unittest

from quant_system.phase22_runtime_probe import (
    build_runtime_config,
    canonical_sha,
    expected_expanded_features,
    runtime_config_snapshot,
)


class Phase22RuntimeProbeTests(unittest.TestCase):
    def test_runtime_copy_disables_start_and_live_retraining(self):
        source = {
            "dry_run": True,
            "initial_state": "running",
            "force_entry_enable": False,
            "freqai": {"enabled": True, "live_retrain_hours": 1},
        }
        safe = build_runtime_config(source, "/tmp/r22-isolated-user-data")
        self.assertEqual(safe["initial_state"], "stopped")
        self.assertEqual(safe["user_data_dir"], "/tmp/r22-isolated-user-data")
        self.assertIs(safe["dry_run"], True)
        self.assertIs(safe["force_entry_enable"], False)
        self.assertEqual(safe["freqai"]["live_retrain_hours"], 1)
        self.assertEqual(source["initial_state"], "running")
        self.assertEqual(source["freqai"]["live_retrain_hours"], 1)

    def test_canonical_hash_is_key_order_independent(self):
        self.assertEqual(canonical_sha({"a": 1, "b": 2}),
                         canonical_sha({"b": 2, "a": 1}))

    def test_runtime_config_snapshot_matches_historical_phase13b_shape(self):
        resolved = {
            "freqai": {"enabled": True, "live_retrain_hours": 1, "resolved_default": 7},
            "exchange": {"name": "okx", "pair_whitelist": ["BTC/USDT:USDT"]},
            "timeframe": "15m",
            "dry_run": True,
            "force_entry_enable": False,
            "initial_state": "stopped",
        }
        snapshot = runtime_config_snapshot(resolved)
        self.assertEqual(
            snapshot,
            {
                "freqai": resolved["freqai"],
                "exchange": {"name": "okx"},
                "timeframe": "15m",
                "dry_run": True,
                "force_entry_enable": False,
            },
        )
        self.assertNotIn("pair_whitelist", snapshot["exchange"])
        self.assertNotIn("initial_state", snapshot)

    def test_expanded_feature_schema_preserves_order_and_shift_groups(self):
        actual = expected_expanded_features("BTC/USDT:USDT", "15m", [14, 28], 2)
        self.assertEqual(len(actual), 20)
        self.assertEqual(len(set(actual)), 20)
        self.assertEqual(actual[0], "%-relative-price_14_BTC/USDTUSDT_15m")
        self.assertEqual(actual[6], "%-relative-price_14_shift-1_BTC/USDTUSDT_15m")
        self.assertEqual(actual[12], "%-relative-price_14_shift-2_BTC/USDTUSDT_15m")
        self.assertEqual(actual[-2:], ["%-day-of-week", "%-hour-of-day"])


if __name__ == "__main__":
    unittest.main()


class Phase22ConfigHashDiagnosticsTests(unittest.TestCase):
    def test_reports_runtime_hashes_and_exact_changed_paths(self):
        from quant_system.phase22_runtime_probe import config_hash_diagnostics

        raw = {
            "freqai": {
                "enabled": True,
                "feature_parameters": {"include_corr_pairlist": []},
            },
            "exchange": {"name": "okx"},
            "timeframe": "15m",
            "dry_run": True,
            "force_entry_enable": False,
        }
        resolved = {
            "freqai": {
                "enabled": True,
                "feature_parameters": {"include_corr_pairlist": ["ETH/USDT:USDT"]},
            },
            "exchange": {"name": "okx"},
            "timeframe": "15m",
            "dry_run": True,
            "force_entry_enable": False,
        }
        result = config_hash_diagnostics(
            resolved,
            raw,
            expected_config_sha256="sha256:expected-config",
            expected_freqai_sha256="sha256:expected-freqai",
        )
        self.assertEqual(result["expected_config_sha256"], "sha256:expected-config")
        self.assertTrue(result["actual_config_sha256"].startswith("sha256:"))
        self.assertEqual(result["expected_freqai_config_sha256"], "sha256:expected-freqai")
        self.assertTrue(result["actual_freqai_config_sha256"].startswith("sha256:"))
        self.assertTrue(result["raw_freqai_config_sha256"].startswith("sha256:"))
        self.assertEqual(
            result["runtime_vs_raw_diff_paths"],
            ["freqai.feature_parameters.include_corr_pairlist"],
        )


class Phase22FreqAIConfigValidationTests(unittest.TestCase):
    def test_schema_validation_reproduces_frozen_post_validation_hashes(self):
        import json
        import tempfile
        from pathlib import Path

        from freqtrade.configuration import Configuration
        from quant_system.phase22_runtime_probe import (
            apply_freqtrade_schema_defaults,
            canonical_sha,
        )

        root = Path(__file__).resolve().parents[1]
        raw = json.loads((root / "freqai_bridge/config.okx-research.json").read_text())
        metadata = json.loads(
            (root / "research_evidence/frozen-model/phase13b-20261104/model-candidate-metadata.json").read_text()
        )

        with tempfile.TemporaryDirectory(prefix="r22-schema-defaults-") as temp:
            user_data = Path(temp) / "user_data"
            user_data.mkdir()
            config_path = Path(temp) / "config.json"
            config_path.write_text(
                json.dumps(build_runtime_config(raw, str(user_data))),
                encoding="utf8",
            )
            loaded = Configuration.from_files([str(config_path)])
            validated = apply_freqtrade_schema_defaults(loaded)

        snapshot = runtime_config_snapshot(validated)
        self.assertEqual(
            canonical_sha(snapshot["freqai"]),
            metadata["freqai_config_sha256"],
        )
        self.assertEqual(canonical_sha(snapshot), metadata["config_sha256"])
        self.assertIs(
            snapshot["freqai"]["feature_parameters"]["shuffle_after_split"],
            False,
        )


class Phase22RuntimeFeatureSchemaTests(unittest.TestCase):
    def test_script_mode_can_restore_repository_root_import_path(self):
        import sys
        from pathlib import Path

        from quant_system.phase22_runtime_probe import ensure_repository_root_on_sys_path

        root = str(Path(__file__).resolve().parents[1])
        original = list(sys.path)
        try:
            sys.path[:] = [entry for entry in sys.path if str(Path(entry or ".").resolve()) != root]
            ensure_repository_root_on_sys_path()
            self.assertEqual(sys.path[0], root)
            import freqai_bridge.ChartProFreqaiResearch  # noqa: F401
        finally:
            sys.path[:] = original

    def test_native_freqai_data_kitchen_expansion_matches_frozen_feature_order(self):
        import json
        import tempfile
        from pathlib import Path

        import pandas as pd
        from freqtrade.configuration import Configuration
        from freqai_bridge.ChartProFreqaiResearch import ChartProFreqaiResearch
        from quant_system.phase22_runtime_probe import (
            apply_freqtrade_schema_defaults,
            build_runtime_config,
            build_runtime_feature_columns,
        )

        root = Path(__file__).resolve().parents[1]
        raw = json.loads((root / "freqai_bridge/config.okx-research.json").read_text())
        metadata = json.loads(
            (root / "research_evidence/frozen-model/phase13b-20261104/model-candidate-metadata.json").read_text()
        )
        with tempfile.TemporaryDirectory(prefix="r22-feature-schema-") as temp:
            user_data = Path(temp) / "user_data"
            user_data.mkdir()
            config_path = Path(temp) / "config.json"
            config_path.write_text(
                json.dumps(build_runtime_config(raw, str(user_data))),
                encoding="utf8",
            )
            config = apply_freqtrade_schema_defaults(
                Configuration.from_files([str(config_path)])
            )

        frame = pd.DataFrame({
            "date": pd.date_range("2026-01-01", periods=96, freq="15min", tz="UTC"),
            "open": [99.5 + i for i in range(96)],
            "high": [101.0 + i for i in range(96)],
            "low": [99.0 + i for i in range(96)],
            "close": [100.0 + i for i in range(96)],
            "volume": [10.0 + (i % 7) for i in range(96)],
        })
        strategy = object.__new__(ChartProFreqaiResearch)
        actual = build_runtime_feature_columns(
            config, strategy, frame, "BTC/USDT:USDT"
        )
        self.assertEqual(actual, metadata["ordered_feature_columns"])
