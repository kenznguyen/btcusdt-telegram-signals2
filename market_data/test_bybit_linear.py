import unittest
from market_data.bybit_linear import BybitLinearAdapter, BybitLinearCandle

START = 1_800_000_000_000
STEP = 900_000
INSTRUMENT = {"symbol":"BTCUSDT","contractType":"LinearPerpetual","status":"Trading","baseCoin":"BTC","quoteCoin":"USDT"}


class FakeBybit:
    def __init__(self, rows=None, instrument=None, server=None):
        self.rows = rows if rows is not None else []
        self.instrument = instrument if instrument is not None else INSTRUMENT
        self.server = server if server is not None else START + 10*STEP
        self.calls = []
    def __call__(self, path, params):
        self.calls.append((path, params))
        if path.endswith("instruments-info"):
            return {"list":[self.instrument]}
        if path.endswith("/time"):
            return {"timeNano":str(self.server*1_000_000)}
        if path.endswith("/kline"):
            return {"list":self.rows}
        raise AssertionError(path)


def row(opened, close="102.00"):
    return [str(opened), "100.00", "105.00", "99.00", close, "1.250", "125.000"]


class BybitLinearAdapterTests(unittest.TestCase):
    def test_fetches_reverse_order_rows_and_preserves_exact_decimal_strings(self):
        fake = FakeBybit([row(START+STEP), row(START)])
        adapter = BybitLinearAdapter(fake)
        result = adapter.fetch_closed_window("15m", START, START+2*STEP, now_ms=START+3*STEP)
        self.assertEqual([c.open_time_ms for c in result], [START, START+STEP])
        self.assertEqual(result[0].close, "102.00")
        self.assertEqual(result[0].volume_btc, "1.250")
        self.assertEqual(result[0].as_dict()["marketType"], "LINEAR_PERPETUAL")
        self.assertEqual(fake.calls[-1][1]["category"], "linear")

    def test_excludes_unclosed_candle_using_earlier_server_or_local_clock(self):
        fake = FakeBybit([row(START+STEP), row(START)], server=START+STEP+100)
        result = BybitLinearAdapter(fake).fetch_closed_window(
            "15m", START, START+2*STEP, now_ms=START+2*STEP
        )
        self.assertEqual([c.open_time_ms for c in result], [START])

    def test_rejects_non_linear_or_non_btcusdt_instrument(self):
        for field, value in (("status","Closed"),("contractType","InversePerpetual"),("quoteCoin","USD")):
            bad = dict(INSTRUMENT); bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                BybitLinearAdapter(FakeBybit(instrument=bad)).fetch_closed_window(
                    "15m", START, START+STEP, now_ms=START+STEP
                )

    def test_rejects_duplicate_unaligned_and_malformed_rows(self):
        cases = (
            [row(START), row(START)],
            [[str(START+1), "100","105","99","102","1","100"]],
            [[str(START), "100","105","99","NaN","1","100"]],
            [[str(START), "100","99","101","102","1","100"]],
        )
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                BybitLinearAdapter(FakeBybit(rows)).fetch_closed_window(
                    "15m", START, START+STEP, now_ms=START+2*STEP
                )

    def test_rejects_unsupported_or_oversized_windows(self):
        adapter = BybitLinearAdapter(FakeBybit())
        for timeframe, start, end in (
            ("5m", START, START+STEP),
            ("15m", START+1, START+STEP),
            ("15m", START, START+1001*STEP),
        ):
            with self.subTest(timeframe=timeframe), self.assertRaises(ValueError):
                adapter.fetch_closed_window(timeframe,start,end,now_ms=START+2000*STEP)

    def test_rejects_non_string_decimal_payload(self):
        with self.assertRaises(ValueError):
            BybitLinearCandle("15m", START, 100, "105", "99", "102", "1", "100", START+STEP)


if __name__ == "__main__":
    unittest.main()
