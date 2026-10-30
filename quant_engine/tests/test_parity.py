import unittest
from quant_engine.parity import compare_traces


class ParityTests(unittest.TestCase):
    def test_missing_trace_fails_closed(self):
        self.assertFalse(compare_traces([], []).parity_verified)
        self.assertFalse(compare_traces(None, [{"event": "ENTRY"}]).parity_verified)

    def test_incomplete_trace_fails_closed(self):
        self.assertFalse(compare_traces([{"event": "ENTRY"}], [{"event": "ENTRY"}]).parity_verified)

    def test_mismatch_fails_closed(self):
        event = dict(symbol="BTCUSDT", trade_id="t", event="DCA", candle_close_ms=100,
                     direction="LONG", expected_fill_price=100.0,
                     actual_fill_price=101.0, fill_difference=1.0)
        other = dict(event, actual_fill_price=102.0)
        self.assertFalse(compare_traces([event], [other]).parity_verified)
        self.assertTrue(compare_traces([event], [dict(event)]).parity_verified)
