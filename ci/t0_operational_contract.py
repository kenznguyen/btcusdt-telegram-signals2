"""Static audit for the T0 Operational Contract & Release Gate.

This module validates Codemagic registration and the canonical feeder's
source-level invariants. It does not start the feeder and does not run any
market_data.test_feeder_* suite.
"""
import json
from pathlib import Path
import subprocess

import yaml


RELEASE_BRANCH = "feature/t0-operational-contract-release-gate-20261102"

GREEN_WORKFLOW_MODULES = {
    "t0-feeder-lifecycle": {
        "market_data.test_feeder_lifecycle",
        "market_data.test_feeder_scheduler",
        "market_data.test_feeder_retry",
        "market_data.test_feeder_recovery",
        "market_data.test_feeder_lease",
        "market_data.test_feeder_health",
        "market_data.test_feeder_health_api",
    },
    "t0-feeder-atomic-fencing": {
        "market_data.test_feeder_atomic_fencing",
        "market_data.test_feeder_lifecycle",
        "market_data.test_feeder_scheduler",
        "market_data.test_feeder_retry",
        "market_data.test_feeder_recovery",
        "market_data.test_feeder_lease",
        "market_data.test_feeder_health",
        "market_data.test_feeder_health_api",
    },
    "t0-feeder-sigkill-recovery": {
        "market_data.test_feeder_sigkill_recovery",
        "market_data.test_feeder_atomic_fencing",
        "market_data.test_feeder_lifecycle",
        "market_data.test_feeder_scheduler",
        "market_data.test_feeder_retry",
        "market_data.test_feeder_recovery",
        "market_data.test_feeder_lease",
        "market_data.test_feeder_health",
        "market_data.test_feeder_health_api",
    },
    "t0-health-runtime-api": {
        "market_data.test_feeder_health_runtime_api",
        "market_data.test_feeder_atomic_fencing",
        "market_data.test_feeder_sigkill_recovery",
        "market_data.test_feeder_lifecycle",
        "market_data.test_feeder_scheduler",
        "market_data.test_feeder_retry",
        "market_data.test_feeder_recovery",
        "market_data.test_feeder_lease",
        "market_data.test_feeder_health",
        "market_data.test_feeder_health_api",
    },
}

SHA_WORKFLOWS = (
    "t0-feeder-scheduler",
    "t0-feeder-health",
    "t0-feeder-lifecycle",
    "t0-feeder-atomic-fencing",
    "t0-feeder-sigkill-recovery",
    "t0-health-runtime-api",
)


def _script_text(workflow):
    return "\n".join(
        item.get("script", "")
        for item in workflow.get("scripts", [])
        if isinstance(item, dict)
    )


def _check(check_id, passed, detail):
    return {"id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail}


def audit_contract(root):
    root = Path(root)
    with (root / "codemagic.yaml").open(encoding="utf-8") as source:
        config = yaml.safe_load(source)
    workflows = config.get("workflows", {})

    inventory_errors = []
    for workflow_name, expected_modules in GREEN_WORKFLOW_MODULES.items():
        workflow = workflows.get(workflow_name)
        if not isinstance(workflow, dict):
            inventory_errors.append(f"missing workflow: {workflow_name}")
            continue
        script = _script_text(workflow)
        missing = sorted(module for module in expected_modules if module not in script)
        if missing:
            inventory_errors.append(f"{workflow_name} missing: {', '.join(missing)}")

    count_contracts = {
        "t0-feeder-atomic-fencing": 'grep -q "Ran 99 tests"',
        "t0-feeder-sigkill-recovery": 'grep -q "Ran 100 tests"',
        "t0-health-runtime-api": 'grep -q "Ran 106 tests"',
    }
    for workflow_name, expected in count_contracts.items():
        if expected not in _script_text(workflows.get(workflow_name, {})):
            inventory_errors.append(f"{workflow_name} missing count assertion {expected}")

    inventory_ok = not inventory_errors
    inventory_detail = (
        "All six original contract groups plus lifecycle, atomic fencing, SIGKILL "
        "recovery and runtime/API integration are registered with their expected "
        "test modules and historical count assertions."
        if inventory_ok else "; ".join(inventory_errors)
    )

    sha_errors = []
    for workflow_name in SHA_WORKFLOWS:
        workflow = workflows.get(workflow_name, {})
        script = _script_text(workflow)
        artifacts = workflow.get("artifacts", [])
        if "ci-source-sha.txt" not in artifacts:
            sha_errors.append(f"{workflow_name} does not publish ci-source-sha.txt")
        if "git rev-parse HEAD" not in script and "ci/setup-python.sh" not in script:
            sha_errors.append(f"{workflow_name} does not record the checked-out source SHA")
    sha_ok = not sha_errors

    release = workflows.get("t0-operational-contract-release-gate", {})
    release_script = _script_text(release)
    patterns = (
        release.get("triggering", {}).get("branch_patterns", [])
        if isinstance(release, dict) else []
    )
    release_branches = {
        item.get("pattern") for item in patterns if isinstance(item, dict)
    }
    changes = set(
        release.get("when", {}).get("changeset", {}).get("includes", [])
        if isinstance(release, dict) else []
    )
    expected_changes = {
        "ci/t0_operational_contract.py",
        "ci/test_t0_operational_contract.py",
        "codemagic.yaml",
    }
    scope_ok = (
        RELEASE_BRANCH in release_branches
        and expected_changes.issubset(changes)
        and "git rev-parse HEAD" in release_script
        and "ci-source-sha.txt" in release.get("artifacts", [])
        and "ci.test_t0_operational_contract" in release_script
    )

    forbidden_runtime_modules = (
        "market_data.test_feeder_",
        "market_data.feeder_service",
        "market_data.sync",
    )
    static_only_ok = (
        all(token not in release_script for token in forbidden_runtime_modules)
        and "ci.test_t0_operational_contract" in release_script
        and '"$CI_PYTHON" ci/t0_operational_contract.py' in release_script
    )

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
        "insert_fenced" in feeder_service,
        "write_fence={" in feeder_service,
        "sync_callback=canonical_sync" in feeder_service,
        "T0_FEEDER_LEASE_DB must resolve to the same file as MARKET_DATA_DB" in feeder_service,
        "Fenced sync requires a store with atomic insert_fenced support" in sync_source,
    ))

    return [
        _check("green_test_inventory", inventory_ok, inventory_detail),
        _check(
            "source_sha_provenance",
            sha_ok,
            "All six T0 Codemagic workflows publish ci-source-sha.txt and record "
            "the checked-out commit SHA." if sha_ok else "; ".join(sha_errors),
        ),
        _check(
            "release_gate_scope",
            scope_ok,
            "Release Gate is bound to its dedicated branch, scoped changeset, "
            "self-test command and source-SHA artifact."
            if scope_ok else "Release Gate branch, changeset, test command or SHA artifact is incomplete.",
        ),
        _check(
            "release_gate_is_static_only",
            static_only_ok,
            "The Release Gate runs only its static contract tests and report; it "
            "does not start the feeder or invoke T0 runtime/SIGKILL suites."
            if static_only_ok else "Release Gate script contains a runtime or T0 suite invocation.",
        ),
        _check(
            "canonical_market_contract",
            canonical_ok,
            "Production composition selects Binance USD-M BTCUSDT; sync validates "
            "the market and stores only closed candles under the canonical identity."
            if canonical_ok else "One or more Binance USD-M / closed-candle source invariants changed.",
        ),
        _check(
            "sqlite_atomic_fencing_contract",
            fencing_ok,
            "Production feeder requires SQLite, a shared candle/lease database, "
            "and the fenced canonical sync path for scheduler and recovery."
            if fencing_ok else "One or more SQLite / atomic-fencing source invariants changed.",
        ),
    ]


def write_report(root, checks):
    root = Path(root)
    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    failed = [item for item in checks if item["status"] != "PASS"]
    report = {
        "schema_version": 1,
        "source_sha": sha,
        "release_branch": RELEASE_BRANCH,
        "result": "FAIL" if failed else "PASS",
        "checks": checks,
        "not_verified": [
            "Controlled Runtime Health Smoke is intentionally not performed by this gate.",
            "Continuous production runtime operation is not established by static checks.",
            "T1-T4 read-only enforcement is outside this T0-only gate and is not certified here.",
            "No Codemagic build/test evidence is created for historical GREEN commits by this report.",
        ],
    }
    json_path = root / "t0-operational-contract-report.json"
    markdown_path = root / "t0-operational-contract-report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# T0 Operational Contract & Release Gate",
        "",
        f"- Result: **{report['result']}**",
        f"- Source SHA: {sha}",
        f"- Branch: {RELEASE_BRANCH}",
        "- Execution scope: static source/configuration audit only; no feeder startup or T0 runtime suite.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(
        f"- [{item['status']}] {item['id']} — {item['detail']}"
        for item in checks
    )
    lines.extend(["", "## Explicitly not verified", ""])
    lines.extend(f"- {item}" for item in report["not_verified"])
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
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
