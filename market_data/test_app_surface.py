"""Regression tests for the T0 health API boundary after Telegram runtime removal."""

import unittest

from app import app


class AppSurfaceContractTest(unittest.TestCase):
    def test_t0_health_endpoints_remain_available(self):
        routes = {(rule.rule, method) for rule in app.url_map.iter_rules()
                  for method in rule.methods}
        for path in ("/health", "/health/live", "/health/ready", "/health/data"):
            self.assertIn((path, "GET"), routes)

    def test_telegram_and_dashboard_routes_are_not_registered(self):
        routes = {rule.rule for rule in app.url_map.iter_rules()}
        removed_routes = {
            "/", "/webhook", "/telegram-webhook", "/dashboard",
            "/api/dashboard/status", "/api/dashboard/backtest",
            "/api/dashboard/run-backtest",
        }
        self.assertTrue(removed_routes.isdisjoint(routes),
                        f"Legacy Telegram/dashboard routes remain: {sorted(removed_routes & routes)}")


if __name__ == "__main__":
    unittest.main()
