"""Fail-closed 1m/5m -> M15/H1 data and simulated stop diagnostics."""
import csv
import tempfile
import unittest
from pathlib import Path

from freqtrade_parity.rules import StrategyRules
from quant_system.intrabar_audit import audit_history


class IntrabarAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.start = 1_800_000_000_000
        self.m15 = self.root / "m15.csv"
        self.h1 = self.root / "h1.csv"
        self.detail = self.root / "detail-5m.csv"
        child, parent, hours = [], [], []
        for index in range(96):
            opened = self.start + index * 900_000
            low = 92. if index == 0 else 99.
            parent.append([opened, 100, 101, low, 100, 3, 1])
            for j in range(3):
                child.append([opened + j * 300_000, 100, 101, low if j == 0 else 99, 100, 1, 1])
        for index in range(24):
            opened = self.start + index * 3_600_000
            hours.append([opened, 100, 101, 92 if index == 0 else 99, 100, 12, 1])
        self.write(self.m15, parent)
        self.write(self.h1, hours)
        self.write(self.detail, child)

    @staticmethod
    def write(path, rows):
        with path.open("w", newline="", encoding="utf-8") as out:
            writer = csv.writer(out)
            writer.writerow(["open_time", "open", "high", "low", "close", "volume", "closed"])
            writer.writerows(rows)

    def call(self, **kwargs):
        args = dict(m15_path=self.m15, h1_path=self.h1, detail_path=self.detail,
                    days=1, detail_minutes=5)
        args.update(kwargs)
        return audit_history(**args)

    def test_exact_pinned_history_is_checked_but_not_certified_as_runtime_parity(self):
        report = self.call()
        self.assertTrue(report["ohlcv_verified"])
        self.assertFalse(report["parity_verified"])
        self.assertFalse(report["full_core_parity_certified"])
        self.assertEqual(report["m15_count"], 96)
        self.assertEqual(report["detail_count"], 288)
        self.assertEqual(report["detail_timeframe"], "5m")
        self.assertTrue(report["dataset_sha256"].startswith("sha256:"))
        self.assertTrue(report["detail_sha256"].startswith("sha256:"))

    def test_emergency_touch_uses_first_fine_candle_open_gap_and_never_invents_fill(self):
        rules = StrategyRules()
        stop = rules.threshold_price("LONG", 100., 90.)
        event = {
            "kind": "EMERGENCY SL", "side": "LONG", "candleTime": self.start,
            "avg_entry": 100., "stop_price": stop,
        }
        report = self.call(events=[event])
        finding = report["event_diagnostics"][0]
        self.assertEqual(finding["event_kind"], "EMERGENCY SL")
        self.assertEqual(finding["first_touch_open_ms"], self.start)
        self.assertEqual(finding["touch_window_ms"], 300_000)
        self.assertIsNotNone(finding["expected_fill_price"])
        self.assertIsNone(finding["actual_fill_price"])
        self.assertIsNone(finding["fill_difference"])
        self.assertFalse(report["parity_verified"])

    def test_soft_sl_cannot_be_declared_filled_from_intrabar_high_low(self):
        event = {"kind": "SOFT SL", "side": "LONG", "candleTime": self.start,
                 "confirmed_at_ms": self.start + 900_000}
        report = self.call(events=[event])
        diagnostic = report["event_diagnostics"][0]
        self.assertEqual(diagnostic["confirmed_at_ms"], self.start + 900_000)
        self.assertIsNone(diagnostic["actual_fill_price"])
        self.assertFalse(report["parity_verified"])

    def test_mismatch_malformed_and_missing_detail_rejected(self):
        text = self.detail.read_text()
        self.detail.write_text(text.replace("100,101,92", "100,101,93", 1))
        with self.assertRaises(ValueError):
            self.call()
        self.detail.write_text(text)
        lines = text.splitlines()
        self.detail.write_text("\n".join([lines[0], *lines[2:]])+"\n")
        with self.assertRaises(ValueError):
            self.call()

    def test_requires_full_requested_180_or_360_day_coverage(self):
        with self.assertRaises(ValueError):
            self.call(days=180)
        with self.assertRaises(ValueError):
            self.call(days=360)

    def test_unsigned_actual_fill_is_diagnostic_only(self):
        stop = StrategyRules().threshold_price("LONG", 100, 90)
        event = {"kind": "EMERGENCY SL", "side": "LONG", "candleTime": self.start,
                 "avg_entry": 100, "stop_price": stop, "actual_fill_price": 93.}
        report = self.call(events=[event])
        self.assertIsNotNone(report["event_diagnostics"][0]["fill_difference"])
        self.assertFalse(report["parity_verified"])

    def test_short_emergency_stop_intrabar_crossing_and_fill_gap_estimate(self):
        for path in (self.m15, self.h1, self.detail):
            lines = path.read_text().splitlines()
            # Raise only the first candle's high; keep H1/M15/5m consistent.
            lines[1] = lines[1].replace(",100,101,", ",100,108,", 1)
            path.write_text("\\n".join(lines) + "\\n")
        stop = StrategyRules().threshold_price("SHORT", 100, 90)
        report = self.call(events=[{
            "kind": "EMERGENCY SL", "side": "SHORT",
            "candleTime": self.start, "avg_entry": 100, "stop_price": stop,
        }])
        touch = report["event_diagnostics"][0]
        self.assertEqual(touch["first_touch_open_ms"], self.start)
        self.assertGreater(touch["expected_fill_price"], stop)
        self.assertIsNone(touch["actual_fill_price"])

    def test_soft_stop_confirmation_must_follow_m15_close(self):
        event = {"kind": "SOFT SL", "side": "LONG", "candleTime": self.start,
                 "confirmed_at_ms": self.start + 300_000}
        with self.assertRaises(ValueError):
            self.call(events=[event])

    def test_forged_emergency_stop_threshold_is_rejected(self):
        event = {"kind": "EMERGENCY SL", "side": "LONG", "candleTime": self.start,
                 "avg_entry": 100, "stop_price": 95.}
        with self.assertRaises(ValueError):
            self.call(events=[event])


if __name__ == "__main__":
    unittest.main()
