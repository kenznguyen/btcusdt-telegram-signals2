"""RED-first contracts for safe construction of the wired Continuous Core runtime."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core_runtime.runtime_factory import (
    RuntimeFactoryError,
    build_continuous_runtime,
    build_core_bundle_provider,
)
from paper_execution.test_core_first_operational import CoreFirstOperationalProofTest
from core_runtime.__main__ import main as core_main


class ContinuousRuntimeFactoryTest(unittest.TestCase):
    def setUp(self):
        self.fixture = CoreFirstOperationalProofTest(
            "test_core_signal_flows_through_shared_risk_into_paper_ledger"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = Path(self.fixture.temp.name)
        self.config = self.root / "continuous-runtime-config.json"
        self.config.write_text(json.dumps({
            "mode": "PAPER",
            "ai_execution_enabled": False,
            "ledger_path": str(self.fixture.path),
            "risk_limits": {
                "maxDrawdownPct": "50",
                "maxDailyLossUsdt": "50",
                "maxExposureUsdt": "1000",
            },
            "max_book_age_ms": 2_000,
            "max_position_base": "0.01",
        }), encoding="utf-8")
        self.journal = self.root / "runner-state" / "journal.sqlite3"
        self.bundle_store = self.root / "runner-state" / "bundles"
        self.journal.parent.mkdir()
        self.env = {
            "AI_EXECUTION_ENABLED": "false",
            "MARKET_DATA_DB": "",
            "T0_FEEDER_LEASE_DB": "",
            "PAPER_DB": "",
            "PAPER_TRADING_DB": "",
            "BINANCE_API_KEY": "",
            "BINANCE_API_SECRET": "",
            "OKX_API_KEY": "",
            "OKX_API_SECRET": "",
            "T0_CANDLE_API_BASE_URL": "https://t0.example.test",
            "T0_CANDLE_API_TOKEN": "t0-test-token",
            "T0_CANDLE_MAX_LAG_MS": "120000",
            "T1_ORDERBOOK_API_BASE_URL": "http://127.0.0.1:8790",
            "T1_ORDERBOOK_API_TOKEN": "t1-test-token",
        }

    def test_builds_provider_and_runner_with_shared_bundle_store_and_paper_guards(self):
        runtime = build_continuous_runtime(
            config_path=self.config,
            journal_path=self.journal,
            bundle_store_dir=self.bundle_store,
            source_sha="a" * 40,
            environ=self.env,
            clock_ms=lambda: self.fixture.now,
        )

        self.assertTrue(self.journal.is_file())
        self.assertFalse(self.bundle_store.exists())
        self.assertEqual(runtime.runner.bundle_store_dir, self.bundle_store.resolve())
        self.assertEqual(runtime.bundle_provider.bundle_store_dir, self.bundle_store.resolve())
        self.assertEqual(runtime.runner.source_sha, "a" * 40)
        self.assertEqual(
            runtime.runner.config_sha256,
            "sha256:" + hashlib.sha256(self.config.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            runtime.bundle_provider.candle_client.config.base_url,
            "https://t0.example.test",
        )
        self.assertEqual(
            runtime.bundle_provider.orderbook_client.config.base_url,
            "http://127.0.0.1:8790",
        )
        self.assertEqual(runtime.runner.settlement_ms, 0)
        self.assertEqual(runtime.runner.max_book_age_ms, 2_000)

    def test_read_only_provider_factory_does_not_create_journal_or_bundle_store(self):
        provider = build_core_bundle_provider(
            config_path=self.config,
            journal_path=self.journal,
            bundle_store_dir=self.bundle_store,
            environ=self.env,
            clock_ms=lambda: self.fixture.now,
        )

        self.assertEqual(provider.config_path, self.config.resolve())
        self.assertFalse(self.journal.exists())
        self.assertFalse(self.bundle_store.exists())

    def test_missing_t0_or_t1_endpoint_configuration_fails_before_journal_creation(self):
        for key in (
            "T0_CANDLE_API_BASE_URL", "T0_CANDLE_API_TOKEN",
            "T0_CANDLE_MAX_LAG_MS", "T1_ORDERBOOK_API_BASE_URL",
            "T1_ORDERBOOK_API_TOKEN",
        ):
            with self.subTest(missing=key):
                env = dict(self.env)
                env.pop(key)
                with self.assertRaises(RuntimeFactoryError):
                    build_continuous_runtime(
                        config_path=self.config,
                        journal_path=self.journal,
                        bundle_store_dir=self.bundle_store,
                        source_sha="a" * 40,
                        environ=env,
                        clock_ms=lambda: self.fixture.now,
                    )
                self.assertFalse(self.journal.exists())

    def test_exchange_credentials_are_rejected_before_journal_creation(self):
        env = dict(self.env, BINANCE_API_KEY="must-not-be-used")
        with self.assertRaisesRegex(RuntimeFactoryError, "EXCHANGE_CREDENTIALS_FORBIDDEN"):
            build_continuous_runtime(
                config_path=self.config,
                journal_path=self.journal,
                bundle_store_dir=self.bundle_store,
                source_sha="a" * 40,
                environ=env,
                clock_ms=lambda: self.fixture.now,
            )
        self.assertFalse(self.journal.exists())

    def test_non_loopback_t1_endpoint_is_rejected_before_journal_creation(self):
        env = dict(self.env, T1_ORDERBOOK_API_BASE_URL="https://remote.example.test")
        with self.assertRaises(RuntimeFactoryError):
            build_continuous_runtime(
                config_path=self.config,
                journal_path=self.journal,
                bundle_store_dir=self.bundle_store,
                source_sha="a" * 40,
                environ=env,
                clock_ms=lambda: self.fixture.now,
            )
        self.assertFalse(self.journal.exists())

    def test_journal_or_bundle_path_overlapping_paper_ledger_is_rejected(self):
        with self.assertRaises(RuntimeFactoryError):
            build_continuous_runtime(
                config_path=self.config,
                journal_path=self.fixture.path,
                bundle_store_dir=self.bundle_store,
                source_sha="a" * 40,
                environ=self.env,
                clock_ms=lambda: self.fixture.now,
            )
        self.assertFalse(self.bundle_store.exists())


    def test_cli_requires_journal_and_bundle_store_for_explicit_continuous_mode(self):
        with self.assertRaises(SystemExit) as raised:
            core_main([
                "--config", str(self.config), "--run-continuous",
            ])
        self.assertEqual(raised.exception.code, 2)

    def test_cli_dispatches_continuous_mode_only_when_explicitly_requested(self):
        with patch("core_runtime.__main__.run_continuous", return_value="STOPPED") as run:
            result = core_main([
                "--config", str(self.config),
                "--run-continuous",
                "--journal-path", str(self.journal),
                "--bundle-store-dir", str(self.bundle_store),
            ])
        self.assertEqual(result, 0)
        run.assert_called_once_with(
            config_path=str(self.config),
            journal_path=str(self.journal),
            bundle_store_dir=str(self.bundle_store),
        )


    def test_run_continuous_hands_factory_bundle_provider_to_runner_loop(self):
        from types import SimpleNamespace
        from core_runtime.__main__ import run_continuous

        provider_calls = []

        def bundle_provider(candle_open_ms):
            provider_calls.append(candle_open_ms)
            return "/disposable/bundle.json"

        class CapturingRunner:
            def run_forever(self, **kwargs):
                self.received_provider = kwargs["bundle_provider"]
                self.bundle_path = self.received_provider(1234567890000)
                return "STOPPED"

        runner = CapturingRunner()
        runtime = SimpleNamespace(
            runner=runner,
            bundle_provider=bundle_provider,
        )

        with patch(
            "core_runtime.runtime_factory.build_continuous_runtime",
            return_value=runtime,
        ):
            result = run_continuous(
                config_path="/disposable/config.json",
                journal_path="/disposable/journal.sqlite3",
                bundle_store_dir="/disposable/bundles",
            )

        self.assertEqual(result, "STOPPED")
        self.assertIs(runner.received_provider, bundle_provider)
        self.assertEqual(runner.bundle_path, "/disposable/bundle.json")
        self.assertEqual(provider_calls, [1234567890000])


if __name__ == "__main__":
    unittest.main()
