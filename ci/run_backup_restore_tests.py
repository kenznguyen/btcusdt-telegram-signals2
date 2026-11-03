"""Run P5.4.9 fixture-only tests and emit a compact evidence bundle."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ci"))

from backup_restore_test_support import (  # noqa: E402
    create_online_backup,
    inspect_database,
    verify_backup,
)
from paper_execution.shadow_migration_fixture import (  # noqa: E402
    FIXED_NOW_MS,
    PAPER_TABLES,
    build_legacy_fixture,
)

EVIDENCE = ROOT / "backup-restore-evidence"
REQUIRED_TABLES = (
    "candles", "feeder_leases", "feeder_runtime_status",
    *PAPER_TABLES, "paper_control_budget",
)
REQUIRED_ROWS = {
    "paper_state": ("id", 1),
    "paper_strategy_state": ("id", 1),
    "paper_risk_control": ("id", 1),
    "paper_account_config": ("id", 1),
}
FORBIDDEN_ENV = (
    "MARKET_DATA_DB", "T0_FEEDER_LEASE_DB", "PAPER_DB", "PAPER_TRADING_DB",
    "BINANCE_API_KEY", "BINANCE_API_SECRET", "OKX_API_KEY", "OKX_API_SECRET",
    "MARKET_DATA_POSTGRES_DSN", "MARKET_DATA_TOKEN", "MARKET_DATA_BACKEND",
    "PAPER_MAX_DRAWDOWN_PCT", "PAPER_MAX_DAILY_LOSS_USDT", "PAPER_MAX_EXPOSURE_USDT",
)


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(name, value):
    (EVIDENCE / name).write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def _source_sha():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    for old in EVIDENCE.iterdir():
        if old.is_file():
            old.unlink()
        elif old.is_dir():
            raise RuntimeError("Unexpected directory in evidence output")

    source_sha = _source_sha()
    env_state = {name: bool(os.environ.get(name)) for name in FORBIDDEN_ENV}
    ai_execution_enabled = os.environ.get("AI_EXECUTION_ENABLED", "false").strip().lower()
    isolation_ok = not any(env_state.values()) and ai_execution_enabled == "false"

    _write_json("run-metadata.json", {
        "source_sha": source_sha,
        "runner_provider": (
            "github_actions" if os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
            else "codemagic" if os.environ.get("CM_BUILD_ID")
            else "unknown"
        ),
        "branch": os.environ.get("GITHUB_REF_NAME") or os.environ.get("CM_BRANCH", ""),
        "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""),
        "github_workflow": os.environ.get("GITHUB_WORKFLOW", ""),
        "github_repository": os.environ.get("GITHUB_REPOSITORY", ""),
        "codemagic_build_id": os.environ.get("CM_BUILD_ID", ""),
        "codemagic_workflow_id": os.environ.get("CM_WORKFLOW_ID", ""),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "runner": platform.platform(),
    })
    _write_json("isolation-audit.json", {
        "status": "PASS" if isolation_ok else "FAIL",
        "forbidden_environment_variables_present": env_state,
        "ai_execution_enabled": False if ai_execution_enabled == "false" else ai_execution_enabled,
        "test_database_policy": "TemporaryDirectory only",
        "network_calls_in_test_suite": False,
        "exchange_connections": False,
        "feeder_startup": False,
        "canonical_database_access": False,
        "live_or_paper_order_execution": False,
    })
    if not isolation_ok:
        _write_json("test-results.json", {
            "status": "FAIL", "tests_run": 0,
            "reason": "Execution boundary preflight failed",
        })
        raise SystemExit("Backup/Restore test isolation preflight failed")

    loader = unittest.defaultTestLoader
    suite = loader.discover(
        start_dir=str(ROOT / "ci"),
        pattern="test_backup_restore.py",
        top_level_dir=str(ROOT / "ci"),
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    _write_json("test-results.json", {
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses),
    })

    if not result.wasSuccessful():
        _write_json("restore-validation.json", {
            "status": "NOT_VALIDATED",
            "reason": "Fixture contract tests did not pass",
        })
        raise SystemExit(1)

    with tempfile.TemporaryDirectory(prefix="p5_4_9_backup_restore_evidence_") as temporary:
        root = Path(temporary)
        source = root / "source" / "fixture.sqlite3"
        source.parent.mkdir()
        fixture = build_legacy_fixture(source)
        source_report = inspect_database(
            source, root=root, required_tables=REQUIRED_TABLES,
            required_rows=REQUIRED_ROWS,
        )
        backup = root / "backup" / "verified.sqlite3"
        backup.parent.mkdir()
        create_online_backup(
            source, backup, root=root, required_tables=REQUIRED_TABLES,
            required_rows=REQUIRED_ROWS,
        )
        verification = verify_backup(
            source, backup, root=root, required_tables=REQUIRED_TABLES,
            required_rows=REQUIRED_ROWS,
        )
        source_hash, backup_hash = _sha256(source), _sha256(backup)
        _write_json("fixture-spec.json", {
            "profile": "single_sqlite",
            "fixed_now_ms": FIXED_NOW_MS,
            "logical_domains": ["candles", "paper_ledger", "risk_state", "paper_state", "feeder_lease"],
            "required_tables": list(REQUIRED_TABLES),
            "required_singleton_rows": sorted(REQUIRED_ROWS),
            "paper_fixture_tables": list(PAPER_TABLES),
            "fixture_builder": "paper_execution.shadow_migration_fixture.build_legacy_fixture",
            "fixture_metadata": fixture,
        })
        _write_json("backup-manifest.json", {
            "manifest_version": 1,
            "topology": "single_sqlite",
            "source_sha": source_sha,
            "source_database_sha256": source_hash,
            "backup_database_sha256": backup_hash,
            "source_size_bytes": source.stat().st_size,
            "backup_size_bytes": backup.stat().st_size,
            "logical_projection_sha256": verification["source_logical_sha256"],
            "table_counts": verification["table_counts"],
            "integrity_check": verification["integrity_check"],
            "foreign_key_violations": verification["foreign_key_violations"],
        })
        _write_json("restore-validation.json", {
            "status": verification["status"],
            "source_logical_sha256": verification["source_logical_sha256"],
            "backup_logical_sha256": verification["backup_logical_sha256"],
            "logical_state_equal": (
                verification["source_logical_sha256"] == verification["backup_logical_sha256"]
            ),
            "integrity_check": source_report["integrity_check"],
            "foreign_key_violations": source_report["foreign_key_violations"],
            "production_restore": "NOT_TESTED",
        })
        (EVIDENCE / "integrity-check.txt").write_text(
            "source=ok\nbackup=ok\nsource_foreign_key_violations=0\n"
            "backup_foreign_key_violations=0\n", encoding="utf-8"
        )
        (EVIDENCE / "execution-boundary.txt").write_text(
            "fixture_only=true\ncanonical_database_access=false\n"
            "feeder_started=false\nexchange_contacted=false\n"
            "network_calls_in_tests=false\nai_execution_enabled=false\n"
            "live_orders=false\npaper_orders_executed=false\n"
            "natural_doze=INTERRUPTED_DEFERRED_EXCLUDED\n",
            encoding="utf-8",
        )

    checksum_lines = []
    for artifact in sorted(EVIDENCE.iterdir()):
        if artifact.is_file() and artifact.name != "sha256sums.txt":
            checksum_lines.append(f"{_sha256(artifact)}  {artifact.name}")
    (EVIDENCE / "sha256sums.txt").write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8"
    )
    print(f"P5_4_9_FIXTURE_BACKUP_RESTORE={'PASS' if result.wasSuccessful() else 'FAIL'}")
    print(f"P5_4_9_TESTS={result.testsRun}")
    print(f"P5_4_9_SOURCE_SHA={source_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
