"""Static audit for the T0 Operational Contract & Release Gate.

The audit verifies the GitHub Actions T0 workflow inventory and source-level
invariants. It never starts the feeder or connects to an exchange/database.
"""
import json
from pathlib import Path
import subprocess

import yaml


RELEASE_BRANCH = "feature/t0-operational-contract-release-gate-20261102"
T0_WORKFLOW = ".github/workflows/t0-validation.yml"
MANUAL_WORKFLOW = ".github/workflows/t0-manual-validation.yml"

GREEN_TEST_MODULES = {
    "market_data.test_feeder_lease",
    "market_data.test_feeder_health",
    "market_data.test_feeder_health_api",
    "market_data.test_feeder_lifecycle",
    "market_data.test_feeder_scheduler",
    "market_data.test_feeder_retry",
    "market_data.test_feeder_recovery",
    "market_data.test_feeder_atomic_fencing",
    "market_data.test_feeder_health_runtime_api",
    "market_data.test_feeder_sigkill_recovery",
}

RETIRED_CODEMAGIC_WORKFLOWS = {
    "market-data-timescaledb",
    "market-data-kraken-adapter-tests",
    "market-data-kraken-spot-sqlite-tests",
    "market-data-kraken-spot-read-api",
    "t0-feeder-scheduler",
    "t0-feeder-health",
    "t0-feeder-lifecycle",
    "t0-feeder-atomic-fencing",
    "t0-health-runtime-api",
    "t0-feeder-sigkill-recovery",
    "t0-operational-contract-release-gate",
    "t0-data-integrity-candle-continuity-gate",
    "t0-final-runtime-configuration-check",
    "t0-component-tests-p3",
    "t0-feeder-lifecycle-red",
    "t0-feeder-atomic-fencing-red",
    "p5-2-4-shadow-migration-red",
    "p5-2-5-runtime-red-validation",
}


def _check(check_id, passed, detail):
    return {"id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail}


def _workflow(root):
    path = Path(root) / T0_WORKFLOW
    with path.open(encoding="utf-8") as source:
        return yaml.safe_load(source)


def _run_text(workflow):
    jobs = workflow.get("jobs", {})
    return "\n".join(
        step.get("run", "")
        for job in jobs.values()
        for step in job.get("steps", [])
        if isinstance(step, dict)
    )


def audit_contract(root):
    root = Path(root)
    workflow = _workflow(root)
    manual_path = root / MANUAL_WORKFLOW
    manual = yaml.safe_load(manual_path.read_text(encoding="utf-8")) if manual_path.exists() else {}
    jobs = workflow.get("jobs", {})
    commands = _run_text(workflow)

    missing_modules = sorted(module for module in GREEN_TEST_MODULES if module not in commands)
    count_contracts = {
        "atomic_fencing_count": 'grep -q "Ran 99 tests"',
        "sigkill_recovery_count": 'grep -q "Ran 100 tests"',
        "health_runtime_api_count": 'grep -q "Ran 106 tests"',
    }
    missing_counts = sorted(name for name, token in count_contracts.items() if token not in commands)
    inventory_ok = "t0-validation" in jobs and not missing_modules and not missing_counts

    artifact_step = any(
        step.get("uses", "").startswith("actions/upload-artifact@")
        and "ci-source-sha.txt" in step.get("with", {}).get("path", "")
        for job in jobs.values()
        for step in job.get("steps", [])
        if isinstance(step, dict)
    )
    sha_ok = "git rev-parse HEAD" in commands and artifact_step

    on_config = workflow.get("on", workflow.get(True, {}))
    push = on_config.get("push", {}) if isinstance(on_config, dict) else {}
    push_branches = set(push.get("branches", []))
    push_paths = set(push.get("paths", []))
    scope_ok = (
        RELEASE_BRANCH in push_branches
        and "ci/**" in push_paths
        and T0_WORKFLOW in push_paths
    )

    static_step = next(
        (
            step for step in jobs.get("t0-validation", {}).get("steps", [])
            if step.get("name") == "Run static operational contract and source audit"
        ),
        {},
    )
    static_script = static_step.get("run", "")
    forbidden_runtime_modules = (
        "market_data.test_feeder_",
        "market_data.feeder_service",
        "market_data.sync",
    )
    static_only_ok = (
        "ci.test_t0_operational_contract" in static_script
        and "ci/t0_operational_contract.py" in static_script
        and all(token not in static_script for token in forbidden_runtime_modules)
    )

    manual_options = (
        manual.get("on", manual.get(True, {}))
        .get("workflow_dispatch", {})
        .get("inputs", {})
        .get("gate", {})
        .get("options", [])
    )
    manual_ok = {
        "final-runtime-config",
        "component-tests-p3",
        "kraken-adapter",
        "kraken-spot-sqlite",
        "kraken-spot-read-api",
        "timescaledb-integration",
    }.issubset(set(manual_options))

    with (root / "codemagic.yaml").open(encoding="utf-8") as source:
        codemagic = yaml.safe_load(source)
    codemagic_workflows = codemagic.get("workflows", {})
    retired_ok = RETIRED_CODEMAGIC_WORKFLOWS.isdisjoint(codemagic_workflows)
    canonical = codemagic_workflows.get("canonical-market-data", {})
    canonical_commands = "\n".join(
        item.get("script", "") for item in canonical.get("scripts", [])
        if isinstance(item, dict)
    )
    t0_core_modules = (
        "market_data.test_store",
        "market_data.test_storage",
        "market_data.test_sync",
        "market_data.test_api",
        "market_data.test_gateway_runtime",
    )
    retired_ok = retired_ok and all(module not in canonical_commands for module in t0_core_modules)

    feeder_service = (root / "market_data/feeder_service.py").read_text(encoding="utf-8")
    sync_source = (root / "market_data/sync.py").read_text(encoding="utf-8")
    store_source = (root / "market_data/store.py").read_text(encoding="utf-8")
    canonical_ok = all((
        "ccxt.binanceusdm(" in feeder_service,
        'if backend != "sqlite":' in feeder_service,
        "Path(lease_path).expanduser().resolve() != Path(candle_path).expanduser().resolve()" in feeder_service,
        '"BTCUSDT"' in sync_source,
        'if exchange.id != "binanceusdm":' in sync_source,
        "opened + interval > closed_through" in sync_source,
        'EXCHANGE, MARKET_TYPE, SYMBOL = "binance", "USDT_PERPETUAL", "BTCUSDT"' in store_source,
    ))

    fencing_ok = all((
        "T0WriteGateway" in feeder_service,
        "LeaseFence" in feeder_service,
        "gateway.insert_batch" in feeder_service,
        "gateway=gateway" in feeder_service,
        "isinstance(gateway, T0WriteGateway)" in sync_source,
        "gateway.insert_batch(candles, lease_token=lease_token, now_ms=lease_clock)" in sync_source,
    ))

    return [
        _check(
            "github_actions_green_test_inventory",
            inventory_ok,
            "T0 feeder lease, health, lifecycle, atomic fencing, runtime/API and SIGKILL suites "
            "are registered in the GitHub Actions workflow with historical count assertions."
            if inventory_ok else f"Missing modules: {missing_modules}; missing count assertions: {missing_counts}",
        ),
        _check(
            "source_sha_provenance",
            sha_ok,
            "The GitHub Actions workflow records git rev-parse HEAD and uploads ci-source-sha.txt."
            if sha_ok else "Exact source SHA recording or artifact upload is missing.",
        ),
        _check(
            "release_gate_scope",
            scope_ok,
            "The static release gate is scoped to its dedicated branch and T0 CI/workflow paths."
            if scope_ok else "Release gate branch or path filters are incomplete.",
        ),
        _check(
            "release_gate_is_static_only",
            static_only_ok,
            "The operational release audit runs only static tests/reporting and does not invoke feeder/runtime suites."
            if static_only_ok else "The static audit step includes a runtime/feeder invocation or is missing.",
        ),
        _check(
            "manual_gates_preserved",
            manual_ok,
            "Final runtime config, P3 components, Kraken isolated tests and TimescaleDB integration remain manual GitHub Actions gates."
            if manual_ok else "One or more manual T0 gate choices are missing.",
        ),
        _check(
            "codemagic_t0_retirement",
            retired_ok,
            "T0-specific Codemagic workflows and T0 core test commands in the mixed workflow are retired."
            if retired_ok else "T0-specific Codemagic workflow entries or core test commands remain.",
        ),
        _check(
            "canonical_market_contract",
            canonical_ok,
            "Production composition selects Binance USD-M BTCUSDT and accepts only closed candles in canonical SQLite."
            if canonical_ok else "One or more Binance USD-M / closed-candle source invariants changed.",
        ),
        _check(
            "sqlite_gateway_fencing_contract",
            fencing_ok,
            "Production feeder and sync use T0WriteGateway with typed LeaseFence for SQLite atomic write admission."
            if fencing_ok else "One or more T0WriteGateway / LeaseFence source invariants changed.",
        ),
    ]


def write_report(root, checks):
    root = Path(root)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    failed = [item for item in checks if item["status"] != "PASS"]
    report = {
        "schema_version": 2,
        "source_sha": sha,
        "release_branch": RELEASE_BRANCH,
        "result": "FAIL" if failed else "PASS",
        "checks": checks,
        "not_verified": [
            "Controlled Runtime Health Smoke is intentionally not performed by this gate.",
            "Continuous production runtime operation is not established by static checks.",
            "External TimescaleDB integration is not run unless the dedicated GitHub secret is configured and the manual gate is selected.",
            "T1-T4 read-only enforcement is outside this T0-only gate and is not certified here.",
            "No canonical database, feeder process, or exchange connection is used by CI.",
        ],
    }
    (root / "t0-operational-contract-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# T0 Operational Contract & Release Gate",
        "",
        f"- Result: **{report['result']}**",
        f"- Source SHA: {sha}",
        f"- Branch contract: {RELEASE_BRANCH}",
        "- CI provider: GitHub Actions",
        "- Execution scope: static source/configuration audit only; no feeder startup or exchange connection.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- [{item['status']}] {item['id']} — {item['detail']}" for item in checks)
    lines.extend(["", "## Explicitly not verified", ""])
    lines.extend(f"- {item}" for item in report["not_verified"])
    (root / "t0-operational-contract-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main():
    root = Path(__file__).resolve().parents[1]
    checks = audit_contract(root)
    report = write_report(root, checks)
    for item in checks:
        print(f"{item['id']}={item['status']}: {item['detail']}")
    print(f"T0_OPERATIONAL_CONTRACT_RELEASE_GATE={report['result']}")
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
