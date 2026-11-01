"""Real PostgreSQL/API runtime acceptance on macOS without Docker or exchange access."""

import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

import psycopg
from psycopg import sql

from deploy.data_lake.runtime import bootstrap, database_uri


ROOT = Path(__file__).resolve().parents[1]


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def request_json(opener, url, token=None):
    headers = {"Authorization": "Bearer " + token} if token else {}
    request = Request(url, headers=headers)
    with opener.open(request, timeout=5) as response:
        return response.status, json.loads(response.read(65537))


def main():
    pg_bin = Path(subprocess.check_output(
        ["brew", "--prefix", "postgresql@17"], text=True
    ).strip()) / "bin"
    for executable in ("initdb", "pg_ctl"):
        if not (pg_bin / executable).is_file():
            raise RuntimeError(f"PostgreSQL 17 executable missing: {executable}")

    with tempfile.TemporaryDirectory(prefix="native-data-lake-") as temporary:
        work = Path(temporary)
        data = work / "postgres"
        pg_log = work / "postgres-server.log"
        api_log = work / "api-server.log"
        pg_port, api_port = free_port(), free_port()
        pg_ctl = str(pg_bin / "pg_ctl")
        server_started = False
        api_process = None

        def run(command, **kwargs):
            subprocess.run(command, cwd=ROOT, check=True, timeout=60, **kwargs)

        try:
            run([str(pg_bin / "initdb"), "-D", str(data), "-U", "data_lake_ci",
                 "--no-locale", "--encoding=UTF8", "--auth-local=trust", "--auth-host=trust"],
                stdout=subprocess.DEVNULL)
            run([pg_ctl, "-D", str(data), "-l", str(pg_log), "-o",
                 f"-F -p {pg_port} -h 127.0.0.1 -k {work}", "-w", "start"],
                stdout=subprocess.DEVNULL)
            server_started = True

            admin_uri = f"postgresql://data_lake_ci@127.0.0.1:{pg_port}/postgres"
            owner_password = secrets.token_urlsafe(36)
            reader_password = secrets.token_urlsafe(36)
            writer_password = secrets.token_urlsafe(36)
            token = secrets.token_urlsafe(36)
            with psycopg.connect(admin_uri, autocommit=True) as admin:
                admin.execute(sql.SQL(
                    "CREATE ROLE lake_owner LOGIN CREATEROLE CREATEDB PASSWORD {}"
                ).format(sql.Literal(owner_password)))
                admin.execute(sql.SQL(
                    "CREATE DATABASE chart_lake OWNER lake_owner"
                ))

            owner_uri = f"postgresql://lake_owner:{owner_password}@127.0.0.1:{pg_port}/chart_lake"
            bootstrap(owner_uri, reader_password, writer_password)
            reader_uri = database_uri(
                "lake_reader", reader_password,
                f"postgresql://lake_owner@127.0.0.1:{pg_port}/chart_lake",
            )

            with psycopg.connect(owner_uri) as owner:
                checks = owner.execute("""
                    SELECT
                      (SELECT rolcreaterole AND NOT rolsuper FROM pg_roles WHERE rolname='lake_owner'),
                      (SELECT rolsuper = false AND rolcreatedb = false AND rolcreaterole = false
                         FROM pg_roles WHERE rolname='lake_reader'),
                      has_schema_privilege('lake_reader', 'public', 'USAGE'),
                      NOT has_schema_privilege('lake_reader', 'public', 'CREATE'),
                      has_table_privilege('lake_reader', 'candles', 'SELECT'),
                      NOT has_table_privilege('lake_reader', 'candles', 'INSERT'),
                      has_schema_privilege('lake_collector', 'public', 'CREATE'),
                      has_table_privilege('lake_collector', 'candles', 'INSERT')
                """).fetchone()
                assert all(checks), f"Role/permission assertion failed: {checks}"

            with psycopg.connect(reader_uri, autocommit=True) as reader:
                assert reader.execute(
                    "SELECT current_setting('transaction_read_only')"
                ).fetchone()[0] == "on"
                try:
                    reader.execute("CREATE TABLE native_smoke_forbidden(id integer)")
                except psycopg.Error:
                    pass
                else:
                    raise AssertionError("lake_reader unexpectedly created a table")

            environment = dict(os.environ)
            environment["DATA_LAKE_DATABASE_URL"] = reader_uri
            environment["MARKET_DATA_TOKEN"] = token
            api_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "data_lake.api:app",
                 "--host", "127.0.0.1", "--port", str(api_port), "--workers", "1"],
                cwd=ROOT, env=environment, stdout=api_log.open("w"), stderr=subprocess.STDOUT,
            )
            opener = build_opener(ProxyHandler({}), NoRedirect())
            base = f"http://127.0.0.1:{api_port}"
            deadline = time.monotonic() + 60
            ready = None
            while time.monotonic() < deadline:
                if api_process.poll() is not None:
                    raise RuntimeError("API process exited before readiness")
                try:
                    status, health = request_json(opener, base + "/health")
                    if status == 200 and health.get("service") == "canonical-data-lake":
                        break
                except (OSError, URLError, TimeoutError):
                    time.sleep(1)
            else:
                raise TimeoutError("API health endpoint did not become available")

            try:
                request_json(opener, base + "/ready")
            except HTTPError as error:
                assert error.code == 401, f"Unauthenticated readiness returned {error.code}"
                error.close()
            else:
                raise AssertionError("Readiness endpoint accepted a request without a token")

            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                try:
                    status, ready = request_json(opener, base + "/ready", token)
                    if status == 200 and ready.get("ready") is True:
                        break
                except (OSError, URLError, HTTPError):
                    pass
                time.sleep(1)
            else:
                raise TimeoutError(f"Authenticated API readiness failed: {ready}")

            assert ready["checks"]["candles"]["ready"] is True
            assert ready["checks"]["archive"]["ready"] is True
            assert ready["freshData"] is False, "Empty test DB must not invent fresh candles"
            assert ready["service"] == "canonical-data-lake"
            assert api_process.poll() is None

            print(json.dumps({
                "result": "PASS",
                "postgres": "PostgreSQL 17 native server",
                "bootstrap": "PASS",
                "rolesAndPermissions": "PASS",
                "readerWriteDenied": "PASS",
                "apiHealth": "PASS",
                "unauthenticatedReadiness": "401",
                "authenticatedReadiness": "PASS",
                "ready": True,
                "freshData": False,
                "exchangeCollection": "NOT_REQUESTED",
                "collectorStarted": False,
            }, sort_keys=True))
        finally:
            if api_process is not None:
                api_process.terminate()
                try:
                    api_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    api_process.kill()
                    api_process.wait(timeout=5)
            if server_started:
                subprocess.run([pg_ctl, "-D", str(data), "-m", "fast", "-w", "stop"],
                               cwd=ROOT, check=False, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            if pg_log.exists():
                shutil.copyfile(pg_log, ROOT / "native-postgres-server.log")
            if api_log.exists():
                shutil.copyfile(api_log, ROOT / "native-api-server.log")


if __name__ == "__main__":
    main()
