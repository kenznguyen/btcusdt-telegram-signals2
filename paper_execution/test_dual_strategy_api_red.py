import io
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline import api


class DualStrategyApiScopeRedTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "paper.sqlite3"
        with sqlite3.connect(self.db) as connection:
            connection.execute("CREATE TABLE seed (id INTEGER PRIMARY KEY)")
        self.environment = patch.dict(os.environ, {
            "MARKET_DATA_DB": str(self.db),
            "MARKET_DATA_TOKEN": "read-token",
            "CONTROL_TOKEN": "control-token",
            "PAPER_MAX_DRAWDOWN_PCT": "50",
            "PAPER_MAX_DAILY_LOSS_USDT": "50",
            "PAPER_MAX_EXPOSURE_USDT": "1000",
        }, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def activate_dual_schema(self):
        from paper_execution.ledger import PaperLedger

        legacy = PaperLedger(self.db)
        legacy.record_equity(
            "100", 1_799_999_940_000, 1_800_000_000_000,
            "sha256:" + "c"*64, "100",
        )
        PaperLedger(
            self.db, strategy_id="STRATEGY_CORE", source_sha="d"*40,
        )


    def get(self, path):
        environ = {
            "PATH_INFO": path, "REQUEST_METHOD": "GET", "QUERY_STRING": "",
            "HTTP_AUTHORIZATION": "Bearer read-token", "CONTENT_LENGTH": "0",
            "wsgi.input": io.BytesIO(b""),
        }
        statuses = []
        payload = b"".join(api.application(
            environ, lambda status, headers: statuses.append((status, headers))
        ))
        return int(statuses[0][0].split()[0]), json.loads(payload)

    def request(self, path, body):
        raw = json.dumps(body).encode()
        environ = {
            "PATH_INFO": path,
            "REQUEST_METHOD": "POST",
            "QUERY_STRING": "",
            "HTTP_AUTHORIZATION": "Bearer control-token",
            "CONTENT_LENGTH": str(len(raw)),
            "wsgi.input": io.BytesIO(raw),
        }
        statuses = []
        payload = b"".join(api.application(
            environ, lambda status, headers: statuses.append((status, headers))
        ))
        return int(statuses[0][0].split()[0]), json.loads(payload)

    def test_ledger_factory_constructs_the_requested_strategy_scope(self):
        from paper_execution import ledger as ledger_module

        with patch.object(ledger_module, "dual_ledger_ready", return_value=True), \
             patch.object(ledger_module, "PaperLedger") as constructor:
            instance = api.ledger(strategy_id="AI_FREQAI")

        self.assertIs(instance, constructor.return_value)
        self.assertEqual(constructor.call_args.kwargs["strategy_id"], "AI_FREQAI")
        self.assertFalse(constructor.call_args.kwargs["apply_migrations"])

    def test_core_decision_reads_only_the_core_ledger(self):
        from paper_execution import ledger as ledger_module
        from pipeline import core_strategy

        self.activate_dual_schema()
        complete = {
            "coverage": {"complete": True},
            "candles": [],
            "datasetVersion": "sha256:" + "a" * 64,
        }
        with patch.object(api, "market_window", side_effect=[complete, complete]), \
             patch.object(ledger_module, "read_snapshot", return_value={
                 "strategyState": {"owner": "STRATEGY_CORE", "dcaUsed": False,
                                   "initialMarginQuote": "0"},
                 "positionBase": "0", "averageEntryPrice": "0",
                 "realizedPnlQuote": "0", "feesQuote": "0",
             }) as read_snapshot, \
             patch.object(core_strategy, "produce", return_value={
                 "action": "WAIT", "reason": "CORE_NO_ENTRY", "intent": None,
             }):
            result = api.core_decide(1_800_000_000_000, book={})

        self.assertNotEqual(result["reason"], "CORE_INPUTS_UNAVAILABLE", result)
        self.assertEqual(result["source"], "STRATEGY_CORE")
        read_snapshot.assert_called_once_with(str(self.db), strategy_id="STRATEGY_CORE")

    def test_cancel_resolves_owner_and_uses_the_matching_scoped_ledger(self):
        self.activate_dual_schema()
        with patch.object(api, "control_permit", return_value=True), \
             patch.object(api, "resolve_order_strategy", return_value="STRATEGY_CORE",
                          create=True) as resolve_owner, \
             patch.object(api, "ledger") as ledger_factory:
            ledger_factory.return_value.cancel.return_value = {
                "orderId": "core-order", "status": "CANCELED",
                "strategyId": "STRATEGY_CORE",
            }
            status, result = self.request(
                "/v1/paper/cancel", {"orderId": "core-order"}
            )

        self.assertEqual(status, 200)
        self.assertEqual(result["strategyId"], "STRATEGY_CORE")
        resolve_owner.assert_called_once_with(str(self.db), "core-order")
        ledger_factory.assert_called_once_with(strategy_id="STRATEGY_CORE")
        ledger_factory.return_value.cancel.assert_called_once_with(
            "core-order", api.now_ms.return_value if hasattr(api.now_ms, "return_value") else unittest.mock.ANY
        )


    def test_equity_snapshot_uses_shared_account_mark_path(self):
        from unittest.mock import Mock

        window = {
            "candles": [{"close": "105", "closeTimeMs": 1_799_999_940_000}],
            "coverage": {"complete": True},
            "datasetVersion": "sha256:" + "e" * 64,
        }
        account = Mock()
        account.record_account_mark.return_value = {"accountEquityQuote": "100"}
        with patch.object(api, "market_window", return_value=window), \
             patch.object(api, "ledger", return_value=account):
            result = api.equity_snapshot(1_800_000_000_000)
        self.assertEqual(result["accountEquityQuote"], "100")
        account.record_account_mark.assert_called_once_with(
            "105", 1_799_999_940_000, 1_800_000_000_000,
            "sha256:" + "e" * 64, "100",
        )
        account.record_equity.assert_not_called()




    def test_first_dual_ledger_mark_is_persisted_but_risk_stays_blocked_without_cutover(self):
        self.activate_dual_schema()
        account = api.ledger()
        observed = 1_800_000_000_000
        result = account.record_account_mark(
            "100", observed-60_000, observed, "sha256:" + "f"*64, "100",
        )

        self.assertTrue(result["available"])
        self.assertFalse(result["riskReady"])
        self.assertEqual(
            result["unavailableReason"], "ACCOUNT_EQUITY_CUTOVER_NOT_ESTABLISHED"
        )
        self.assertEqual(result["accountEquityQuote"], "100")
        with sqlite3.connect(self.db) as connection:
            risk = connection.execute(
                """SELECT last_equity_quote,high_water_mark_quote,last_mark_price,
                          mark_observed_at_ms,risk_ready,daily_baseline_utc_day_ms
                   FROM paper_account_risk_state WHERE account_id=1"""
            ).fetchone()
        self.assertEqual(risk, ("100", "100", "100", observed, 0, None))


    def test_core_decision_does_not_activate_dual_ledger_migration(self):
        from paper_execution import ledger as ledger_module
        from pipeline import core_strategy

        complete = {
            "coverage": {"complete": True},
            "candles": [],
            "datasetVersion": "sha256:" + "a" * 64,
        }
        with patch.object(api, "market_window", side_effect=[complete, complete]), \
             patch.object(ledger_module, "read_snapshot", return_value={
                 "strategyState": {"owner": None, "dcaUsed": False,
                                   "initialMarginQuote": "0"},
                 "positionBase": "0", "averageEntryPrice": "0",
                 "realizedPnlQuote": "0", "feesQuote": "0",
             }) as read_snapshot, \
             patch.object(core_strategy, "produce", return_value={
                 "action": "WAIT", "reason": "CORE_NO_ENTRY", "intent": None,
             }):
            result = api.core_decide(1_800_000_000_000, book={})

        self.assertEqual(result["reason"], "CORE_NO_ENTRY")
        read_snapshot.assert_called_once_with(str(self.db))
        with sqlite3.connect(self.db) as connection:
            migration_table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_schema_migrations'"
            ).fetchone()
        self.assertIsNone(migration_table)


    def test_paper_read_api_separates_account_and_both_strategy_ledgers(self):
        self.activate_dual_schema()
        status, result = self.get("/v1/paper")

        self.assertEqual(status, 200)
        self.assertFalse(result["liveTradingSupported"])
        self.assertEqual(
            result["strategyCore"]["strategyState"]["strategyId"], "STRATEGY_CORE"
        )
        self.assertEqual(
            result["aiStrategy"]["strategyState"]["strategyId"], "AI_FREQAI"
        )
        self.assertFalse(result["account"]["riskReady"])
        self.assertEqual(
            result["account"]["unavailableReason"],
            "ACCOUNT_RISK_SNAPSHOT_UNAVAILABLE",
        )

    def test_resolver_rejects_unverified_strategy_owner_even_if_document_claims_one(self):
        from pipeline.api import resolve_order_strategy

        with sqlite3.connect(self.db) as connection:
            connection.execute(
                "CREATE TABLE paper_orders (order_id TEXT PRIMARY KEY, strategy_id TEXT, document TEXT)"
            )
            connection.execute(
                "INSERT INTO paper_orders VALUES (?,?,?)",
                ("legacy-order", None, json.dumps({"strategyId": "STRATEGY_CORE"})),
            )

        with self.assertRaisesRegex(ValueError, "PAPER_ORDER_OWNER_UNVERIFIED"):
            resolve_order_strategy(str(self.db), "legacy-order")


    def test_cancel_api_cancels_the_persisted_owner_without_cross_strategy_write(self):
        self.activate_dual_schema()
        order = {
            "orderId": "api-core-pending", "createdAtMs": 1_799_999_000_000,
            "status": "OPEN", "filledBase": "0",
            "strategyId": "STRATEGY_CORE",
        }
        with sqlite3.connect(self.db) as connection:
            connection.execute(
                """INSERT INTO paper_orders
                   (intent_id,payload_hash,order_id,status,document,account_id,
                    strategy_id,strategy_event,reservation_id,created_schema_version)
                   VALUES (?,?,?,?,?,1,'STRATEGY_CORE','ENTRY',NULL,1)""",
                ("api-core-intent", "payload-hash", order["orderId"], "OPEN",
                 json.dumps(order)),
            )

        with patch.object(api, "control_permit", return_value=True):
            status, result = self.request(
                "/v1/paper/cancel", {"orderId": "api-core-pending"}
            )

        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "CANCELED")
        self.assertEqual(result["strategyId"], "STRATEGY_CORE")
        with sqlite3.connect(self.db) as connection:
            stored = connection.execute(
                "SELECT status,strategy_id FROM paper_orders WHERE order_id=?",
                ("api-core-pending",),
            ).fetchone()
        self.assertEqual(stored, ("CANCELED", "STRATEGY_CORE"))

if __name__ == "__main__":
    unittest.main()
