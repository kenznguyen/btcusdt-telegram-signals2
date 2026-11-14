"""Offline D07.8 package builder for a user-supplied Tardis funding export.

Preserves the compressed source bytes and emits a structure-validated manifest,
field mapping, and checksums. It does not acquire/authenticate data, establish
collector independence, assert an expected schedule, or write to a ledger.
"""
import csv
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from paper_execution.funding_evidence_package import validate_funding_evidence_manifest

_COLUMNS = (
    "exchange", "symbol", "timestamp", "local_timestamp", "funding_timestamp",
    "funding_rate", "predicted_funding_rate", "open_interest", "last_price",
    "index_price", "mark_price",
)
_REQUIRED = {"exchange", "symbol", "timestamp", "local_timestamp", "funding_timestamp", "funding_rate"}
_PACKAGE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SOURCE_SHA = re.compile(r"^[0-9a-f]{40}$")
_MAX_COMPRESSED = 50 * 1024 * 1024
_MAX_UNCOMPRESSED = 100 * 1024 * 1024
_MAX_ROWS = 1_000_000


def _sha256(value):
    return hashlib.sha256(value).hexdigest()


def _validate_utc(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("FUNDING_PACKAGE_ASSEMBLY_TIME_INVALID")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise ValueError("FUNDING_PACKAGE_ASSEMBLY_TIME_INVALID") from None
    if parsed.utcoffset().total_seconds() != 0:
        raise ValueError("FUNDING_PACKAGE_ASSEMBLY_TIME_INVALID")


def _read_gzip_csv(path):
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("FUNDING_PACKAGE_SOURCE_INVALID")
    raw = source.read_bytes()
    if not raw or len(raw) > _MAX_COMPRESSED:
        raise ValueError("FUNDING_PACKAGE_SOURCE_SIZE_INVALID")
    if not raw.startswith(b"\x1f\x8b"):
        raise ValueError("FUNDING_PACKAGE_SOURCE_NOT_GZIP")
    try:
        chunks = []
        total = 0
        with gzip.GzipFile(fileobj=io.BytesIO(raw), mode="rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > _MAX_UNCOMPRESSED:
                    raise ValueError("FUNDING_PACKAGE_SOURCE_SIZE_INVALID")
                chunks.append(chunk)
        text = b"".join(chunks).decode("utf-8-sig")
    except (OSError, EOFError):
        raise ValueError("FUNDING_PACKAGE_SOURCE_GZIP_INVALID") from None
    except UnicodeDecodeError:
        raise ValueError("FUNDING_PACKAGE_SOURCE_ENCODING_INVALID") from None
    return source, raw, text


def _inspect_csv(text):
    reader = csv.DictReader(io.StringIO(text, newline=""))
    names = reader.fieldnames
    if not names or len(names) != len(set(names)) or tuple(names) != _COLUMNS:
        raise ValueError("FUNDING_PACKAGE_SOURCE_SCHEMA_INVALID")

    rows = 0
    exchanges, symbols, funding_ms, rates = set(), set(), set(), set()
    message_us, receive_us = [], []
    try:
        for row in reader:
            rows += 1
            if rows > _MAX_ROWS:
                raise ValueError("FUNDING_PACKAGE_SOURCE_RECORD_LIMIT")
            if None in row or set(row) != set(names):
                raise ValueError("FUNDING_PACKAGE_SOURCE_ROW_INVALID")
            if any(not row.get(k) or not row[k].strip() for k in _REQUIRED):
                raise ValueError("FUNDING_PACKAGE_SOURCE_ROW_INVALID")
            exchanges.add(row["exchange"].strip())
            symbols.add(row["symbol"].strip())
            try:
                msg, recv, fund = (int(row[k]) for k in ("timestamp", "local_timestamp", "funding_timestamp"))
            except (TypeError, ValueError):
                raise ValueError("FUNDING_PACKAGE_SOURCE_TIME_INVALID") from None
            if min(msg, recv, fund) < 0 or fund % 1000:
                raise ValueError("FUNDING_PACKAGE_SOURCE_TIME_INVALID")
            try:
                rate = Decimal(row["funding_rate"].strip())
            except (InvalidOperation, ValueError):
                raise ValueError("FUNDING_PACKAGE_SOURCE_RATE_INVALID") from None
            if not rate.is_finite():
                raise ValueError("FUNDING_PACKAGE_SOURCE_RATE_INVALID")
            message_us.append(msg)
            receive_us.append(recv)
            funding_ms.add(fund // 1000)
            rates.add(str(rate))
    except csv.Error:
        raise ValueError("FUNDING_PACKAGE_SOURCE_ROW_INVALID") from None

    if rows == 0:
        raise ValueError("FUNDING_PACKAGE_SOURCE_EMPTY")
    if exchanges != {"binance-futures"} or symbols != {"BTCUSDT"}:
        raise ValueError("FUNDING_PACKAGE_SOURCE_IDENTITY_INVALID")
    return {
        "recordCount": rows,
        "observedSettlementTimesMs": sorted(funding_ms),
        "messageTimestampStartUs": min(message_us),
        "messageTimestampEndUs": max(message_us),
        "receiveTimestampStartUs": min(receive_us),
        "receiveTimestampEndUs": max(receive_us),
        "fundingRateValues": sorted(rates),
    }


def build_tardis_funding_evidence_package(
    source_path, output_dir, *, package_id, assembled_at_utc, builder_source_sha
):
    """Build a new package; destination must not exist and source is never modified."""
    if not isinstance(package_id, str) or not _PACKAGE_ID.fullmatch(package_id):
        raise ValueError("FUNDING_PACKAGE_ID_INVALID")
    _validate_utc(assembled_at_utc)
    if not isinstance(builder_source_sha, str) or not _SOURCE_SHA.fullmatch(builder_source_sha):
        raise ValueError("FUNDING_PACKAGE_BUILDER_REVISION_INVALID")

    source, raw, text = _read_gzip_csv(source_path)
    inspected = _inspect_csv(text)
    destination = Path(output_dir)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("FUNDING_PACKAGE_DESTINATION_EXISTS")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".d07-package-", dir=destination.parent))

    try:
        raw_path = "raw/BTCUSDT.csv.gz"
        mapping_path = "transforms/field-mapping.json"
        (staging / "raw").mkdir()
        (staging / "transforms").mkdir()
        (staging / "checksums").mkdir()
        raw_target = staging / raw_path
        raw_target.write_bytes(raw)
        copied = raw_target.read_bytes()
        if len(copied) != len(raw) or _sha256(copied) != _sha256(raw):
            raise ValueError("FUNDING_PACKAGE_RAW_READBACK_MISMATCH")

        mapping = {
            "schemaVersion": "TARDIS_FUNDING_FIELD_MAPPING_V1",
            "packageId": package_id,
            "assembledAtUtc": assembled_at_utc,
            "builderSourceSha": builder_source_sha,
            "sourceFilename": source.name,
            "sourceContainerFormat": "GZIP",
            "sourceTextEncoding": "UTF-8",
            "sourceColumns": list(_COLUMNS),
            "sourceTimestampUnit": "MICROSECONDS",
            "timestampFieldSemantics": "EXCHANGE_MESSAGE_TIMESTAMP",
            "receivedTimestampField": "local_timestamp",
            "receivedTimestampUnit": "MICROSECONDS",
            "fundingTimestampField": "funding_timestamp",
            "fundingTimestampSourceUnit": "MICROSECONDS",
            "fundingTimestampNormalization": "integer_microseconds_divided_by_1000",
            "normalizedFundingTimestampUnit": "MILLISECONDS",
            "normalizedFundingTimestampSemantics": "FUNDING_EVENT_TIME_KEY",
            "sourceObservationWindow": {
                "messageTimestampStartUs": inspected["messageTimestampStartUs"],
                "messageTimestampEndUs": inspected["messageTimestampEndUs"],
                "receiveTimestampStartUs": inspected["receiveTimestampStartUs"],
                "receiveTimestampEndUs": inspected["receiveTimestampEndUs"],
            },
            "fundingRateValuesObserved": inspected["fundingRateValues"],
            "limitations": [
                "Provider and issuer authenticity are not independently authenticated.",
                "Collector operational independence is not established.",
                "No authoritative expected settlement schedule was supplied.",
                "Structural row validation does not establish source enumeration or global completeness.",
            ],
        }
        mapping_bytes = (json.dumps(mapping, indent=2, sort_keys=True) + "\n").encode()
        (staging / mapping_path).write_bytes(mapping_bytes)

        observed = inspected["observedSettlementTimesMs"]
        manifest = {
            "schemaVersion": "TARDIS_BINANCE_FUNDING_EVIDENCE_V1",
            "packageId": package_id,
            "issuer": {
                "venue": "BINANCE",
                "authority": "BINANCE_USDM_DECLARED_BY_USER_SUPPLIED_TARDIS_EXPORT_NOT_AUTHENTICATED",
            },
            "collector": {
                "name": "TARDIS",
                "channel": "TARDIS_DATASET_EXPORT_USER_SUPPLIED_NOT_AUTHENTICATED",
            },
            "instrument": {
                "symbol": "BTCUSDT",
                "marketType": "USD_M_FUTURES",
                "contractType": "PERPETUAL",
                "marginAsset": "USDT",
                "settlementAsset": "USDT",
            },
            "time": {
                "eventTimeField": "funding_timestamp",
                "eventTimeUnit": "MILLISECONDS",
                "timezone": "UTC",
                "receivedTimeField": "local_timestamp",
            },
            "coverage": {
                "startAtMs": observed[0],
                "endAtMs": observed[-1] + 1,
                "expectedSettlementTimesMs": [],
                "observedSettlementTimesMs": observed,
                "expectedSetAuthority": "NOT_SUPPLIED_NO_AUTHORITATIVE_EXPECTED_SET",
            },
            "files": [
                {
                    "path": raw_path,
                    "byteLength": len(raw),
                    "sha256": _sha256(raw),
                    "recordCount": inspected["recordCount"],
                    "mediaType": "application/gzip",
                },
                {
                    "path": mapping_path,
                    "byteLength": len(mapping_bytes),
                    "sha256": _sha256(mapping_bytes),
                    "recordCount": 0,
                    "mediaType": "application/json",
                },
            ],
        }
        validation = validate_funding_evidence_manifest(manifest)
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
        (staging / "manifest.json").write_bytes(manifest_bytes)
        sums = [
            f"{_sha256(raw)}  {raw_path}",
            f"{_sha256(mapping_bytes)}  {mapping_path}",
            f"{_sha256(manifest_bytes)}  manifest.json",
        ]
        (staging / "checksums" / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="ascii")
        os.rename(staging, destination)
        return {
            "packagePath": str(destination),
            "manifest": manifest,
            "validation": validation,
            "sourceByteLength": len(raw),
            "sourceSha256": _sha256(raw),
        }
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
