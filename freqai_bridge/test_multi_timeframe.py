"""Independent fixture tests for paginated M15/H1 T0 HTTP consumption."""

import hashlib
import json
import unittest

from freqai_bridge.http_candles import CandleHttpClient, CandleHttpConfig, CandleHttpError


STEP = {"15m": 900_000, "1h": 3_600_000}
START = 1_800_000_000_000


class FakeResponse:
    def __init__(self, payload):
        self.status_code = 200
        self.headers = {"Content-Type": "application/json"}
        self.body = json.dumps(payload, separators=(",", ":")).encode()

    def iter_content(self, chunk_size=8192):
        for offset in range(0, len(self.body), chunk_size):
            yield self.body[offset:offset + chunk_size]

    def close(self):
        pass


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def page(timeframe, start, end, as_of, *, bad_coverage=False, bad_identity=False, lag=1_000):
    interval = STEP[timeframe]
    candles = []
    for opened in range(start, end, interval):
        closed = opened + interval
        candles.append({
            "exchange": "binance", "marketType": "USDT_PERPETUAL",
            "symbol": "ETHUSDT" if bad_identity else "BTCUSDT",
            "timeframe": timeframe, "openTimeMs": opened, "closeTimeMs": closed,
            "open": "100", "high": "102", "low": "99", "close": "101",
            "volume": "2", "isClosed": True, "availableAtMs": closed + lag,
            "availabilityKind": "FIRST_OBSERVED", "quality": "VALIDATED",
            "source": "ccxt.binanceusdm",
        })
    generated = as_of + 5_000
    latest = candles[-1]
    return {
        "contractVersion": "1.0.0", "schemaVersion": 1,
        "exchange": "binance", "marketType": "USDT_PERPETUAL", "symbol": "BTCUSDT",
        "timeframe": timeframe, "startMs": start, "endMs": end, "asOfMs": as_of,
        "candles": candles, "datasetVersion": "sha256:" + "a" * 64,
        "coverage": {
            "expected": len(candles), "returned": len(candles) - int(bad_coverage),
            "complete": not bad_coverage, "gaps": [{"startMs": start, "endMs": end}] if bad_coverage else [],
        },
        "volumeUnit": "BTC_BASE_ASSET", "source": "ccxt.binanceusdm",
        "generatedAtMs": generated,
        "freshness": {
            "latestExpectedOpenTimeMs": latest["openTimeMs"],
            "latestReturnedOpenTimeMs": latest["openTimeMs"],
            "latestCloseTimeMs": latest["closeTimeMs"],
            "latestAvailableAtMs": latest["availableAtMs"],
            "observationAgeMs": generated - latest["availableAtMs"],
            "closeLagMs": generated - latest["closeTimeMs"], "evaluable": True,
        },
    }


class T2MultiTimeframeFixtureTest(unittest.TestCase):
    def client(self, responses):
        session = FakeSession(responses)
        client = CandleHttpClient(
            CandleHttpConfig("https://t0.example.invalid", "fixture-token", 120_000),
            session=session, sleep=lambda _: None, clock_ms=lambda: 2**62,
        )
        return client, session

    def run_window(self, timeframe, bars, responses):
        interval = STEP[timeframe]
        start = START // interval * interval
        end = start + bars * interval
        as_of = end + 60_000
        client, session = self.client(responses(start, end, as_of, interval))
        result = client.fetch(start, end, as_of, timeframe=timeframe)
        return result, session, start, end, as_of

    def test_m15_window_over_32_bars_is_paginated_and_hashes_full_dataset(self):
        def fixtures(start, end, as_of, interval):
            return [
                FakeResponse(page("15m", start, start + 32 * interval, as_of)),
                FakeResponse(page("15m", start + 32 * interval, end, as_of)),
            ]
        result, session, start, end, as_of = self.run_window("15m", 33, fixtures)
        self.assertEqual([c["timeframe"] for c in result["candles"]], ["15m"] * 33)
        self.assertEqual([call["params"]["timeframe"] for call in session.calls], ["15m", "15m"])
        self.assertEqual([call["params"]["startMs"] for call in session.calls], [start, start + 32 * STEP["15m"]])
        self.assertEqual(result["coverage"], {"expected": 33, "returned": 33, "complete": True, "gaps": []})
        identity = {key: result[key] for key in ("exchange", "marketType", "symbol", "timeframe", "startMs", "endMs", "asOfMs", "candles")}
        expected_hash = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(result["datasetVersion"], "sha256:" + expected_hash)
        self.assertEqual(result["asOfMs"], as_of)

    def test_h1_window_over_32_bars_is_paginated_on_hour_boundaries(self):
        def fixtures(start, end, as_of, interval):
            return [
                FakeResponse(page("1h", start, start + 32 * interval, as_of)),
                FakeResponse(page("1h", start + 32 * interval, end, as_of)),
            ]
        result, session, start, end, _ = self.run_window("1h", 34, fixtures)
        self.assertEqual(len(result["candles"]), 34)
        self.assertEqual(result["timeframe"], "1h")
        self.assertEqual(session.calls[0]["params"]["startMs"], start)
        self.assertEqual(session.calls[1]["params"]["startMs"], start + 32 * STEP["1h"])
        self.assertEqual(session.calls[1]["params"]["endMs"], end)
        self.assertEqual(result["coverage"]["complete"], True)

    def test_any_page_with_incomplete_coverage_fails_closed(self):
        def fixtures(start, end, as_of, interval):
            return [
                FakeResponse(page("15m", start, start + 32 * interval, as_of)),
                FakeResponse(page("15m", start + 32 * interval, end, as_of, bad_coverage=True)),
            ]
        interval = STEP["15m"]
        start = START // interval * interval
        end = start + 33 * interval
        client, _ = self.client(fixtures(start, end, end + 60_000, interval))
        with self.assertRaises(CandleHttpError):
            client.fetch(start, end, end + 60_000, timeframe="15m")

    def test_identity_mismatch_in_later_page_fails_closed(self):
        def fixtures(start, end, as_of, interval):
            return [
                FakeResponse(page("1h", start, start + 32 * interval, as_of)),
                FakeResponse(page("1h", start + 32 * interval, end, as_of, bad_identity=True)),
            ]
        interval = STEP["1h"]
        start = START // interval * interval
        end = start + 33 * interval
        client, _ = self.client(fixtures(start, end, end + 60_000, interval))
        with self.assertRaises(CandleHttpError):
            client.fetch(start, end, end + 60_000, timeframe="1h")

    def test_ingestion_freshness_over_limit_in_any_page_fails_closed(self):
        def fixtures(start, end, as_of, interval):
            return [
                FakeResponse(page("15m", start, start + 32 * interval, as_of)),
                FakeResponse(page("15m", start + 32 * interval, end, as_of, lag=120_001)),
            ]
        interval = STEP["15m"]
        start = START // interval * interval
        end = start + 33 * interval
        client, _ = self.client(fixtures(start, end, end + 180_000, interval))
        with self.assertRaises(CandleHttpError):
            client.fetch(start, end, end + 180_000, timeframe="15m")

    def test_unsupported_timeframe_and_oversized_total_window_are_rejected_before_io(self):
        client, session = self.client([])
        with self.assertRaises(CandleHttpError):
            client.fetch(START, START + STEP["15m"], START + STEP["15m"], timeframe="4h")
        with self.assertRaises(CandleHttpError):
            client.fetch(START, START + 3001 * STEP["15m"], START + 3001 * STEP["15m"], timeframe="15m")
        self.assertEqual(session.calls, [])


if __name__ == "__main__":
    unittest.main()
