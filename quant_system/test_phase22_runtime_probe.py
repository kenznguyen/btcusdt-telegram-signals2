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
        safe = build_runtime_config(source)
        self.assertEqual(safe["initial_state"], "stopped")
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
