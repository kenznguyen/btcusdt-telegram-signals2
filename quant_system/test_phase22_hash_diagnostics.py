"""TDD contract for actionable Phase 22 config-hash mismatch diagnostics."""
import unittest

from quant_system.phase22_runtime_probe import config_hash_diagnostics


class Phase22ConfigHashDiagnosticsTests(unittest.TestCase):
    def test_reports_runtime_hashes_and_exact_changed_paths(self):
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


if __name__ == "__main__":
    unittest.main()
