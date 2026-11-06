"""Contract tests for the read-only T0 -> Freqtrade offline exporter."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from quant_system.t0_freqtrade_adapter import (
    T0FreqtradeAdapterError,
    export_t0_snapshot,
)


INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000}


def make_snapshot(timeframe="15m"):
    candles = []
    for index in range(2):
        opened = 1_800_000_000_000 + index * INTERVAL_MS[timeframe]
        candles.append({
            "exchange": "binance",
            "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT",
            "timeframe": timeframe,
            "openTimeMs": opened,
            "closeTimeMs": opened + INTERVAL_MS[timeframe],
            "open": "65000.10",
            "high": "65100.20",
            "low": "64900.05",
            "close": "65050.25",
            "volume": "12.345",
            "isClosed": True,
            "availableAtMs": opened + INTERVAL_MS[timeframe] + 1000,
            "availabilityKind": "FIRST_OBSERVED",
            "quality": "VALIDATED",
            "source": "ccxt.binanceusdm",
        })
    payload = {
        "exchange": "binance",
        "marketType": "USDT_PERPETUAL",
        "symbol": "BTCUSDT",
        "timeframe": timeframe,
        "startMs": candles[0]["openTimeMs"],
        "endMs": candles[-1]["closeTimeMs"],
        "asOfMs": None,
        "candles": candles,
    }
    payload["datasetVersion"] = "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    payload["coverage"] = {
        "expected": 2, "returned": 2, "complete": True, "gaps": []
    }
    payload["generatedAtMs"] = candles[-1]["availableAtMs"] + 1
    return payload


class T0FreqtradeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.snapshot = self.root / "snapshot.json"
        self.output = self.root / "freqtrade-data"
        self.payload = make_snapshot()
        self.write_snapshot()

    def write_snapshot(self):
        self.snapshot.write_text(
            json.dumps(self.payload, separators=(",", ":")), encoding="utf-8"
        )

    def test_exports_closed_canonical_binance_futures_rows_and_manifest(self):
        result = export_t0_snapshot(self.snapshot, self.output)
        data = json.loads(Path(result["data_file"]).read_text(encoding="utf-8"))
        manifest = json.loads(
            Path(result["manifest_file"]).read_text(encoding="utf-8")
        )

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0][0], self.payload["candles"][0]["openTimeMs"])
        self.assertEqual(data[0][1:], [65000.1, 65100.2, 64900.05, 65050.25, 12.345])
        self.assertEqual(manifest["source"], "T0_CANONICAL_BINANCE_USDT_PERPETUAL")
        self.assertEqual(manifest["source_dataset_version"], self.payload["datasetVersion"])
        self.assertEqual(manifest["row_count"], 2)
        self.assertTrue(manifest["float64_conversion"])
        self.assertFalse(manifest["strategy_core_modified"])
        self.assertFalse(manifest["native_orders_enabled"])

    def test_rejects_okx_shadow_data(self):
        self.payload["exchange"] = "okx"
        self.write_snapshot()
        with self.assertRaisesRegex(T0FreqtradeAdapterError, "UNSUPPORTED_SOURCE_IDENTITY"):
            export_t0_snapshot(self.snapshot, self.output)

    def test_rejects_incomplete_coverage(self):
        self.payload["coverage"]["complete"] = False
        self.payload["coverage"]["gaps"] = [{"startMs": 1, "endMs": 2}]
        self.write_snapshot()
        with self.assertRaisesRegex(T0FreqtradeAdapterError, "INCOMPLETE_T0_WINDOW"):
            export_t0_snapshot(self.snapshot, self.output)

    def test_rejects_dataset_version_tampering(self):
        self.payload["candles"][0]["close"] = "65051.00"
        self.write_snapshot()
        with self.assertRaisesRegex(T0FreqtradeAdapterError, "DATASET_VERSION_MISMATCH"):
            export_t0_snapshot(self.snapshot, self.output)

    def test_rejects_non_contiguous_candles(self):
        self.payload["candles"][1]["openTimeMs"] += INTERVAL_MS["15m"]
        self.payload["candles"][1]["closeTimeMs"] += INTERVAL_MS["15m"]
        self.payload["datasetVersion"] = "sha256:" + hashlib.sha256(
            json.dumps(
                {key: self.payload[key] for key in (
                    "exchange", "marketType", "symbol", "timeframe",
                    "startMs", "endMs", "asOfMs", "candles"
                )},
                sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        self.write_snapshot()
        with self.assertRaisesRegex(T0FreqtradeAdapterError, "CANDLE_GAP_OR_OVERLAP"):
            export_t0_snapshot(self.snapshot, self.output)

    def test_rejects_unclosed_or_unvalidated_candle(self):
        self.payload["candles"][0]["isClosed"] = False
        self.write_snapshot()
        with self.assertRaisesRegex(T0FreqtradeAdapterError, "CANDLE_NOT_CLOSED_AND_VALIDATED"):
            export_t0_snapshot(self.snapshot, self.output)


    def test_exports_h1_without_changing_the_requested_timeframe(self):
        self.payload = make_snapshot("1h")
        self.write_snapshot()
        result = export_t0_snapshot(self.snapshot, self.output)
        manifest = json.loads(
            Path(result["manifest_file"]).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["timeframe"], "1h")
        self.assertEqual(manifest["row_count"], 2)
        self.assertIn("1h-futures.json", manifest["freqtrade_data_file"])

    def test_rejects_candle_observed_after_as_of_cutoff(self):
        self.payload["asOfMs"] = self.payload["candles"][0]["availableAtMs"]
        identity = {key: self.payload[key] for key in (
            "exchange", "marketType", "symbol", "timeframe",
            "startMs", "endMs", "asOfMs", "candles"
        )}
        self.payload["datasetVersion"] = "sha256:" + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.write_snapshot()
        with self.assertRaisesRegex(T0FreqtradeAdapterError, "CANDLE_AFTER_AS_OF_CUTOFF"):
            export_t0_snapshot(self.snapshot, self.output)

    def test_refuses_to_overwrite_an_existing_dataset_export(self):
        first = export_t0_snapshot(self.snapshot, self.output)
        original = Path(first["data_file"]).read_bytes()
        with self.assertRaisesRegex(T0FreqtradeAdapterError, "EXPORT_ALREADY_EXISTS"):
            export_t0_snapshot(self.snapshot, self.output)
        self.assertEqual(Path(first["data_file"]).read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
