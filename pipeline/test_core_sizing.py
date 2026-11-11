import unittest
from unittest.mock import patch
import os
import tempfile
from pathlib import Path

from pipeline.core_strategy import LEVERAGE, produce
from paper_execution.ledger import PaperLedger


def candles(count, interval, start=1_700_000_000_000, trend=1.0):
    rows = []
    price = 100.0
    for i in range(count):
        opened = start + i * interval
        price += trend * (0.15 if i % 7 else 0.3)
        rows.append({
            "openTimeMs": opened, "closeTimeMs": opened + interval,
            "availableAtMs": opened + interval, "open": str(price - 0.05),
            "high": str(price + 0.2), "low": str(price - 0.2),
            "close": str(price), "volume": "1", "isClosed": True,
        })
    return rows


def window(rows, timeframe):
    return {
        "timeframe": timeframe, "candles": rows,
        "coverage": {"expected": len(rows), "returned": len(rows), "complete": True},
        "datasetVersion": "sha256:" + "a" * 64,
    }


def scenario(position="0", average="0", dca_used=False, initial_margin="0"):
    start = 1_700_000_000_000
    m15 = candles(120, 900_000, start)
    now = m15[-1]["closeTimeMs"]
    h1_start = (now // 3_600_000 * 3_600_000) - 120 * 3_600_000
    h1 = candles(120, 3_600_000, h1_start)
    close = float(m15[-1]["close"])
    m15_values = [{"rsi": 20.0, "adx": 50.0} for _ in m15]
    m15_values[-2] = {"rsi": 29.0, "adx": 50.0}
    m15_values[-1] = {"rsi": 35.0, "adx": 50.0}
    h1_values = [{"plus_di": 40.0, "minus_di": 10.0, "adx": 30.0} for _ in h1]
    book = {
        "source": "hummingbot", "connector": "binance_perpetual",
        "symbol": "BTCUSDT", "observedAtMs": now - 1000,
        "bids": [{"price": str(close - 0.01), "quantity": "1"}],
        "asks": [{"price": str(close + 0.01), "quantity": "1"}],
    }
    paper = {
        "positionBase": position, "averageEntryPrice": average,
        "realizedPnlQuote": "0", "feesQuote": "0",
    }
    state = {
        "owner": "STRATEGY_CORE" if float(position) else None,
        "dcaUsed": dca_used, "initialMarginQuote": initial_margin,
    }
    return m15, h1, now, close, book, paper, state, m15_values, h1_values


class CoreSizingContractTest(unittest.TestCase):
    def test_core_leverage_is_fixed_at_thirteen_x(self):
        self.assertEqual(LEVERAGE, 13.0)

    def test_entry_uses_one_percent_of_current_account_equity(self):
        m15, h1, now, close, book, paper, state, m15_values, h1_values = scenario()
        with patch("pipeline.core_strategy.indicators", side_effect=[m15_values, h1_values]):
            result = produce(
                window(m15, "15m"), window(h1, "1h"), paper, state, book, now,
                account_equity_quote="100", max_position_base="10",
            )
        self.assertEqual(result["reason"], "RSI_ADX_ENTRY")
        self.assertEqual(float(result["intent"]["initialMarginQuote"]), 1.0)
        self.assertAlmostEqual(float(result["intent"]["targetPositionBase"]), 13.0 / (close + 0.01))

    def test_dca_uses_fresh_one_percent_budget_not_persisted_initial_margin(self):
        m15, h1, now, close, book, paper, state, m15_values, h1_values = scenario(
            position="0.01", average="0", initial_margin="50",
        )
        paper["averageEntryPrice"] = str(close / 0.98)
        with patch("pipeline.core_strategy.indicators", side_effect=[m15_values, h1_values]):
            result = produce(
                window(m15, "15m"), window(h1, "1h"), paper, state, book, now,
                account_equity_quote="100", max_position_base="10",
            )
        self.assertEqual(result["reason"], "DCA")
        self.assertAlmostEqual(
            float(result["intent"]["targetPositionBase"]) - 0.01,
            13.0 / (close + 0.01),
        )
        self.assertEqual(float(result["intent"]["initialMarginQuote"]), 1.0)

    def test_core_ledger_rejects_any_leverage_other_than_thirteen_x(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "CORE_LEVERAGE_POLICY_MISMATCH"):
                PaperLedger(
                    Path(directory) / "paper.sqlite3",
                    strategy_id="STRATEGY_CORE", leverage="12",
                )

    def test_api_factory_keeps_ai_leverage_config_separate_from_fixed_core_leverage(self):
        from pipeline import api
        limits = {
            "maxDrawdownPct": "50", "maxDailyLossUsdt": "50",
            "maxExposureUsdt": "1000",
        }
        with patch.dict(os.environ, {"MARKET_DATA_DB": "/tmp/core-sizing-paper.sqlite3",
                                     "LEVERAGE": "2"}):
            with patch("paper_execution.ledger.dual_ledger_ready", return_value=True), \
                 patch("paper_execution.equity.parse_limits", return_value=limits), \
                 patch("paper_execution.ledger.PaperLedger") as factory:
                api.ledger("STRATEGY_CORE")
                self.assertEqual(factory.call_args.kwargs["leverage"], "13")
                api.ledger("AI_FREQAI")
                self.assertEqual(factory.call_args.kwargs["leverage"], "2")

    def test_entry_without_reconciled_account_equity_never_emits_trade_intent(self):
        m15, h1, now, close, book, paper, state, m15_values, h1_values = scenario()
        with patch("pipeline.core_strategy.indicators", side_effect=[m15_values, h1_values]):
            result = produce(
                window(m15, "15m"), window(h1, "1h"), paper, state, book, now,
                max_position_base="10",
            )
        self.assertEqual(result["action"], "BUY")
        self.assertEqual(result["reason"], "CORE_ACCOUNT_EQUITY_UNAVAILABLE")
        self.assertIsNone(result["intent"])


if __name__ == "__main__":
    unittest.main()
