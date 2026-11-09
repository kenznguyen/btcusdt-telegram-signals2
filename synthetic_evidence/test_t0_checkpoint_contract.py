import hashlib
import unittest

from synthetic_evidence.t0_checkpoint_contract import (
    canonical_json_bytes, canonical_row_bytes, checkpoint_object_digest,
    merkle_root, parse_json_strict, row_leaf, assess_partition,
    verify_canonical_bytes, partition_leaf, checkpoint_content_root, candle_rows_root,
)


class CanonicalizationTests(unittest.TestCase):
    def row(self):
        return {"exchange": "binance", "market_type": "USDT_PERPETUAL", "symbol": "BTCUSDT",
                "timeframe": "15m", "open_time_ms": "0", "open": "1", "high": "2",
                "low": "1", "close": "2", "volume": "0", "available_at_ms": "900000"}

    def test_normative_row_vector_exact_bytes_and_leaf(self):
        expected = (b'{"available_at_ms":"900000","close":"2","exchange":"binance",'
                    b'"high":"2","low":"1","market_type":"USDT_PERPETUAL",'
                    b'"open":"1","open_time_ms":"0","symbol":"BTCUSDT",'
                    b'"timeframe":"15m","volume":"0"}')
        self.assertEqual(canonical_row_bytes(self.row()), expected)
        self.assertEqual(len(expected), 193)
        self.assertEqual(row_leaf(self.row()), "ca1d9eae5d9ae2022ccfe5226cc06f3429f5c1428e04e1d1c54b1f83c56fa32f")

    def test_jcs_utf16_key_order_and_unicode_no_normalization(self):
        self.assertEqual(canonical_json_bytes({"😀": "x", "\ue000": "y", "a": "z"}),
                         '{"a":"z","😀":"x","\ue000":"y"}'.encode())
        self.assertNotEqual(canonical_json_bytes({"v": "é"}), canonical_json_bytes({"v": "e\u0301"}))

    def test_rejects_duplicate_keys_invalid_utf8_and_bom(self):
        for data in (b'{"a":"1","a":"2"}', b'{"v":"\xff"}', b'\xef\xbb\xbf{"v":"1"}'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                parse_json_strict(data)

    def test_rejects_json_numbers_and_unpaired_surrogates(self):
        for value in ({"v": 1}, {"v": 1.5}, {"v": float("nan")}, {"v": "\ud800"}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                canonical_json_bytes(value)

    def test_rejects_noncanonical_bytes(self):
        self.assertEqual(verify_canonical_bytes(b'{"a":"1","b":"2"}'), {"a": "1", "b": "2"})
        with self.assertRaisesRegex(ValueError, "not canonical"):
            verify_canonical_bytes(b'{ "a":"1", "b":"2" }')

    def test_object_digest_domain_and_length_binding(self):
        payload = b'{"schema":"synthetic"}'
        expected = hashlib.sha256(b"T0-EVIDENCE-OBJECT-V1\0" + len(payload).to_bytes(8, "big") + payload).hexdigest()
        self.assertEqual(checkpoint_object_digest(payload), expected)


class MerkleTests(unittest.TestCase):
    def test_empty_root_and_single_leaf(self):
        self.assertEqual(merkle_root([]).hex(), "ccf8ef877bb093aa73ae77a02b9200985c41519920c83b515a0a4a99561e73f7")
        leaf = b"\x11" * 32
        self.assertEqual(merkle_root([leaf]), leaf)

    def test_odd_node_is_promoted_without_duplication(self):
        leaves = [bytes([n]) * 32 for n in (1, 2, 3)]
        left = hashlib.sha256(b"T0-MERKLE-NODE-V1\0" + leaves[0] + leaves[1]).digest()
        self.assertEqual(merkle_root(leaves), hashlib.sha256(b"T0-MERKLE-NODE-V1\0" + left + leaves[2]).digest())

    def test_rows_root_rejects_mixed_timeframe_and_wrong_order(self):
        row0 = CanonicalizationTests().row()
        row1 = dict(row0, open_time_ms="900000", available_at_ms="1800000")
        self.assertEqual(len(candle_rows_root([row0, row1])), 64)
        with self.assertRaises(ValueError):
            candle_rows_root([row1, row0])
        with self.assertRaises(ValueError):
            candle_rows_root([row0, dict(row1, timeframe="1h")])

    def test_partition_root_and_ordered_checkpoint_root(self):
        base = {"exchange": "binance", "market_type": "USDT_PERPETUAL", "symbol": "BTCUSDT",
                "start_ms": "0", "end_ms": "3600000", "row_count": "0",
                "first_open_time_ms": None, "last_open_time_ms": None,
                "row_root": "ccf8ef877bb093aa73ae77a02b9200985c41519920c83b515a0a4a99561e73f7"}
        m15, h1 = dict(base, timeframe="15m"), dict(base, timeframe="1h")
        self.assertEqual(checkpoint_content_root([m15, h1]), checkpoint_content_root([m15, h1]))
        self.assertEqual(len(partition_leaf(m15)), 64)
        with self.assertRaisesRegex(ValueError, "ordered"):
            checkpoint_content_root([h1, m15])

    def test_rejects_overlapping_partition_ranges(self):
        base = {"exchange": "binance", "market_type": "USDT_PERPETUAL", "symbol": "BTCUSDT",
                "timeframe": "15m", "row_count": "0", "first_open_time_ms": None,
                "last_open_time_ms": None,
                "row_root": "ccf8ef877bb093aa73ae77a02b9200985c41519920c83b515a0a4a99561e73f7"}
        a = dict(base, start_ms="0", end_ms="1800000")
        b = dict(base, start_ms="900000", end_ms="2700000")
        with self.assertRaisesRegex(ValueError, "overlap"):
            checkpoint_content_root([a, b])


class CompletenessOracleTests(unittest.TestCase):
    def row(self, opening):
        return {"exchange": "binance", "market_type": "USDT_PERPETUAL", "symbol": "BTCUSDT",
                "timeframe": "15m", "open_time_ms": str(opening), "open": "1", "high": "2",
                "low": "1", "close": "2", "volume": "0", "available_at_ms": str(opening + 900000)}

    def assess(self, rows, **kwargs):
        return assess_partition("15m", "0", "2700000", rows, **kwargs)

    def test_complete_exact_expected_set(self):
        result = self.assess([self.row(0), self.row(900000), self.row(1800000)])
        self.assertEqual((result["status"], result["expected_count"], result["returned_count"]), ("COMPLETE", 3, 3))
        self.assertEqual(result["gaps"], [])

    def test_missing_middle_slot_exact_gap(self):
        result = self.assess([self.row(0), self.row(1800000)])
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["gaps"], [{"start_ms": "900000", "end_ms": "1800000", "missing_count": 1}])

    def test_empty_range_data_is_incomplete(self):
        result = self.assess([])
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["gaps"], [{"start_ms": "0", "end_ms": "2700000", "missing_count": 3}])

    def test_duplicate_offgrid_outside_wrong_market_and_unclosed_rows_are_invalid(self):
        cases = [
            [self.row(0), self.row(0)],
            [self.row(0), self.row(900001)],
            [self.row(0), self.row(2700000)],
            [dict(self.row(0), symbol="ETHUSDT")],
            [dict(self.row(0), available_at_ms="899999")],
        ]
        for rows in cases:
            with self.subTest(rows=rows):
                self.assertEqual(self.assess(rows)["status"], "INVALID")

    def test_asof_violation_is_invalid_and_missing_page_is_unknown(self):
        self.assertEqual(self.assess([self.row(0)], as_of_ms="899999")["status"], "INVALID")
        self.assertEqual(self.assess([self.row(0)], input_complete=False)["status"], "UNKNOWN")

    def test_noncanonical_decimal_and_invalid_range_are_invalid(self):
        self.assertEqual(self.assess([dict(self.row(0), open="1.00")])["status"], "INVALID")
        self.assertEqual(assess_partition("15m", "1", "2700000", [])["status"], "INVALID")
        self.assertEqual(assess_partition("15m", "0", "0", [])["status"], "INVALID")


if __name__ == "__main__":
    unittest.main()
