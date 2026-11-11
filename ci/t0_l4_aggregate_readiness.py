"""Fail-closed L4M-10 readiness evaluation; this module never issues final L4 acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__:
    from .t0_l4_claim_discipline import audit_crosswalk
else:
    from t0_l4_claim_discipline import audit_crosswalk

ACTIVE_CONTROL_IDS = tuple(
    [f"L4M-{number:02d}" for number in range(1, 9)] + ["L4M-10"]
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_BASELINE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def _valid_utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def _validate_owner_disposition(disposition, baseline_id, baseline_sha256):
    if not isinstance(disposition, dict):
        return False, "OWNER_DISPOSITION_INVALID", None
    required = (
        "schema_version", "decision", "baseline_id", "baseline_sha256",
        "assessor_identity", "assessor_role", "conflict_disclosure",
        "disposition_timestamp",
    )
    if any(not isinstance(disposition.get(key), str) or not disposition[key].strip() for key in required):
        return False, "OWNER_DISPOSITION_INVALID", None
    if disposition["schema_version"] != "T0_L4_OWNER_DISPOSITION_V1":
        return False, "OWNER_DISPOSITION_INVALID", None
    if disposition["decision"] not in ("ACCEPT", "REJECT"):
        return False, "OWNER_DISPOSITION_INVALID", None
    if not _valid_utc_timestamp(disposition["disposition_timestamp"]):
        return False, "OWNER_DISPOSITION_INVALID", None
    if disposition["baseline_id"] != baseline_id or disposition["baseline_sha256"] != baseline_sha256:
        return False, "OWNER_DISPOSITION_BASELINE_MISMATCH", None
    return True, None, disposition["decision"]


def evaluate_aggregate(
    control_statuses,
    *,
    baseline_id=None,
    baseline_sha256=None,
    owner_disposition=None,
):
    """Evaluate readiness only; a structurally valid owner record still needs manual finalization."""
    reasons = []
    if not isinstance(control_statuses, dict) or set(control_statuses) != set(ACTIVE_CONTROL_IDS):
        reasons.append("CONTROL_SET_MISMATCH")
        controls = control_statuses if isinstance(control_statuses, dict) else {}
    else:
        controls = control_statuses

    active_all_pass = (
        set(controls) == set(ACTIVE_CONTROL_IDS)
        and all(controls.get(control_id) == "PASS" for control_id in ACTIVE_CONTROL_IDS)
    )
    if not active_all_pass:
        reasons.append("ACTIVE_CONTROLS_NOT_ALL_PASS")

    baseline_valid = (
        isinstance(baseline_id, str)
        and bool(_BASELINE_ID.fullmatch(baseline_id))
        and isinstance(baseline_sha256, str)
        and bool(_SHA256.fullmatch(baseline_sha256))
    )
    if not baseline_valid:
        reasons.append("FROZEN_BASELINE_REQUIRED")

    disposition_valid = False
    disposition_decision = None
    if owner_disposition is None:
        reasons.append("OWNER_DISPOSITION_REQUIRED")
    elif baseline_valid:
        disposition_valid, error_code, disposition_decision = _validate_owner_disposition(
            owner_disposition, baseline_id, baseline_sha256
        )
        if error_code:
            reasons.append(error_code)
    else:
        reasons.append("OWNER_DISPOSITION_INVALID")

    if disposition_valid and disposition_decision == "REJECT":
        verdict = "OWNER_REJECTED"
    elif (
        active_all_pass
        and baseline_valid
        and disposition_valid
        and disposition_decision == "ACCEPT"
    ):
        verdict = "OWNER_DISPOSITION_PRESENT — MANUAL FINALIZATION REQUIRED"
    else:
        verdict = "BLOCKED / NOT VERIFIED"

    return {
        "schema_version": "T0_L4M10_AGGREGATE_READINESS_V1",
        "aggregate_verdict": verdict,
        "claims_l4_minimum_accepted": False,
        "active_control_count": len(ACTIVE_CONTROL_IDS),
        "waived_control_excluded": "L4M-09",
        "controls": {key: controls.get(key, "MISSING") for key in ACTIVE_CONTROL_IDS},
        "active_controls_all_pass": active_all_pass,
        "frozen_baseline_present": baseline_valid,
        "owner_disposition_structurally_valid": disposition_valid,
        "owner_disposition_decision": disposition_decision,
        "owner_identity_authentication": "NOT_VERIFIED_BY_THIS_CHECK",
        "reason_codes": sorted(set(reasons)),
        "scope": "readiness guard only; no final owner acceptance, identity authentication or cryptographic signature",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crosswalk", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--baseline-id")
    parser.add_argument("--baseline-sha256")
    parser.add_argument("--owner-disposition")
    args = parser.parse_args(argv)

    try:
        source_commit = os.environ["GITHUB_SHA"]
        if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
            raise ValueError("source commit invalid")
        crosswalk_text = Path(args.crosswalk).read_text(encoding="utf-8")
        crosswalk_report = audit_crosswalk(crosswalk_text, source_commit=source_commit)
        statuses = {
            key: value for key, value in crosswalk_report["controls"].items()
            if key in ACTIVE_CONTROL_IDS
        }
        disposition = None
        if args.owner_disposition:
            disposition = json.loads(Path(args.owner_disposition).read_text(encoding="utf-8"))
        report = evaluate_aggregate(
            statuses,
            baseline_id=args.baseline_id,
            baseline_sha256=args.baseline_sha256,
            owner_disposition=disposition,
        )
        report["source_commit"] = source_commit
        report["crosswalk_source"] = args.crosswalk

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        payload = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        manifest = output_dir / "aggregate-readiness-report.json"
        sidecar = output_dir / "aggregate-readiness-report.sha256"
        manifest.write_bytes(payload)
        sidecar.write_text(hashlib.sha256(payload).hexdigest() + "  " + manifest.name + "\n", encoding="ascii")
    except (KeyError, OSError, UnicodeError, ValueError, json.JSONDecodeError):
        print("L4M10_AGGREGATE_READINESS=BLOCKED INPUT_INVALID", file=sys.stderr)
        return 1

    print("L4M10_AGGREGATE_READINESS=" + report["aggregate_verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
