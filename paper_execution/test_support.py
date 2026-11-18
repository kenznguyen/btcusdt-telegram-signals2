"""Shared synthetic evidence fixture for isolated Dual Ledger bootstrap tests."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace


def write_json(path, value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    path.write_bytes(raw)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def build_dual_ledger_bootstrap_manifest(root, now, db_path, source_sha):
    """Create synthetic, explicitly non-authoritative bootstrap evidence."""
    fixture = SimpleNamespace(
        root=Path(root), now=now, db_path=Path(db_path), source_sha=source_sha,
    )
    fixture.funding_evidence = fixture.root / "funding-evidence.json"
    fixture.cutover_evidence = fixture.root / "equity-cutover-evidence.json"
    fixture.owner_attestation = fixture.root / "owner-attestation.json"
    fixture.manifest = {
        "schemaVersion": 1,
        "mode": "PAPER",
        "sourceSha": fixture.source_sha,
        "initialCapitalQuote": "100",
        "maxPositionBase": "0.01",
        "riskLimits": {
            "maxDrawdownPct": "50",
            "maxDailyLossUsdt": "50",
            "maxExposureUsdt": "1000",
        },
        "aiLeverage": "3",
        "markPrice": "100",
        "markCandleCloseMs": fixture.now - 60_000,
        "markObservedAtMs": fixture.now,
        "datasetVersion": "sha256:" + "1" * 64,
        "fundingCoverageStartAtMs": fixture.now - 86_400_000,
        "fundingCoverageId": "bootstrap-funding-coverage-001",
        "fundingSource": "OWNER_RECONCILED_EVIDENCE",
        "fundingSnapshotId": "owner-funding-001",
        "fundingEvidencePath": str(fixture.funding_evidence),
        "fundingPayloadHash": "",
        "fundingExpectedPopulation": {
            "schemaVersion": 1,
            "populationType": "EXPECTED_FUNDING_EVENTS",
            "populationDefinitionId": "owner-statement-enumeration-v1",
            "snapshotId": "owner-funding-001",
            "source": "owner-funding-statement",
            "startAtMs": fixture.now - 86_400_000,
            "endAtMs": fixture.now,
            "currency": "USDT",
            "events": [],
        },
        "cutoverId": "bootstrap-equity-cutover-001",
        "cutoverSource": "OWNER_RECONCILED_EVIDENCE",
        "cutoverSnapshotId": "owner-equity-001",
        "cutoverEvidencePath": str(fixture.cutover_evidence),
        "cutoverPayloadHash": "",
        "ownerAttestationPath": str(fixture.owner_attestation),
        "ownerAttestationPayloadHash": "",
        "configVersion": "paper-risk-v1",
        "recordedAtMs": fixture.now,
    }
    funding_document = {
        "snapshotId": "owner-funding-001",
        "status": "VERIFIED",
        "startAtMs": fixture.now - 86_400_000,
        "endAtMs": fixture.now,
        "source": "OWNER_RECONCILED_EVIDENCE",
        "configVersion": "paper-risk-v1",
        "fundingByStrategy": {
            "STRATEGY_CORE": "0",
            "AI_FREQAI": "0",
            "LEGACY_UNATTRIBUTED": "0",
        },
        "expectedPopulation": fixture.manifest["fundingExpectedPopulation"],
    }
    cutover_document = {
        "snapshotId": "owner-equity-001",
        "initialCapitalQuote": "100",
        "realizedPnlQuote": "0",
        "feesQuote": "0",
        "fundingQuote": "0",
        "accountEquityQuote": "100",
        "markPrice": "100",
        "markCandleCloseMs": fixture.now - 60_000,
        "markObservedAtMs": fixture.now,
        "datasetVersion": "sha256:" + "1" * 64,
        "fundingCoverageStartAtMs": fixture.now - 86_400_000,
        "source": "OWNER_RECONCILED_EVIDENCE",
        "configVersion": "paper-risk-v1",
    }
    fixture.manifest["fundingPayloadHash"] = write_json(
        fixture.funding_evidence, funding_document
    )
    fixture.manifest["cutoverPayloadHash"] = write_json(
        fixture.cutover_evidence, cutover_document
    )
    owner_attestation = {
        "schemaVersion": 1,
        "attestationType": "DUAL_LEDGER_BOOTSTRAP_EVIDENCE_REVIEW",
        "attestorRole": "OWNER_DECLARATION",
        "claimScope": "FUNDING_AND_EQUITY_SNAPSHOT_REVIEW",
        "sourceSha": fixture.source_sha,
        "fundingSnapshotId": "owner-funding-001",
        "fundingPayloadHash": fixture.manifest["fundingPayloadHash"],
        "cutoverSnapshotId": "owner-equity-001",
        "cutoverPayloadHash": fixture.manifest["cutoverPayloadHash"],
        "reviewedAtMs": fixture.now,
        "reviewStatement": "I_REVIEWED_THE_IDENTIFIED_FUNDING_AND_EQUITY_SNAPSHOTS",
        "nonClaims": [
            "FACTUAL_TRUTH",
            "FRESHNESS",
            "POPULATION_COMPLETENESS",
            "PRIVILEGED_ACTION_AUTHORIZATION",
            "SOURCE_AUTHENTICITY",
        ],
    }
    fixture.manifest["ownerAttestationPayloadHash"] = write_json(
        fixture.owner_attestation, owner_attestation
    )
    fixture.db_path = Path(db_path)
    fixture.db_path.parent.mkdir(parents=True, exist_ok=True)
    return fixture.manifest
