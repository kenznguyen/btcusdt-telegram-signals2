"""Fail-closed guard for the manual live market-data acceptance target."""
from urllib.parse import unquote, urlparse

EXPECTED_DATABASE = "tsdb"
EXPECTED_CONFIRMATION = "tsdb-is-dedicated-staging"
PROXY_ENVIRONMENT_VARIABLES = (
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy",
)


def validate_direct_egress(environment) -> None:
    """Reject proxy configuration; Binance access must use the runner's direct egress."""
    configured = [name for name in PROXY_ENVIRONMENT_VARIABLES if environment.get(name)]
    if configured:
        raise ValueError("Proxy environment is not permitted for direct Binance acceptance")


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

    validate_direct_egress(os.environ)
    validate_acceptance_database(
        os.environ["MARKET_DATA_ACCEPTANCE_DATABASE_URL"],
        os.environ.get("MARKET_DATA_ACCEPTANCE_DATABASE_CONFIRMED", ""),
    )
    print("acceptance_database_guard=PASS database=tsdb")
