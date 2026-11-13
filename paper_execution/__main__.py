"""Explicit PAPER ledger initialization and read-only inspection; never sends orders."""

import argparse
import json
from pathlib import Path
import subprocess

from paper_execution.ledger import PaperLedger


def _reject_duplicate_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("BOOTSTRAP_MANIFEST_DUPLICATE_KEY")
        result[key] = value
    return result


def _load_manifest(path):
    manifest_path = Path(path).expanduser().resolve(strict=True)
    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("BOOTSTRAP_MANIFEST_UNREADABLE") from None
    if not isinstance(manifest, dict):
        raise ValueError("BOOTSTRAP_MANIFEST_INVALID")
    for field in ("fundingEvidencePath", "cutoverEvidencePath"):
        evidence_path = Path(manifest.get(field, "")).expanduser()
        if not evidence_path.is_absolute():
            manifest[field] = str((manifest_path.parent / evidence_path).resolve(strict=False))
    return manifest


def _current_source_sha():
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        raise ValueError("BOOTSTRAP_SOURCE_SHA_UNAVAILABLE") from None
    source_sha = completed.stdout.strip()
    if (len(source_sha) != 40
            or any(character not in "0123456789abcdef" for character in source_sha)):
        raise ValueError("BOOTSTRAP_SOURCE_SHA_UNAVAILABLE")
    return source_sha


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="SQLite database path")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--bootstrap-manifest",
        help="Create a fresh PAPER Dual Ledger database from a provenance manifest",
    )
    modes.add_argument(
        "--inspect", action="store_true",
        help="Inspect an existing Dual Ledger database using read-only SQLite access",
    )
    parser.add_argument(
        "--now-ms", type=int,
        help="Required UTC epoch milliseconds for read-only inspection",
    )
    parser.add_argument("--max-position-base", default="0.01")
    parser.add_argument("--fee-rate", default="0.0005")
    parser.add_argument("--max-spread-bps", default="50")
    args = parser.parse_args(argv)

    if args.inspect:
        if args.now_ms is None:
            parser.error("--inspect requires --now-ms")
        from paper_execution.bootstrap import inspect_paper_account
        result = inspect_paper_account(args.db, now_ms=args.now_ms)
        print(json.dumps(result, allow_nan=False, sort_keys=True))
        return 0 if result["riskReady"] else 2

    if args.bootstrap_manifest:
        if args.now_ms is not None:
            parser.error("--now-ms is only valid with --inspect")
        from paper_execution.bootstrap import bootstrap_paper_account
        manifest = _load_manifest(args.bootstrap_manifest)
        if manifest.get("sourceSha") != _current_source_sha():
            raise ValueError("BOOTSTRAP_SOURCE_SHA_MISMATCH")
        result = bootstrap_paper_account(args.db, manifest)
        print(json.dumps(result, allow_nan=False, sort_keys=True))
        return 0

    if args.now_ms is not None:
        parser.error("--now-ms is only valid with --inspect")
    ledger = PaperLedger(
        args.db, max_position_base=args.max_position_base,
        fee_rate=args.fee_rate, max_spread_bps=args.max_spread_bps,
    )
    print(json.dumps(ledger.snapshot(), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
