import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from data_lake.client import DataLakeClient, DataLakeError
from data_lake.export import export_freqtrade, main
from data_lake.test_client import ApiTransport
from market_data.store import Candle, CandleStore, INTERVAL_MS


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.db = self.base/"candles.sqlite3"
        self.step = INTERVAL_MS["15m"]
        self.start = 1_700_000_000_000//self.step*self.step
        self.end = self.start+2*self.step
        self.cutoff = self.end+100
        self.store = CandleStore(self.db)
        self.add_candles(2)
        self.transport = ApiTransport(self.db)
        self.client = DataLakeClient("http://127.0.0.1:8788", self.transport.token)
        self.client._opener = self.transport
        self.destination = self.base/"research"

    def add_candles(self, count):
        self.store.insert([Candle("15m", self.start+i*self.step,
                                  "100.00000000000000000001", "101", "99", "100.5", "2.5",
                                  self.start+(i+1)*self.step+7) for i in range(count)])

    def export(self, **kwargs):
        return export_freqtrade(self.client, "15m", self.start, self.end, self.destination,
                                as_of_ms=kwargs.get("as_of_ms", self.cutoff))

    def test_pages_freeze_as_of_and_manifest_binds_exact_records_and_files(self):
        self.add_candles(2001)
        self.end, self.cutoff = self.start+2001*self.step, self.start+2001*self.step+100

        def marker_only_writer(candles, path):
            # This test checks paging/publication, not Feather encoding (tested below).
            self.assertFalse((self.destination/"manifest.json").exists())
            self.assertEqual(len(candles), 2001)
            path.write_bytes(b"inert publication-test payload")

        with patch("data_lake.export._write_feather", side_effect=marker_only_writer):
            manifest = self.export()
        self.assertEqual(manifest["bars"], 2001)
        self.assertEqual([page["rows"] for page in manifest["pages"]], [2000, 1])
        requests = [parse_qs(urlsplit(r.full_url).query) for r, _ in self.transport.requests]
        self.assertEqual([q["asOfMs"] for q in requests], [[str(self.cutoff)]]*2)
        self.assertEqual(requests[0]["endMs"], requests[1]["startMs"])
        canonical = json.loads((self.destination/"canonical.json").read_text())
        self.assertEqual(canonical["candles"][0]["open"], "100.00000000000000000001")
        self.assertEqual(canonical["asOfMs"], self.cutoff)
        self.assertEqual(canonical["datasetVersion"], manifest["datasetVersion"])
        self.assertIn("float64", manifest["precisionNote"])
        self.assertEqual(manifest["format"], "FREQTRADE_2026_9_OHLCV_FEATHER")
        self.assertIn("futures/BTC_USDT_USDT-15m-futures.feather", manifest["files"])
        self.assertEqual(json.loads((self.destination/"manifest.json").read_text()), manifest)
        for relative, details in manifest["files"].items():
            raw = (self.destination/relative).read_bytes()
            self.assertEqual(details, {"sha256": "sha256:"+hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        self.assertNotIn(self.transport.token, json.dumps(manifest))
        self.assertFalse(list(self.destination.glob(".staging-*")))

    def test_incomplete_late_page_and_encoder_failure_publish_no_completed_export(self):
        self.add_candles(2000)
        self.end, self.cutoff = self.start+2001*self.step, self.start+2001*self.step+100
        with patch("data_lake.export._write_feather") as writer, self.assertRaises(DataLakeError):
            self.export()
        writer.assert_not_called()
        self.assertEqual(len(self.transport.requests), 2)
        self.assertFalse(self.destination.exists())
        self.end, self.cutoff = self.start+2*self.step, self.start+2*self.step+100
        with patch("data_lake.export._write_feather", side_effect=OSError("encoder failed")), self.assertRaises(OSError):
            self.export()
        self.assertFalse(self.destination.exists())

    def test_existing_destinations_are_never_overwritten_and_invalid_ranges_do_not_fetch(self):
        for kind in ("file", "empty_directory", "directory", "symlink"):
            destination = self.base/kind
            if kind == "file":
                destination.write_text("keep")
            elif kind == "symlink":
                destination.symlink_to(self.db)
            else:
                destination.mkdir()
                if kind == "directory":
                    (destination/"manifest.json").write_text("keep")
            with self.subTest(kind=kind), self.assertRaises(FileExistsError):
                export_freqtrade(self.client, "15m", self.start, self.end, destination, as_of_ms=self.cutoff)
        self.assertEqual((self.base/"file").read_text(), "keep")
        self.assertEqual((self.base/"directory/manifest.json").read_text(), "keep")
        for end, cutoff in ((self.start+100001*self.step, self.start+100001*self.step+100),
                            (self.end, self.end-1), (self.end, 2**63-1)):
            with self.subTest(end=end, cutoff=cutoff), self.assertRaises(DataLakeError):
                export_freqtrade(self.client, "15m", self.start, end, self.destination, as_of_ms=cutoff)
        self.assertEqual(self.transport.requests, [])
        self.assertFalse(self.destination.exists())

    def test_commit_failure_removes_owned_files_without_claiming_success(self):
        real_link = os.link

        def fail_manifest(source, destination):
            if Path(destination).name == "manifest.json":
                raise OSError("simulated final publication failure")
            return real_link(source, destination)

        with patch("data_lake.export._write_feather", side_effect=lambda c, p: p.write_bytes(b"test-only")), \
                patch("data_lake.export.os.link", side_effect=fail_manifest), self.assertRaises(OSError):
            self.export()
        self.assertFalse(self.destination.exists())

    def test_default_as_of_is_frozen_once_and_cli_does_not_print_token(self):
        now = self.cutoff+500
        with patch("data_lake.export.time.time_ns", return_value=now*1_000_000), \
                patch("data_lake.export._write_feather", side_effect=lambda c, p: p.write_bytes(b"test-only")):
            manifest = export_freqtrade(self.client, "15m", self.start, self.end, self.destination)
        self.assertEqual(manifest["sourceAsOfMs"], now)
        secret = "unlogged-consumer-canary-token"
        error = io.StringIO()
        with patch.dict(os.environ, {"MARKET_DATA_TOKEN": secret}), patch("sys.stderr", error):
            code = main(["--base-url", "https://user:"+secret+"@example.com", "--timeframe", "15m",
                         "--start-ms", str(self.start), "--end-ms", str(self.end),
                         "--output-dir", str(self.base/"cli")])
        self.assertEqual(code, 1)
        self.assertEqual(error.getvalue(), "EXPORT_FAILED\n")
        self.assertNotIn(secret, error.getvalue())

    @unittest.skipUnless(importlib.util.find_spec("pyarrow"), "pyarrow unavailable locally; CI requires real Feather round-trip")
    def test_real_feather_round_trip_matches_freqtrade_2026_9_schema(self):
        import pandas as pd

        manifest = self.export()
        frame = pd.read_feather(self.destination/"futures/BTC_USDT_USDT-15m-futures.feather")
        self.assertEqual(list(frame.columns), ["date", "open", "high", "low", "close", "volume"])
        self.assertEqual(frame["date"].tolist(), pd.to_datetime([self.start, self.start+self.step], unit="ms", utc=True).tolist())
        self.assertEqual(str(frame["date"].dt.tz), "UTC")
        self.assertTrue(all(str(frame[c].dtype) == "float64" for c in frame.columns[1:]))
        self.assertEqual(frame["close"].tolist(), [100.5, 100.5])
        self.assertEqual(manifest["bars"], 2)
        self.assertEqual(json.loads((self.destination/"canonical.json").read_text())["candles"][0]["open"],
                         "100.00000000000000000001")


if __name__ == "__main__":
    unittest.main()
