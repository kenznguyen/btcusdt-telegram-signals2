"""Fail-closed guard for the manual live market-data acceptance target."""
from urllib.parse import unquote, urlparse

EXPECTED_DATABASE = "tsdb"
EXPECTED_CONFIRMATION = "tsdb-is-dedicated-staging"


def validate_acceptance_database(dsn: str, confirmation: str) -> str:
    """Return the database name only when the dedicated staging target is confirmed."""
    parsed = urlparse(dsn)
    database = unquote(parsed.path.lstrip("/")).lower()
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("Acceptance DSN must use PostgreSQL")
    if database != EXPECTED_DATABASE:
        raise ValueError("Acceptance DSN must target the explicitly approved database tsdb")
    if confirmation != EXPECTED_CONFIRMATION:
        raise ValueError("Dedicated staging database confirmation is missing or invalid")
    return database


if __name__ == "__main__":
    import os

    validate_acceptance_database(
        os.environ["MARKET_DATA_ACCEPTANCE_DATABASE_URL"],
        os.environ.get("MARKET_DATA_ACCEPTANCE_DATABASE_CONFIRMED", ""),
    )
    print("acceptance_database_guard=PASS database=tsdb")
