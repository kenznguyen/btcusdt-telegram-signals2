import unittest

from market_data.kraken_spot import (
    InstrumentIdentity,
    KrakenSpotAdapter,
    SourceCandle,
    SYMBOL,
)

START = 1_800_000_000_000
STEP = 900_000


def row(opened, close="102.0"):
    return [opened, 100.0, 105.0, 99.0, close, 1.5]


class FakeKraken:
    id = "kraken"

    def __init__(self, rows=None):
        self.rows = rows or []
        self.market = {
            "id": "XBTUSDT",
            "symbol": SYMBOL,
            "base": "BTC",
            "quote": "USDT",
            "active": True,
            "spot": True,
            "swap": False,
        }
        self.fetch_args = None
        self.server_time = START + 10 * STEP

    def load_markets(self):
        return {SYMBOL: self.market}

    def fetch_time(self):
        return self.server_time

    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        self.fetch_args = (symbol, timeframe, since, limit)
        return self.rows


class KrakenSpotAdapterTest(unittest.TestCase):
    def test_validates_active_spot_identity_and_preserves_native_market_id(self):
        adapter = KrakenSpotAdapter(FakeKraken())
        identity = adapter.validate_market()
        self.assertEqual(
            identity,
            InstrumentIdentity("kraken", "SPOT", "XBTUSDT", "BTC/USDT"),
        )

    def test_rejects_wrong_exchange_market_type_and_missing_native_id(self):
        cases = (
            ("binanceusdm", {}),
            ("kraken", {"active": False}),
            ("kraken", {"spot": False}),
            ("kraken", {"swap": True}),
            ("kraken", {"quote": "USD"}),
            ("kraken", {"id": ""}),
        )
        for exchange_id, override in cases:
            exchange = FakeKraken()
            exchange.id = exchange_id
            exchange.market.update(override)
            with self.subTest(exchange=exchange_id, override=override):
                with self.assertRaises(ValueError):
                    KrakenSpotAdapter(exchange).validate_market()

    def test_fetches_only_closed_candles_and_retains_source_provenance(self):
        exchange = FakeKraken([row(START), row(START + STEP)])
        candles = KrakenSpotAdapter(exchange).fetch_closed_window(
            "15m", START, START + 2 * STEP, now_ms=START + STEP + 500
        )
        self.assertEqual(len(candles), 1)
        candle = candles[0]
        self.assertEqual(candle.instrument.exchange, "kraken")
        self.assertEqual(candle.instrument.market_type, "SPOT")
        self.assertEqual(candle.instrument.native_market_id, "XBTUSDT")
        self.assertEqual(candle.instrument.canonical_symbol, "BTC/USDT")
        self.assertEqual(candle.available_at_ms, START + STEP + 500)
        self.assertEqual(
            exchange.fetch_args, (SYMBOL, "15m", START, 2)
        )
        self.assertEqual(candle.as_dict()["source"], "ccxt.kraken")
        self.assertEqual(candle.as_dict()["marketType"], "SPOT")

    def test_uses_the_earlier_exchange_or_local_clock_for_closed_status(self):
        exchange = FakeKraken([row(START), row(START + STEP)])
        exchange.server_time = START + STEP + 100
        candles = KrakenSpotAdapter(exchange).fetch_closed_window(
            "15m", START, START + 2 * STEP, now_ms=START + 2 * STEP
        )
        self.assertEqual([item.open_time_ms for item in candles], [START])

    def test_rejects_unaligned_oversized_or_unsupported_windows(self):
        adapter = KrakenSpotAdapter(FakeKraken())
        for args in (
            ("5m", START, START + STEP),
            ("15m", START + 1, START + STEP),
            ("15m", START, START + 2001 * STEP),
            ("15m", START + STEP, START),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                adapter.fetch_closed_window(*args, now_ms=START + 10 * STEP)

    def test_rejects_out_of_order_and_malformed_ohlcv_rows(self):
        for rows in (
            [row(START + STEP), row(START)],
            [[START, 100.0, 105.0, 99.0, 102.0]],
            [row(START, close="NaN")],
            [[START, 100.0, 99.0, 101.0, 102.0, 1.5]],
        ):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                KrakenSpotAdapter(FakeKraken(rows)).fetch_closed_window(
                    "15m", START, START + 2 * STEP,
                    now_ms=START + 3 * STEP,
                )

    def test_source_candle_rejects_negative_volume_and_conflicting_ohlc(self):
        identity = InstrumentIdentity("kraken", "SPOT", "XBTUSDT", SYMBOL)
        base = dict(
            instrument=identity, timeframe="15m", open_time_ms=START,
            open="100", high="105", low="99", close="102",
            volume="1", available_at_ms=START + STEP,
        )
        with self.assertRaises(ValueError):
            SourceCandle(**dict(base, volume="-1"))
        with self.assertRaises(ValueError):
            SourceCandle(**dict(base, close="106"))


if __name__ == "__main__":
    unittest.main()
