"""Static-only Continuous Core dry-run; never opens or mutates runtime state."""

import hashlib
import os
from pathlib import Path

from core_runtime.one_shot import _runner_policy
from core_runtime.preflight import (
    PreflightError,
    _CREDENTIAL_ENV_KEYS,
    _load_config,
)


class ContinuousDryRunError(ValueError):
    """Stable, user-safe static dry-run rejection."""


_T0_PATH_ENV_KEYS = ("MARKET_DATA_DB", "T0_FEEDER_LEASE_DB")


def _canonical(path):
    try:
        return Path(path).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        raise ContinuousDryRunError("RUNNER_PATH_INVALID") from None


def _overlaps(left, right):
    if left == right:
        return True
    try:
        if left.exists() and right.exists() and os.path.samefile(left, right):
            return True
    except OSError:
        raise ContinuousDryRunError("RUNNER_PATH_ALIAS_CHECK_FAILED") from None
    return left in right.parents or right in left.parents


def inspect_continuous_dry_run(
    config_path,
    *,
    journal_path,
    bundle_store_dir,
    environ=None,
):
    """Validate static PAPER configuration and paths without touching runtime state.

    This deliberately does not open the ledger, initialize a journal, create a
    bundle directory, acquire a process lock, recover cycles, request bundles,
    or invoke One-shot/PaperLedger.
    """
    env = os.environ if environ is None else environ
    try:
        config, ledger_path = _load_config(config_path)
        _runner_policy(config)
    except PreflightError as exc:
        raise ContinuousDryRunError(str(exc)) from None

    if set(config) != {
        "mode", "ai_execution_enabled", "ledger_path", "risk_limits",
        "max_book_age_ms", "max_position_base",
    }:
        raise ContinuousDryRunError("RUNNER_CONFIG_REQUIRED")

    if env.get("AI_EXECUTION_ENABLED") != "false":
        raise ContinuousDryRunError("AI_EXECUTION_MUST_BE_EXPLICITLY_DISABLED")
    if any(env.get(key) for key in _CREDENTIAL_ENV_KEYS):
        raise ContinuousDryRunError("EXCHANGE_CREDENTIALS_FORBIDDEN")

    if not ledger_path.is_file():
        raise ContinuousDryRunError("LEDGER_FILE_REQUIRED")

    journal = _canonical(journal_path)
    bundle_store = _canonical(bundle_store_dir)
    ledger = _canonical(ledger_path)

    if journal == bundle_store or journal in bundle_store.parents or bundle_store in journal.parents:
        raise ContinuousDryRunError("RUNNER_PATHS_OVERLAP")

    for candidate in (journal, bundle_store):
        for env_key in _T0_PATH_ENV_KEYS:
            protected_value = env.get(env_key)
            if protected_value and _overlaps(candidate, _canonical(protected_value)):
                raise ContinuousDryRunError("RUNNER_PATH_OVERLAPS_PROTECTED_DATA")
        if _overlaps(candidate, ledger):
            raise ContinuousDryRunError("RUNNER_PATH_OVERLAPS_PROTECTED_DATA")

    if not journal.parent.is_dir() or not bundle_store.parent.is_dir():
        raise ContinuousDryRunError("RUNNER_PATH_PARENT_REQUIRED")
    if journal.exists() and (journal.is_symlink() or not journal.is_file()):
        raise ContinuousDryRunError("RUNNER_JOURNAL_PATH_INVALID")
    if bundle_store.exists() and (bundle_store.is_symlink() or not bundle_store.is_dir()):
        raise ContinuousDryRunError("RUNNER_BUNDLE_STORE_PATH_INVALID")

    raw_config = Path(config_path).read_bytes()
    return {
        "status": "DRY_RUN_CONFIG_VALIDATED",
        "mode": "PAPER",
        "decisionCycle": "NOT_RUN",
        "configSha256": "sha256:" + hashlib.sha256(raw_config).hexdigest(),
        "ledgerPath": str(ledger),
        "ledgerContentsVerified": False,
        "journalPath": str(journal),
        "journalCreated": False,
        "bundleStoreDir": str(bundle_store),
        "bundleStoreCreated": False,
        "oneShotInvoked": False,
        "aiExecutionEnabled": False,
        "exchangeCredentialsUsed": False,
        "persistentStateAccess": "NONE",
    }
