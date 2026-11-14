import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from paper_execution.funding_evidence_package_builder import build_tardis_funding_evidence_package

HEADER = (
    "exchange,symbol,timestamp,local_timestamp,funding_timestamp,funding_rate,"
    "predicted_funding_rate,open_interest,last_price,index_price,mark_price\n"
)

def gzip_csv(rows):
    import io
    return gzip.compress((HEADER + "".join(rows)).encode("utf-8"), mtime=0)

def row(ts, local, funding, rate="0.0001", exchange="binance-futures", symbol="BTCUSDT"):
    return f"{exchange},{symbol},{ts},{local},{funding},{rate},,,,100,100\n"


class FundingEvidencePackageBuilderTest(unittest.TestCase):
    def test_preserves_exact_gzip_source_and_records_its_digest(self):
        source_bytes = gzip_csv([row(1_000_000, 1_000_001, 8_000_000)])
        with tempfile.TemporaryDirectory() as td:
            source, output = Path(td) / "BTCUSDT.csv", Path(td) / "package"
            source.write_bytes(source_bytes)
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            result = build_tardis_funding_evidence_package(
                source, output, package_id="fixture-001",
                assembled_at_utc="2026-11-14T12:00:00Z", builder_source_sha="a" * 40,
            )
            raw_copy = output / "raw" / "BTCUSDT.csv.gz"
            self.assertEqual(raw_copy.read_bytes(), source_bytes)
            self.assertEqual(hashlib.sha256(raw_copy.read_bytes()).hexdigest(), before)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)
            self.assertEqual(result["manifest"]["files"][0]["sha256"], before)

    def test_manifest_records_rows_observed_settlement_keys_and_no_invented_schedule(self):
        source_bytes = gzip_csv([
            row(1_000_000, 1_000_001, 8_000_000),
            row(2_000_000, 2_000_001, 8_000_000),
            row(3_000_000, 3_000_001, 16_000_000),
        ])
        with tempfile.TemporaryDirectory() as td:
            source, output = Path(td) / "BTCUSDT.csv", Path(td) / "package"
            source.write_bytes(source_bytes)
            result = build_tardis_funding_evidence_package(
                source, output, package_id="fixture-002",
                assembled_at_utc="2026-11-14T12:00:00Z", builder_source_sha="b" * 40,
            )
            manifest = result["manifest"]
            self.assertEqual(manifest["files"][0]["recordCount"], 3)
            self.assertEqual(manifest["coverage"]["observedSettlementTimesMs"], [8_000, 16_000])
            self.assertEqual(manifest["coverage"]["expectedSettlementTimesMs"], [])
            self.assertEqual(manifest["coverage"]["expectedSetAuthority"], "NOT_SUPPLIED_NO_AUTHORITATIVE_EXPECTED_SET")
            self.assertEqual(result["validation"]["completeness"], "NOT_VERIFIED")

    def test_field_mapping_preserves_source_microsecond_units(self):
        with tempfile.TemporaryDirectory() as td:
            source, output = Path(td) / "BTCUSDT.csv", Path(td) / "package"
            source.write_bytes(gzip_csv([row(1_234_567, 1_234_568, 8_000_000)]))
            build_tardis_funding_evidence_package(
                source, output, package_id="fixture-003",
                assembled_at_utc="2026-11-14T12:00:00Z", builder_source_sha="c" * 40,
            )
            mapping = json.loads((output / "transforms" / "field-mapping.json").read_text())
            self.assertEqual(mapping["sourceTimestampUnit"], "MICROSECONDS")
            self.assertEqual(mapping["fundingTimestampNormalization"], "integer_microseconds_divided_by_1000")
            self.assertEqual(mapping["builderSourceSha"], "c" * 40)

    def test_rejects_non_gzip_source_without_creating_package(self):
        with tempfile.TemporaryDirectory() as td:
            source, output = Path(td) / "BTCUSDT.csv", Path(td) / "package"
            source.write_text(HEADER, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "FUNDING_PACKAGE_SOURCE_NOT_GZIP"):
                build_tardis_funding_evidence_package(
                    source, output, package_id="fixture-004",
                    assembled_at_utc="2026-11-14T12:00:00Z", builder_source_sha="d" * 40,
                )
            self.assertFalse(output.exists())

    def test_rejects_wrong_exchange_or_symbol(self):
        with tempfile.TemporaryDirectory() as td:
            source, output = Path(td) / "BTCUSDT.csv", Path(td) / "package"
            source.write_bytes(gzip_csv([row(1_000_000, 1_000_001, 8_000_000, exchange="other")]))
            with self.assertRaisesRegex(ValueError, "FUNDING_PACKAGE_SOURCE_IDENTITY_INVALID"):
                build_tardis_funding_evidence_package(
                    source, output, package_id="fixture-005",
                    assembled_at_utc="2026-11-14T12:00:00Z", builder_source_sha="e" * 40,
                )
            self.assertFalse(output.exists())

    def test_rejects_funding_timestamp_not_exactly_normalizable_to_ms(self):
        with tempfile.TemporaryDirectory() as td:
            source, output = Path(td) / "BTCUSDT.csv", Path(td) / "package"
            source.write_bytes(gzip_csv([row(1_000_000, 1_000_001, 8_000_001)]))
            with self.assertRaisesRegex(ValueError, "FUNDING_PACKAGE_SOURCE_TIME_INVALID"):
                build_tardis_funding_evidence_package(
                    source, output, package_id="fixture-006",
                    assembled_at_utc="2026-11-14T12:00:00Z", builder_source_sha="f" * 40,
                )
            self.assertFalse(output.exists())

    def test_refuses_to_overwrite_an_existing_package(self):
        with tempfile.TemporaryDirectory() as td:
            source, output = Path(td) / "BTCUSDT.csv", Path(td) / "package"
            source.write_bytes(gzip_csv([row(1_000_000, 1_000_001, 8_000_000)]))
            output.mkdir()
            sentinel = output / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "FUNDING_PACKAGE_DESTINATION_EXISTS"):
                build_tardis_funding_evidence_package(
                    source, output, package_id="fixture-007",
                    assembled_at_utc="2026-11-14T12:00:00Z", builder_source_sha="1" * 40,
                )
            self.assertEqual(sentinel.read_text(), "keep")

    def test_rejects_malformed_csv_row_width(self):
        payload = HEADER + "binance-futures,BTCUSDT,1000000,1000001,8000000,0.0001,,,,100,100,EXTRA\n"
        with tempfile.TemporaryDirectory() as td:
            source, output = Path(td) / "BTCUSDT.csv", Path(td) / "package"
            source.write_bytes(gzip.compress(payload.encode()))
            with self.assertRaisesRegex(ValueError, "FUNDING_PACKAGE_SOURCE_ROW_INVALID"):
                build_tardis_funding_evidence_package(
                    source, output, package_id="fixture-008",
                    assembled_at_utc="2026-11-14T12:00:00Z", builder_source_sha="2" * 40,
                )
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
