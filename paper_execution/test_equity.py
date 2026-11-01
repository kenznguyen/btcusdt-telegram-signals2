import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution import equity


class EquityHistoryTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"equity.sqlite3"
        self.db=sqlite3.connect(self.path)
        equity.ensure(self.db)
        self.db.commit()

    def record(self, at, mark, position="0", average="0", realized="0", fees="0"):
        with self.db:
            return equity.record(self.db,initial_capital="100",position=position,average=average,
                realized=realized,fees=fees,mark_price=mark,candle_close_ms=at,observed_at_ms=at,
                dataset_version="sha256:"+"a"*64)

    def test_persists_equity_and_calculates_high_water_drawdown(self):
        self.record(1_800_000_000_000,"100","1","100")
        self.record(1_800_000_900_000,"110","1","100")
        result=self.record(1_800_001_800_000,"90","1","100")
        self.assertEqual(result["latest"]["equity"],"90")
        self.assertEqual(result["latest"]["highWaterMark"],"110")
        self.assertEqual(result["latest"]["drawdownUsdt"],"20")
        self.assertAlmostEqual(float(result["maxDrawdownPct"]),20/110*100)

    def test_daily_baseline_is_persisted_once_and_daily_loss_is_positive_loss(self):
        start=1_800_000_000_000
        self.record(start,"100","1","100")
        result=self.record(start+900_000,"94","1","100")
        self.assertEqual(result["dailyBaselineKind"],"FIRST_OBSERVED_UTC_DAY")
        self.assertEqual(result["dailyLossUsdt"],"6")
        self.assertEqual(result["dailyPnlUsdt"],"-6")

    def test_mark_to_market_includes_short_and_long_positions(self):
        start=1_800_000_000_000
        long=self.record(start,"110","0.1","100")
        self.assertEqual(long["latest"]["unrealizedPnl"],"1.0")
        self.assertEqual(long["latest"]["equity"],"101.0")
        short=self.record(start+900_000,"110","-0.1","100")
        self.assertEqual(short["latest"]["unrealizedPnl"],"-1.0")
        self.assertEqual(short["latest"]["equity"],"99.0")

    def test_duplicate_snapshots_are_idempotent(self):
        at=1_800_000_000_000
        self.record(at,"100")
        self.record(at,"100")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM paper_equity_history").fetchone()[0],1)

    def test_initial_capital_is_persisted_and_cannot_silently_rebase_equity(self):
        at=1_800_000_000_000
        self.record(at,"100")
        with self.assertRaisesRegex(ValueError,"PAPER_INITIAL_CAPITAL_CHANGED"):
            with self.db:
                equity.record(self.db,initial_capital="200",position="0",average="0",
                    realized="0",fees="0",mark_price="100",candle_close_ms=at+900_000,
                    observed_at_ms=at+900_000,dataset_version="sha256:"+"b"*64)

    def test_max_drawdown_daily_loss_and_exposure_limits_are_enforced(self):
        from decimal import Decimal
        at=1_800_000_000_000
        self.record(at,"100","1","100")
        self.record(at+900_000,"110","1","100")
        self.record(at+1_800_000,"80","1","100")
        limits={"maxDrawdownPct":Decimal("20"),"maxDailyLossUsdt":Decimal("95"),
                "maxExposureUsdt":Decimal("1000")}
        with self.db:
            reason, kill=equity.block_reason(self.db,target_position="0",limit_price="80",
                limits=limits,require_limits=True,now_ms=at+1_800_000)
        self.assertEqual(reason,"MAX_DRAWDOWN_LIMIT")
        self.assertEqual(kill,"MAX_DRAWDOWN_LIMIT")

    def test_daily_loss_limit_blocks_and_exposure_limit_rejects_without_killing(self):
        from decimal import Decimal
        at=1_800_000_000_000
        self.record(at,"100","0")
        self.record(at+900_000,"89","0",realized="-11")
        limits={"maxDrawdownPct":Decimal("90"),"maxDailyLossUsdt":Decimal("10"),
                "maxExposureUsdt":Decimal("10")}
        with self.db:
            reason, kill=equity.block_reason(self.db,target_position="0",limit_price="89",
                limits=limits,require_limits=True,now_ms=at+900_000)
        self.assertEqual(reason,"DAILY_LOSS_LIMIT")
        self.assertEqual(kill,"DAILY_LOSS_LIMIT")
        exposure_limits={**limits,"maxDailyLossUsdt":Decimal("100")}
        with self.db:
            reason, kill=equity.block_reason(self.db,target_position="0.2",limit_price="89",
                limits=exposure_limits,require_limits=True,now_ms=at+900_000)
        self.assertEqual(reason,"MAX_EXPOSURE_LIMIT")
        self.assertIsNone(kill)

    def test_out_of_order_snapshot_is_rejected_without_corrupting_equity_history(self):
        start=1_800_000_000_000
        self.record(start+900_000,"100")
        with self.assertRaisesRegex(ValueError,"OUT_OF_ORDER_EQUITY_SNAPSHOT"):
            with self.db:
                equity.record(self.db,initial_capital="100",position="0",average="0",
                    realized="0",fees="0",mark_price="90",candle_close_ms=start,
                    observed_at_ms=start,dataset_version="sha256:"+"b"*64)
        result=equity.snapshot(self.db,start+900_000)
        self.assertEqual(len(result["points"]),1)
        self.assertEqual(result["maxDrawdownUsdt"],"0")


if __name__=="__main__":
    unittest.main()
