"""Offline certification gate. Never certify absent or empty event traces."""
import argparse
import json
from pathlib import Path

from compare_events import compare


def certify(android_events, freqtrade_events, *, source_commit, dataset_sha256):
    if not isinstance(source_commit, str) or len(source_commit.strip()) < 7:
        raise ValueError("Source commit required")
    if not isinstance(dataset_sha256, str) or len(dataset_sha256) != 64 or any(
        c not in "0123456789abcdef" for c in dataset_sha256.lower()
    ):
        raise ValueError("Dataset SHA256 required")
    if not android_events or not freqtrade_events:
        return {"verified": False, "reason": "empty_trace", "comparison": None}
    result = compare(android_events, freqtrade_events)
    reason = "manual_strategy_review_required" if result["passed"] else "trace_mismatch"
    return {"verified": False, "reason": reason,
            "comparison": result, "source_commit": source_commit,
            "dataset_sha256": dataset_sha256}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("android_trace", type=Path)
    parser.add_argument("freqtrade_trace", type=Path)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = certify(json.loads(args.android_trace.read_text(encoding="utf-8")),
                     json.loads(args.freqtrade_trace.read_text(encoding="utf-8")),
                     source_commit=args.source_commit, dataset_sha256=args.dataset_sha256)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    # Matching traces are necessary but NOT sufficient for certification.
    # Fail closed until the real Freqtrade adapter and manual review are complete.
    if not result["verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
