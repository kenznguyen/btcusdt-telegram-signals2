"""Fail-closed SQLite path guard for CI-only T0 audit/test processes.

Production feeder modules do not import this guard. In CI, every audited database
must be explicitly placed below an existing disposable root and match T0_TEST_DB.
"""
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit


_DATABASE_ENV_KEYS = (
    "MARKET_DATA_DB",
    "T0_FEEDER_LEASE_DB",
    "PAPER_DB",
    "PAPER_TRADING_DB",
)


class TestIsolationError(RuntimeError):
    """Raised before SQLite is opened when CI isolation cannot be proven."""


def _plain_path(value):
    if isinstance(value, os.PathLike):
        value = os.fspath(value)
    if not isinstance(value, str) or not value.strip():
        raise TestIsolationError("database path is required")
    raw = value.strip()
    if raw.startswith("file:"):
        parsed = urlsplit(raw)
        if parsed.scheme != "file" or parsed.netloc not in ("", "localhost"):
            raise TestIsolationError("SQLite URI must be a local file URI")
        if parsed.query and any(
            item.split("=", 1)[0] not in {"mode", "cache", "immutable"}
            for item in parsed.query.split("&")
        ):
            raise TestIsolationError("SQLite URI contains unsupported parameters")
        raw = unquote(parsed.path)
        if not raw:
            raise TestIsolationError("SQLite URI path is empty")
    return Path(raw).expanduser()


def validate_test_database_path(db_path, environ=None):
    """Return the resolved DB path, rejecting unsafe CI paths before connect.

    Outside CI this is a no-op path normalization. In CI (or explicit test mode),
    T0_TEST_MODE=1, an existing T0_TEST_ROOT, and an exact T0_TEST_DB match are
    mandatory. Symlink escapes are rejected by resolving before containment checks.
    """
    values = os.environ if environ is None else environ
    in_ci = str(values.get("GITHUB_ACTIONS", "")).lower() == "true" or (
        str(values.get("CI", "")).lower() == "true"
    )
    test_mode = values.get("T0_TEST_MODE") == "1"
    candidate = _plain_path(db_path).resolve(strict=False)

    if not in_ci and not test_mode:
        return candidate
    if not test_mode:
        raise TestIsolationError("T0_TEST_MODE=1 is required in CI")
    root_value = values.get("T0_TEST_ROOT", "")
    expected_value = values.get("T0_TEST_DB", "")
    if not root_value or not expected_value:
        raise TestIsolationError("T0_TEST_ROOT and T0_TEST_DB are required")
    root = Path(root_value).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise TestIsolationError("T0_TEST_ROOT must be an existing directory")
    expected = _plain_path(expected_value).resolve(strict=False)

    try:
        candidate.relative_to(root)
        expected.relative_to(root)
    except ValueError as error:
        raise TestIsolationError("database path must be inside T0_TEST_ROOT") from error
    if candidate != expected:
        raise TestIsolationError("database path must exactly match T0_TEST_DB")

    for key in _DATABASE_ENV_KEYS:
        value = values.get(key, "")
        if not value:
            continue
        configured = _plain_path(value).resolve(strict=False)
        try:
            configured.relative_to(root)
        except ValueError as error:
            raise TestIsolationError(f"{key} points outside T0_TEST_ROOT") from error
        if configured != expected:
            raise TestIsolationError(f"{key} must match T0_TEST_DB when set")

    # Reject aliases to existing configured database files (including hard links).
    try:
        candidate_stat = candidate.stat()
    except FileNotFoundError:
        candidate_stat = None
    if candidate_stat is not None:
        for key in _DATABASE_ENV_KEYS:
            value = values.get(key, "")
            if not value:
                continue
            configured = _plain_path(value).resolve(strict=False)
            try:
                configured_stat = configured.stat()
            except FileNotFoundError:
                continue
            if (candidate_stat.st_dev, candidate_stat.st_ino) != (
                configured_stat.st_dev, configured_stat.st_ino
            ):
                continue
            if configured != expected:
                raise TestIsolationError(f"{key} aliases the selected database")

    return candidate
