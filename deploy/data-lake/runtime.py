"""Small local-container launcher; credentials never become command arguments or logs."""

import json
import os
import signal
import sys
import time
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


READER, WRITER = "lake_reader", "lake_collector"


def secret(name):
    value = os.environ.get(name, "")
    if not 32 <= len(value) <= 4096 or any(not 33 <= ord(char) <= 126 for char in value):
        raise ValueError("Invalid local credential configuration")
    return value


def database_uri(role, password, location="postgresql://postgres:5432/chart_lake"):
    parts = urlsplit(location)
    if parts.scheme not in {"postgres", "postgresql"} or not parts.hostname or parts.fragment:
        raise ValueError("Invalid local database location")
    host = "[" + parts.hostname + "]" if ":" in parts.hostname else parts.hostname
    authority = quote(role, safe="") + ":" + quote(password, safe="") + "@" + host
    if parts.port is not None:
        authority += ":" + str(parts.port)
    return urlunsplit((parts.scheme, authority, parts.path, parts.query, ""))


def bootstrap(owner_uri, reader_password, writer_password, *, reader_role=READER, writer_role=WRITER):
    import psycopg
    from psycopg import sql
    from market_data.archive import init_archive
    from market_data.store import open_store

    # The bootstrap role is deliberately not a superuser. Keep connection
    # startup options to user-settable timeouts; PostgreSQL logging GUCs such
    # as log_statement are privileged and cause FATAL during authentication.
    # The server's own logging policy must be configured by its administrator.
    options = "-c statement_timeout=5000 -c lock_timeout=5000"
    with psycopg.connect(owner_uri, autocommit=True, connect_timeout=5, options=options) as owner:
        owner.execute("SELECT pg_advisory_lock(6072027)")
        for role, password in ((reader_role, reader_password), (writer_role, writer_password)):
            exists = owner.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone()
            verb = sql.SQL("ALTER" if exists else "CREATE")
            owner.execute(sql.SQL("{} ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION "
                                  "NOBYPASSRLS NOINHERIT PASSWORD {}").format(verb, sql.Identifier(role), sql.Literal(password)))
            owner.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(owner.info.dbname), sql.Identifier(role)))
        owner.execute(sql.SQL("ALTER ROLE {} SET default_transaction_read_only=on").format(sql.Identifier(reader_role)))
        owner.execute(sql.SQL("ALTER ROLE {} SET default_transaction_read_only=off").format(sql.Identifier(writer_role)))
        owner.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        owner.execute(sql.SQL("REVOKE ALL ON SCHEMA public FROM {}").format(sql.Identifier(reader_role)))
        owner.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(reader_role)))
        owner.execute(sql.SQL("GRANT USAGE,CREATE ON SCHEMA public TO {}").format(sql.Identifier(writer_role)))
        writer_uri = database_uri(writer_role, writer_password, owner_uri)
        open_store(writer_uri)
        init_archive(writer_uri)
        # Tables are created by the collector role, so only that role owns
        # them and can grant/revoke their privileges. Apply both current-table
        # and future-table reader grants through the owning role.
        with psycopg.connect(writer_uri, autocommit=True, connect_timeout=5) as writer:
            writer.execute(sql.SQL("REVOKE ALL ON candles,intelligence_snapshots FROM {}").format(
                sql.Identifier(reader_role)))
            writer.execute(sql.SQL("GRANT SELECT ON candles,intelligence_snapshots TO {}").format(
                sql.Identifier(reader_role)))
            writer.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {}").format(
                sql.Identifier(reader_role)))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def probe():
    request = Request("http://127.0.0.1:8788/ready", headers={"Authorization": "Bearer " + secret("MARKET_DATA_TOKEN")})
    with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=5) as response:
        raw = response.read(65_537)
    if len(raw) > 65_536:
        raise ValueError("Oversized readiness response")
    report = json.loads(raw)
    if report.get("service") != "canonical-data-lake" or report.get("ready") is not True:
        raise ValueError("Local API is not ready")


def collect(location):
    import ccxt
    from data_lake.refresh import refresh_once
    exchange = ccxt.binanceusdm({"enableRateLimit": True, "timeout": 15_000})
    while True:
        try:
            result = refresh_once(exchange, location)
            print(json.dumps(result, allow_nan=False), flush=True)
        except Exception:
            print("LOCAL_COLLECTOR_REFRESH_FAILED", file=sys.stderr, flush=True)
        time.sleep(60)


def interrupted(signum, frame):
    raise KeyboardInterrupt


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in {"api", "bootstrap", "collector", "probe", "refresh", "backfill"}:
        print("LOCAL_RUNTIME_UNSUPPORTED_COMMAND", file=sys.stderr)
        return 2
    mode = args[0]
    if mode not in {"refresh", "backfill"} and len(args) != 1:
        print("LOCAL_RUNTIME_UNSUPPORTED_ARGUMENTS", file=sys.stderr)
        return 2
    try:
        if mode == "probe":
            probe()
            return 0
        if mode == "bootstrap":
            bootstrap(database_uri("lake_owner", secret("LAKE_OWNER_PASSWORD")),
                      secret("LAKE_READER_PASSWORD"), secret("LAKE_WRITER_PASSWORD"))
            print('{"initialized":true}')
            return 0
        location = database_uri(READER if mode == "api" else WRITER, secret("LAKE_DB_PASSWORD"))
        os.environ["DATA_LAKE_DATABASE_URL"] = location
        if mode == "api":
            secret("MARKET_DATA_TOKEN")
            os.execv(sys.executable, [sys.executable, "-m", "uvicorn", "data_lake.api:app", "--host", "0.0.0.0",
                                     "--port", "8788", "--workers", "2", "--limit-concurrency", "16"])
        elif mode == "collector":
            signal.signal(signal.SIGTERM, interrupted)
            collect(location)
        else:
            module_args = ["-m", "data_lake.refresh"] if mode == "refresh" else ["-m", "data_lake", "backfill"]
            os.execv(sys.executable, [sys.executable, *module_args, *args[1:]])
    except KeyboardInterrupt:
        return 0
    except Exception:
        print("LOCAL_RUNTIME_FAILED", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
