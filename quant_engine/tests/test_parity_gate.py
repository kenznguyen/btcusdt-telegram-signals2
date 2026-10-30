import unittest
from quant_engine.parity_gate import verify_bundle


EVENT = dict(symbol="BTCUSDT", trade_id="t1", event="ENTRY",
             candle_close_ms=100, direction="LONG",
             expected_fill_price=100.0, actual_fill_price=100.0,
             fill_difference=0.0)


def bundle(engine):
    return dict(schema_version=1, producer=engine, engine_commit="abc123",
                candle_sha256="f" * 64, closed_candles_only=True,
                events=[dict(EVENT)])


class ParityGateTests(unittest.TestCase):
    def test_independent_valid_traces_match(self):
        self.assertTrue(verify_bundle(bundle("KOTLIN"), bundle("PYTHON"))["parity_verified"])

    def test_missing_producer_fails(self):
        self.assertFalse(verify_bundle(None, bundle("PYTHON"))["parity_verified"])

    def test_same_producer_fails(self):
        self.assertFalse(verify_bundle(bundle("PYTHON"), bundle("PYTHON"))["parity_verified"])

    def test_candle_checksum_mismatch_fails(self):
        py = bundle("PYTHON")
        py["candle_sha256"] = "a" * 64
        self.assertFalse(verify_bundle(bundle("KOTLIN"), py)["parity_verified"])

    def test_open_candle_fails(self):
        py = bundle("PYTHON")
        py["closed_candles_only"] = False
        self.assertFalse(verify_bundle(bundle("KOTLIN"), py)["parity_verified"])

    def test_empty_traces_fail(self):
        a, b = bundle("KOTLIN"), bundle("PYTHON")
        a["events"] = []
        b["events"] = []
        self.assertFalse(verify_bundle(a, b)["parity_verified"])

    def test_event_difference_fails(self):
        py = bundle("PYTHON")
        py["events"][0]["direction"] = "SHORT"
        self.assertFalse(verify_bundle(bundle("KOTLIN"), py)["parity_verified"])

if __name__ == "__main__":
    unittest.main()
