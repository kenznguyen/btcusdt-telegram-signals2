"""Validate claim boundaries in the current T0 L4 control-to-source crosswalk."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

EXPECTED_STATUSES = {
    "L4M-01": "PARTIAL",
    "L4M-02": "NOT VERIFIED",
    "L4M-03": "PARTIAL — DESIGN ONLY / NOT IMPLEMENTED",
    "L4M-04": "PARTIAL — SYNTHETIC/CI ONLY",
    "L4M-05": "PARTIAL — SYNTHETIC MODEL ONLY",
    "L4M-06": "PARTIAL — SYNTHETIC POLICY ONLY",
    "L4M-07": "PARTIAL — SYNTHETIC MODEL ONLY",
    "L4M-08": "DOCUMENTARY PASS ONLY",
    "L4M-09": "OWNER-WAIVED / NOT MANDATORY",
    "L4M-10": "NOT VERIFIED / PENDING OWNER ASSESSMENT",
}
ACTIVE_CONTROL_COUNT = 9
FORBIDDEN_POSITIVE_CLAIMS = (
    re.compile(r"\bWORM\s*[:=]\s*PASS\b", re.IGNORECASE),
    re.compile(r"\bindependent(?:\s+security)?\s+assurance\s*[:=]\s*PASS\b", re.IGNORECASE),
    re.compile(r"\bindependent(?:\s+security)?\s+review\s*[:=]\s*PASS\b", re.IGNORECASE),
    re.compile(r"\bowner\s+acceptance\s*[:=]\s*PASS\b", re.IGNORECASE),
    re.compile(r"\bruntime\s+(?:accepted|pass)\b", re.IGNORECASE),
    re.compile(r"\baggregate\s+L4(?:-minimum)?\s*[:=]?\s*PASS\b", re.IGNORECASE),
)


class ClaimDisciplineError(ValueError):
    """Raised when the active crosswalk overstates an L4 assurance claim."""


def _fail(code: str) -> None:
    raise ClaimDisciplineError(code)


def _control_rows(crosswalk: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for line in crosswalk.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        match = re.match(r"\*{0,2}(L4M-\d{2})\b", cells[0])
        if not match:
            continue
        control_id = match.group(1)
        if control_id in rows:
            _fail("DUPLICATE_CONTROL")
        status = cells[-1].strip().strip("* ").upper()
        rows[control_id] = (status, line)
    return rows


def audit_crosswalk(crosswalk: str, source_commit: str = "") -> dict:
    if not isinstance(crosswalk, str) or not crosswalk.strip():
        _fail("CROSSWALK_EMPTY")
    if source_commit and not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        _fail("SOURCE_COMMIT_INVALID")

    rows = _control_rows(crosswalk)
    if set(rows) != set(EXPECTED_STATUSES):
        _fail("CONTROL_SET_MISMATCH")

    for control_id, expected in EXPECTED_STATUSES.items():
        observed, _ = rows[control_id]
        if observed != expected:
            _fail("CONTROL_STATUS_UNSUPPORTED")

    header = "\n".join(crosswalk.splitlines()[:12]).upper()
    if "AGGREGATE BLOCKED" not in header or "NO CONTROL ACCEPTANCE" not in header:
        _fail("AGGREGATE_STATUS_UNSUPPORTED")

    for pattern in FORBIDDEN_POSITIVE_CLAIMS:
        if pattern.search(crosswalk):
            _fail("UNSUPPORTED_ASSURANCE_CLAIM")

    row_01 = rows["L4M-01"][1].lower()
    row_04 = rows["L4M-04"][1].lower()
    row_07 = rows["L4M-07"][1].lower()
    row_10 = rows["L4M-10"][1].lower()
    if "no complete owner-controlled package" not in row_01 and "owner custody is not verified" not in row_01:
        _fail("REQUIRED_LIMITATION_MISSING")
    if "no owner-run verification" not in row_04 and "owner-run offline verification is not verified" not in crosswalk.lower():
        _fail("REQUIRED_LIMITATION_MISSING")
    if "no worm/immutability claim" not in row_07:
        _fail("REQUIRED_LIMITATION_MISSING")
    if "no frozen baseline" not in row_10 and "owner acceptance is not verified" not in crosswalk.lower():
        _fail("REQUIRED_LIMITATION_MISSING")

    return {
        "schema_version": "T0_L4M08_CLAIM_DISCIPLINE_V1",
        "source_commit": source_commit or None,
        "scope": "current control-to-source crosswalk only; not a repository-wide claim scan",
        "verdict": "PASS",
        "aggregate": "BLOCKED / NOT VERIFIED",
        "active_control_count": ACTIVE_CONTROL_COUNT,
        "controls": {key: rows[key][0] for key in sorted(rows)},
        "checks": [
            "all ten control identifiers occur exactly once",
            "control dispositions match the current approved crosswalk baseline",
            "L4M-09 remains owner-waived and outside the active denominator",
            "aggregate acceptance remains blocked",
            "no unsupported WORM, independent-assurance, owner-acceptance or runtime claim",
            "owner-only custody, offline verification and frozen-baseline limitations remain explicit",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crosswalk", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    try:
        source_commit = os.environ["GITHUB_SHA"]
        if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
            _fail("SOURCE_COMMIT_INVALID")
        crosswalk = Path(args.crosswalk).read_text(encoding="utf-8")
        report = audit_crosswalk(crosswalk, source_commit)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        payload = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        manifest = output_dir / "claim-discipline-report.json"
        sidecar = output_dir / "claim-discipline-report.sha256"
        manifest.write_bytes(payload)
        sidecar.write_text(hashlib.sha256(payload).hexdigest() + "  " + manifest.name + "\n", encoding="ascii")
    except ClaimDisciplineError as exc:
        print("L4M08_CLAIM_DISCIPLINE=BLOCKED " + str(exc), file=sys.stderr)
        return 1
    except (KeyError, OSError, UnicodeError, ValueError):
        print("L4M08_CLAIM_DISCIPLINE=BLOCKED INPUT_INVALID", file=sys.stderr)
        return 1
    print("L4M08_CLAIM_DISCIPLINE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
