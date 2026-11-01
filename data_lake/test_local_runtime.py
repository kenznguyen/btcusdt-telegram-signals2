import importlib.util
import io
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit, urlunsplit
import uuid


SPEC = importlib.util.spec_from_file_location("local_lake_runtime", Path(__file__).resolve().parents[1] / "deploy/data-lake/runtime.py")
RUNTIME = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNTIME)
DSN = os.environ.get("DATA_LAKE_TEST_POSTGRES", "")
REQUIRED = os.environ.get("DATA_LAKE_REQUIRE_POSTGRES") == "1"


class LocalRuntimeTest(unittest.TestCase):
    def test_password_is_percent_encoded_without_changing_literal_plus(self):
        password = "a" * 32 + "+/@:#?"
        uri = RUNTIME.database_uri("reader", password, "postgresql://[::1]:55439/test?sslmode=disable")
        parts = urlsplit(uri)
        self.assertEqual(unquote(parts.password), password)
        self.assertEqual(parts.hostname, "::1")
        self.assertEqual(parts.port, 55439)
        self.assertEqual(parts.query, "sslmode=disable")
        self.assertNotIn(password, uri)

    def test_exec_arguments_never_contain_credentials_and_roles_are_selected_by_mode(self):
        password, token = "p" * 40, "t" * 40
        for mode, role in (("api", RUNTIME.READER), ("refresh", RUNTIME.WRITER), ("backfill", RUNTIME.WRITER)):
            with self.subTest(mode=mode), patch.dict(os.environ, {"LAKE_DB_PASSWORD": password, "MARKET_DATA_TOKEN": token}, clear=True), \
                    patch.object(RUNTIME.os, "execv") as execute:
                self.assertEqual(RUNTIME.main([mode]), 0)
                argv = execute.call_args.args[1]
                self.assertNotIn(password, " ".join(argv))
                self.assertNotIn(token, " ".join(argv))
                self.assertEqual(urlsplit(os.environ["DATA_LAKE_DATABASE_URL"]).username, role)

    def test_unknown_commands_and_failures_do_not_echo_arguments_or_secret_exceptions(self):
        secret = "unlogged-secret" * 3
        for args in (["unsupported", secret], ["api", secret]):
            output = io.StringIO()
            with patch("sys.stderr", output), patch.object(RUNTIME, "secret") as read_secret:
                self.assertEqual(RUNTIME.main(args), 2)
                read_secret.assert_not_called()
            self.assertNotIn(secret, output.getvalue())
        output = io.StringIO()
        with patch("sys.stderr", output), patch.object(RUNTIME, "probe", side_effect=OSError(secret)):
            self.assertEqual(RUNTIME.main(["probe"]), 1)
        self.assertEqual(output.getvalue(), "LOCAL_RUNTIME_FAILED\n")

    def test_probe_is_direct_loopback_and_does_not_follow_redirects(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, size):
                return b'{"service":"canonical-data-lake","ready":true}'

        with patch.dict(os.environ, {"MARKET_DATA_TOKEN": "t" * 40}), patch.object(RUNTIME, "build_opener") as opener:
            opener.return_value.open.return_value = Response()
            RUNTIME.probe()
        handlers = opener.call_args.args
        self.assertTrue(any(isinstance(handler, RUNTIME.ProxyHandler) and handler.proxies == {} for handler in handlers))
        redirect = next(handler for handler in handlers if isinstance(handler, RUNTIME.NoRedirect))
        self.assertIsNone(redirect.redirect_request(None, None, 302, "", {}, "https://untrusted.example"))
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:8788/ready")

    def test_collector_retries_fixed_errors_and_stops_on_interrupt(self):
        fake = types.SimpleNamespace(binanceusdm=lambda config: config)
        error, output = io.StringIO(), io.StringIO()
        with patch.dict(sys.modules, {"ccxt": fake}), patch("data_lake.refresh.refresh_once", side_effect=[
                ValueError("secret-database-uri"), {"windows": []}, KeyboardInterrupt]), \
                patch.object(RUNTIME.time, "sleep") as sleep, patch("sys.stderr", error), patch("sys.stdout", output):
            with self.assertRaises(KeyboardInterrupt):
                RUNTIME.collect("not-printed")
        self.assertEqual(error.getvalue(), "LOCAL_COLLECTOR_REFRESH_FAILED\n")
        self.assertIn('"windows": []', output.getvalue())
        self.assertEqual(sleep.call_count, 2)


@unittest.skipUnless(DSN or REQUIRED, "Real PostgreSQL local-role bootstrap requires DATA_LAKE_TEST_POSTGRES")
class LocalBootstrapPostgresTest(unittest.TestCase):
    def test_bootstrap_is_idempotent_and_reader_cannot_write_even_if_readonly_default_is_disabled(self):
        if not DSN:
            self.fail("PostgreSQL is required but its test URI is absent")
        import psycopg
        from psycopg import sql
        from data_lake.readiness import check_readiness
        from market_data.store import Candle, open_store, read_window

        suffix = uuid.uuid4().hex
        database, reader, writer = "test_local_lake_" + suffix, "test_lake_r_" + suffix, "test_lake_w_" + suffix
        reader_password, writer_password = "r" * 40, "w" * 40
        with psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))

        def cleanup():
            with psycopg.connect(DSN, autocommit=True) as admin:
                admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database)))
                for role in (reader, writer):
                    admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))

        self.addCleanup(cleanup)
        parts = urlsplit(DSN)
        owner_uri = urlunsplit((parts.scheme, parts.netloc, "/" + database, parts.query, ""))
        RUNTIME.bootstrap(owner_uri, reader_password, writer_password, reader_role=reader, writer_role=writer)
        writer_uri = RUNTIME.database_uri(writer, writer_password, owner_uri)
        reader_uri = RUNTIME.database_uri(reader, reader_password, owner_uri)
        candle = Candle("15m", 0, "100", "101", "99", "100.5", "2", 900_001)
        open_store(writer_uri).insert([candle])
        RUNTIME.bootstrap(owner_uri, reader_password, writer_password, reader_role=reader, writer_role=writer)
        self.assertEqual(read_window(reader_uri, "BTCUSDT", "15m", 0, 900_000)["candles"], [candle.as_dict()])
        self.assertTrue(check_readiness(reader_uri)["ready"])
        with psycopg.connect(reader_uri, autocommit=True) as connection:
            self.assertEqual(connection.execute("SHOW default_transaction_read_only").fetchone()[0], "on")
            connection.execute("SET default_transaction_read_only=off")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("DELETE FROM candles")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("CREATE TABLE forbidden (id INTEGER)")
            flags = connection.execute("SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=current_user").fetchone()
            self.assertEqual(flags, (False,) * 5)


if __name__ == "__main__":
    unittest.main()
