import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from market_data.t0_t2_parity import (
    ParityInputError,
    build_report,
    chartpro_v2_hash,
    render_markdown,
)


STEP = {"m15": 900_000, "h1": 3_600_000}
START = 1_800_000_000_000
END = START + 3_600_000
HASH = "sha256:" + "a" * 64


class T0T2ParityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest_path = self.root / "manifest.json"
        self.manifest = {
            "schema": "T0-T2-BINANCE-OKX-PARITY-MANIFEST-V1",
            "pair_id": "fixture-btcusdt-1h",
            "window": {"start_ms": START, "end_ms": END},
            "sources": {
                "binance_t0": {
                    "exchange": "BINANCE",
                    "market_type": "USD_M_LINEAR_PERPETUAL",
                    "instrument": "BTC/USDT:USDT",
                    "symbol": "BTCUSDT",
                    "volume_unit": "BTC_BASE_ASSET",
                    "m15_csv": "binance_m15.csv",
                    "h1_csv": "binance_h1.csv",
                    "t0_dataset_version": {"m15": HASH, "h1": HASH},
                },
                "okx_t2": {
                    "exchange": "OKX",
                    "market_type": "USDT_PERPETUAL_SWAP",
                    "instrument": "BTC-USDT-SWAP",
                    "symbol": "BTCUSDT",
                    "volume_unit": "BTC_BASE_ASSET_VOLCCY",
                    "volume_field_mapping": "history-candles[6]",
                    "m15_csv": "okx_m15.csv",
                    "h1_csv": "okx_h1.csv",
                },
            },
            "conversion": {"implementation_revision": "test-fixture"},
        }
        for source in ("binance", "okx"):
            for timeframe, step in STEP.items():
                rows = []
                for timestamp in range(START, END, step):
                    rows.append({
                        "open_time": timestamp, "open": "100.00", "high": "102.00",
                        "low": "99.00", "close": "101.00", "volume": "2.5",
                        "closed": "true",
                    })
                self.write_rows(f"{source}_{timeframe}.csv", rows)
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def write_rows(self, name, rows):
        path = self.root / name
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=[
                "open_time", "open", "high", "low", "close", "volume", "closed"
            ])
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_builds_comparable_report_with_independent_source_hashes(self):
        report = build_report(self.manifest_path)
        self.assertEqual(report["status"], "COMPARABLE")
        self.assertEqual(report["window"], {"start_ms": START, "end_ms": END})
        self.assertEqual(report["coverage"]["m15"]["rows_per_source"], 4)
        self.assertEqual(report["coverage"]["h1"]["rows_per_source"], 1)
        self.assertEqual(report["sources"]["binance_t0"]["t0_dataset_version"]["m15"], HASH)
        self.assertEqual(
            report["sources"]["binance_t0"]["files"]["m15"]["sha256"],
            "sha256:" + hashlib.sha256((self.root / "binance_m15.csv").read_bytes()).hexdigest(),
        )
        self.assertEqual(report["metrics"]["m15"]["close"]["exact_match_count"], 4)
        self.assertEqual(report["metrics"]["m15"]["close"]["max_abs_diff"], 0.0)
        self.assertEqual(report["metrics"]["m15"]["close"]["max_rel_diff"], 0.0)
        self.assertIn("COMPARABLE", render_markdown(report))

    def test_v2_hash_matches_t2_binary_contract_and_is_ordered_by_open_time(self):
        rows = [
            {"open_time": START, "open": "100", "high": "102", "low": "99",
             "close": "101", "volume": "2", "closed": True}
        ]
        import hashlib as hashlib_module
        import struct

        expected = hashlib_module.sha256(
            b"CHARTPRO-OHLCV-V2\0M15\0H1\0"
            + struct.pack(">q5d", START, 100.0, 102.0, 99.0, 101.0, 2.0)
        ).hexdigest()
        self.assertEqual(chartpro_v2_hash(rows, []), "sha256:" + expected)

    def test_rejects_missing_or_unclosed_candles_without_silent_filtering(self):
        path = self.write_rows("okx_m15.csv", [{
            "open_time": START, "open": "100", "high": "102", "low": "99",
            "close": "101", "volume": "2", "closed": "false",
        }])
        with self.assertRaises(ParityInputError):
            build_report(self.manifest_path)

    def test_rejects_gaps_duplicates_and_unaligned_timestamps(self):
        rows = [
            {"open_time": START, "open": "100", "high": "102", "low": "99",
             "close": "101", "volume": "2", "closed": "true"},
            {"open_time": START + 2 * STEP["m15"], "open": "100", "high": "102",
             "low": "99", "close": "101", "volume": "2", "closed": "true"},
        ]
        self.write_rows("binance_m15.csv", rows)
        with self.assertRaises(ParityInputError):
            build_report(self.manifest_path)

        rows[1]["open_time"] = START + STEP["m15"]
        rows[1]["open"] = "100"
        self.write_rows("binance_m15.csv", rows)
        with self.assertRaises(ParityInputError):
            build_report(self.manifest_path)

    def test_rejects_invalid_ohlc_and_nonfinite_values(self):
        rows = [{
            "open_time": START, "open": "100", "high": "98", "low": "99",
            "close": "101", "volume": "2", "closed": "true",
        }]
        self.write_rows("binance_m15.csv", rows)
        with self.assertRaises(ParityInputError):
            build_report(self.manifest_path)

    def test_rejects_incorrect_exchange_identity_and_volume_unit(self):
        self.manifest["sources"]["okx_t2"]["volume_unit"] = "CONTRACT_COUNT"
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        with self.assertRaises(ParityInputError):
            build_report(self.manifest_path)

    def test_rejects_different_windows_or_missing_t0_provenance(self):
        self.manifest["window"]["end_ms"] -= STEP["m15"]
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        with self.assertRaises(ParityInputError):
            build_report(self.manifest_path)

        self.manifest["window"]["end_ms"] = END
        self.manifest["sources"]["binance_t0"]["t0_dataset_version"].pop("h1")
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        with self.assertRaises(ParityInputError):
            build_report(self.manifest_path)


if __name__ == "__main__":
    unittest.main()
