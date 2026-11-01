import unittest

from ci.market_data_acceptance_guard import validate_acceptance_database, validate_direct_egress


class AcceptanceDatabaseGuardTests(unittest.TestCase):
    def test_accepts_direct_environment_without_proxy_variables(self):
        validate_direct_egress({"PATH": "/usr/bin"})

    def test_rejects_proxy_environment_for_direct_binance_access(self):
        for variable in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
            with self.subTest(variable=variable), self.assertRaisesRegex(ValueError, "Proxy environment"):
                validate_direct_egress({variable: "configured"})

    def test_accepts_confirmed_dedicated_tsdb_database(self):
        self.assertEqual(
            validate_acceptance_database(
                "postgresql://user:pass@db.example:5432/tsdb?sslmode=require",
                "tsdb-is-dedicated-staging",
            ),
            "tsdb",
        )

    def test_rejects_non_postgresql_scheme(self):
        with self.assertRaisesRegex(ValueError, "PostgreSQL"):
            validate_acceptance_database("mysql://db/tsdb", "tsdb-is-dedicated-staging")

    def test_rejects_database_other_than_tsdb(self):
        with self.assertRaisesRegex(ValueError, "approved database tsdb"):
            validate_acceptance_database(
                "postgresql://db/production",
                "tsdb-is-dedicated-staging",
            )

    def test_rejects_missing_confirmation(self):
        with self.assertRaisesRegex(ValueError, "confirmation"):
            validate_acceptance_database("postgresql://db/tsdb", "")

    def test_rejects_incorrect_confirmation(self):
        with self.assertRaisesRegex(ValueError, "confirmation"):
            validate_acceptance_database(
                "postgresql://db/tsdb",
                "production-is-safe",
            )


if __name__ == "__main__":
    unittest.main()
