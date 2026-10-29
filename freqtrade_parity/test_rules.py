import unittest
from freqtrade_parity.rules import StrategyParameters, StrategyRules, compare_event_traces


class StrategyRulesTest(unittest.TestCase):
    def setUp(self):
        self.rules = StrategyRules()

    def test_pinned_android_defaults(self):
        p = StrategyParameters()
        self.assertEqual((p.leverage, p.tp_roe, p.dca_roe, p.soft_sl_roe, p.emergency_sl_roe),
                         (13.0, 5.0, -20.0, -35.0, -90.0))
        self.assertEqual((p.entry_margin_pct, p.dca_margin_ratio, p.fee_rate, p.slippage_bps),
                         (0.5, 1.0, 0.0005, 5.0))

    def test_entry_cross_and_prior_closed_h1_filter(self):
        self.assertTrue(self.rules.long_entry(29, 31, 26, 12, 22))
        self.assertFalse(self.rules.long_entry(31, 32, 26, 12, 22))
        self.assertFalse(self.rules.long_entry(29, 31, 26, 12, 20))
        self.assertTrue(self.rules.short_entry(71, 69, 9, 24, 23))

    def test_dca_tp_and_stop_ordering(self):
        self.assertTrue(self.rules.dca("LONG", -21, 46, 23, 22))
        self.assertFalse(self.rules.dca("LONG", -21, 45, 23, 22))
        self.assertTrue(self.rules.tp("SHORT", 23, 5))
        self.assertTrue(self.rules.emergency("LONG", 92000, 100000, 100000))
        self.assertEqual("EMERGENCY SL", self.rules.exit_priority(True, True, True))
        self.assertEqual("SOFT SL", self.rules.exit_priority(False, True, True))
        self.assertEqual("TAKE PROFIT", self.rules.exit_priority(False, False, True))

    def test_explicit_trace_parity_requires_separate_provenance(self):
        checksum = "sha256:" + "a"*64
        rows = [{"kind":"DCA","candleTime":900000}]
        kotlin = {"engine":"kotlin","dataset_sha256":checksum,"events":rows}
        python = {"engine":"freqtrade","dataset_sha256":checksum,"events":rows}
        self.assertFalse(compare_event_traces(rows,rows,checksum)["parity_verified"])
        self.assertTrue(compare_event_traces(kotlin,python,checksum)["parity_verified"])
        self.assertFalse(compare_event_traces(kotlin,{**python,"dataset_sha256":"sha256:"+"b"*64},checksum)["parity_verified"])
        self.assertFalse(compare_event_traces(kotlin,{**python,"engine":"kotlin"},checksum)["parity_verified"])
        self.assertFalse(compare_event_traces(kotlin,{**python,"events":[]},checksum)["parity_verified"])
        self.assertFalse(compare_event_traces(None,python,checksum)["parity_verified"])
        self.assertFalse(compare_event_traces(kotlin,python,"abc")["parity_verified"])


if __name__ == "__main__":
    unittest.main()
