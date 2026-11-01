import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from data_lake.local_setup import SECRET_KEYS, prepare_configuration
from data_lake.local_verify import main, verify_local, verify_windows
from data_lake.client import DataLakeClient
from data_lake.test_client import ApiTransport, Response
from market_data.store import Candle, CandleStore, INTERVAL_MS, MAX_TIMESTAMP, read_window


class LocalVerifyTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.database = self.directory / "candles.sqlite3"
        self.store = CandleStore(self.database)
        self.now = 1_700_000_000_000 // INTERVAL_MS["1h"] * INTERVAL_MS["1h"] + INTERVAL_MS["15m"] + 1234
        self.candles = {}
        for timeframe, step in INTERVAL_MS.items():
            end = self.now // step * step
            self.candles[timeframe] = [Candle(timeframe, end + (i-2)*step, "100", "101", "99",
                                            "100.00000000000000000001", "2.5", end+(i-1)*step+7)
                                       for i in range(2)]
        self.transport = ApiTransport(self.database)
        self.client = DataLakeClient("http://127.0.0.1:8788", self.transport.token)
        self.client._opener = self.transport

    def test_complete_real_api_windows_keep_hash_precision_and_one_frozen_cutoff(self):
        self.store.insert([candle for candles in self.candles.values() for candle in candles])
        with patch("data_lake.local_verify.time") as clock:
            clock.time_ns.return_value = self.now * 1_000_000
            result = verify_windows(self.client, bars=2)
        self.assertTrue(result["verified"])
        clock.time_ns.assert_called_once_with()
        for timeframe, step in INTERVAL_MS.items():
            end = self.now // step * step
            canonical = read_window(self.database, "BTCUSDT", timeframe, end-2*step, end, self.now)
            self.assertEqual(result["timeframes"][timeframe], {
                "expected": 2, "returned": 2, "complete": True,
                "datasetVersion": canonical["datasetVersion"], "latestCloseTimeMs": end,
                "latestClose": "100.00000000000000000001", "reason": "VERIFIED"})
        for request, _ in self.transport.requests:
            self.assertEqual(parse_qs(urlsplit(request.full_url).query)["asOfMs"], [str(self.now)])

    def test_partial_empty_stale_and_not_yet_observed_data_are_honest(self):
        self.store.insert([self.candles["15m"][0]])
        hourly = self.candles["1h"][0]
        self.store.insert([Candle("1h", hourly.open_time_ms-INTERVAL_MS["1h"], "100", "101", "99", "100", "1",
                                 hourly.open_time_ms),
                           Candle("1h", hourly.open_time_ms, "100", "101", "99", "100", "1", self.now+1)])
        result = verify_windows(self.client, bars=2, now_ms=self.now)
        self.assertFalse(result["verified"])
        partial, empty = result["timeframes"]["15m"], result["timeframes"]["1h"]
        self.assertEqual((partial["returned"], partial["complete"], partial["reason"]), (1, False, "INCOMPLETE_WINDOW"))
        self.assertEqual(partial["latestCloseTimeMs"], self.candles["15m"][0].as_dict()["closeTimeMs"])
        self.assertEqual((empty["returned"], empty["complete"], empty["latestClose"], empty["latestCloseTimeMs"]),
                         (0, False, None, None))
        self.assertTrue(empty["datasetVersion"].startswith("sha256:"))

    def test_invalid_arguments_fail_before_requests(self):
        for bars in (0, -1, True, 2001, 1.5, "20"):
            with self.subTest(bars=bars), self.assertRaisesRegex(ValueError, "^INVALID_VERIFY_BARS$"):
                verify_windows(self.client, bars=bars, now_ms=self.now)
        for now in (-1, True, MAX_TIMESTAMP+1, 0, time.time_ns()//1_000_000+60_000):
            with self.subTest(now=now), self.assertRaisesRegex(ValueError, "^INVALID_VERIFY_TIME$"):
                verify_windows(self.client, now_ms=now)
        self.assertEqual(self.transport.requests, [])

    def test_corrupt_hash_source_and_future_response_are_failures_without_fake_prices(self):
        self.store.insert([candle for candles in self.candles.values() for candle in candles])
        original_open = self.transport.open
        mutations = ((lambda body: body.update(datasetVersion="sha256:"+"0"*64), "DATASET_HASH_MISMATCH"),
                     (lambda body: body["candles"][0].update(source="untrusted"), "INVALID_CANDLE_PROVENANCE"),
                     (lambda body: body.update(generatedAtMs=time.time_ns()//1_000_000+60_000), "FUTURE_RESPONSE"))
        for mutate, reason in mutations:
            def corrupt(request, timeout):
                response = original_open(request, timeout)
                if parse_qs(urlsplit(request.full_url).query)["timeframe"] == ["1h"]:
                    return response
                with response:
                    body = json.loads(response.read())
                mutate(body)
                return Response(body)

            with self.subTest(reason=reason), patch.object(self.transport, "open", side_effect=corrupt):
                result = verify_windows(self.client, bars=2, now_ms=self.now)
            self.assertFalse(result["verified"])
            failed = result["timeframes"]["15m"]
            self.assertEqual(failed["reason"], reason)
            self.assertEqual((failed["returned"], failed["latestClose"], failed["datasetVersion"]), (None, None, None))
            self.assertTrue(result["timeframes"]["1h"]["complete"])

    def test_transport_errors_never_echo_credentials_or_report_zero_candles(self):
        for failure in (OSError(self.transport.token), RuntimeError(self.transport.token)):
            with self.subTest(error=type(failure)), patch.object(self.transport, "open", side_effect=failure):
                result = verify_windows(self.client, bars=2, now_ms=self.now)
            self.assertFalse(result["verified"])
            self.assertNotIn(self.transport.token, json.dumps(result))
            for frame in result["timeframes"].values():
                self.assertIsNone(frame["returned"])
                self.assertFalse(frame["complete"])

    def test_local_cli_uses_private_token_readonly_and_emits_only_safe_summary(self):
        self.store.insert([candle for candles in self.candles.values() for candle in candles])
        config = self.directory / "private.env"
        values = prepare_configuration(config, port=8899)
        self.transport.token = values["LAKE_READ_TOKEN"]
        original = config.read_bytes()
        output = io.StringIO()
        with patch("data_lake.client.build_opener", return_value=self.transport), \
                patch("data_lake.local_verify.time") as clock, patch("sys.stdout", output):
            clock.time_ns.return_value = self.now*1_000_000
            self.assertEqual(main(["--config", str(config), "--bars", "2"]), 0)
        self.assertTrue(json.loads(output.getvalue())["verified"])
        self.assertEqual(config.read_bytes(), original)
        for key in SECRET_KEYS:
            self.assertNotIn(values[key], output.getvalue())
        for request, _ in self.transport.requests:
            self.assertEqual(urlsplit(request.full_url).netloc, "127.0.0.1:8899")
            self.assertEqual(request.get_header("Authorization"), "Bearer "+values["LAKE_READ_TOKEN"])

    def test_cli_missing_invalid_and_incomplete_fail_safely_without_creating_configuration(self):
        config = self.directory / "missing-secret-path.env"
        with self.assertRaisesRegex(ValueError, "^LOCAL_CONFIG_UNAVAILABLE_OR_INVALID$"):
            verify_local(config, bars=2, now_ms=self.now)
        for arguments, reason in ((["--config", str(config)], "LOCAL_CONFIG_UNAVAILABLE_OR_INVALID"),
                                  (["--bars", self.transport.token], "INVALID_VERIFY_BARS"),
                                  (["--unknown-secret-argument"], "INVALID_VERIFY_ARGUMENTS")):
            output, errors = io.StringIO(), io.StringIO()
            with self.subTest(reason=reason), patch("sys.stdout", output), patch("sys.stderr", errors):
                self.assertEqual(main(arguments), 1)
            self.assertEqual(json.loads(output.getvalue()), {"verified": False, "reason": reason})
            self.assertEqual(errors.getvalue(), "")
        self.assertFalse(config.exists())
        config.write_text("secret="+self.transport.token)
        config.chmod(0o600)
        output = io.StringIO()
        with patch("sys.stdout", output):
            self.assertEqual(main(["--config", str(config)]), 1)
        self.assertNotIn(self.transport.token, output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["reason"], "LOCAL_CONFIG_UNAVAILABLE_OR_INVALID")
        config.unlink()
        values = prepare_configuration(config)
        self.transport.token = values["LAKE_READ_TOKEN"]
        output = io.StringIO()
        with patch("data_lake.client.build_opener", return_value=self.transport), patch("sys.stdout", output):
            self.assertEqual(main(["--config", str(config), "--bars", "2"]), 1)
        result = json.loads(output.getvalue())
        self.assertFalse(result["verified"])
        self.assertEqual(result["timeframes"]["15m"]["returned"], 0)


if __name__ == "__main__":
    unittest.main()
