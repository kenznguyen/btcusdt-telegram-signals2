"""Collector tests use fabricated API replies only to test rejection rules.
No test fixture may serve as a certified market-data parity dataset.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from quant_engine.okx_ohlcv import fetch_closed, parse_ohlcv_row, write_dataset


def candle(ts, *, confirmed="1", close="100.0"):
    return [str(ts), "100", "105", "95", close, "10", "100", "1000", confirmed]


def payload(rows):
    return {"code": "0", "msg": "", "data": rows}


class OkxCollectorTests(unittest.TestCase):
    def test_confirmed_rows_only(self):
        self.assertIsNone(parse_ohlcv_row(candle(900000, confirmed="0"), 900000, now_ms=5000000))
        self.assertEqual(parse_ohlcv_row(candle(900000), 900000, now_ms=5000000)["close"], 100.0)

    def test_reject_future_confirmed_timestamp_and_unaligned_rows(self):
        with self.assertRaises(ValueError):
            parse_ohlcv_row(candle(900000 * 20), 900000, now_ms=900000 * 20)
        with self.assertRaises(ValueError):
            parse_ohlcv_row(candle(123456), 900000, now_ms=10000000)

    def test_reject_invalid_ohlc(self):
        with self.assertRaises(ValueError):
            parse_ohlcv_row(["0", "100", "99", "95", "100", "10", "100", "1000", "1"],
                            900000, now_ms=10000000)

    def test_reject_api_error_without_synthetic_fallback(self):
        with self.assertRaises(ValueError):
            fetch_closed("15m", 900000, 2, fetch_page=lambda _: {"code":"500","data":[]},
                         now_ms=10000000)

    def test_pagination_deduplicates_boundary_and_checks_continuity(self):
        first = payload([candle(3*900000), candle(2*900000)])
        second = payload([candle(2*900000), candle(900000)])
        queries = []
        def provider(after):
            queries.append(after)
            return first if len(queries)==1 else second
        got = fetch_closed("15m", 900000, 3, fetch_page=provider, now_ms=10*900000)
        self.assertEqual([x["open_time"] for x in got],[900000, 1800000, 2700000])
        self.assertEqual(queries, [None, "1800000"])

    def test_reject_missing_candle_gap(self):
        def provider(after):
            return payload([candle(4*900000), candle(2*900000), candle(900000)])
        with self.assertRaises(ValueError):
            fetch_closed("15m", 900000, 3, fetch_page=provider, now_ms=10*900000)

    def test_refuse_inconsistent_duplicate(self):
        with self.assertRaises(ValueError):
            fetch_closed("15m",900000,3,fetch_page=lambda _:payload([
                candle(3*900000),candle(3*900000,close="99"),candle(2*900000)]),now_ms=10*900000)

    @patch("quant_engine.okx_ohlcv.time.sleep")
    def test_rate_limited_page_retries_then_keeps_real_data(self, sleep):
        outcomes = iter([{"code":"50011","data":[]},
                         payload([candle(3*900000),candle(2*900000)])])
        got=fetch_closed("15m",900000,2,fetch_page=lambda _:next(outcomes),
                         now_ms=10*900000)
        self.assertEqual([c["open_time"] for c in got],[1800000,2700000])
        self.assertTrue(sleep.called)

    @patch("quant_engine.okx_ohlcv.time.sleep")
    def test_rate_limit_exhaustion_fails_closed(self, sleep):
        with self.assertRaises(ValueError):
            fetch_closed("15m",900000,2,fetch_page=lambda _:{"code":"50011","data":[]},
                         now_ms=10*900000)
    def test_atomic_csv_and_manifest(self):
        m = [{"open_time":i*900000,"open":100.0,"high":105.0,"low":95.0,
              "close":100.0,"volume":10.0,"closed":True} for i in range(2)]
        h = [{"open_time":i*3600000,"open":100.0,"high":105.0,"low":95.0,
              "close":100.0,"volume":10.0,"closed":True} for i in range(2)]
        with tempfile.TemporaryDirectory() as tmp:
            metadata = write_dataset(Path(tmp),m,h,requested_at_ms=30000000)
            self.assertTrue((Path(tmp)/"m15.csv").exists())
            self.assertTrue((Path(tmp)/"h1.csv").exists())
            self.assertTrue(metadata["dataset_sha256"].startswith("sha256:"))
            self.assertEqual(json.loads((Path(tmp)/"manifest.json").read_text())["source"],"OKX_PUBLIC_HISTORY")

if __name__=="__main__":
    unittest.main()
