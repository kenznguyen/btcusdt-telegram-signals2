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
        self.record(1_800_000_000_000,"100")
        self.record(1_800_000_900_000,"110")
        result=self.record(1_800_001_800_000,"90")
        self.assertEqual(result["latest"]["equity"],"100")
        self.assertEqual(result["latest"]["highWaterMark"],"110")
        self.assertEqual(result["latest"]["drawdownUsdt"],"10")
        self.assertAlmostEqual(float(result["maxDrawdownPct"]),10/110*100)

    def test_daily_baseline_is_persisted_once_and_daily_loss_is_positive_loss(self):
        start=1_800_000_000_000
        self.record(start,"100")
        result=self.record(start+900_000,"94")
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


if __name__=="__main__":
    unittest.main()
