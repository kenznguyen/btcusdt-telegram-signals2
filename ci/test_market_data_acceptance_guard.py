import unittest

from ci.market_data_acceptance_guard import validate_acceptance_database


class AcceptanceDatabaseGuardTests(unittest.TestCase):
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
