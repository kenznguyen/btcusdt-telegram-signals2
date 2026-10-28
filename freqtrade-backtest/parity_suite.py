"""Deterministic Android-vs-Python replay parity suite; no live trading.

The Python replay models Android predicates; it is NOT the Freqtrade runtime.
For each case, inputs come from matching deterministic constructions or a
shared JSON fixture. Event traces are compared field-by-field with hard fail.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from compare_events import compare

ROOT = Path(__file__).resolve().parent
CASES = (
    ("emergency", "export_emergency_parity_trace.py", "android-emergency-trace.json",
     "shared JSON fixture", "fixtures/android_python_emergency_exit_v1.json"),
    ("entry", "export_entry_parity_trace.py", "android-entry-trace.json",
     "shared JSON fixture", "fixtures/android_python_entry_ohlc_v1.json"),
    ("dca", "export_dca_parity_trace.py", "android-dca-trace.json",
     "mirrored deterministic generators", None),
    ("tp", "export_tp_parity_trace.py", "android-tp-trace.json",
     "mirrored deterministic generators", None),
)
REQUIRED_KINDS = {"emergency": "EMERGENCY_SL", "entry": "ENTRY",
                  "dca": "DCA", "tp": "TP"}


def compare_case(name, android_events, python_events):
    """Return a diagnostic rather than silently treating empty traces as parity."""
    result = compare(android_events, python_events)
    if not android_events or not python_events:
        result["passed"] = False
        result["mismatches"].append({"index": 0, "field": "empty_trace"})
    from compare_events import normalize_event
    android_kinds = {normalize_event(e)["kind"] for e in android_events}
    python_kinds = {normalize_event(e)["kind"] for e in python_events}
    expected = REQUIRED_KINDS[name]
    if expected not in android_kinds or expected not in python_kinds:
        result["passed"] = False
        result["mismatches"].append({
            "index": 0, "field": "required_event_kind",
            "required": expected, "android": sorted(android_kinds),
            "python": sorted(python_kinds),
        })
    result["case"] = name
    return result


def run_suite(android_dir, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = []
    for name, exporter, filename, provenance, fixture in CASES:
        android_file = android_dir / filename
        python_file = output_dir / ("python-" + name + "-trace.json")
        item = {"case": name, "android_trace": filename,
                "python_trace": python_file.name, "data_provenance": provenance,
                "shared_fixture_sha256": (
                    hashlib.sha256((ROOT / fixture).read_bytes()).hexdigest()
                    if fixture else None)}
        try:
            if not android_file.is_file():
                raise FileNotFoundError(f"Missing Android trace: {android_file}")
            subprocess.run([sys.executable, str(ROOT / exporter), str(python_file)],
                           check=True, capture_output=True, text=True)
            left = json.loads(android_file.read_text(encoding="utf-8"))
            right = json.loads(python_file.read_text(encoding="utf-8"))
            item["comparison"] = compare_case(name, left, right)
            item["passed"] = item["comparison"]["passed"]
        except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
            item["passed"] = False
            item["error"] = str(exc)
            if isinstance(exc, subprocess.CalledProcessError):
                item["stderr_tail"] = (exc.stderr or "")[-2000:]
        cases.append(item)
    passed = all(item["passed"] for item in cases)
    report = {
        "schema_version": 1,
        "engine_android": "StrategyEngine (Kotlin/JVM tests)",
        "engine_python": "offline Android-rule Python replay (NOT Freqtrade runtime)",
        "freqtrade_runtime_verified": False,
        "verified": False,
        "parity_checks_passed": passed,
        "cases": cases,
        "limitations": [
            "DCA/TP candles are created by mirrored generators, not loaded from a common fixture.",
            "Parity on synthetic fixtures does not establish historical profitability or exchange-fill parity.",
            "Freqtrade strategy/runtime execution and independent trade-ledger parity are not yet proven.",
        ],
    }
    (output_dir / "parity-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--android-dir", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=Path("parity-results"))
    args = parser.parse_args()
    report = run_suite(args.android_dir, args.output_dir)
    for case in report["cases"]:
        state = "PASS" if case["passed"] else "FAIL"
        print(f"{state}: {case['case']} ({case.get('data_provenance')})")
        for mismatch in case.get("comparison", {}).get("mismatches", [])[:20]:
            print("  mismatch: " + json.dumps(mismatch, ensure_ascii=False))
        if "error" in case:
            print("  error: " + case["error"])
    print("Report: " + str(args.output_dir / "parity-report.json"))
    raise SystemExit(0 if report["parity_checks_passed"] else 1)


if __name__ == "__main__":
    main()
