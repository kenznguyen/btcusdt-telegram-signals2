"""Strict offline parser tests for captured Binance USDⓈ-M funding-rate pages."""

import hashlib
import json
import unittest

from paper_execution.binance_public_funding import (
    parse_binance_usdm_funding_rate_page,
)


START = 1_000
END = 10_000
SNAPSHOT = "d07-public-market-snapshot-001"


def row(at=2_000, *, rate="0.001", mark="100", symbol="BTCUSDT", rate_type="Regular"):
    return {
        "symbol": symbol,
        "fundingRate": rate,
        "fundingTime": at,
        "markPrice": mark,
        "rateType": rate_type,
    }


def parse(records, *, raw=None, expected_count=None, start=START, end=END,
          snapshot=SNAPSHOT, digest=None, byte_length=None):
    body = json.dumps(records, separators=(",", ":")).encode() if raw is None else raw
    return parse_binance_usdm_funding_rate_page(
        body,
        evidence_snapshot_id=snapshot,
        expected_sha256=digest or "sha256:" + hashlib.sha256(body).hexdigest(),
        expected_byte_length=len(body) if byte_length is None else byte_length,
        start_at_ms=start,
        end_at_ms=end,
        expected_record_count=expected_count,
    )


class BinancePublicFundingParserTest(unittest.TestCase):
    def test_valid_page_maps_to_funding_model_contract(self):
        result = parse([row()])

        self.assertEqual(result, [{
            "eventId": "binance-usdm-funding:BTCUSDT:2000",
            "symbol": "BTCUSDT",
            "fundingTimeMs": 2_000,
            "fundingRate": "0.001",
            "markPrice": "100",
            "sourceSnapshotId": SNAPSHOT,
        }])

    def test_records_must_be_in_ascending_funding_time_order(self):
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_PAGE_ORDER_INVALID"):
            parse([row(at=3_000), row(at=2_000)])

    def test_duplicate_funding_time_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_TIME_DUPLICATE"):
            parse([row(), row()])

    def test_special_rate_type_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_RATE_TYPE_UNSUPPORTED"):
            parse([row(rate_type="Special")])

    def test_symbol_must_be_btcusdt(self):
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_SYMBOL_INVALID"):
            parse([row(symbol="ETHUSDT")])

    def test_rate_and_mark_must_be_decimal_strings(self):
        for field in ("fundingRate", "markPrice"):
            with self.subTest(field=field):
                item = row()
                item[field] = 0.001
                with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_DECIMAL_INVALID"):
                    parse([item])

    def test_mark_price_must_be_positive_and_finite(self):
        for mark in ("0", "-1", "NaN", "Infinity"):
            with self.subTest(mark=mark):
                with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_MARK_PRICE_INVALID"):
                    parse([row(mark=mark)])

    def test_funding_rate_must_be_finite(self):
        for rate_value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(rate=rate_value):
                with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_RATE_INVALID"):
                    parse([row(rate=rate_value)])

    def test_funding_time_must_be_integer_not_boolean(self):
        item = row()
        item["fundingTime"] = True
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_TIME_INVALID"):
            parse([item])

    def test_scope_is_half_open(self):
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_TIME_OUTSIDE_SCOPE"):
            parse([row(at=END)])

    def test_unknown_or_missing_response_fields_are_rejected(self):
        item = row()
        item["extra"] = "value"
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_RECORD_FIELDS_INVALID"):
            parse([item])

        item = row()
        del item["rateType"]
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_RECORD_FIELDS_INVALID"):
            parse([item])

    def test_duplicate_json_object_keys_are_rejected(self):
        raw = b'[{"symbol":"BTCUSDT","symbol":"ETHUSDT","fundingRate":"0.001","fundingTime":2000,"markPrice":"100","rateType":"Regular"}]'
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_JSON_DUPLICATE_KEY"):
            parse([], raw=raw)

    def test_invalid_json_and_invalid_utf8_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_JSON_INVALID"):
            parse([], raw=b"{")
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_JSON_INVALID"):
            parse([], raw=b"\xff")

    def test_page_hash_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_PAGE_DIGEST_MISMATCH"):
            parse([row()], digest="sha256:" + "0" * 64)

    def test_page_byte_length_mismatch_is_rejected(self):
        body = json.dumps([row()]).encode()
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_PAGE_LENGTH_MISMATCH"):
            parse([row()], byte_length=len(body) + 1)

    def test_page_record_count_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_PAGE_COUNT_MISMATCH"):
            parse([row()], expected_count=2)

    def test_page_limit_is_1000_records(self):
        records = [row(at=2_000 + index) for index in range(1_001)]
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_PAGE_TOO_LARGE"):
            parse(records)

    def test_empty_terminal_page_is_valid(self):
        self.assertEqual(parse([]), [])

    def test_source_snapshot_id_is_required(self):
        with self.assertRaisesRegex(ValueError, "BINANCE_FUNDING_SNAPSHOT_ID_INVALID"):
            parse([row()], snapshot=" ")


if __name__ == "__main__":
    unittest.main()
