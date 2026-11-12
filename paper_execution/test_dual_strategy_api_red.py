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
            instance = api.ledger(strategy_id="AI_FREQAI", admitted_leverage="2")

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
             patch.object(ledger_module, "read_account_risk_snapshot", return_value={
                 "riskReady": True, "accountEquityQuote": "123.45",
             }) as account_risk, \
             patch.object(core_strategy, "produce", return_value={
                 "action": "WAIT", "reason": "CORE_NO_ENTRY", "intent": None,
             }) as producer:
            result = api.core_decide(1_800_000_000_000, book={})

        self.assertNotEqual(result["reason"], "CORE_INPUTS_UNAVAILABLE", result)
        self.assertEqual(result["source"], "STRATEGY_CORE")
        read_snapshot.assert_called_once_with(str(self.db), strategy_id="STRATEGY_CORE")
        account_risk.assert_called_once_with(str(self.db), now_ms=1_800_000_000_000)
        self.assertEqual(producer.call_args.kwargs["account_equity_quote"], "123.45")

    def test_cancel_route_uses_cancel_only_transaction_without_ai_ledger_construction(self):
        self.activate_dual_schema()
        from paper_execution import ledger as ledger_module

        expected = {
            "orderId": "core-order", "status": "CANCELED",
            "strategyId": "STRATEGY_CORE",
        }
        with patch.object(api, "control_permit", return_value=True), \
             patch.object(ledger_module, "cancel_dual_order", return_value=expected) as cancel_helper, \
             patch.object(api, "ledger") as ledger_factory, \
             patch.object(api, "resolve_order_strategy", create=True) as resolve_owner:
            status, result = self.request(
                "/v1/paper/cancel", {"orderId": "core-order"}
            )

        self.assertEqual(status, 200)
        self.assertEqual(result["strategyId"], "STRATEGY_CORE")
        cancel_helper.assert_called_once_with(
            str(self.db), "core-order", unittest.mock.ANY
        )
        ledger_factory.assert_not_called()
        resolve_owner.assert_not_called()


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
        reservation_id = "api-core-cancel-reservation"
        order = {
            "orderId": "api-core-pending", "intentId": "api-core-intent",
            "reservationId": reservation_id, "createdAtMs": 1,
            "status": "OPEN", "filledBase": "0",
            "strategyId": "STRATEGY_CORE",
        }
        with sqlite3.connect(self.db) as connection:
            connection.execute(
                """INSERT INTO paper_orders
                   (intent_id,payload_hash,order_id,status,document,account_id,
                    strategy_id,strategy_event,reservation_id,created_schema_version)
                   VALUES (?,?,?,?,?,1,'STRATEGY_CORE','ENTRY',?,1)""",
                ("api-core-intent", "payload-hash", order["orderId"], "OPEN",
                 json.dumps(order), reservation_id),
            )
            connection.execute(
                """INSERT INTO paper_risk_reservations
                   (reservation_id,account_id,intent_id,strategy_id,reservation_kind,status,
                    reserved_margin_quote,remaining_margin_quote,reserved_notional_quote,
                    remaining_notional_quote,leverage,equity_basis_quote,risk_config_version,
                    created_at_ms,updated_at_ms,expires_at_ms)
                   VALUES (?,1,?,'STRATEGY_CORE','ENTRY','ACTIVE','1','1','13','13','13','100',
                           'test-risk-v1',1,1,9999999999999)""",
                (reservation_id, "api-core-intent"),
            )

        with patch.object(api, "control_permit", return_value=True):
            status, result = self.request(
                "/v1/paper/cancel", {"orderId": "api-core-pending"}
            )

        self.assertEqual(status, 200, result)
        self.assertEqual(result["status"], "CANCELED")
        self.assertEqual(result["strategyId"], "STRATEGY_CORE")
        with sqlite3.connect(self.db) as connection:
            stored = connection.execute(
                "SELECT status,strategy_id FROM paper_orders WHERE order_id=?",
                ("api-core-pending",),
            ).fetchone()
            reservation = connection.execute(
                "SELECT status,remaining_margin_quote,remaining_notional_quote FROM paper_risk_reservations WHERE reservation_id=?",
                (reservation_id,),
            ).fetchone()
        self.assertEqual(stored, ("CANCELED", "STRATEGY_CORE"))
        self.assertEqual(reservation, ("RELEASED", "0", "0"))


    def test_reset_readiness_blocks_unassigned_pending_order_and_unready_shared_risk(self):
        self.activate_dual_schema()
        order = {
            "orderId": "ai-pending", "createdAtMs": 1,
            "status": "OPEN", "filledBase": "0", "strategyId": "LEGACY_UNATTRIBUTED",
        }
        with sqlite3.connect(self.db) as connection:
            connection.execute(
                """INSERT INTO paper_orders
                   (intent_id,payload_hash,order_id,status,document,account_id,
                    strategy_id,strategy_event,reservation_id,created_schema_version)
                   VALUES (?,?,?,?,?,1,NULL,'ENTRY',NULL,1)""",
                ("ai-pending-intent", "payload-hash-ai", order["orderId"], "OPEN",
                 json.dumps(order)),
            )
        with patch.object(api, "context", return_value={
            "candles": {"coverage": {"complete": True}}, "book": {},
        }):
            readiness = api.control_readiness(1_800_000_000_000)

        self.assertFalse(readiness["ready"])
        self.assertFalse(readiness["checks"]["noPendingPaperOrders"])
        self.assertFalse(readiness["checks"]["accountRiskReady"])


    def test_scoped_api_ledger_construction_does_not_mutate_migration_or_audit_state(self):
        self.activate_dual_schema()
        with sqlite3.connect(self.db) as connection:
            before = (
                connection.execute("SELECT COUNT(*) FROM paper_schema_migrations").fetchone()[0],
                connection.execute("SELECT COUNT(*) FROM paper_audit").fetchone()[0],
            )

        scoped = api.ledger(strategy_id="AI_FREQAI", admitted_leverage="2")
        self.assertEqual(scoped.strategy_id, "AI_FREQAI")

        with sqlite3.connect(self.db) as connection:
            after = (
                connection.execute("SELECT COUNT(*) FROM paper_schema_migrations").fetchone()[0],
                connection.execute("SELECT COUNT(*) FROM paper_audit").fetchone()[0],
            )
        self.assertEqual(after, before)


    def test_resolver_rejects_legacy_schema_without_persisted_strategy_column(self):
        from pipeline.api import resolve_order_strategy

        legacy_db = Path(self.temp.name) / "legacy-orders.sqlite3"
        with sqlite3.connect(legacy_db) as connection:
            connection.execute(
                "CREATE TABLE paper_orders (order_id TEXT PRIMARY KEY, document TEXT)"
            )
            connection.execute(
                "INSERT INTO paper_orders VALUES (?,?)",
                ("legacy-order", json.dumps({"strategyId": "STRATEGY_CORE"})),
            )

        with self.assertRaisesRegex(ValueError, "PAPER_ORDER_OWNER_UNVERIFIED"):
            resolve_order_strategy(str(legacy_db), "legacy-order")


    def test_account_mark_fails_closed_on_partial_or_checksum_mismatched_migration(self):
        account = api.ledger()
        with sqlite3.connect(self.db) as connection:
            connection.execute(
                """CREATE TABLE paper_schema_migrations (
                    version INTEGER PRIMARY KEY, checksum TEXT NOT NULL,
                    status TEXT NOT NULL
                )"""
            )
            connection.execute(
                "INSERT INTO paper_schema_migrations VALUES (1,'wrong-checksum','APPLIED')"
            )

        with self.assertRaisesRegex(
            sqlite3.DatabaseError, "DUAL_LEDGER_MIGRATION_CHECKSUM_MISMATCH"
        ):
            account.record_account_mark(
                "100", 1_799_999_940_000, 1_800_000_000_000,
                "sha256:" + "a"*64, "100",
            )


    def test_legacy_account_mark_fallback_preserves_equity_history_without_migration(self):
        account = api.ledger()
        result = account.record_account_mark(
            "100", 1_799_999_940_000, 1_800_000_000_000,
            "sha256:" + "a"*64, "100",
        )

        self.assertTrue(result["available"])
        self.assertEqual(result["latest"]["equity"], "100")
        with sqlite3.connect(self.db) as connection:
            migration_table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_schema_migrations'"
            ).fetchone()
        self.assertIsNone(migration_table)


    def test_ai_buy_while_core_wait_routes_only_to_ai_ledger_and_shared_risk_rejects(self):
        from paper_execution.ledger import PaperLedger, read_snapshot

        self.activate_dual_schema()
        PaperLedger(self.db, strategy_id="AI_FREQAI", source_sha="e" * 40, leverage="3")
        timestamp = 1_800_000_000_000
        book = {
            "source": "hummingbot", "connector": "binance_perpetual",
            "symbol": "BTCUSDT", "observedAtMs": timestamp,
            "bids": [{"price": "100", "quantity": "1"}],
            "asks": [{"price": "101", "quantity": "1"}],
        }
        decision = {
            "source": "AI_FREQAI", "action": "BUY",
            "reason": "ALIGNED_PAPER_SIGNAL",
            "intent": {
                "intentId": "ai-buy-while-core-waits",
                "symbol": "BTCUSDT", "exchange": "binance",
                "marketType": "USDT_PERPETUAL",
                "strategyVersion": "ai-contract-red",
                "modelVersion": "ai-contract-red",
                "datasetVersion": "sha256:" + "a" * 64,
                "targetPositionBase": "0.001", "limitPrice": "101",
                "decisionAtMs": timestamp - 100,
                "validUntilMs": timestamp + 30_000,
                "inputSnapshotId": "sha256:" + "b" * 64,
                "mode": "PAPER",
            },
        }
        core_wait = {
            "source": "STRATEGY_CORE", "action": "WAIT",
            "reason": "CORE_NO_ENTRY", "intent": None,
        }
        empty_mark = {"candles": [], "coverage": {"complete": False}}
        before_core = read_snapshot(str(self.db), strategy_id="STRATEGY_CORE")
        before_ai = read_snapshot(str(self.db), strategy_id="AI_FREQAI")

        with patch.object(api, "now_ms", return_value=timestamp), \
             patch.object(api, "context", return_value={"book": book}), \
             patch.object(api, "decide", return_value=decision), \
             patch.object(api, "core_decide", return_value=core_wait), \
             patch.object(api, "control_permit", return_value=True), \
             patch.object(api, "market_window", return_value=empty_mark):
            signals = api.signal_snapshot(timestamp)
            status, response = self.request("/v1/paper/evaluate", {})

        self.assertEqual(signals["strategyCore"]["action"], "WAIT")
        self.assertEqual(signals["aiStrategy"]["action"], "BUY")
        self.assertEqual(status, 200, response)
        self.assertEqual(response["decision"]["source"], "AI_FREQAI")
        self.assertEqual(response["order"]["status"], "REJECTED", response)
        self.assertEqual(response["order"]["reason"], "RISK_INPUTS_UNAVAILABLE")

        # A rejected AI candidate must not leave a risk reservation behind.
        with sqlite3.connect(self.db) as connection:
            reservations = connection.execute(
                "SELECT COUNT(*) FROM paper_risk_reservations"
            ).fetchone()[0]
        self.assertEqual(reservations, 0)

        after_core = read_snapshot(str(self.db), strategy_id="STRATEGY_CORE")
        after_ai = read_snapshot(str(self.db), strategy_id="AI_FREQAI")
        self.assertEqual(after_core["positionBase"], before_core["positionBase"])
        self.assertEqual(after_core["orders"], before_core["orders"])
        self.assertEqual(after_ai["positionBase"], before_ai["positionBase"])
        self.assertEqual(len(after_ai["orders"]), len(before_ai["orders"]) + 1)
        self.assertEqual(after_ai["orders"][0]["strategyId"], "AI_FREQAI")


    def test_ai_cancel_succeeds_without_prediction_or_new_admitted_leverage(self):
        self.activate_dual_schema()
        order_id = "api-ai-cancel-no-new-leverage"
        intent_id = "api-ai-cancel-intent"
        reservation_id = "api-ai-cancel-reservation"
        order = {
            "orderId": order_id,
            "intentId": intent_id,
            "reservationId": reservation_id,
            "createdAtMs": 1,
            "status": "OPEN",
            "filledBase": "0",
            "remainingBase": "0.01",
            "strategyId": "AI_FREQAI",
        }
        with sqlite3.connect(self.db) as connection:
            connection.execute(
                """INSERT INTO paper_orders
                   (intent_id,payload_hash,order_id,status,document,account_id,
                    strategy_id,strategy_event,reservation_id,created_schema_version)
                   VALUES (?,?,?,?,?,1,'AI_FREQAI','ENTRY',?,1)""",
                (intent_id, "api-ai-cancel-payload", order_id, "OPEN",
                 json.dumps(order), reservation_id),
            )
            connection.execute(
                """INSERT INTO paper_risk_reservations
                   (reservation_id,account_id,intent_id,strategy_id,reservation_kind,status,
                    reserved_margin_quote,remaining_margin_quote,reserved_notional_quote,
                    remaining_notional_quote,leverage,equity_basis_quote,risk_config_version,
                    created_at_ms,updated_at_ms,expires_at_ms)
                   VALUES (?,1,?,'AI_FREQAI','ENTRY','ACTIVE','1','1','3','3','3','100',
                           'test-risk-v1',1,1,9999999999999)""",
                (reservation_id, intent_id),
            )

        with patch.object(api, "control_permit", return_value=True):
            status, result = self.request(
                "/v1/paper/cancel", {"orderId": order_id}
            )

        self.assertEqual(status, 200, result)
        self.assertEqual(result["status"], "CANCELED")
        self.assertEqual(result["strategyId"], "AI_FREQAI")
        with sqlite3.connect(self.db) as connection:
            stored_order = connection.execute(
                "SELECT status FROM paper_orders WHERE order_id=?", (order_id,)
            ).fetchone()
            stored_reservation = connection.execute(
                "SELECT status,remaining_margin_quote,remaining_notional_quote FROM paper_risk_reservations WHERE reservation_id=?",
                (reservation_id,),
            ).fetchone()
        self.assertEqual(stored_order, ("CANCELED",))
        self.assertEqual(stored_reservation, ("RELEASED", "0", "0"))


if __name__ == "__main__":
    unittest.main()
