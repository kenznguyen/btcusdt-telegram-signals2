"""Fail-closed allowlist for optional TimescaleDB integration tests."""
import argparse
import hashlib
import hmac
import os
import re
from urllib.parse import unquote, urlsplit


class TestDatabaseAllowlistError(RuntimeError):
    """Raised when a PostgreSQL test endpoint is not explicitly allowlisted."""


def validate_disposable_postgres_dsn(dsn, expected_sha256):
    if not isinstance(dsn, str) or not dsn.strip():
        raise TestDatabaseAllowlistError("MARKET_DATA_TEST_DATABASE_URL is required")
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise TestDatabaseAllowlistError(
            "MARKET_DATA_TEST_DATABASE_URL_SHA256 must be a 64-character SHA-256 hex digest"
        )
    parsed = urlsplit(dsn.strip())
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise TestDatabaseAllowlistError("test database URL must use postgres or postgresql scheme")
    if not parsed.hostname or not unquote(parsed.path.lstrip("/")):
        raise TestDatabaseAllowlistError("test database URL must include a host and database name")
    actual = hashlib.sha256(dsn.strip().encode("utf-8")).hexdigest()
    if not hmac.compare_digest(actual, expected_sha256.lower()):
        raise TestDatabaseAllowlistError("test database URL does not match the configured disposable endpoint allowlist")
    return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-environment", action="store_true")
    parser.parse_args()
    try:
        validate_disposable_postgres_dsn(
            os.environ.get("MARKET_DATA_TEST_DATABASE_URL", ""),
            os.environ.get("MARKET_DATA_TEST_DATABASE_URL_SHA256", ""),
        )
    except TestDatabaseAllowlistError as error:
        parser.error(str(error))
    print("T0_POSTGRES_TEST_ENDPOINT_ALLOWLIST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
