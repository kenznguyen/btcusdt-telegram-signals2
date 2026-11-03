"""Offline contracts for the TimescaleDB test endpoint allowlist."""
import hashlib
import unittest

from ci.t0_test_database_url import (
    TestDatabaseAllowlistError,
    validate_disposable_postgres_dsn,
)


class T0PostgresTestDatabaseAllowlistTests(unittest.TestCase):
    def setUp(self):
        self.dsn = "postgresql://test_user:test_password@timescale.example:5432/test_market_data?sslmode=require"
        self.digest = hashlib.sha256(self.dsn.encode("utf-8")).hexdigest()

    def test_valid_exact_endpoint_fingerprint_passes(self):
        self.assertEqual(validate_disposable_postgres_dsn(self.dsn, self.digest), self.digest)

    def test_missing_database_url_fails(self):
        with self.assertRaises(TestDatabaseAllowlistError):
            validate_disposable_postgres_dsn("", self.digest)

    def test_missing_fingerprint_fails(self):
        with self.assertRaises(TestDatabaseAllowlistError):
            validate_disposable_postgres_dsn(self.dsn, "")

    def test_malformed_fingerprint_fails(self):
        with self.assertRaises(TestDatabaseAllowlistError):
            validate_disposable_postgres_dsn(self.dsn, "not-a-hash")

    def test_non_postgres_scheme_fails(self):
        with self.assertRaises(TestDatabaseAllowlistError):
            validate_disposable_postgres_dsn("https://timescale.example/test", self.digest)

    def test_missing_host_fails(self):
        with self.assertRaises(TestDatabaseAllowlistError):
            validate_disposable_postgres_dsn("postgresql:///test_market_data", self.digest)

    def test_missing_database_name_fails(self):
        with self.assertRaises(TestDatabaseAllowlistError):
            validate_disposable_postgres_dsn("postgresql://timescale.example/", self.digest)

    def test_endpoint_change_fails_fingerprint_check(self):
        changed = self.dsn.replace("test_market_data", "production")
        with self.assertRaises(TestDatabaseAllowlistError):
            validate_disposable_postgres_dsn(changed, self.digest)

    def test_credentials_change_fails_fingerprint_check(self):
        changed = self.dsn.replace("test_password", "other_password")
        with self.assertRaises(TestDatabaseAllowlistError):
            validate_disposable_postgres_dsn(changed, self.digest)

    def test_query_parameter_change_fails_fingerprint_check(self):
        changed = self.dsn.replace("sslmode=require", "sslmode=disable")
        with self.assertRaises(TestDatabaseAllowlistError):
            validate_disposable_postgres_dsn(changed, self.digest)


if __name__ == "__main__":
    unittest.main()
