"""Canonical isolation checks for the configured PAPER ledger path."""

import os
from pathlib import Path


_T0_DATABASE_ENV_KEYS = ("MARKET_DATA_DB", "T0_FEEDER_LEASE_DB")
_PAPER_DATABASE_ENV_KEYS = ("PAPER_DB", "PAPER_TRADING_DB")


def _canonical(path):
    try:
        return Path(path).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        raise ValueError("LEDGER_PATH_INVALID") from None


def _overlaps(left, right):
    if left == right:
        return True
    try:
        if left.exists() and right.exists() and os.path.samefile(left, right):
            return True
    except OSError:
        raise ValueError("LEDGER_PATH_ALIAS_CHECK_FAILED") from None
    return left in right.parents or right in left.parents


def validate_ledger_path_isolated(ledger_path, *, environ=None):
    """Reject T0 aliases/overlaps and mismatched PAPER ledger aliases."""
    env = os.environ if environ is None else environ
    ledger = _canonical(ledger_path)

    for key in _T0_DATABASE_ENV_KEYS:
        value = env.get(key)
        if value and _overlaps(ledger, _canonical(value)):
            raise ValueError("T0_LEDGER_PATH_FORBIDDEN")

    for key in _PAPER_DATABASE_ENV_KEYS:
        value = env.get(key)
        if value and _canonical(value) != ledger:
            raise ValueError("LEDGER_PATH_ENV_MISMATCH")

    return ledger
