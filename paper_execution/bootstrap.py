"""Fail-closed, disposable-first bootstrap for a fresh PAPER Dual Ledger account."""

from contextlib import closing
from decimal import Decimal, DecimalException
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from paper_execution.ledger import (
    PaperLedger,
    dual_ledger_ready,
    read_account_risk_snapshot,
)
from paper_execution.funding import (
    record_account_equity_cutover,
    record_funding_coverage,
)
from risk_policy import CORE_LEVERAGE
from paper_execution.owner_attestation import load_manual_owner_attestation


MANIFEST_FIELDS = {
    "schemaVersion", "mode", "sourceSha", "initialCapitalQuote",
    "maxPositionBase", "riskLimits", "aiLeverage", "markPrice",
    "markCandleCloseMs", "markObservedAtMs", "datasetVersion",
    "fundingCoverageStartAtMs", "fundingCoverageId", "fundingSource",
    "fundingSnapshotId", "fundingEvidencePath", "fundingPayloadHash",
    "cutoverId", "cutoverSource", "cutoverSnapshotId",
    "cutoverEvidencePath", "cutoverPayloadHash", "ownerAttestationPath",\n    "ownerAttestationPayloadHash", "configVersion",
    "recordedAtMs",
}
STRATEGY_SCOPES = (
    "AI_FREQAI", "LEGACY_UNATTRIBUTED", "STRATEGY_CORE",
)
CREDENTIAL_ENV = (
    "BINANCE_API_KEY", "BINANCE_API_SECRET", "OKX_API_KEY", "OKX_API_SECRET",
)
PROTECTED_PATH_ENV = (
    "MARKET_DATA_DB", "T0_FEEDER_LEASE_DB",
)
MAX_EVIDENCE_BYTES = 1_048_576


def _required_text(value, code, limit=300):
    if (not isinstance(value, str) or not value.strip()
            or len(value) > limit or not value.isprintable()):
        raise ValueError(code)
    return value.strip()


def _decimal(value, code, *, positive=False):
    try:
        number = Decimal(str(value))
    except (DecimalException, TypeError, ValueError):
        raise ValueError(code) from None
    if not number.is_finite() or (positive and number <= 0):
        raise ValueError(code)
    return number


def _timestamp(value, code):
    if type(value) is not int or value < 0:
        raise ValueError(code)
    return value


def _digest(value, code):
    value = _required_text(value, code, 71)
    if (len(value) != 71 or not value.startswith("sha256:")
            or any(char not in "0123456789abcdef" for char in value[7:])):
        raise ValueError(code)
    return value


def _validate_environment():
    if os.environ.get("AI_EXECUTION_ENABLED") != "false":
        raise ValueError("BOOTSTRAP_AI_EXECUTION_MUST_BE_DISABLED")
    if any(os.environ.get(name) for name in CREDENTIAL_ENV):
        raise ValueError("BOOTSTRAP_EXCHANGE_CREDENTIALS_FORBIDDEN")


def _target_path(db_path):
    raw = Path(db_path).expanduser()
    if raw.exists() or raw.is_symlink():
        raise ValueError("BOOTSTRAP_TARGET_ALREADY_EXISTS")
    if not raw.parent.exists() or not raw.parent.is_dir():
        raise ValueError("BOOTSTRAP_TARGET_PARENT_UNAVAILABLE")
    target = raw.resolve(strict=False)
    for variable in PROTECTED_PATH_ENV:
        protected = os.environ.get(variable)
        if not protected:
            continue
        protected_path = Path(protected).expanduser().resolve(strict=False)
        if target == protected_path:
            raise ValueError("BOOTSTRAP_TARGET_PROTECTED_PATH")
    return target


def _reject_duplicate_json_keys(pairs):
    document = {}
    for key, value in pairs:
        if key in document:
            raise ValueError("BOOTSTRAP_EVIDENCE_DUPLICATE_KEY")
        document[key] = value
    return document


def _verify_evidence(path_value, expected_digest, expected_snapshot_id, expected_document):
    path = Path(_required_text(path_value, "BOOTSTRAP_EVIDENCE_PATH_INVALID")).expanduser()
    if path.is_symlink() or not path.is_file():
        raise ValueError("BOOTSTRAP_EVIDENCE_FILE_UNAVAILABLE")
    try:
        raw = path.read_bytes()
    except OSError:
        raise ValueError("BOOTSTRAP_EVIDENCE_FILE_UNAVAILABLE") from None
    if not raw or len(raw) > MAX_EVIDENCE_BYTES:
        raise ValueError("BOOTSTRAP_EVIDENCE_SIZE_INVALID")
    actual = "sha256:" + hashlib.sha256(raw).hexdigest()
    if actual != expected_digest:
        raise ValueError("BOOTSTRAP_EVIDENCE_DIGEST_MISMATCH")
    try:
        document = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_json_keys
        )
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("BOOTSTRAP_EVIDENCE_JSON_INVALID") from None
    if not isinstance(document, dict) or document.get("snapshotId") != expected_snapshot_id:
        raise ValueError("BOOTSTRAP_EVIDENCE_SNAPSHOT_MISMATCH")
    if document != expected_document:
        raise ValueError("BOOTSTRAP_EVIDENCE_CONTENT_MISMATCH")
    return actual


def _validate_manifest(manifest, target):
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_FIELDS:
        raise ValueError("BOOTSTRAP_MANIFEST_FIELDS_INVALID")
    if type(manifest["schemaVersion"]) is not int or manifest["schemaVersion"] != 1:
        raise ValueError("BOOTSTRAP_MANIFEST_VERSION_UNSUPPORTED")
    if manifest["mode"] != "PAPER":
        raise ValueError("BOOTSTRAP_MODE_MUST_BE_PAPER")
    source_sha = _required_text(manifest["sourceSha"], "DUAL_LEDGER_SOURCE_SHA_REQUIRED", 40)
    if (len(source_sha) != 40
            or any(char not in "0123456789abcdef" for char in source_sha.lower())):
        raise ValueError("DUAL_LEDGER_SOURCE_SHA_REQUIRED")

    capital = _decimal(manifest["initialCapitalQuote"], "BOOTSTRAP_CAPITAL_INVALID", positive=True)
    maximum = _decimal(manifest["maxPositionBase"], "BOOTSTRAP_MAX_POSITION_INVALID", positive=True)
    ai_leverage = _decimal(manifest["aiLeverage"], "BOOTSTRAP_AI_LEVERAGE_INVALID", positive=True)
    if not Decimal("1") <= ai_leverage <= Decimal("3"):
        raise ValueError("AI_LEVERAGE_OUT_OF_RANGE")

    limits = manifest["riskLimits"]
    expected_limits = {"maxDrawdownPct", "maxDailyLossUsdt", "maxExposureUsdt"}
    if not isinstance(limits, dict) or set(limits) != expected_limits:
        raise ValueError("BOOTSTRAP_RISK_LIMITS_INVALID")
    normalized_limits = {}
    for field, value in limits.items():
        parsed = _decimal(value, "BOOTSTRAP_RISK_LIMITS_INVALID", positive=True)
        if field == "maxDrawdownPct" and parsed > 100:
            raise ValueError("BOOTSTRAP_RISK_LIMITS_INVALID")
        normalized_limits[field] = str(parsed)

    mark = _decimal(manifest["markPrice"], "BOOTSTRAP_MARK_INVALID", positive=True)
    candle = _timestamp(manifest["markCandleCloseMs"], "BOOTSTRAP_MARK_TIME_INVALID")
    observed = _timestamp(manifest["markObservedAtMs"], "BOOTSTRAP_MARK_TIME_INVALID")
    recorded = _timestamp(manifest["recordedAtMs"], "BOOTSTRAP_RECORDED_TIME_INVALID")
    coverage_start = _timestamp(
        manifest["fundingCoverageStartAtMs"], "BOOTSTRAP_FUNDING_COVERAGE_INVALID"
    )
    if (candle > observed or observed - candle > 30 * 60_000
            or observed > recorded or recorded - observed > 30 * 60_000
            or coverage_start >= observed):
        raise ValueError("BOOTSTRAP_MARK_OR_COVERAGE_TIME_INVALID")

    dataset = _required_text(manifest["datasetVersion"], "BOOTSTRAP_DATASET_VERSION_INVALID")
    if len(dataset) > 300:
        raise ValueError("BOOTSTRAP_DATASET_VERSION_INVALID")
    funding_id = _required_text(manifest["fundingCoverageId"], "FUNDING_COVERAGE_ID_INVALID", 200)
    funding_source = _required_text(manifest["fundingSource"], "FUNDING_SOURCE_REQUIRED")
    funding_snapshot = _required_text(
        manifest["fundingSnapshotId"], "FUNDING_SOURCE_SNAPSHOT_REQUIRED"
    )
    funding_digest = _digest(manifest["fundingPayloadHash"], "FUNDING_PAYLOAD_HASH_INVALID")
    cutover_id = _required_text(manifest["cutoverId"], "ACCOUNT_EQUITY_CUTOVER_ID_INVALID", 200)
    cutover_source = _required_text(manifest["cutoverSource"], "ACCOUNT_EQUITY_CUTOVER_SOURCE_REQUIRED")
    cutover_snapshot = _required_text(
        manifest["cutoverSnapshotId"], "ACCOUNT_EQUITY_CUTOVER_SNAPSHOT_REQUIRED"
    )
    cutover_digest = _digest(
        manifest["cutoverPayloadHash"], "ACCOUNT_EQUITY_CUTOVER_HASH_INVALID"
    )
    config_version = _required_text(manifest["configVersion"], "ACCOUNT_EQUITY_CUTOVER_CONFIG_REQUIRED", 200)

    funding_evidence = {
        "snapshotId": funding_snapshot,
        "status": "VERIFIED",
        "startAtMs": coverage_start,
        "endAtMs": observed,
        "source": funding_source,
        "configVersion": config_version,
        "fundingByStrategy": {
            "STRATEGY_CORE": "0",
            "AI_FREQAI": "0",
            "LEGACY_UNATTRIBUTED": "0",
        },
    }
    cutover_evidence = {
        "snapshotId": cutover_snapshot,
        "initialCapitalQuote": str(capital),
        "realizedPnlQuote": "0",
        "feesQuote": "0",
        "fundingQuote": "0",
        "accountEquityQuote": str(capital),
        "markPrice": str(mark),
        "markCandleCloseMs": candle,
        "markObservedAtMs": observed,
        "datasetVersion": dataset,
        "fundingCoverageStartAtMs": coverage_start,
        "source": cutover_source,
        "configVersion": config_version,
    }
    _verify_evidence(
        manifest["fundingEvidencePath"], funding_digest, funding_snapshot,
        funding_evidence,
    )
    _verify_evidence(
        manifest["cutoverEvidencePath"], cutover_digest, cutover_snapshot,
        cutover_evidence,
    )
    owner_attestation = load_manual_owner_attestation(
        manifest["ownerAttestationPath"],
        manifest["ownerAttestationPayloadHash"],
        manifest,
    )
    for evidence_path in (
        manifest["fundingEvidencePath"],
        manifest["cutoverEvidencePath"],
        manifest["ownerAttestationPath"],
    ):
        resolved = Path(evidence_path).expanduser().resolve(strict=True)
        if resolved == target:
            raise ValueError("BOOTSTRAP_EVIDENCE_PATH_CONFLICT")

    return {
        "source_sha": source_sha.lower(),
        "capital": str(capital),
        "maximum": str(maximum),
        "limits": normalized_limits,
        "ai_leverage": str(ai_leverage),
        "mark": str(mark),
        "candle": candle,
        "observed": observed,
        "recorded": recorded,
        "coverage_start": coverage_start,
        "dataset": dataset,
        "funding_id": funding_id,
        "funding_source": funding_source,
        "funding_snapshot": funding_snapshot,
        "funding_digest": funding_digest,
        "cutover_id": cutover_id,
        "cutover_source": cutover_source,
        "cutover_snapshot": cutover_snapshot,
        "cutover_digest": cutover_digest,
        "config_version": config_version,
        "owner_attestation": owner_attestation,
    }


def _finalize_sqlite(path):
    with closing(sqlite3.connect(path, timeout=10)) as db:
        db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        db.execute("PRAGMA journal_mode=DELETE")


def bootstrap_paper_account(db_path, manifest):
    """Build a new account in a private sibling DB and publish it without overwrite."""
    _validate_environment()
    target = _target_path(db_path)
    values = _validate_manifest(manifest, target)

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".dual-ledger-bootstrap-", suffix=".sqlite3", dir=target.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        base = PaperLedger(temporary, max_position_base=values["maximum"])
        base.record_equity(
            values["mark"], values["candle"], values["observed"],
            values["dataset"], values["capital"],
        )
        PaperLedger(
            temporary, max_position_base=values["maximum"],
            strategy_id="STRATEGY_CORE", source_sha=values["source_sha"],
            risk_limits=values["limits"], require_risk_limits=True,
            leverage=str(CORE_LEVERAGE),
        )
        PaperLedger(
            temporary, max_position_base=values["maximum"],
            strategy_id="AI_FREQAI", source_sha=values["source_sha"],
            risk_limits=values["limits"], require_risk_limits=True,
            leverage=values["ai_leverage"],
        )
        record_funding_coverage(
            temporary, coverage_id=values["funding_id"],
            start_at_ms=values["coverage_start"], end_at_ms=values["observed"],
            status="VERIFIED", source=values["funding_source"],
            source_snapshot_id=values["funding_snapshot"],
            payload_hash=values["funding_digest"],
            config_version=values["config_version"],
            recorded_at_ms=values["recorded"],
        )
        record_account_equity_cutover(
            temporary, cutover_id=values["cutover_id"],
            expected_initial_capital_quote=values["capital"],
            expected_realized_pnl_quote="0", expected_fees_quote="0",
            expected_funding_quote="0", expected_account_equity_quote=values["capital"],
            mark_price=values["mark"], mark_candle_close_ms=values["candle"],
            mark_observed_at_ms=values["observed"],
            dataset_version=values["dataset"],
            funding_coverage_start_at_ms=values["coverage_start"],
            source=values["cutover_source"],
            source_snapshot_id=values["cutover_snapshot"],
            payload_hash=values["cutover_digest"],
            config_version=values["config_version"],
            recorded_at_ms=values["recorded"],
        )
        if not dual_ledger_ready(temporary):
            raise sqlite3.DatabaseError("DUAL_LEDGER_MIGRATION_NOT_READY")
        risk = read_account_risk_snapshot(temporary, now_ms=values["recorded"])
        if (risk.get("mode") != "PAPER" or risk.get("liveTradingSupported") is not False
                or risk.get("riskReady") is not True
                or risk.get("accountEquityQuote") != values["capital"]):
            raise sqlite3.DatabaseError("BOOTSTRAP_ACCOUNT_RECONCILIATION_NOT_READY")
        _finalize_sqlite(temporary)
        os.link(temporary, target)
        temporary.unlink()
        return {
            "mode": "PAPER",
            "liveTradingSupported": False,
            "riskReady": True,
            "accountEquityQuote": risk["accountEquityQuote"],
            "strategyScopes": list(STRATEGY_SCOPES),
            "coreLeverage": str(CORE_LEVERAGE),
            "aiLeverage": values["ai_leverage"],
            "sourceSha": values["source_sha"],
            "databaseCreated": True,
            "evidenceIntegrity": "SHA256_AND_CONTENT_MATCHED",
            "sourceAuthenticity": "NOT_VERIFIED",
            "ownerAttestation": values["owner_attestation"],
        }
    finally:
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(temporary) + suffix)
            if sidecar.exists():
                sidecar.unlink()
        if temporary.exists():
            temporary.unlink()


def inspect_paper_account(db_path, *, now_ms):
    """Read-only inspection; stale or incomplete accounts always report not-ready."""
    path = Path(db_path).expanduser().resolve(strict=False)
    if not path.is_file():
        raise FileNotFoundError("Paper ledger is unavailable")
    now = _timestamp(now_ms, "BOOTSTRAP_INSPECT_TIME_INVALID")
    try:
        migrations_ready = dual_ledger_ready(path)
        risk = read_account_risk_snapshot(path, now_ms=now)
        ready = (
            migrations_ready and risk.get("mode") == "PAPER"
            and risk.get("liveTradingSupported") is False
            and risk.get("riskReady") is True
        )
        reason = risk.get("unavailableReason")
        equity = risk.get("accountEquityQuote")
    except (sqlite3.DatabaseError, ValueError, OSError) as exc:
        ready = False
        migrations_ready = False
        reason = str(exc)[:160]
        equity = None
    uri = path.as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, timeout=10)) as db:
        db.execute("PRAGMA query_only=ON")
        scopes = [
            row[0] for row in db.execute(
                "SELECT strategy_id FROM paper_strategy_ledgers "
                "WHERE account_id=1 ORDER BY strategy_id"
            )
        ] if db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_strategy_ledgers'"
        ).fetchone() else []
    return {
        "mode": "PAPER",
        "liveTradingSupported": False,
        "riskReady": ready,
        "migrationsReady": migrations_ready,
        "accountEquityQuote": equity,
        "unavailableReason": reason,
        "strategyScopes": scopes,
        "readOnly": True,
        "sourceAuthenticity": "NOT_VERIFIED",
    }
