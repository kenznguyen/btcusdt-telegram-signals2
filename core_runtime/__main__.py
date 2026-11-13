"""Fail-closed PAPER Core preflight and explicitly invoked one-shot runner."""

import argparse
import json
import sys

from core_runtime.preflight import PreflightError, _preflight


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Explicit paper-only JSON config")
    parser.add_argument("--run-once", action="store_true",
                        help="Run exactly one validated Bundle v1 Core decision cycle")
    parser.add_argument("--bundle", help="Path to one immutable Core Decision Input Bundle v1 JSON")
    args = parser.parse_args(argv)
    if args.run_once and not args.bundle:
        parser.error("--run-once requires --bundle")
    if not args.run_once and args.bundle:
        parser.error("--bundle requires --run-once")
    try:
        if args.run_once:
            from core_runtime.one_shot import run_once
            result = run_once(args.config, args.bundle)
            print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))
            return 0 if result["runStatus"] in ("NO_SIGNAL", "PAPER_ACCEPTED") else 2
        result = _preflight(args.config)
    except PreflightError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception:
        print("PREFLIGHT_FAILED", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
