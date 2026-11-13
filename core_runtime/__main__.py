"""Fail-closed PAPER Core preflight, static dry-run and explicit one-shot runner."""

import argparse
import json
import sys

from core_runtime.preflight import PreflightError, _preflight
from core_runtime.continuous_dry_run import (
    ContinuousDryRunError,
    inspect_continuous_dry_run,
)


def main(argv=None, *, now_ms=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Explicit paper-only JSON config")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Static PAPER config/path validation; never opens or mutates runtime state",
    )
    parser.add_argument(
        "--journal-path",
        help="Future Continuous Runner journal path (not created)",
    )
    parser.add_argument(
        "--bundle-store-dir",
        help="Future immutable bundle directory (not created)",
    )
    parser.add_argument(
        "--run-once", action="store_true",
        help="Run exactly one validated Bundle v1 Core decision cycle",
    )
    parser.add_argument("--bundle", help="Path to one immutable Core Decision Input Bundle v1 JSON")
    args = parser.parse_args(argv)

    if args.ledger_preflight and (args.dry_run or args.run_once or args.bundle or args.journal_path or args.bundle_store_dir):
        parser.error("--ledger-preflight cannot be combined with runner execution or dry-run options")
    if args.dry_run and (args.run_once or args.bundle):
        parser.error("--dry-run cannot be combined with --run-once or --bundle")
    if args.dry_run and (not args.journal_path or not args.bundle_store_dir):
        parser.error("--dry-run requires --journal-path and --bundle-store-dir")
    if not args.dry_run and (args.journal_path or args.bundle_store_dir):
        parser.error("--journal-path and --bundle-store-dir require --dry-run")
    if args.run_once and not args.bundle:
        parser.error("--run-once requires --bundle")
    if not args.run_once and args.bundle:
        parser.error("--bundle requires --run-once")

    try:
        if args.dry_run:
            result = inspect_continuous_dry_run(
                args.config,
                journal_path=args.journal_path,
                bundle_store_dir=args.bundle_store_dir,
            )
            print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))
            return 0
        if args.run_once:
            from core_runtime.one_shot import run_once
            result = run_once(args.config, args.bundle, now_ms=now_ms)
            print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))
            return 0 if result["runStatus"] in ("NO_SIGNAL", "PAPER_ACCEPTED") else 2
        result = _preflight(args.config)
    except (PreflightError, ContinuousDryRunError, PaperLedgerPreflightError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception:
        print("PREFLIGHT_FAILED", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
