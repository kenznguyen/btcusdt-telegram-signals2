"""Regression tests for strategy/backtest execution parity; no strategy params changed."""
import unittest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import bot

ROOT = Path(__file__).resolve().parents[1]
BACKTEST_SOURCE = (ROOT / "backtest.py").read_text(encoding="utf-8")
BOT_SOURCE = (ROOT / "bot.py").read_text(encoding="utf-8")
ANDROID_SOURCE = (ROOT / "android-app/app/src/main/java/com/kenznguyen/btclivealerts/StrategyEngine.kt").read_text(encoding="utf-8")
ANDROID_SERVICE = (ROOT / "android-app/app/src/main/java/com/kenznguyen/btclivealerts/StrategyMonitorService.kt").read_text(encoding="utf-8")
ANDROID_MARKET = (ROOT / "android-app/app/src/main/java/com/kenznguyen/btclivealerts/MarketEngine.kt").read_text(encoding="utf-8")
ANDROID_DASHBOARD = (ROOT / "android-app/app/src/main/java/com/kenznguyen/btclivealerts/CompleteDashboard.kt").read_text(encoding="utf-8")


class StrategyRuleTests(unittest.TestCase):
    def test_entry_cross_and_h1_filter_rules_are_present(self):
        self.assertIn("prev_rsi <= LONG_RSI_ENTRY and rsi > LONG_RSI_ENTRY", BOT_SOURCE)
        self.assertIn("prev_rsi >= SHORT_RSI_ENTRY and rsi < SHORT_RSI_ENTRY", BOT_SOURCE)
        self.assertIn("h1_plus > h1_minus and h1_adx > H1_ADX_ENTRY", BOT_SOURCE)
        self.assertIn("h1_minus > h1_plus and h1_adx > H1_ADX_ENTRY", BOT_SOURCE)

    def test_dca_threshold_and_direction_rules_are_present(self):
        self.assertIn("current_roe <= DCA_ROE", BOT_SOURCE)
        self.assertIn("adx > DCA_ADX", BOT_SOURCE)
        self.assertIn("rsi > LONG_DCA_RSI", BOT_SOURCE)
        self.assertIn("rsi > prev_rsi", BOT_SOURCE)
        self.assertIn("rsi < SHORT_DCA_RSI", BOT_SOURCE)
        self.assertIn("rsi < prev_rsi", BOT_SOURCE)
        self.assertIn("available_margin = max(0.0", BOT_SOURCE)
        self.assertIn("add_margin <= available_margin + 1e-9", BOT_SOURCE)

    def test_tp_requires_rsi_and_roe(self):
        self.assertIn("rsi >= LONG_RSI_TP", BOT_SOURCE)
        self.assertIn("rsi <= SHORT_RSI_TP", BOT_SOURCE)
        self.assertIn("roe >= TP_ROE", BOT_SOURCE)

    def test_stop_gap_and_slippage_are_adverse(self):
        self.assertLess(bot.stop_fill_price("LONG", 97.0, 95.0), 95.0)
        self.assertGreater(bot.stop_fill_price("SHORT", 103.0, 105.0), 105.0)
        self.assertLess(bot.execution_fill_price(100.0, "SELL"), 100.0)
        self.assertGreater(bot.execution_fill_price(100.0, "BUY"), 100.0)

    def test_fee_and_slippage_defaults_are_unchanged(self):
        self.assertAlmostEqual(bot.FEE_RATE, 0.0005)
        self.assertAlmostEqual(bot.SLIPPAGE_BPS, 5.0)

    def test_entry_dca_and_end_exit_use_adverse_fills(self):
        self.assertIn('fill_price = execution_fill_price(close, "BUY")', BOT_SOURCE)
        self.assertIn('fill_price = execution_fill_price(close, "SELL")', BOT_SOURCE)
        self.assertIn("fill_price = bot.execution_fill_price(close, action)", BACKTEST_SOURCE)
        self.assertIn('exit_price = bot.execution_fill_price(reference_exit, exit_action)', BACKTEST_SOURCE)
        self.assertIn('avg_entry": fill_price', BOT_SOURCE)
        self.assertIn('entry_notional": new_qty * fill_price', BOT_SOURCE)

    def test_h1_filter_uses_latest_candle_closed_by_m15_close(self):
        self.assertIn('t + pd.Timedelta(hours=1) <= closed_at', BOT_SOURCE)
        self.assertIn('h1["close_time"] <= row["close_time"]', BACKTEST_SOURCE)
        self.assertIn("h1CandleClosedByM15Close(hours[hidx + 1].openTime, c.openTime)", ANDROID_SOURCE)
        self.assertIn("h1CandleClosedByM15Close(it.openTime, c.openTime)", ANDROID_SOURCE)

    def test_protective_stop_checks_are_not_skipped_for_nan_indicators(self):
        self.assertNotIn('if pd.isna(row["rsi"]) or pd.isna(row["adx"]):', BOT_SOURCE)
        self.assertNotIn('if i == 0 or pd.isna(row["rsi"]) or pd.isna(row["adx"]):', BACKTEST_SOURCE)
        self.assertIn("if (!hasRsi && state.position == null)", ANDROID_SOURCE)
        self.assertIn("val emergency = emergencyStopTriggered", ANDROID_SOURCE)

    def test_state_save_is_atomic_and_corrupt_state_is_not_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = os.path.join(tmp, "state.json")
            with patch.object(bot, "STATE_FILE", state_path):
                expected = {"side": "LONG", "qty": 0.01, "avg_entry": 65000.0,
                            "account_balance": 100.0, "last_processed_open": None}
                bot.save_state(expected)
                self.assertEqual(bot.load_state()["side"], "LONG")
                self.assertTrue(os.path.exists(state_path))
                self.assertFalse(any(name.endswith(".tmp") for name in os.listdir(tmp)))
                with open(state_path, "w", encoding="utf-8") as f:
                    f.write("{broken")
                with self.assertRaisesRegex(RuntimeError, "refusing to reset"):
                    bot.load_state()

    def test_telegram_outbox_retries_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = {
                "TELEGRAM_OUTBOX_FILE": os.path.join(tmp, "outbox.json"),
                "TELEGRAM_SENT_FILE": os.path.join(tmp, "sent.json"),
            }
            with patch.multiple(bot, **paths):
                candle_time = bot.pd.Timestamp("2026-10-20T12:00:00Z")
                with patch.object(bot, "telegram_send", side_effect=RuntimeError("network down")) as send:
                    bot.send_event("LONG ENTRY", "LONG", 65000.0, candle_time)
                    self.assertEqual(send.call_count, 1)
                    queued = json.loads(Path(paths["TELEGRAM_OUTBOX_FILE"]).read_text(encoding="utf-8"))
                    self.assertEqual(len(queued), 1)
                with patch.object(bot, "telegram_send", return_value=None) as send:
                    self.assertEqual(bot.flush_telegram_outbox(), 0)
                    self.assertEqual(send.call_count, 1)
                    self.assertEqual(json.loads(Path(paths["TELEGRAM_OUTBOX_FILE"]).read_text(encoding="utf-8")), [])
                    sent = json.loads(Path(paths["TELEGRAM_SENT_FILE"]).read_text(encoding="utf-8"))
                    self.assertEqual(len(sent), 1)
                    bot.send_event("LONG ENTRY", "LONG", 65000.0, candle_time)
                    self.assertEqual(send.call_count, 1)

    def test_candle_data_validation_precedes_strategy_loop(self):
        source = BOT_SOURCE[BOT_SOURCE.index("def get_klines"):BOT_SOURCE.index("def rma")]
        self.assertIn("OKX returned NaN/inf candle values", source)
        self.assertIn("invalid_ohlc.any()", source)
        self.assertIn("Conflicting duplicate OKX candle", source)
        self.assertIn("candle gap(s)", source)

    def test_outbox_and_state_support_persistent_mount(self):
        self.assertIn('os.getenv("BOT_STATE_DIR", ".")', BOT_SOURCE)
        self.assertIn("TELEGRAM_OUTBOX_FILE", BOT_SOURCE)
        self.assertIn("TELEGRAM_SENT_FILE", BOT_SOURCE)

    def test_android_data_state_and_notifications_fail_safe(self):
        self.assertIn("Binance returned invalid OHLCV candle", ANDROID_MARKET)
        self.assertIn("conflicting duplicate candle", ANDROID_MARKET)
        self.assertIn("Cannot safely restore strategy state", ANDROID_SOURCE)
        self.assertIn('putString(pendingKey, pending.toString())', ANDROID_SERVICE)
        self.assertIn('putString(pendingKey, remaining.toString())', ANDROID_SERVICE)
        self.assertIn("drainPendingChartNotifications(this@StrategyMonitorService, prefs)", ANDROID_SERVICE)
        self.assertIn("enqueuePendingChartNotification(prefs, key, title, body)", ANDROID_SERVICE)
        self.assertIn("pending_android_notifications_json", ANDROID_DASHBOARD)
        self.assertIn("if (!manager.areNotificationsEnabled())", ANDROID_DASHBOARD)

    def test_backtest_end_exit_applies_adverse_slippage(self):
        tail_start = BACKTEST_SOURCE.find('if pos:\n            row = m15.iloc[-1]')
        tail_end = BACKTEST_SOURCE.find("# KPI definitions", tail_start)
        self.assertGreaterEqual(tail_start, 0)
        self.assertIn("bot.execution_fill_price(reference_exit, exit_action)", BACKTEST_SOURCE[tail_start:tail_end])

if __name__ == "__main__":
    unittest.main(verbosity=2)
